import argparse
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

from elephant.statistics import isi, mean_firing_rate
from elephant.spike_train_surrogates import trial_shifting

import matplotlib.pyplot as plt

from alpaca import Provenance, activate, alpaca_setting, save_provenance
from alpaca.utils import get_file_name

from neao_annotation import annotate_neao


SEED = 689


# Apply the decorator to the functions used

add_epoch = Provenance(inputs=['segment', 'event1', 'event2'])(add_epoch)

get_events = Provenance(inputs=['container'],
                        container_output=True)(get_events)

cut_segment_by_epoch = Provenance(inputs=['seg', 'epoch'],
                                  container_output=True)(cut_segment_by_epoch)

trial_shifting = annotate_neao(
    "neao_steps:GenerateTrialShiftingSurrogate",
    arguments={
        'spiketrains': "neao_data:SpikeTrain",
        'dither': "neao_params:DitheringTime"},
    returns={'***': "neao_data:SpikeTrainSurrogate"})(trial_shifting)
trial_shifting = Provenance(inputs=[], container_input=['spiketrains'],
                            container_output=1)(trial_shifting)


isi = annotate_neao(
    "neao_steps:ComputeInterspikeIntervals",
    returns={0: "neao_data:InterspikeIntervals"})(isi)
isi = Provenance(inputs=['spiketrain'])(isi)


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
def get_suas_trials(trials, min_snr=5.0, min_firing_rate=20*pq.Hz):
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
        cur_trial_ids = set()
        for st in trial.spiketrains:
            # Select SUAs with minimum SNR
            if st.annotations.get('sua') and \
                    st.annotations.get('SNR') >= min_snr:
                # Compute firing rate and filter
                firing_rate = mean_firing_rate(st)
                if firing_rate >= min_firing_rate:
                    st_id = st.annotations['id']
                    cur_trial_ids.add(st_id)
                    suas[st_id].append(st)
        ids_by_trial.append(cur_trial_ids)

    # Intersect all sets to find units that meet the selection criteria for
    # all trials
    unit_ids = set.intersection(*ids_by_trial)

    # Filter out the SUAs
    selected_suas = {st_id: sts for st_id, sts in suas.items() if
                     st_id in unit_ids}

    return selected_suas


@Provenance(inputs=['isi_times'])
@annotate_neao("neao_steps:ComputeInterspikeIntervalHistogram",
               arguments={'bin_size': "neao_params:BinSize"},
               returns={0: "neao_data:InterspikeIntervalHistogram"})
def isi_histogram(isi_times, bin_size=5*pq.ms, max_time=200*pq.ms):
    """
    Compute an ISI histogram from an array of ISI times.
    """
    upper_bound = max_time.rescale(bin_size.units).magnitude.item()
    step = bin_size.magnitude.item()
    edges = np.arange(0, upper_bound, step)

    if isinstance(isi_times, pq.Quantity):
        times = isi_times.rescale(bin_size.units).magnitude
    elif isinstance(isi_times, np.ndarray):
        times = isi_times
    else:
        raise TypeError("ISI times are not `pq.Quantity` or `np.ndarray`!")

    counts, edges = np.histogram(times, bins=edges)
    return counts, (edges * bin_size.units)


@Provenance(inputs=['sua_histogram', 'edges', 'mean', 'std_dev'])
def plot_isi_histogram(sua_histogram, edges, mean, std_dev, title):
    """
    Plot the ISI histogram as a bar plot, together with a mean +/-
    standard deviation area as step plot.
    """
    fig, ax = plt.subplots()
    x = edges[:-1].magnitude
    bar_widths = np.diff(edges)

    # Bar plot
    ax.bar(x, sua_histogram, align='edge', width=bar_widths, alpha=0.40,
           zorder=1, color="C0", label="Data")

    # Mean step line
    ax.step(x, mean, where="post", linestyle="solid", lw=0.75, zorder=3,
            color="C1", label="$\\mathrm{{Surrogate}\\:{mean}\\pm{SD}}$")

    # +/- SD area
    ax.fill_between(x, mean + std_dev, mean - std_dev, step="post", alpha=0.60,
                    lw=0, zorder=2, color="C1")

    ax.legend()
    ax.set_xlabel(f"Inter-spike interval ({edges.dimensionality.string})")
    ax.set_ylabel("Count")
    ax.set_title(title)

    return fig


@Provenance(inputs=['histograms'])
def aggregate_isi_histograms(*histograms):
    stacked = np.vstack(histograms)
    return np.sum(stacked, axis=0)


@Provenance(inputs=['arrays'])
def mean_and_sd(*arrays, axis=0):
    stacked = np.vstack(arrays)
    mean = np.mean(stacked, axis=axis)
    std_dev = np.std(stacked, axis=axis)
    return mean, std_dev


def main(session_file, output_dir, bin_size, max_time, n_surrogates,
         min_firing_rate=15*pq.Hz, min_snr=5.0):

    # Use builtin hash for matplotlib objects
    alpaca_setting('use_builtin_hash_for_module', ['matplotlib'])
    alpaca_setting('authority', "fz-juelich.de")

    # Activate provenance tracking
    activate()

    # Parameters for the surrogate function
    surr_parameters = {'dither': 25 * pq.ms,
                       'n_surrogates': n_surrogates}

    # Parameters for the ISI histogram function
    histogram_parameters = {'bin_size': bin_size,
                            'max_time': max_time}

    # *** ANALYSIS ***

    # Set seeds for reproducible surrogate generation
    random.seed(SEED)
    np.random.seed(SEED)

    # Get session repository and directory to write the files for the session
    session_name = session_file.stem
    session_dir = output_dir / session_name
    session_dir.mkdir(exist_ok=True)

    logging.info(f"Loading data file: {session_file}")
    block = load_data(session_file)

    # Select the trial intervals for the analysis
    logging.info("Extracting trial data")
    start_events = get_events(block.segments[0],
                              trial_event_labels='TS-ON',
                              performance_in_trial_str='correct_trial')[0]
    end_events = get_events(block.segments[0],
                            trial_event_labels='STOP',
                            performance_in_trial_str='correct_trial')[0]
    trial_epochs = add_epoch(block.segments[0], start_events, end_events,
                             attach_result=False)
    trial_segments = cut_segment_by_epoch(block.segments[0], trial_epochs,
                                          reset_time=True)

    # Select the data for the ISI histogram computation
    # For each SUA, a list of `neo.SpikeTrain`s, each containing the data
    # of a single trial, is returned.
    logging.info("Selecting SUAs for analysis")

    suas = get_suas_trials(trial_segments, min_snr=min_snr,
                           min_firing_rate=min_firing_rate)

    logging.info(f"SUAs selected: {','.join(suas.keys())}")

    # For each unit
    for unit, trial_suas in tqdm(suas.items(), "Unit"):

        # Define title and output file name
        title = f"{session_name} - {unit}"
        out_file = session_dir / f"{unit}.png"
        out_file.parents[0].mkdir(parents=True, exist_ok=True)

        all_sua_histograms = list()
        all_sua_edges = list()

        # {surr_idx_1: [surr_trial_1, surr_trial_2, ..., surr_trial_Nt],
        #  surr_idx_2: [surr_trial_1, surr_trial_2, ..., surr_trial_Nt],
        #  ...
        #  surr_idx_N: [surr_trial_1, surr_trial_2, ..., surr_trial_Nt]}
        # where N = number of surrogates and Nt = number of trials
        all_surrogate_histograms = defaultdict(list)

        # Obtain `n_surrogates` for the spike trains containing the trials
        # of the unit (returns list of lists; `n_surrogates` x `n_trials`)
        surrogates = trial_shifting(trial_suas, **surr_parameters)

        # For the spike train of each trial of that unit...
        for trial, sua in enumerate(trial_suas):

            # Compute the ISI histogram for the spike train and store
            sua_isis = isi(sua)
            sua_histogram, sua_edges = isi_histogram(sua_isis,
                                                     **histogram_parameters)
            all_sua_histograms.append(sua_histogram)
            all_sua_edges.append(sua_edges)

            # For each surrogate, compute the ISI histogram of the trial
            for idx, surrogate in enumerate(surrogates):
                trial_surrogate = surrogate[trial]
                surrogate_isis = isi(trial_surrogate)
                surrogate_histogram, _ = isi_histogram(surrogate_isis,
                                                       **histogram_parameters)
                all_surrogate_histograms[idx].append(surrogate_histogram)

        # Aggregate ISI histograms of the SUA across trials
        agg_sua_histogram = aggregate_isi_histograms(*all_sua_histograms)

        # Aggregate each surrogate ISI histogram across trials
        agg_surr_histograms = [aggregate_isi_histograms(*surrogate_histograms)
                               for surrogate_histograms in
                               all_surrogate_histograms.values()]

        # Compute surrogate ISI histogram statistics
        mean, std_dev = mean_and_sd(*agg_surr_histograms)

        # Plot ISI histograms from the SUA and surrogate statistics
        plot_edges = all_sua_edges[0]
        fig = plot_isi_histogram(agg_sua_histogram, plot_edges,
                                 mean=mean, std_dev=std_dev,
                                 title=title)

        # Save plot as PNG
        fig.savefig(out_file, format="png", facecolor="white")
        plt.close(fig)

    # Save provenance information as Turtle file
    prov_file_format = "ttl"
    prov_file = get_file_name(__file__, output_dir=session_dir,
                              extension=prov_file_format)

    logging.info(f"Saving provenance to {prov_file}")

    save_provenance(prov_file, file_format=prov_file_format,
                    show_progress=True)


if __name__ == "__main__":
    # Parse inputs to the script
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('--bin_size', type=int, required=False, default=5)
    parser.add_argument('--max_time', type=int, required=False,
                        default=200)
    parser.add_argument('--n_surrogates', type=int, required=False,
                        default=30)
    parser.add_argument('input', metavar='input', nargs=1)
    args = parser.parse_args()

    # Define values passed as parameters to the main function, and create any
    # directories needed
    session_file = Path(args.input[0]).expanduser().absolute()
    output_dir = Path(args.output_path).expanduser().absolute()
    output_dir.mkdir(parents=True, exist_ok=True)
    max_time = args.max_time * pq.ms
    bin_size = args.bin_size * pq.ms
    n_surrogates = args.n_surrogates

    # Run the analysis
    start = datetime.now()
    logging.info(f"Start time: {start}")

    main(session_file, output_dir, bin_size=bin_size,
         max_time=max_time, n_surrogates=n_surrogates)

    end = datetime.now()
    logging.info(f"End time: {end}; Total processing time:{end - start}")
