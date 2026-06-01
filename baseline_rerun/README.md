please download the hbase_lite.tar file. Then run the command `docker load -i hbase_lite.tar hbase:lite`

Adjust the sleep time after lunching each container, or remove the sleep entirely https://github.com/shanto-Rahman/NOD-Test-Repair/blob/359d8e88e6c8ede248635a85b570dca0a58139c5/baseline_rerun/hbase_10k_runs.sh#L54

If you plan to put only 4-5 rows on the hbase.csv file (https://github.com/shanto-Rahman/NOD-Test-Repair/blob/master/baseline_rerun/hbase.csv) then you can remove the sleep entirely to lunch all containers at once.

Then run the script `bash hbase_10k_runs.sh` from the `NOD-Test-Repair/baseline_rerun`

python3 parse_error_to_get_uniq_failures.py extracted_failures.csv
python3 extract_uniq_failures.py extracted_failures.csv
