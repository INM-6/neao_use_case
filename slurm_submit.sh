#!/bin/bash
#SBATCH --job-name neao_use_case

#SBATCH --partition blaustein
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 20

#SBATCH --workdir ./
#SBATCH -o outputs/analyses/run_analyses.out
#SBATCH -e outputs/analyses/run_analyses.err

#SBATCH --time 6-00:00:00

conda activate neao_use_case

./run_analyses.sh