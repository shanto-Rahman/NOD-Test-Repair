#!/usr/bin/env bash

INPUT_CSV=$(realpath "$1")
OUTPUT_NAME="$2"

if [ -z "$OUTPUT_NAME" ]; then
    echo "Usage: bash docker_runner.sh input.csv output_name"
    echo "Example: bash docker_runner.sh tmp.csv hbase"
    exit 1
fi

if [[ "$OUTPUT_NAME" == "hbase" ]]; then
    IMAGE_NAME="hbase:shanto_modified_v2"
    PROJECT_MOUNT=""
elif [[ "$OUTPUT_NAME" == "spring" ]]; then
    IMAGE_NAME="spring:talank_modified"
    PROJECT_MOUNT="-v $(pwd)/..:/NOD-Test-Repair"
elif [[ "$OUTPUT_NAME" == "activiti" ]]; then
    IMAGE_NAME="activiti:talank_modified"
    PROJECT_MOUNT="-v $(pwd)/..:/NOD-Test-Repair"
else
    IMAGE_NAME="docker-nod-repair-env:latest"
    PROJECT_MOUNT="-v $(pwd)/..:/NOD-Test-Repair"
fi

mkdir -p docker_results docker_logs docker_traces

docker rm -f "spring_run_${OUTPUT_NAME}" 2>/dev/null || true
docker rm -f "hbase_run_${OUTPUT_NAME}" 2>/dev/null || true
docker rm -f "docker_run_${OUTPUT_NAME}" 2>/dev/null || true

docker run --rm \
    --user "$(id -u):$(id -g)" \
     -e HOME=/tmp \
    --name "docker_run_${OUTPUT_NAME}" \
    -v "$INPUT_CSV:/tmp/input.csv" \
    -v "$(pwd)/docker_results:/docker_results" \
    -v "$(pwd)/docker_logs:/docker_logs" \
    -v "$(pwd)/docker_traces:/docker_traces" \
    $PROJECT_MOUNT \
    "$IMAGE_NAME" \
    bash -c "
        set -o pipefail

        . /opt/conda/etc/profile.d/conda.sh

        cd /NOD-Test-Repair/Results

        cd /NOD-Test-Repair/tdrepro
        git config --global --add safe.directory '*'

        conda activate tdrepro || echo 'Conda activation failed'

        export MAVEN_OPTS="-Dmaven.repo.local=/NOD-Test-Repair/tdrepro/FlakeSync-Shanto-Modified/?/.m2/repository"
        bash runAll.sh /tmp/input.csv Result/

        cp /NOD-Test-Repair/tdrepro/Result/Test-Specific-Stat.csv /docker_results/${OUTPUT_NAME}_Test-Specific-Stat.csv || true
        cp -r /NOD-Test-Repair/tdrepro/logs /docker_logs/${OUTPUT_NAME}_raw_logs_while_collecting_stat/ || true
        cp -r /NOD-Test-Repair/tdrepro/traces /docker_traces/ || true

        chown -R \$(stat -c '%u:%g' /docker_logs) /docker_logs /docker_results /docker_traces || true
    " 2>&1 | tee "docker_logs/${OUTPUT_NAME}.log" #"docker_logs/${OUTPUT_NAME}.log" 2>&1

echo "All tests finished."
echo "Results saved in docker_results/"
echo "Logs saved in docker_logs/"

