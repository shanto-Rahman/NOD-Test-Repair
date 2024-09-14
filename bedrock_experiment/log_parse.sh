dir="test_run_logs_after_fm_changed/*"
rm "all_log_file_content.txt"
for file in $dir; do
    echo "Filename=$file" >> all_log_file_content.txt
    cat "$file" >> all_log_file_content.txt
    echo "" >> all_log_file_content.txt  # Add an empty line for separation
done
python3 log_parse.py
