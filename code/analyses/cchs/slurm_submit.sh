#!/bin/bash
#SBATCH --job-name neao_use_case_cch

#SBATCH --partition blaustein
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 20

#SBATCH -o ../../../outputs/analyses/run_cchs.out
#SBATCH -e ../../../outputs/analyses/run_cchs.err

#SBATCH --time 6-00:00:00

conda activate neao_use_case

./run_cchs.sh