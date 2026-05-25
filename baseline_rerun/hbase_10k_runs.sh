#!/usr/bin/env bash

IMAGE="hbase:lite"
MEMORY="16g"
CPUS="4"
ARTIFACT_DIR_BASE="./hbase_artifacts_baseline_10k"

# Skip CSV header
tail -n +2 hbase.csv | while IFS=',' read -r id slug sha module test_name
do
  echo "============================================="
  echo "Running ID: $id"
  echo "Test: $test_name"
  echo "============================================="
#   if $id starts with #, then skip it
  if [[ "$id" == \#* ]]; then
    echo "Skipping ID: $id (commented out)"
    echo ""
    continue
  fi

  ARTIFACT_DIR="$ARTIFACT_DIR_BASE/$id"
  rerun_logs_dir="$ARTIFACT_DIR/logs"
  rerun_results_dir="$ARTIFACT_DIR/results"

  mkdir -p "$rerun_logs_dir"
  mkdir -p "$rerun_results_dir"

  docker run -d \
    --name "baseline_rerun_hbase${id}" \
    --memory="$MEMORY" \
    --cpus="$CPUS" \
    -v "$rerun_logs_dir":/rerun_baseline/rerun-logs \
    -v "$rerun_results_dir":/rerun_baseline/results \
    "$IMAGE" \
    bash -c "
      set -o
      apt install bc -y 
      apt install lsof -y
      . \$HOME/.profile

      cd /rerun_baseline

      echo '#id,slug,sha,module,testName' > tmp.csv
      echo '$id,$slug,$sha,$module,$test_name' >> tmp.csv

      bash re-run_baseline.sh tmp.csv results
    "

  echo "Ran ID: $id"
  echo "Check to the dir $ARTIFACT_DIR for logs and artifacts."
  echo ""

  # sleep for 3 hours (this will avoid overwhelming the system with too many concurrent containers. If the resource available is high then you can sleep for shorter time)
  #sleep 10800
done

echo "All containers launched."
echo "Waiting for completion..."

# Wait for all containers to stop
for cname in $(docker ps -a --format '{{.Names}}' | grep '^baseline_rerun_hbase'); do
  docker wait "$cname" > /dev/null
  docker rm "$cname" > /dev/null
  echo "Container $cname finished and removed."
done

echo "All containers finished."
