import re

#dir="test_run_logs_after_fm_changed/*"
#for file in dir; do
#    echo "===== $file =====" >> "all_log_file_content.txt"
#    cat "$file" >> "all_log_file_content.txt"
#    echo "" >> "all_log_file_content.txt"  # Add an empty line for separation
#done
#
# Path to the log file
log_file_path = "all_log_file_content.txt"

# Open the log file and read the lines
with open(log_file_path, 'r') as file:
    lines = file.readlines()

error_lines = [line for line in lines if re.match(r"^E\s{4}", line)]

# Print or process the extracted lines
for line in error_lines:
    print(line.strip())

# Optionally, save the extracted lines to a new file
with open("extracted_errors_from_log.txt", 'w') as output_file:
    output_file.writelines(error_lines)
    output_file.writelines("========================")
    output_file.writelines("========================")

