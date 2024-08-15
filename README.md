# Neuroelectrophysiology Analysis Ontology Use Case

Repository containing the code necessary to reproduce the results of the 
Neuroelectrophysiology Analysis Ontology (NEAO) manuscript.


## Table of contents
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Code repository](#code-repository)
  - [How to run](#how-to-run)
  - [Outputs](#outputs)
  - [Acknowledgments](#acknowledgments)
  - [License](#license)


## Prerequisites

### Clone the repository to a local folder

This repository must be cloned to a local folder. This can be done using the 
`git` CLI client:

```bash
git clone https://github.com/INM-6/neao_use_case.git
```

### Data

To run the analyses, the public experimental datasets availabe at 
[https://doi.gin.g-node.org/10.12751/g-node.f83565](https://doi.gin.g-node.org/10.12751/g-node.f83565) must be downloaded.

The scripts use the datasets in the NIX format, without the full (30 kHz)
bandwidth neural signal. The file used in the analyses with experimental data
is **i140703-001_no_raw.nix** that can be directly downloaded [here](https://gin.g-node.org/INT/multielectrode\_grasp/src/a6d508be099c41b4047778bc2de55ac216f4e673/datasets\_nix/i140703-001\_no\_raw.nix). 
You can also follow the [instructions on the GIN repository](https://gin.g-node.org/INT/multielectrode_grasp)
to download the files to a local repository folder using the `gin` client.

The NIX file must be downloaded/copied into the folder `/data` with respect
to the root of this repository. This allows running the analyses using the
`bash` script provided. If the data was downloaded using the `gin` client, a 
symbolic link can be created to the path where the GIN repository was cloned 
in your system (subfolder `datasets_nix`):

```bash
ln -s /path/to/multielectrode_grasp/datasets_nix ./data
```


## Installation

### Requirements

Project requires Python 3.9 and the following packages:

- scipy
- numpy
- matplotlib
- nixio
- neo
- elephant
- viziphant
- odml
- alpaca-prov
- multipledispatch
- gastrodon
- pytest (only if running the code tests)

The code was run using Ubuntu 18.04.6 LTS 64-bit and `conda` 22.9.0.

### Environment

The environment can be created using `conda` with the template in the
`/environment` folder. For instructions on how to install `conda` in your
system, please check the `conda` [documentation](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

For convenience, the environment can be created using a `bash` script (this 
rewrites existing versions of the environment):

```bash
./create_env.sh
```

### GraphDB Free

The use case describes how to query the provenance information structured in
RDF files and annotated with the NEAO. To integrate the provenance captured by
Alpaca during the execution of each analysis script and execute SPARQL queries,
a triple store must be available. This work used the Ontotext GraphDB Free 
edition (version 10.1.0, with RDF4J 4.2.0).

GraphDB Free needs to be installed locally in your system. To download and
install, follow the instructions on [https://www.ontotext.com/products/graphdb/download](https://www.ontotext.com/products/graphdb/download).

To import data, GraphDB must have access to a writable folder. In Ubuntu, this
is usually `$HOME\.graphdb` (more details [here](https://graphdb.ontotext.com/documentation/10.1/directories-and-config-properties.html)).
To make sure that the application points to the correct folder, a GraphDB
configuration file is provided in `/code/triple_store/config/graphdb.properties`
and can be copied to replace the default file in the GraphDB configuration
folder. In Ubuntu, the default file is `/opt/graphdb-desktop/lib/app/conf/graphdb.properties`. 
The `graphdb_setup.sh` script is provided in `/code/triple_store/` to copy the
configuration file provided to replace the GraphDB default (it will ask for
the administrator password):

```bash
cd code/triple_store
./graphdb_setup.sh
```

In Ubuntu, the `graphdb-desktop` launch application is located in
`/opt/graphdb-desktop/bin/graphdb-desktop` by default. If installing to a 
different location, the `bash` scripts need to be modified in order to run the
analyses (details below).

## Code repository

The code is organized into subfolders inside the `/code` folder:

- `analyses`: set of analyses implemented to demonstrate the use of NEAO.
              Provenance is tracked with Alpaca, and annotated with NEAO
              classes. Three main analyses are implemented, each in an 
              additional subfolder:
  - `isi_histograms`: generation of artificial spike trains using either a
                      stationary Poisson or stationary Gamma process, and
                      plotting the interspike interval histogram and CV2.
                      The analysis code is in `isi_analysis.py`.
  - `psd_by_trial`: from the Reach2Grasp dataset, plot the power spectral
                    density (PSD) of each trial in the session, using different
                    method/package combinations: Welch method implemented in
                    Elephant (`elephant_welch`), multitaper method implemented
                    in Elephant (`elephant_multitaper`), or Welch method
                    implemented in SciPy (`scipy`). The analysis code is in
                    `psd_by_trial.py` inside each folder.
  - `surrogate_isih`: from the Reach2Grasp dataset, plot the intesrpike
                      interval histogram of selected units during correct 
                      trials in the session. Compute surrogate spike trains
                      using different methods, and plot the mean and standard
                      deviation of the interspike interval histograms obtained
                      from the surrogates. The spike train surrogate generation
                      methods are uniform spike time dithering (`surrogate_1`)
                      and trial shifting (`surrogate_2`). The analysis code is
                      in `compute_isi_histograms.py` inside each folder.
- `manuscript_tables`: code to read the query results saved as CSV files, and
                       produce the tables presented in the manuscript. Each
                       `table_*.py` generates one manuscript table
                       (split into several text files, each containing a sub
                       table). Utility code shared among all scripts to format
                       the results is in `utils.py`.
- `neao_mapping`: a set of SPARQL queries to insert additional triples in the
                  triple store to map provenance information structured by
                  Alpaca into the NEAO ontology model.
                 `insert_neao_steps.sparql` adds the main relationships,
                 `insert_neao_implementation.sparql` adds the relationships
                 describing the implementation code of functions, and
                 `insert_container_outputs.sparql` adds triples for function
                 outputs stored inside collections.
- `queries`: SPARQL queries for each question regarding the analysis, which are
             presented in the manuscript. Each query will generate a CSV
             file with the raw output of the query.
- `triple_store`: Python interface to a local GraphDB triple store. For,
                  details, check the specific `README.md` file in
                  `\code\triple_store\README.md`.
- `neao_annotation.py`: implements a decorator used by all analysis scripts
                        to insert ontology annotations into the functions used
                        by the script.


## How to run

### Activate the environment

```bash
conda activate neao_use_case
```

### Check GraphDB installation (optional)

If you wish to check if GraphDB was installed properly and the triple store
is accessible, a small test suite is provided in Python and can be run using 
`pytest`. This is located in the `/code/triple_store/test` folder.

For convenience, a `bash` script is provided. It will instantiate the GraphDB 
server, perform the tests, clean the test repositories, and close the 
application:

```bash
cd code/triple_store
./test.sh
```

If all five tests pass, GraphDB and the Python interface implemented for this
project are working properly.

### Running the analyses

The first step is to execute the different Python scripts that implement some
analyses of electrophysiology data (`/code/analyses` subfolder). A `bash`
script runs all the scripts (3 examples for PSD, 2 examples for surrogates and
the ISI histograms of artificial data), and outputs the files to the
`/outputs/analyses` folder, with respect to the root of this repository:

```bash
./run_analyses.sh
```

### Inserting provenance data and ontology definitions into GraphDB

Once the analyses are run, provenance information is saved as TTL files 
together with the plots. This needs to be imported into GraphDB to be able to 
query the information using SPARQL. A `bash` script is implemented to perform
this automatically:

```bash
./insert_provenance_data.sh
```

### Executing the SPARQL queries and generating manuscript tables

After the data is imported, a `bash` script will run all SPARQL queries to 
address questions regarding the analysis and demonstrate the use of the NEAO.

This is accomplished in two steps:

1. Queries from individual SPARQL files (in `/code/queries`) are
   executed, generating CSV files with the raw query output. The CSV outputs
   are stored in the `/outputs/query_results` folder. This is accomplished
   by the `./run_queries.sh` script. By default, GraphDB is instantiated and
   closed automatically. This can be avoided by using the `running`
   argument: `./run_queries.sh running`.

2. Query outputs are transformed into visualization tables and formatted as
   LaTeX text files. These are the tables that are published in the manuscript.
   They are stored in the `/outputs/manuscript_tables` folder. This is
   accomplished by the `./generate_manuscript_tables.sh` script. 

For convenience, the whole process can be accomplished by running a single
`bash` script:

```bash
./get_manuscript_results.sh
```


## Outputs

After running the scripts above, a folder `\outputs` will be present with
all the outputs. The files used for the manuscript are included in the
Zenodo archive release, together with the code in this repository.

### Analyses

The `\outputs\analyses` folder contains the outputs from the scripts in
`\code\analyses`. The outputs are separated by sub folders:
- `isi_histograms`: outputs from the analysis in 
                    `\code\analyses\isi_histograms`. Files from `1.png`
                    to `100.png` are generated by a stationary Poisson
                    process, and from `101.png` to `200.png` by a 
                    stationary Gamma process.
- `reach2grasp`: groups the outputs of all analyses that utilized the
                 Reach2Grasp dataset. As several implementations of an
                 analysis exist, the output of each implementation is
                 collected into a different sub folder:
  - `psd_by_trial`: output from `\code\analyses\psd_by_trial\elephant_welch`
  - `psd_by_trial_2`: output from `\code\analyses\psd_by_trial\elephant_multitaper`
  - `psd_by_trial_3`: output from `\code\analyses\psd_by_trial\scipy`
  - `surrogate_isih_1`: output from `\code\analyses\surrogate_isih\surrogate_1`
  - `surrogate_isih_2`: output from `\code\analyses\surrogate_isih\surrogate_2`

Each output folder contains the plots generated by the analysis (as PNG files),
together with the provenance information stored in Turtle format (`*.ttl`
files).

For each main output folder in `reach2grasp`, the plots and 
provenance files are stored inside a folder named after the Reach2Grasp 
experimental session used (`i140703-001`).

For the outputs in `psd_by_trial*`, the plot files are named with the trial
number (i.e., `138.png` is the plot for trial with ID `138` in the session).

For the outputs in `surrogate_isih*`, the plot files are named with the SUA
unit ID in the session dataset (i.e., `Unit [ID].png`).

### Raw SPARQL query outputs

The `\outputs\query_results` folder contains the outputs from the SPARQL
queries in `\code\queries`. The execution of each `*.sparql` file generates
a CSV file stored with the same name as the query file + `_raw` (e.g.,
`steps.sparql` --> `steps_raw.csv`).

### Tables

The `\outputs\manuscript_tables` folder contains the text files with the
LaTeX code for the tables presented in the manuscript, generated by the
scripts in `\code\manuscript_tables`. As the tables are composed by several
sub tables, each script generates a separate TXT file. The files are named
as the script file + the letter of the specific sub table (e.g., 
`table_steps.py` --> `table_steps_A.txt`, `table_steps_B.txt`).

### Logs

The details of the Python and package version information are stored in the
`/outputs/logs/environment.txt` file.

Details about the GraphDB server and GraphDB logs are stored in the
`/outputs/logs` folder.


## Acknowledgments

This work was performed as part of the Helmholtz School for Data Science in 
Life, Earth and Energy (HDS-LEE) and received funding from the Helmholtz 
Association of German Research Centres. This project has received funding from 
the European Union’s Horizon 2020 Framework Programme for Research and 
Innovation under Specific Grant Agreements No. 785907 (Human Brain Project 
SGA2) and 945539 (Human Brain Project SGA3), and by the Helmholtz Association 
Initiative and Networking Fund under project number ZT-I-0003.


## License

BSD 3-Clause License
