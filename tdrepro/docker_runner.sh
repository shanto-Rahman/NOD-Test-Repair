#!/usr/bin/env bash

INPUT_CSV=$(realpath "$1")
OUTPUT_NAME="$2"

if [ -z "$OUTPUT_NAME" ]; then
    echo "Usage: bash docker_runner.sh input.csv output_name"
    echo "Example: bash docker_runner.sh tmp.csv hbase"
    exit 1
fi

mkdir -p docker_results docker_logs

docker rm -f "hbase_run_${OUTPUT_NAME}" 2>/dev/null || true

docker run --rm \
    --name "hbase_run_${OUTPUT_NAME}" \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -v "$INPUT_CSV:/tmp/input.csv" \
    -v "$(pwd)/docker_results:/docker_results" \
    -v "$(pwd)/docker_logs:/docker_logs" \
    hbase:shanto_modified \
    bash -c "
        set -o pipefail

        . \$HOME/.profile
        . /root/miniconda3/etc/profile.d/conda.sh

        cd /NOD-Test-Repair/Results
        unzip -o *.zip

        cd /NOD-Test-Repair/tdrepro
        conda activate tdrepro || echo 'Conda activation failed'

        bash runAll.sh /tmp/input.csv Result/

        cp /NOD-Test-Repair/tdrepro/Result/Test-Specific-Stat.csv /docker_results/${OUTPUT_NAME}_Test-Specific-Stat.csv || true
        cp -r /NOD-Test-Repair/tdrepro/logs /docker_logs/${OUTPUT_NAME}_raw_logs_while_collecting_stat/ || true

        chown -R \$(stat -c '%u:%g' /docker_logs) /docker_logs /docker_results || true
    " 2>&1 | tee "docker_logs/${OUTPUT_NAME}.log" #"docker_logs/${OUTPUT_NAME}.log" 2>&1

echo "All tests finished."
echo "Results saved in docker_results/"
echo "Logs saved in docker_logs/"

##!/usr/bin/env bash
## docker_runner.sh <input-csv> <output-dir> <iterations>
#
## Use realpath to ensure Docker volume mounts don't resolve to "volume names"
##docker_runner.sh ../data/new_70_tests.csv hbase_Result 1
#INPUT_CSV=$(realpath "$1")
## Collect all CSV rows into an array
#declare -a IDS
#while IFS=',' read -r id slug commit module test_name; do
#    [[ "$id" =~ ^# ]] && continue
#    IDS+=("$id,$slug,$commit,$module,$test_name")
#done < <(grep ',apache/hbase,' "$INPUT_CSV")
#
#
#if [ ${#IDS[@]} -eq 0 ]; then
#    echo "Error: No tests found matching 'apache/hbase' in $INPUT_CSV"
#    exit 1
#fi
#echo "Starting ${#IDS[@]} tests in parallel..."
#
#mkdir -p docker_results docker_logs
## Loop through every single collected ID
#for entry in "${IDS[@]}"; do
#    IFS=',' read -r id slug commit module test_name <<< "$entry"
#    
#    echo "Launching container for: $test_name (ID: $id)"
#
#    # Execute Docker in the background
#    docker run -d --rm \
#        --name "hbase_run_${id}" \
#        -v "$INPUT_CSV:/tmp/input.csv" \
#        -v "$(pwd)/docker_results:/docker_results" \
#        -v "$(pwd)/docker_logs:/docker_logs" \
#        hbase:shanto_modified \
#        bash -c "
#            set -o pipefail
#            . \$HOME/.profile
#            . /root/miniconda3/etc/profile.d/conda.sh
#            cd /NOD-Test-Repair/Results
#            unzip *.zip
#            cd /NOD-Test-Repair/tdrepro
#            conda activate tdrepro || echo 'Conda activation failed'
#            export OPENAI_API_KEY=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
#            bash runAll.sh /tmp/input.csv Result/
#            mkdir -p /docker_logs/${id}
#            mkdir -p /docker_results
#
#            cp /NOD-Test-Repair/tdrepro/Result/Test-Specific-Stat.csv /docker_results/${id}_Test-Specific-Stat.csv
#            cp -r /NOD-Test-Repair/tdrepro/logs-to-reproduce /docker_logs/${id} || true 
#            chown -R \$(stat -c '%u:%g' /docker_logs) /docker_logs /docker_results || true
#        "
#
#    docker logs -f "hbase_run_${id}" &
#done
#
##cp /NOD-Test-Repair/tdrepro/results/tdrepro.csv /docker_results/${id}.csv || true
#
## Safety: Only run docker wait if containers were actually started
#RUNNING_CONTAINERS=$(docker ps -q --filter "name=hbase_run_")
#if [ -n "$RUNNING_CONTAINERS" ]; then
#    echo "Waiting for containers to finish..."
#    docker wait $RUNNING_CONTAINERS > /dev/null
#else
#    echo "No containers are running now."
#fi
#
#
##for entry in "${IDS[@]}"; do
##    IFS=',' read -r id slug commit module test_name <<< "$entry"
##    if [[ $id -ne 202 ]]; then
##        continue
##    fi
##    docker cp hbase_run_${id}:/NOD-Test-Repair/Java/results/tdrepro.csv docker_results/${id}.csv
##    docker cp hbase_run_${id}:/NOD-Test-Repair/Java/logs-to-reproduce docker_logs/${id}
##done
#echo "All containers finished."
