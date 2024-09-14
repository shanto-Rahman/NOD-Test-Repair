import csv

def claude_result_changed_fm_save_to_file(output_filename,proj_name,fm_file_name,test_file_name,unit_test_name,fm_name,changed_fm):
    with open(output_filename, 'a') as file:
        file.write(f'{proj_name},{test_file_name},{fm_file_name},{unit_test_name},{fm_name},{changed_fm}\n')

def claude_result_save_to_file(output_filename, proj_name, git_link, file_name, test_method, api_call):
    with open(output_filename, 'a') as file:
        file.write(f'{proj_name},{git_link},{file_name},{test_method},{api_call}\n')

