import argparse
from pathlib import Path
from datetime import datetime

import logging
import warnings
from tqdm import tqdm
from itertools import chain

import numpy as np
import quantities as pq

from elephant.spike_train_generation import (homogeneous_gamma_process,
                                             homogeneous_poisson_process)
from elephant.statistics import isi, cv2

import matplotlib.pyplot as plt

from alpaca import Provenance, activate, save_provenance, alpaca_setting
from alpaca.utils.files import get_file_name

from neao_annotation import annotate_neao


warnings.filterwarnings('ignore', category=DeprecationWarning)


# Apply the Provenance decorator and NEAO annotations to the functions used

homogeneous_poisson_process = annotate_neao(
    "neao_steps:GenerateStationaryPoissonProcess",
    arguments={'rate': "neao_params:FiringRate"},
    returns={0: "neao_data:SpikeTrain"})(homogeneous_poisson_process)
homogeneous_poisson_process = Provenance(inputs=[])(homogeneous_poisson_process)

homogeneous_gamma_process = annotate_neao(
    "neao_steps:GenerateStationaryGammaProcess",
    arguments={'a': "neao_params:ShapeFactor", 'b': "neao_params:FiringRate"},
    returns={0: "neao_data:SpikeTrain"})(homogeneous_gamma_process)
homogeneous_gamma_process = Provenance(inputs=[])(homogeneous_gamma_process)

isi = annotate_neao(
    "neao_steps:ComputeInterspikeIntervals",
    arguments={'spiketrain': "neao_data:SpikeTrain"},
    returns={0: "neao_data:InterspikeIntervals"})(isi)
isi = Provenance(inputs=['spiketrain'])(isi)

cv2 = annotate_neao("neao_steps:ComputeCV2",
                    arguments={'time_intervals':
                                   "neao_data:InterspikeIntervals"},
                    returns={0: "neao_data:CV2"})(cv2)
cv2 = Provenance(inputs=['time_intervals'])(cv2)

plt.Figure.savefig = Provenance(inputs=['self'], file_output=['fname'])(plt.Figure.savefig)


# Setup logging
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(module)s - %(levelname)s: %(message)s")


@Provenance(inputs=['isi_times'])
@annotate_neao("neao_steps:ComputeInterspikeIntervalHistogram",
               arguments={'isi_times': "neao_data:InterspikeIntervals",
                          'bin_size': "neao_params:BinSize"},
               returns={0: "neao_data:InterspikeIntervalHistogram"})
def isi_histogram(isi_times, bin_size=5*pq.ms, max_time=500*pq.ms):
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


@Provenance(inputs=['counts', 'edges', 'cv_value'])
def plot_isi_histogram(counts, edges, cv_value):
    """
    Plot the ISI histogram together with the CV2 value.
    """
    fig, ax = plt.subplots()
    bar_widths = np.diff(edges)
    ax.bar(edges[:-1].magnitude, height=counts, align='edge', width=bar_widths)
    ax.set_xlabel(f"Inter-spike interval ({edges.dimensionality.string})")
    ax.set_ylabel("Count")
    ax.set_title(f"ISI variability: {cv_value}")
    return fig, ax


def main(output_dir, rate, t_stop, n_spiketrains=100):

    # Use builtin hash for matplotlib objects
    alpaca_setting('use_builtin_hash_for_module', ['matplotlib'])
    alpaca_setting('authority', "fz-juelich.de")

    # Activate provenance tracking
    activate()

    # Generate spike trains
    poisson_process = [homogeneous_poisson_process(rate=rate, t_stop=t_stop)
                       for _ in range(n_spiketrains)]

    gamma_process = [homogeneous_gamma_process(a=1, b=rate, t_stop=t_stop)
                     for _ in range(n_spiketrains)]

    # For each spiketrain, compute the ISI histogram and variability statistics
    for idx, spiketrain in enumerate(
            tqdm(chain(poisson_process, gamma_process), total=2*n_spiketrains,
                 desc="Processing spiketrains")):

        # Define output file name
        out_file = output_dir / f"{idx+1}.png"

        # Compute the ISIs
        isi_times = isi(spiketrain)

        # Compute ISI variability
        variability = cv2(isi_times)

        # Compute the histogram of the ISIs
        isi_counts, isi_edges = isi_histogram(isi_times)

        # Plot and save as PNG
        figure, ax = plot_isi_histogram(isi_counts, isi_edges, variability)
        figure.savefig(out_file)
        plt.close(figure)

    # Save the provenance as PROV
    prov_file_format = "ttl"
    prov_file = get_file_name(__file__, output_dir=output_dir,
                              extension=prov_file_format)
    save_provenance(prov_file)


if __name__ == "__main__":

    # Parse inputs to the script
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('--n_spiketrains', type=int, required=False,
                        default=100)
    parser.add_argument("--rate", type=int, required=False, default=10)
    parser.add_argument("--t_stop", type=int, required=False, default=100)
    args = parser.parse_args()

    # Define values passed as parameters to the main function, and create any
    # directories needed
    output_dir = Path(args.output_path).expanduser().absolute()
    output_dir.mkdir(parents=True, exist_ok=True)
    rate = args.rate * pq.Hz
    t_stop = args.t_stop * pq.s
    n_spiketrains = args.n_spiketrains

    # Run the analysis
    start = datetime.now()
    logging.info(f"Start time: {start}")

    main(output_dir, rate=rate, t_stop=t_stop, n_spiketrains=n_spiketrains)

    end = datetime.now()
    logging.info(f"End time: {end}; Total processing time:{end - start}")
