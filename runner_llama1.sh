# column in csv : Git	Sha	Test-Name	Python-Version	Category

data_file="/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_data/exp_data.csv"

# read the file line by line
while IFS=, read -r id git sha test_name python_version category
do
    line="$git,$sha,$test_name,$python_version,$category"
    echo $line > exp_data/$id.csv

    # cp /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/llama.slurm /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/llama_$id.slurm
    cp /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/preprocess.slurm /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/preprocess_$id.slurm

    rm /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/llama_$id.slurm
    # replace <ID> with $id in the slurm file
    # sed -i "s/<ID>/$id/g" /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/llama_$id.slurm
    sed -i "s/<ID>/$id/g" /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/preprocess_$id.slurm

    # sbatch /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/llama_$id.slurm
    sbatch /scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/exp_jobs/preprocess_$id.slurm

done < $data_file
