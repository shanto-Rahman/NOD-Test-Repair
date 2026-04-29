#!/usr/bin/env bash

INPUT_CSV=$(realpath "$1")
OUTPUT_NAME="$2"

if [ -z "$OUTPUT_NAME" ]; then
    echo "Usage: bash docker_runner.sh input.csv output_name"
    echo "Example: bash docker_runner.sh tmp.csv hbase"
    exit 1
fi

if [[ "$OUTPUT_NAME" == "hbase" ]]; then
    IMAGE_NAME="hbase:shanto_modified"
    PROJECT_MOUNT=""
else
    IMAGE_NAME="docker-nod-repair-env:latest"
    PROJECT_MOUNT="-v $(pwd)/..:/NOD-Test-Repair"
fi

mkdir -p docker_results docker_logs

docker rm -f "hbase_run_${OUTPUT_NAME}" 2>/dev/null || true

docker run --rm \
    --name "hbase_run_${OUTPUT_NAME}" \
    -v "$INPUT_CSV:/tmp/input.csv" \
    -v "$(pwd)/..:/NOD-Test-Repair" \
    -v "$(pwd)/docker_results:/docker_results" \
    -v "$(pwd)/docker_logs:/docker_logs" \
    $PROJECT_MOUNT \
    "$IMAGE_NAME" \
    bash -c "
        set -o pipefail

        . \$HOME/.profile
        . /root/miniconda3/etc/profile.d/conda.sh

        cd /NOD-Test-Repair/Results
        unzip -o *.zip

        cd /NOD-Test-Repair/tdrepro
        git config --global --add safe.directory '*'

        conda activate tdrepro || echo 'Conda activation failed'

        bash runAll.sh /tmp/input.csv Result/

        cp /NOD-Test-Repair/tdrepro/Result/Test-Specific-Stat.csv /docker_results/${OUTPUT_NAME}_Test-Specific-Stat.csv || true
        cp -r /NOD-Test-Repair/tdrepro/logs /docker_logs/${OUTPUT_NAME}_raw_logs_while_collecting_stat/ || true

        chown -R \$(stat -c '%u:%g' /docker_logs) /docker_logs /docker_results || true
    " 2>&1 | tee "docker_logs/${OUTPUT_NAME}.log" #"docker_logs/${OUTPUT_NAME}.log" 2>&1

echo "All tests finished."
echo "Results saved in docker_results/"
echo "Logs saved in docker_logs/"

