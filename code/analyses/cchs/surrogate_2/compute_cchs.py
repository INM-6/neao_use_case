import argparse
import itertools
from pathlib import Path
from datetime import datetime
import logging
from tqdm import tqdm

from collections import defaultdict

import random
import numpy as np
import quantities as pq

import neo
from neo.utils import add_epoch, get_events, cut_segment_by_epoch

from elephant.spike_train_correlation import cross_correlation_histogram
from elephant.spike_train_surrogates import trial_shifting
from elephant.conversion import BinnedSpikeTrain
from elephant.statistics import mean_firing_rate
from viziphant.spike_train_correlation import plot_cross_correlation_histogram

import matplotlib.pyplot as plt

from alpaca import Provenance, activate, alpaca_setting, save_provenance
from alpaca.utils import get_file_name

from neao_annotation import annotate_neao

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()


SEED = 689


# Apply the decorator to the functions used

add_epoch = Provenance(inputs=['segment', 'event1', 'event2'])(add_epoch)

get_events = Provenance(inputs=['container'],
                        container_output=True)(get_events)

cut_segment_by_epoch = Provenance(inputs=['seg', 'epoch'],
                                  container_output=True)(cut_segment_by_epoch)

BinnedSpikeTrain.__init__ = annotate_neao(
    "neao:ApplySpikeTrainBinning",
    arguments={'bin_size': "neao:BinSize"},
    returns={None: "neao:BinnedSpikeTrain"})(BinnedSpikeTrain.__init__)
BinnedSpikeTrain.__init__ = Provenance(
    inputs=[],
    container_input=['spiketrains'],
    container_output=0)(BinnedSpikeTrain.__init__)

cross_correlation_histogram = annotate_neao(
    "neao:ComputeCrossCorrelationHistogram",
    arguments={'bin_size': "neao:BinSize"},
    returns={0: "neao:CrossCorrelationHistogram"})(cross_correlation_histogram)
cross_correlation_histogram = Provenance(
    inputs=['binned_spiketrain_i',
            'binned_spiketrain_j'])(cross_correlation_histogram)

trial_shifting = annotate_neao(
    "neao:GenerateTrialShiftingSurrogate",
    arguments={'dither': "neao:DitheringTime"},
    returns={None: "neao:SpikeTrainSurrogate"})(trial_shifting)
trial_shifting = Provenance(inputs=[], container_input=['spiketrains'],
                            container_output=1)(trial_shifting)

plt.Figure.savefig = Provenance(
    inputs=['self'], file_output=['fname'])(plt.Figure.savefig)


# Setup logging
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(module)s - %(levelname)s: %(message)s")


@Provenance(inputs=[], file_input=['file_name'])
def load_data(file_name):
    """
    Reads all blocks in the NIX data file `file_name`.
    """
    with neo.NixIO(str(file_name)) as session:
        block = session.read_block()
    return block


@Provenance(inputs=[], container_input=['trials'], container_output=1)
def get_suas_trials(trials, min_snr=5.0, min_firing_rate=5 * pq.Hz):
    """
    This function takes a list of `neo.Segment`s containing trial-level data,
    and returns a dictionary with the `neo.SpikeTrain` objects of each trial
    for a selected subset of SUA units.

    The `neo.SpikeTrain`s are expected to have annotations `sua == True` and
    `SNR`. The parameter `min_snr` will be compared against the latter to
    filter out the units. The parameter `min_firing_rate` filters out
    spike trains with a mean firing rate in the trial less than its value.

    The return object is a dictionary where the unit id is the key and the
    values are a list of `neo.SpikeTrain`s, each containing the data of a
    single trial for that SUA unit.

    If a unit does not have data available for all the trials, it is not
    included.
    """
    ids_by_trial = []
    suas = defaultdict(list)

    # For each selected SUA, store the `neo.SpikeTrain` of each trial in a
    # list. The overall unit indexes for each trial are stored. Later, this
    # will be used to filter out only the units that fit the selection
    # criteria in all trials.
    for trial in trials:
        ids_by_trial.append(set())
        for st in trial.spiketrains:
            # Select SUAs with minimum SNR
            if st.annotations.get('sua') and \
                    st.annotations.get('SNR') >= min_snr:
                # Compute firing rate and filter
                firing_rate = mean_firing_rate(st)
                if firing_rate >= min_firing_rate:
                    st_id = st.annotations['id']
                    ids_by_trial[-1].add(st_id)
                    suas[st_id].append(st)

    # Intersect all sets to find units that meet the selection criteria for
    # all trials
    unit_ids = set.intersection(*ids_by_trial)

    # Filter out the SUAs
    selected_suas = {st_id: sts for st_id, sts in suas.items() if
                     st_id in unit_ids}

    return selected_suas


@Provenance(inputs=['cch'], container_input=['surrogate_cchs'])
def plot_cch_with_significance(cch, surrogate_cchs,
                               significance_threshold=3.0,
                               max_lag=200 * pq.ms,
                               title=None):
    fig, axes = plt.subplots()

    cch_mean = np.mean(surrogate_cchs, axis=0)
    cch_sd = np.std(surrogate_cchs, axis=0, ddof=1)
    cch_threshold = cch_mean + significance_threshold * cch_sd

    # Viziphant function expects each CCH to be a `neo.AnalogSignal`
    # Duplicate using the original CCH to keep the annotations
    cch_mean = cch.duplicate_with_new_data(cch_mean)
    cch_threshold = cch.duplicate_with_new_data(cch_threshold)

    kwargs = {}
    if title is not None:
        kwargs['title'] = title

    axes = plot_cross_correlation_histogram(
        [cch, cch_mean, cch_threshold], axes=axes, units='ms',
        maxlag=max_lag,
        legend=['Raw CCH', 'Mean surrogate CCH', 'Significance threshold'],
        **kwargs)

    return fig, axes


@Provenance(inputs=[], container_input=['cchs'])
@annotate_neao("neao:ApplySum", returns={0: "neao:CrossCorrelationHistogram"})
def aggregate_cchs(cchs, max_lag, n_lags):
    """
    Sums a list of trial-level cross-correlation histograms, to obtain an
    aggregate across all trials. Each element in `cchs` is the
    cross-correlation histogram computed between a pair of units in a single
    trial.
    """
    cch_shape = cchs[0].shape
    num_bins = 2 * n_lags + 1

    # Reshape
    if cch_shape[0] != num_bins:
        # Surrogate CCHs:.must be rescaled
        cchs = [surr_cch.reshape(num_bins, -1) for surr_cch in cchs]

    agg_cch = neo.AnalogSignal(np.zeros(num_bins) * pq.dimensionless,
                               sampling_period=cchs[0].sampling_period,
                               t_start=-max_lag)
    for cch in cchs:
        agg_cch += cch
        agg_cch.annotations.update(cch.annotations)
    return agg_cch


def main(session_file, output_dir, bin_size, max_lag, n_surrogates):
    # Use builtin hash for matplotlib objects
    alpaca_setting('use_builtin_hash_for_module', ['matplotlib'])

    # Activate provenance tracking
    activate()

    # *** GLOBAL PARAMETERS **

    min_firing_rate = 10 * pq.Hz    # Minimum mean firing rate to select SUA
    min_snr = 3                   # Minimum SNR to select SUA

    event_label = 'CUE-OFF'         # Label of event of interest
    trial_type = 'PGLF'   # Trial type(s) of interest
    t_pre = 0.3 * pq.s              # Time before event where trial data starts
    t_post = 0.5 * pq.s             # Time after event where trial data ends

    # Parameters for the surrogate function
    surr_parameters = {'dither': 15 * pq.ms,
                       'n_surrogates': n_surrogates}

    # Parameters to compute the CCH
    n_lags = int((max_lag / bin_size).simplified)
    cch_parameters = {'window': [-n_lags, n_lags],
                      'border_correction': True}

    # *** ANALYSIS ***

    # Set seeds for reproducible surrogate generation
    random.seed(SEED)
    np.random.seed(SEED)

    # Get session repository and directory to write the files for the session
    session_name = session_file.stem
    session_dir = output_dir / session_name
    session_dir.mkdir(exist_ok=True)

    if rank == 0:
        # Load the Neo Block with the data
        logging.info(f"Loading data file: {session_file}")
        block = load_data(session_file)

        # Select the trial intervals for the analysis
        logging.info("Extracting trial data")
        start_events = get_events(block.segments[0],
                                  trial_event_labels=event_label,
                                  performance_in_trial_str='correct_trial',
                                  belongs_to_trialtype=trial_type)[0]
        trial_epochs = add_epoch(block.segments[0], start_events, pre=-t_pre,
                                 post=t_post, attach_result=False)
        trial_segments = cut_segment_by_epoch(block.segments[0], trial_epochs,
                                              reset_time=True)
        n_trials = len(trial_segments)

        # Select the data for the CCH computation
        # For each SUA, a list of `neo.SpikeTrain`s, each containing the data
        # of a single trial, is returned.
        logging.info("Selecting SUAs for analysis")

        suas = get_suas_trials(trial_segments, min_snr=min_snr,
                               min_firing_rate=min_firing_rate)

        # Bin the spike trains
        # Store in a dict with the unit id as key to avoid recomputing
        logging.info("Binning spike trains")

        binned_suas = {sua_id: BinnedSpikeTrain(sua, bin_size=bin_size)
                       for sua_id, sua in suas.items()}

        # For each spike train, obtain a list of `n_surrogates`, and bin using
        # the same parameters as the original spike trains.
        # Each `BinnedSpikeTrain` object will be stored in a dictionary where
        # the unit id is the key. Each dictionary entry will have
        # `n_surrogates` `BinnedSpikeTrain`s objects, each with the
        # `n_trials` of a surrogate.
        logging.info("Generating spike train surrogates and binning")

        binned_surrogates = defaultdict(list)
        # For each unit...
        for unit, trial_suas in tqdm(suas.items(), "Unit"):
            # Obtain `n_surrogates` for the spike trains containing the trials
            # of the unit (returns list of lists; `n_surrogates` x `n_trials`)
            surrogates = trial_shifting(trial_suas, **surr_parameters)

            for surrogate in surrogates:
                # Bin and store the surrogate. Each binned spike train
                # contains all trials for that surrogate
                binned_surrogate = BinnedSpikeTrain(surrogate,
                                                    bin_size=bin_size)
                binned_surrogates[unit].append(binned_surrogate)

        # Define the pairs which to compute the CCH for
        pairs = list(itertools.permutations(suas.keys(), 2))

        n_pairs = len(pairs)
        if n_pairs < nprocs:
            raise Exception(f"Need {n_pairs} processes for parallelization. "
                            "Check your MPI run configuration.")

    else:
        binned_surrogates = None
        binned_suas = None
        pairs = None
        n_trials = None

    binned_suas = comm.bcast(binned_suas, root=0)
    binned_surrogates = comm.bcast(binned_surrogates, root=0)
    pairs = comm.bcast(pairs, root=0)
    n_trials = comm.bcast(n_trials, root=0)

    logging.info("Computing CCHs")

    # Define the parameters used by the CCH aggregation function
    aggregation_parameters = {'max_lag': max_lag, 'n_lags': n_lags}

    # For each SUA pair...
    for idx, (unit_i, unit_j) in enumerate(pairs):
        if idx != rank:
            continue

        logging.info(f"Computing {unit_i} x {unit_j}")

        # Define title and output file name
        title = f"CCH ({unit_i} x {unit_j})"
        out_file = session_dir / f"cch_{unit_i}_{unit_j}.png"

        # Get the binned spike train for each unit in the pair
        binned_spiketrain_i = binned_suas[unit_i]
        binned_spiketrain_j = binned_suas[unit_j]

        # Get the binned surrogates for each unit in the pair
        binned_surrogates_i = binned_surrogates[unit_i]
        binned_surrogates_j = binned_surrogates[unit_j]

        # Lists to store the computed CCHs for later aggregations and
        # mean/SD estimation
        cchs = []
        surrogate_cchs = defaultdict(list)

        # For each trial...
        for trial in tqdm(range(n_trials), "Trial"):

            # Compute the CCH between the pair of units

            binned_trial_spiketrain_i = binned_spiketrain_i[trial]
            binned_trial_spiketrain_j = binned_spiketrain_j[trial]
            cch, _ = cross_correlation_histogram(binned_trial_spiketrain_i,
                                                 binned_trial_spiketrain_j,
                                                 **cch_parameters)
            cchs.append(cch)

            # Compute the CCH for each surrogate pair
            for n_surrogate in range(n_surrogates):
                binned_trial_surrogate_i = \
                    binned_surrogates_i[n_surrogate][trial]
                binned_trial_surrogate_j = \
                    binned_surrogates_j[n_surrogate][trial]
                surr_cch, _ = cross_correlation_histogram(
                    binned_trial_surrogate_i, binned_trial_surrogate_j,
                    **cch_parameters)
                surrogate_cchs[n_surrogate].append(surr_cch)

        # Aggregate CCH across trials
        agg_cch = aggregate_cchs(cchs, **aggregation_parameters)

        # Aggregate each surrogate CCH across trials
        agg_surr_cchs = [aggregate_cchs(cchs, **aggregation_parameters)
                         for cchs in surrogate_cchs.values()]

        fig, _ = plot_cch_with_significance(agg_cch, agg_surr_cchs,
                                            max_lag=max_lag, title=title)
        # Save plot as PNG
        fig.savefig(out_file, format="png", facecolor="white")
        plt.close(fig)

    # Save provenance information as Turtle file
    prov_file_format = "ttl"
    prov_file_suffix = f"_{rank}" if rank > 0 else None
    prov_file = get_file_name(__file__, output_dir=session_dir,
                              extension=prov_file_format,
                              suffix=prov_file_suffix)

    logging.info(f"Saving provenance to {prov_file}")

    save_provenance(prov_file, file_format=prov_file_format,
                    show_progress=True)


if __name__ == "__main__":
    # Parse inputs to the script
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('--bin_size', type=int, required=False, default=1)
    parser.add_argument('--max_lag', type=int, required=False, default=200)
    parser.add_argument('--n_surrogates', type=int, required=False,
                        default=1000)
    parser.add_argument('input', metavar='input', nargs=1)
    args = parser.parse_args()

    # Define values passed as parameters to the main function, and create any
    # directories needed
    session_file = Path(args.input[0]).expanduser().absolute()
    output_dir = Path(args.output_path).expanduser().absolute()
    output_dir.mkdir(parents=True, exist_ok=True)
    max_lag = args.max_lag * pq.ms
    bin_size = args.bin_size * pq.ms
    n_surrogates = args.n_surrogates

    # Run the analysis
    start = datetime.now()
    logging.info(f"Start time: {start}")

    main(session_file, output_dir, bin_size=bin_size, max_lag=max_lag,
         n_surrogates=n_surrogates)

    end = datetime.now()
    logging.info(f"End time: {end}; Total processing time:{end - start}")
