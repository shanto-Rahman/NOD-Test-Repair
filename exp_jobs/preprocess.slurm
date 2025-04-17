#!/bin/bash
#SBATCH --partition=bigmem                          
#SBATCH --qos=normal                                     
#SBATCH --job-name=preprocess_<ID>
#SBATCH --output=./jobs/logs/preprocess_<ID>.out
#SBATCH --error=./jobs/logs/preprocess_<ID>.err
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16                 # up to 128;
                
#SBATCH --mem=500GB                #total memory is 1 TB (1,000,000 MB)
#SBATCH --export=ALL
#SBATCH --time=4-23:00:00                   # set to 1hr; please choose carefully

module load gnu10 git

mkdir ./jobs/logs

source /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/env38/bin/activate

cd /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair

python run_tests_in_venv_talank.py exp_data/<ID>.csv
python ask_llama.py exp_data/<ID>.csv

