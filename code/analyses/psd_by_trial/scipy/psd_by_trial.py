import argparse
from pathlib import Path
from datetime import datetime
import logging
from tqdm import tqdm

import quantities as pq

import neo
from neo.utils import get_events, cut_segment_by_epoch, add_epoch

from elephant.signal_processing import butter
from scipy.signal import welch

import matplotlib.pyplot as plt

from alpaca import Provenance, activate, save_provenance, alpaca_setting
from alpaca.utils.files import get_file_name

from neao_annotation import annotate_neao


# Setup plotting style
plt.style.use(Path(__file__).parents[1] / "psd.mplstyle")


# Apply the Provenance decorator and NEAO annotations to the functions used

butter = annotate_neao(
    "neao_steps:ApplyButterworthFilter",
    arguments={'lowpass_frequency': "neao_params:LowPassFrequencyCutoff",
               'highpass_frequency': "neao_params:HighPassFrequencyCutoff"})(butter)
butter = Provenance(inputs=['signal'])(butter)

welch = annotate_neao(
    "neao_steps:ComputePowerSpectralDensityWelch",
    arguments={'nperseg': "neao_params:WindowLengthSamples",
               'noverlap': "neao_params:WindowOverlapSamples",
               'fs': "neao_params:SamplingFrequency",
               'window': "neao_params:WindowFunction"},
    returns={1: "neao_data:PowerSpectralDensity"})(welch)
welch = Provenance(inputs=['x'])(welch)


add_epoch = Provenance(inputs=['segment', 'event1', 'event2'])(add_epoch)

get_events = Provenance(inputs=['container'],
                        container_output=True)(get_events)

cut_segment_by_epoch = Provenance(inputs=['seg', 'epoch'],
                                  container_output=True)(cut_segment_by_epoch)

neo.AnalogSignal.downsample = annotate_neao(
    "neao_steps:ApplyDownsampling",
    arguments={'downsampling_factor':
                   "neao_params:DownsampleFactor"})(neo.AnalogSignal.downsample)
neo.AnalogSignal.downsample = Provenance(inputs=['self'])(neo.AnalogSignal.downsample)

plt.Figure.savefig = Provenance(inputs=['self'], file_output=['fname'])(plt.Figure.savefig)


# Setup logging
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(module)s - %(levelname)s: %(message)s")


@Provenance(inputs=[], file_input=['file_name'])
def load_data(file_name):
    """
    Reads all blocks in the NIX data file `file_name`.
    """
    with neo.NixIO(str(file_name), 'ro') as session:
        block = session.read_block()
    return block


@Provenance(inputs=['freqs', 'psd'])
def plot_psds(freqs, psd, title=None, freq_range=None, **kwargs):
    """
    Plot the PSD result, with an optional title and frequency range.
    """
    fig, axes = plt.subplots(1, 1, figsize=(15, 7),
                             constrained_layout=False)

    axes.semilogy(freqs, psd, **kwargs)
    axes.set_ylabel("Power [$\\mathrm{\\frac{{\\mu}V^{2}}{Hz}}$]")
    axes.set_xlabel("Frequency [Hz]")

    if freq_range:
        axes.set_xlim(freq_range)

    if title:
        fig.suptitle(title)

    return fig, axes


def main(session_file, output_dir):
    frequency_resolution = 2   # In Hz
    overlap = 0.5

    # Use builtin hash for matplotlib objects
    alpaca_setting('use_builtin_hash_for_module', ['matplotlib'])
    alpaca_setting('authority', "fz-juelich.de")

    # Activate provenance tracking
    activate()

    # Load the Neo Block with the data
    logging.info(f"Processing data file: {session_file}")
    block = load_data(session_file)

    # Get session repository and directory to write the files for the session
    session_name = session_file.stem
    session_dir = output_dir / session_name
    session_dir.mkdir(exist_ok=True)

    # Select the trials for the analysis
    logging.info("Extracting trial data")
    start_events = get_events(block.segments[0], trial_event_labels='TS-ON')[0]
    stop_events = get_events(block.segments[0], trial_event_labels='STOP')[0]
    trial_epochs = add_epoch(block.segments[0], start_events, stop_events,
                             attach_result=False)
    trial_segments = cut_segment_by_epoch(block.segments[0], trial_epochs)

    # Iterate over each trial, compute the PSDs, and save the plots
    for trial in tqdm(trial_segments, desc="Computing PSD for trial"):

        # Define title and output file name
        trial_id = trial.annotations['trial_id']
        title = f"{session_name} - Trial {trial_id} (all channels)"
        out_file = session_dir / f"{trial_id}.png"

        # Filter and downsample signal
        filtered_signal = butter(trial.analogsignals[0],
                                 lowpass_frequency=250 * pq.Hz)
        downsampled_signal = filtered_signal.downsample(2)

        # Get parameters for `welch` based on the desired frequency
        # resolution
        fs = downsampled_signal.sampling_rate.rescale('Hz').magnitude
        nperseg = int(fs / frequency_resolution)

        if downsampled_signal.shape[0] >= nperseg:
            # Compute the PSD if enough data
            noverlap = int(nperseg * overlap)
            freqs, psd = welch(downsampled_signal, fs=fs, nperseg=nperseg,
                               noverlap=noverlap, axis=0)

            # Plot and save as PNG
            fig, axes = plot_psds(freqs, psd, title=title, color='blue',
                                  lw=1, freq_range=(0, 100))
            fig.savefig(out_file, format="png", facecolor="white")
            plt.close(fig)

        else:
            logging.info(f"Trial {trial_id} is too short to compute the PSD.")

        del filtered_signal
        del downsampled_signal

    # Save provenance information as Turtle file
    prov_file_format = "ttl"
    prov_file = get_file_name(__file__, output_dir=session_dir,
                              extension=prov_file_format)
    save_provenance(prov_file, file_format=prov_file_format)


if __name__ == "__main__":

    # Parse inputs to the script
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('input', metavar='input', nargs=1)
    args = parser.parse_args()

    # Define values passed as parameters to the main function, and create any
    # directories needed
    session_file = Path(args.input[0]).expanduser().absolute()
    output_dir = Path(args.output_path).expanduser().absolute()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run the analysis
    start = datetime.now()
    logging.info(f"Start time: {start}")

    main(session_file, output_dir)

    end = datetime.now()
    logging.info(f"End time: {end}; Total processing time:{end - start}")
