import pandas as pd
import boto3
import sys
import os
import json
import time
from access_in_claude import BedrockClientWithAutoRefresh, Claude
from save_result import claude_result_changed_fm_save_to_file
from prompt_engineering import generate_prompt_with_static_slices_for_test_repair_that_was_failed, collect_static_slice_prompt, generate_prompt_with_dynamic_traces_for_test_repair_that_was_failed, generate_prompt_without_any_slice_for_test_repair_that_was_failed, generate_prompt_without_slice_that_had_less_cc, generate_prompt_with_dynamic_trace_that_had_less_cc, generate_prompt_with_static_slice_that_had_less_cc
from modify_python_file import hack_into_sut, hack_into_test
from change_curation_helper import get_function_code, check_llm_response, run_test, parse_test_log, extract_failure_reasons, fail_to_get_changed_fm, read_log_file, fail_to_refine_test
from parse_git_change import collect_git_diff
import csv
import re
import shutil


region_name='us-east-1' # is for Claude3.5
#role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
session_name = "BedrockSession"

def read_csv_to_dict(csv_file_path):
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data

def get_fm_line_num(data, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name):
    #print(fm_file_path)
    for row in data:
        #print(row['proj_name'] )
        #print(row['test_filename'] )
        #print(row['test_method'] )
        #print(row['fm_filename'] )
        #print(row['fm_method'] )
        if (row['proj_name'] == proj_name
            and row['test_filename'] == test_file_path 
            and row['test_method'] == unit_test_name
            #and row['fm_filename'] == fm_file_path):
            and fm_file_path in row['fm_filename']
            and row['fm_method'] == fm_name):
            print('FOUND**') 
            return row['fm_line_num'], row['test_line_num']
        #exit()
    return None

def updated_fm_lines(changed_fm_code, fm_lines):
    #print('fm_lines=', fm_lines)
    #print('changed_fm_code=', changed_fm_code)
    lines = changed_fm_code.splitlines()
    # Count the number of lines
    new_code_lines = len(lines)
    #print('new_code_lines=',new_code_lines)
    match = re.match(r'\[(\d+)-(\d+)\]', fm_lines)
    if match:
        start_line = int(match.group(1))
        end_line = int(match.group(2))
    
        # Update end line number based on the number of lines in the new code
        updated_start_line = end_line + 2 # last method line number + a blank line + next line is the starting one
        updated_end_line = updated_start_line + new_code_lines - 1 # one is minus because it alrady comes into new_code_lines
    
        # Create the updated line range string
        updated_fm_lines_str = f'[{updated_start_line}-{updated_end_line}]'

    #print(updated_fm_lines_str)
    return updated_fm_lines_str

#def parse_log_for_test_session(log_file_path):
    '''sparse_log_for_test_sessiontart_marker = "============================= test session starts =============================="
    log_content = []

    with open(log_file_path, 'r') as file:
        lines = file.readlines()
    
    # Flag to track when the test session starts
    recording = False

    for line in lines:
        if start_marker in line:
            recording = True
        if recording:
            log_content.append(line)
    
    return ''.join(log_content)'''

def extract_lines_with_context(log_file_path):
    extracted_lines = []  # List to store extracted lines
    
    with open(log_file_path, 'r') as log_file:
        previous_line = ""
        for line in log_file:
            stripped_line = line.lstrip()
            if stripped_line.startswith('E') and (len(stripped_line) == 1 or stripped_line[1].isspace()):
                if previous_line.lstrip().startswith('>') and (len(previous_line.lstrip()) == 1 or previous_line.lstrip()[1].isspace()):
                    extracted_lines.append(previous_line.rstrip())  # Store previous line
                extracted_lines.append(stripped_line.rstrip())  # Store current line
            previous_line = line  # Update previous_line for next iteration
    
    return "\n".join(extracted_lines)  # Join extracted lines with newline

def is_valid_fm_code(changed_fm_code):
    if pd.isna(changed_fm_code) or changed_fm_code == "NA":
        print("NA found")
        return False
    return True

def collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name):
    prompt_static_slices = collect_static_slice_prompt(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name)
    #print(prompt_static_slices)
    static_slices = claude.generate_static_slice_using_claude(prompt_static_slices, True)

    match_tag = re.search(r'(<relevant_program_slice>(.*?)</relevant_program_slice>)', static_slices, re.DOTALL)
    static_slice_for_context = ""
    if match_tag:
        static_slice_for_context = match_tag.group(2).strip()
    #print("******===== static slice =", static_slice_for_context)
    return static_slice_for_context

def collect_trace_based_on_slice_type(slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace):
    #slice_for_context = ""
    additional_context = ""
    if slice_type == "Tool-Static":
        slice_for_context = collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name)
        additional_context = ( f"For additional information, you are given the program context with `<optional_focal_method_context>` tag. This context comes from static analysis of the focal method and may include relevant classes or methods.\n"
"<optional_focal_method_context>\n"
f"{slice_for_context}"
"</optional_focal_method_context>"
)

    elif slice_type == "Tool-Dynamic":
        slice_for_context = dynamic_trace
        print("I AM DYNAMIC-TOOL", dynamic_trace)
        additional_context = ( f"For additional information, you are given the program context with `<optional_focal_method_context>` tag. This context comes from dynamic analysis of the focal method and may include relevant classes or methods.\n"
"<optional_focal_method_context>\n"
f"{slice_for_context}"
"</optional_focal_method_context>"
) 
    elif slice_type == "Tool-Static-And-Dynamic":
        slice_for_context = collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name)
        additional_context = ( 
    f"For more information, the program context is provided within the `<optional_focal_method_context>` tag. This context has two types: "
    "1. The `<static_context>` tag, which contains static analysis data from the focal method, helpful for repairing the test. "
    "2. The `<dynamic_context>` tag, which includes the execution traces of all methods called from the focal method. \n"
    "<optional_focal_method_context>\n"
    "<static_context>\n"
    f"{slice_for_context}\n"
    "</static_context>\n"
    "<dynamic_context>\n"
    f"{dynamic_trace}\n"
    "</dynamic_context>\n"
    "</optional_focal_method_context>\n"
)

        #additional_context = static_context + dynamic_context
        print('****Context=',additional_context)
    return additional_context

def generate_failure_message_from_results(test_results, log_file_path, cot_count, slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace):
    log = extract_lines_with_context(log_file_path)
    additional_context = ""

    if test_results['syntax_errors'] > 0:
        additional_context = collect_trace_based_on_slice_type(slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace)

        failure_message = (
                f"<instructions>\n"
                "A SyntaxError occurred in your previously generated test. Here is the failure log:\n" 
                "</instructions>\n"
                "<failure_log>\n"
                f"{log}\n"
                "</failure_log>\n"
                f"{additional_context}" 
                )

    elif test_results['assertion_errors'] > 0 or test_results['failed'] > 0 or test_results['errors'] > 0:
        additional_context = collect_trace_based_on_slice_type(slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace)
#        if slice_type == "Tool-Static" and cot_count == 0 and slice_for_context != "": 
#            additional_context = ( f"For additional information, you are given the program context with `<optional_focal_method_context>` tag. This context comes from static analysis of the focal method and may include relevant classes or methods.\n"
#"<optional_focal_method_context>\n"
#f"{slice_for_context}"
#"</optional_focal_method_context>") 
#        elif slice_type == "Tool-Dynamic" and cot_count == 0 and slice_for_context != "":
#            additional_context = ( f"For additional information, you are given the program context with `<optional_focal_method_context>` tag. This context comes from dynamic analysis of the focal method and may include relevant classes or methods.\n"
#"<optional_focal_method_context>\n"
#f"{slice_for_context}"
#"</optional_focal_method_context>"
#)
        failure_message = (
    f"<instructions>\n"
    "The changes you made to the test method did not pass the test. "
    "Please revise your test code to ensure it passes successfully. "
    "Below is the failure log from your previously suggested repaired test:\n"
    "</instructions>\n"
    "<failure_log>\n"
    f"{log}\n"
    "</failure_log>\n"
     f"{additional_context}"
)
    else:
        failure_message = ""

    return failure_message

def save_refinement_logs(prompt, refined_test_response):
    with open("Claude_prompt_from_test_refine.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([prompt])
        writer.writerow("*********************")
    
    with open("Refined_test.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([refined_test_response])
        writer.writerow("*********************")


def fm_and_test_file_content(fm_file_path, test_file_path):
    with open(fm_file_path, 'r') as file:
        fm_file_content = file.read()
    with open(test_file_path, 'r') as file:
        test_file_content = file.read()
    return fm_file_content, test_file_content

def copy_org_test_file(test_file_path):
    # Get the current directory (where you want to copy the file)
    current_dir = os.getcwd()

    # Extract the filename from the test_file_path
    filename = os.path.basename(test_file_path)
    
    # Set the destination path in the current directory
    destination_path = os.path.join(current_dir, filename)
    
    # Copy the file to the current directory
    shutil.copy(test_file_path, destination_path)
    
    print(f"File copied to: {destination_path}")

def refine_test_with_claude(claude, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, fm_lines, failure_message, diff_fm, objective, threshold_to_cot, static_slice_csv_writer, dynamic_trace, claude_result_file, slice_type, start_time):
    cot_count = 0
    assert_refine_af = False
    log_content = ""
    fm_file_content, test_file_content = fm_and_test_file_content(fm_file_path, test_file_path)
    copy_org_test_file(test_file_path)
    #static_program_slice_retrieved = False
    while True:
        if objective == "Refine_AF":
            if cot_count > threshold_to_cot:
                if not assert_refine_af:
                    #fail_to_refine_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective)
                    # End the timer
                    end_time = time.time()
                    # Calculate the elapsed time
                    elapsed_time = end_time - float(start_time)
                    fail_to_refine_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, str(cot_count), dynamic_trace, elapsed_time) # save into the result file if we are unsuccessful
                    #csv_file_path' and 'chain_count_cc'
                    break
            if assert_refine_af:
                break
            if cot_count == 0:
                if slice_type == "Static":
                    prompt_static_slices = collect_static_slice_prompt(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name)
                    #print(prompt_static_slices)
                    static_slices = claude.generate_static_slice_using_claude(prompt_static_slices)
                    #print(static_slices)
                    match_tag = re.search(r'<relevant_program_slice>(.*?)</relevant_program_slice>', static_slices, re.DOTALL)
                    static_slice_for_context = ""
                    if match_tag:
                        static_slice_for_context = match_tag.group(1).strip()

                    static_slice_csv_writer.writerow([proj_name, unit_test_name, fm_name, static_slice_for_context])
                    prompt = generate_prompt_with_static_slices_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body, unit_test_name, "test_lines", fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, failure_message, diff_fm, static_slice_for_context)
                    
                elif slice_type == "Dynamic":
                    prompt = generate_prompt_with_dynamic_traces_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body, unit_test_name, "test_lines", fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, failure_message, diff_fm, dynamic_trace)
                else: #No slicing, Tool (OurTechnique)
                    prompt = generate_prompt_without_any_slice_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body, unit_test_name, "test_lines", fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, failure_message, diff_fm)
            else: 
                prompt = failure_message
            print("**** prompt=",prompt)
            refined_test_response = claude.infer_using_claude(prompt, True)
            #print('refined_test_response=', refined_test_response)

            save_refinement_logs(prompt, refined_test_response)

            cleaned_code, changes_types = check_llm_response(refined_test_response, "test_meth")

            #print('************** cleaned_code=', cleaned_code)
            if cleaned_code == "incomplete_changed_test":
                cot_count += 1
                failure_message = "</instruction>Your previously generated test method is incomplete. Please give a complete changed test method.</instruction>"
                continue
            
            hack_into_test(cleaned_code, test_file_path, unit_test_name, test_lines)
            #exit()
            diff_test, changed_line_numbers_in_fm, diff_in_fm_with_line_numbers = collect_git_diff(test_file_path, "../test_analysis/projects/"+proj_name, proj_name)
            log_file_path = f"test_run_logs_after_fm_changed/log_{proj_name}_{unit_test_name}_{fm_name}_{objective}_claude_{cot_count}"
            
            run_test(cleaned_code, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective, error_type, diff_fm, changed_fm_code, diff_test, dynamic_trace, "", "", start_time)

            log_content, test_results = read_log_file(log_file_path, objective)
            failure_message = generate_failure_message_from_results(test_results, log_file_path, cot_count, slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace)
            #print(failure_message)
            if failure_message == "":
                print("Empty-Failure Found, Means test pass *****")
                #exit()
            #print(test_results['passed'],  test_results['assertion_errors'], test_results['failed'], test_results['errors'], test_results["syntax_errors"])
            if test_results['passed'] > 0 and  (test_results['assertion_errors'] == 0 and test_results['failed'] == 0 and test_results['errors'] == 0):
                assert_refine_af = True

            cot_count += 1
        time.sleep(5)

def data_from_row(row):
    proj_name = row['Project'] 
    if proj_name.strip().startswith('#'):
        return None
    test_file_path = row['TestCaseFile']
    unit_test_name = row['TestCaseMethod']
    old_unit_test_body = row['old_test_case_code'] #old_test_code
    new_test_lines = row['TestCaseLines']
    fm_file_path = row['FocalMethodFile']
    fm_name = row['FocalMethod']
    changed_fm_code = row['original_focal_method_code'] #coming from new_test
    error_type = row['result'] #test_result
    coverage_percentage = row['covered_percentage']
    if not is_valid_fm_code(changed_fm_code): #pd.isna(changed_fm_code) or changed_fm_code == "NA":
        return None
    return proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, error_type, coverage_percentage, old_unit_test_body, new_test_lines

if __name__ == "__main__":
    file_path = sys.argv[1] #Results/Combined_result_of_fm_and_tests.csv; data/assertion_error_real_data.csv
    objective = sys.argv[2] #CC (Code Coverage) or Refine_AF (Assertion Failure) 
    file_name = file_path.split('/')[-1]
    df = pd.read_csv(file_path)

    outputDir = "Results"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)
  
    #slice_type="Static" 
    #slice_type="Dynamic" 
    #slice_type="NA" 
    #slice_type="Tool-NA" 
    #slice_type="Tool-Static" 
    #slice_type="Tool-Dynamic" 
    #slice_type="Tool-Static-And-Dynamic"
 
    slice_type = sys.argv[3]
    #slice_file_to_repair = "Results/Generated_"+slice_type+"_Slices_to_"+objective+".csv"
    slice_file_to_repair = "Results/Generated_"+slice_type+"_Slices_to_"+objective+".csv"
    
    # Open the CSV file and create a writer object
    with open(slice_file_to_repair, mode='a', newline='') as csvfile:
        slice_csv_writer = csv.writer(csvfile)
        slice_csv_writer.writerow(['proj_name', 'OldTestCaseFunction', 'OriginalFocalMethodFunction', 'slice_for_context'])  # I find for old and new commit fm and tests are the same. So, extracting anyone is fine
        
        for index, row in df.iterrows():
            # Initialize the Claude instance for this row
            session_memory = {}
            # Initialize the Bedrock client
            '''bedrock_client = BedrockClientWithAutoRefresh(role_arn, session_name, region_name)
            claude = Claude(bedrock_client, session_memory)'''
            row_data = data_from_row(row)
            if row_data is None:
                continue
            proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, error_type, coverage_percentage, old_unit_test_body, new_test_lines = row_data

            csv_file_path = "Results/Combined_result_of_fm_and_tests.csv" 
            data = read_csv_to_dict(csv_file_path)

            print( proj_name, test_file_path, unit_test_name, fm_file_path, fm_name)
            #fm_lines, test_lines = get_fm_line_num(data, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name)

            changed_fm_code = changed_fm_code.strip()
            if changed_fm_code.startswith('"') and changed_fm_code.endswith('"'):
                changed_fm_code = changed_fm_code[1:-1].strip()
            unit_test_body = get_function_code(test_file_path, unit_test_name)
            #fm_lines = hack_into_sut(changed_fm_code, fm_file_path, fm_name, fm_lines) #added the change into CUT by removing existing method code
            #diff_fm, changed_line_numbers_in_test, diff_in_test_with_line_numbers = collect_git_diff(fm_file_path, "../test_analysis/projects/"+proj_name, proj_name) 
            after_adding_old_test_start_line, after_adding_old_test_end_line = hack_into_test(old_unit_test_body, test_file_path, unit_test_name, new_test_lines)
            cot_count = 0 
            threshold_to_cot = 5
            reproduce_result_file = "Results/Reproduce_test_outcome.csv"
            
            if objective == "Refine_AF":
                coverage_percentage, dynamic_trace, covered_lines = run_test("To-reproduce-only", fm_file_path, fm_name, "fm_lines", unit_test_name, test_file_path, reproduce_result_file, proj_name, str(cot_count), "claude", "See-Previous", "Reproduce-AF",error_type) #Main aim is to reproduce the AF/CC and to collect the log
                if slice_type == "Dynamic":
                    slice_csv_writer.writerow([proj_name, unit_test_name, fm_name, dynamic_trace])
                log_file = "test_run_logs_after_fm_changed/log_"+proj_name+"_"+unit_test_name+"_"+fm_name+"_Reproduce-AF_claude_0" 
                log = extract_lines_with_context(log_file)
                failure_message=f"With the following modified focal method, the test assertion failed. Please correct the test code to ensure the test passes. Here is the failure log: \n<log>\n{log}\n</log>"
                claude_result_file = "Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF_with_"+slice_type+"_slice_with_Real_tests.csv"
                print(after_adding_old_test_start_line, after_adding_old_test_end_line)
                start_time = time.time()
                #exit()
                claude = "CLAUDE"
                refine_test_with_claude(claude, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, "fm_lines", failure_message, "diff_fm", objective, threshold_to_cot, slice_csv_writer, dynamic_trace, claude_result_file, slice_type, str(start_time))

