#!/usr/bin/env bash
# docker_runner.sh <input-csv> <output-dir> <iterations>

# Use realpath to ensure Docker volume mounts don't resolve to "volume names"
#docker_runner.sh ../data/new_70_tests.csv hbase_Result 1
INPUT_CSV=$(realpath "$1")

#if [[ -z "$INPUT_CSV" || -z "$OUTPUT_DIR" || -z "$ITERATIONS" ]]; then
#    echo "Usage: $0 <input-csv> <output-dir> <iterations>"
#    exit 1
#fi

#LOGS_DIR="$(pwd)/rerun-logs"
#mkdir -p "$OUTPUT_DIR"
#mkdir -p "$LOGS_DIR"
#
# Collect all CSV rows into an array
declare -a IDS
while IFS=',' read -r id slug commit module test_name; do
    [[ "$id" =~ ^# ]] && continue
    IDS+=("$id,$slug,$commit,$module,$test_name")
done < <(grep ',apache/hbase,' "$INPUT_CSV")


if [ ${#IDS[@]} -eq 0 ]; then
    echo "Error: No tests found matching 'apache/hbase' in $INPUT_CSV"
    exit 1
fi
echo "Starting ${#IDS[@]} tests in parallel..."

# Loop through every single collected ID
for entry in "${IDS[@]}"; do
    IFS=',' read -r id slug commit module test_name <<< "$entry"
    
    echo "Launching container for: $test_name (ID: $id)"

    # Execute Docker in the background
    docker run -d -rm \
        --name "hbase_run_${id}" \
        hbase:shanto \
        bash -c "
            set -x pipefail
            . \$HOME/.profile
            cd /NOD-Test-Repair/Results
            unzip *.zip
            cd /NOD-Test-Repair/Java
            conda activate tdrepro || echo 'Conda activation failed'
            export OPENAI_API_KEY=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
            bash runAll.sh ../data/talank_with_test_id_idoft.csv Result/
        "

    docker logs -f "hbase_run_${id}" &
done

# docker wait $(docker ps -q --filter "name=hbase_run_") > /dev/null
# Safety: Only run docker wait if containers were actually started
RUNNING_CONTAINERS=$(docker ps -q --filter "name=hbase_run_")
if [ -n "$RUNNING_CONTAINERS" ]; then
    echo "Waiting for containers to finish..."
    docker wait $RUNNING_CONTAINERS > /dev/null
else
    echo "No containers are running now."
fi


for entry in "${IDS[@]}"; do
    IFS=',' read -r id slug commit module test_name <<< "$entry"
    if [[ $id -ne 202 ]]; then
        continue
    fi
    docker cp hbase_run_${id}:/NOD-Test-Repair/Java/results/tdrepro.csv docker_results/${id}.csv
    docker cp -r hbase_run_${id}:/NOD-Test-Repair/Java/logs-to-reproduce docker_logs/${id}
done
echo "All containers finished."
