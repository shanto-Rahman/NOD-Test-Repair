import pandas as pd
import boto3
import sys
import os
import json
import time
from access_in_claude import BedrockClientWithAutoRefresh, Claude
from save_result import claude_result_changed_fm_save_to_file
from prompt_engineering import generate_prompt_with_static_slices_for_test_repair_that_was_failed, collect_static_slice_prompt, generate_prompt_with_dynamic_traces_for_test_repair_that_was_failed, generate_prompt_without_any_slice_for_test_repair_that_was_failed, generate_prompt_without_slice_that_had_less_cc, generate_prompt_with_dynamic_trace_that_had_less_cc, generate_prompt_with_static_slice_that_had_less_cc, generate_prompt_with_both_static_and_dynamic_trace_that_had_less_cc
from modify_python_file import hack_into_sut, hack_into_test, hack_into_test_for_cc
from change_curation_helper import get_function_code, check_llm_response_for_cc, run_test, parse_test_log, extract_failure_reasons, fail_to_get_changed_fm, read_log_file, fail_to_generate_test
from parse_git_change import collect_git_diff
import csv
import re


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

def generate_failure_message_from_results(test_results, log_file_path, cot_count):
    log = extract_lines_with_context(log_file_path)
    #print("Test Results Summary:")
    #print(f"SyntaxError: {test_results['syntax_errors']}")
    #print(f"Failed: {test_results['failed']}")
    #print(f"Errors: {test_results['errors']}")
    ##print(f"Skipped: {test_results['skipped']}")
    if test_results['syntax_errors'] > 0:
        failure_message = (
                f"<instructions>\n"
                "A SyntaxError occurred in your previously generated test. Here is the failure message:\n" 
                "<failure_log>\n"
                f"{log}\n"
                "</failure_log>\n"
                "</instructions>"
                )
    elif test_results['assertion_errors'] > 0 or test_results['failed'] > 0 or test_results['errors'] > 0:
        #failure_message = f"<failure_message>The changes you previously made to the test method cannot make test pass. Please correct your changes in the test code to ensure the test pass. Following is the log of your previously suggested repaired test: <log>{log}</log> </failure_message>"
        failure_message = (
    f"<instructions>\n"
    "Your generated test method did not pass during execution. Please revise your generated test code to ensure it runs successfully."
    "Below is the failure message from your previously generated test:\n"
    "<failure_log>\n"
    f"{log}\n"
    "</failure_log>\n"
    "</instructions>"
)

        #f"<failure_message>The changes you made to the test method did not pass the test. Please revise your test code to ensure it passes successfully. Below is the log from your previously suggested repaired test: <log>{log}</log></failure_message>"

    elif test_results['passed'] > 0:
        failure_message = "passed"
    else:
        failure_message = "NA"
    return failure_message

def generate_low_coverage_message_from_results(test_results, log_file_path, cot_count, covered_lines, changed_line_numbers, coverage_percentage, total_uncovered_lines):
    #if isinstance(changed_line_numbers, str):
    #    changed_line_numbers = [int(num.strip()) for num in changed_line_numbers.split(',')]

    uncovered_lines = list(set(total_uncovered_lines) - set(covered_lines))
    total_uncovered_lines = list(set(total_uncovered_lines) - set(covered_lines))
    total_uncovered_lines.sort()

    uncovered_lines.sort()
    log = extract_lines_with_context(log_file_path)
    if test_results['passed'] > 0:
        low_coverage_message = f"<instructions> Your previously generated test method passed, but it does not execute all the changed lines: <all_changed_line_numbers>{changed_line_numbers}</all_changed_line_numbers> in the focal method. The lines your test currently executes are {covered_lines}. Now create a new test to ensure that all remaining lines <unexecuted_lines>{uncovered_lines}</unexecuted_lines> are also executed during the test run. </instructions>"

    print('low_coverage_message=',low_coverage_message)
    #exit()
    #test_results['skipped'] > 0 or 
    #print(' *** TEST_GENERATION.py low_coverage_message=',low_coverage_message)
    #exit()
    return low_coverage_message, total_uncovered_lines 

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


def collect_minimal_set_test(refinement_dict, changed_line_numbers):
    # Initialize variables to store the selected tests and covered lines
    selected_tests = set()
    covered_lines_set = set()
    total_changed_lines = len(changed_line_numbers)  # Total lines to cover

    # Use a greedy algorithm to select the minimum number of tests
    while covered_lines_set != changed_line_numbers:
        best_test = None
        best_new_coverage = set()
        
        # Find the test that covers the most uncovered lines
        for cot_count, test_data in refinement_dict.items():
            test_covered_lines = set(test_data['covered_lines'])
            new_coverage = test_covered_lines - covered_lines_set  # Uncovered lines this test can cover
            
            if len(new_coverage) > len(best_new_coverage):
                best_test = cot_count
                best_new_coverage = new_coverage
        
        if best_test is None:
            break  # No more tests can cover additional lines (shouldn't happen if data is correct)
    
        # Add the best test to the selected tests and update the covered lines
        selected_tests.add(best_test)
        covered_lines_set.update(refinement_dict[best_test]['covered_lines'])
   
       # Calculate percentage of covered lines
    covered_percentage = (len(covered_lines_set) / total_changed_lines) * 100 if total_changed_lines > 0 else 0

    # Output the result
    #print(f"Selected tests to cover all changed lines: {selected_tests}")
    #print(f"Covered lines: {sorted(list(covered_lines_set))}")
    #print(f"Percentage of maximum covered lines: {covered_percentage:.2f}%")

    return selected_tests, sorted(list(covered_lines_set)), len(selected_tests), covered_percentage

def collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name):
    prompt_static_slices = collect_static_slice_prompt(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name)
    #print(prompt_static_slices)
    static_slices = claude.generate_static_slice_using_claude(prompt_static_slices, True)

    match_tag = re.search(r'(<relevant_program_slice>(.*?)</relevant_program_slice>)', static_slices, re.DOTALL)
    static_slice_for_context = ""
    if match_tag:
        static_slice_for_context = match_tag.group(2).strip()

    return static_slice_for_context

def calculate_coverage_percentage(changed_line_numbers, total_uncovered_lines):
    # Calculate the lengths
    len_changed = len(changed_line_numbers)
    len_uncovered = len(total_uncovered_lines)
    
    # Perform the calculation
    result = ((len_changed - len_uncovered) / len_changed) * 100
    return result

def refine_test_with_claude_to_improve_cc(claude, proj_name, test_file_path, org_unit_test_name, fm_file_path, fm_name, changed_fm_code, fm_lines, feedback_message, diff_fm_with_line_numbers, objective, threshold_to_cot, slice_csv_writer, dynamic_trace, claude_result_file, slice_type, changed_line_numbers, diff_fm, start_time):
    cot_count = 0
    test_refine_cc = False
    log_content = ""
    fm_file_content, test_file_content = fm_and_test_file_content(fm_file_path, test_file_path)
    unit_test_name = org_unit_test_name
    generated_test_dict = {}
    if isinstance(changed_line_numbers, str):
        all_changed_line_numbers_list = [int(num.strip()) for num in changed_line_numbers.split(',')]

    total_uncovered_lines = all_changed_line_numbers_list.copy()
    print('changed_line_numbers=', changed_line_numbers)

    copy_org_test_file(test_file_path)
    #static_program_slice_retrieved = False
    while True:
        print('***** cot_count=',cot_count)
        if cot_count > threshold_to_cot:
            if not test_refine_cc:
                selected_tests, covered_lines_set, count_selected_tests_that_covers_all_tests, covered_percentage =  collect_minimal_set_test(generated_test_dict, all_changed_line_numbers_list) 
                covered_percentage = calculate_coverage_percentage(all_changed_line_numbers_list, total_uncovered_lines) # This is the actual coverage happened by all the generated tests
                end_time = time.time()
                elapsed_time = end_time - float(start_time)
                print("FROM FAIL TO SAVE: Not a single generated test can make 100.0% coverage, covered_percentage=", all_changed_line_numbers_list, total_uncovered_lines, covered_percentage)

                fail_to_generate_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, str(cot_count), dynamic_trace, covered_percentage, count_selected_tests_that_covers_all_tests, covered_lines_set, elapsed_time) #save into the result file if we are unsuccess
                break

        if test_refine_cc:
            break

        if cot_count == 0:
            if slice_type == "Static":
                static_slice_for_context = collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name)
                slice_csv_writer.writerow([proj_name, unit_test_name, fm_name, static_slice_for_context])
                prompt = generate_prompt_with_static_slice_that_had_less_cc(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, feedback_message, diff_fm_with_line_numbers, all_changed_line_numbers_list, static_slice_for_context, diff_fm)
            elif slice_type == "Dynamic":
                prompt = generate_prompt_with_dynamic_trace_that_had_less_cc(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, feedback_message, diff_fm_with_line_numbers, all_changed_line_numbers_list, dynamic_trace, diff_fm)
            elif slice_type == "Static_And_Dynamic":
                static_slice_for_context = collect_static_slice(fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, feedback_message, unit_test_name, fm_name)
                prompt = generate_prompt_with_both_static_and_dynamic_trace_that_had_less_cc(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, feedback_message, diff_fm_with_line_numbers, all_changed_line_numbers_list, static_slice_for_context, diff_fm, dynamic_trace)
            else: #No slicing
                print("No Slicing ****")
                prompt = generate_prompt_without_slice_that_had_less_cc(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, feedback_message, diff_fm_with_line_numbers, all_changed_line_numbers_list, diff_fm) 

        else: 
            prompt = feedback_message
        print(prompt)
        exit()
        refined_test_response = claude.infer_using_claude(prompt, True)
        #print('refined_test_response=', refined_test_response)
        #print('***************')
        save_refinement_logs(prompt, refined_test_response)

        cleaned_code, changes_types, unit_test_name = check_llm_response_for_cc(refined_test_response, "test_meth")
        #print('cleaned_code=',cleaned_code)
        #print(unit_test_name)
        if cleaned_code == "incomplete_changed_test" or cleaned_code == "root_not_found":
            cot_count += 1
            feedback_message = "</instructions>Your previously generated test method is incomplete. Please give a complete changed test method.</instructions>"
            continue

        #print('generated_test=',cleaned_code)
        #exit()
        hack_into_test_for_cc(cleaned_code, test_file_path, unit_test_name, test_lines)
        #diff_test = collect_git_diff(test_file_path, "../test_analysis/projects/"+proj_name, proj_name)
        log_file_path = f"test_run_logs_after_fm_changed/log_{proj_name}_{unit_test_name}_{fm_name}_{objective}_claude_{cot_count}"
        #print(org_unit_test_name)
        coverage_percentage, dyn, covered_lines = run_test(cleaned_code, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective, error_type, diff_fm_with_line_numbers, changed_fm_code, "", "", org_unit_test_name, changed_line_numbers, start_time) #Here dyn is dynamic trace which will be empty
        #exit()
        #print('log_file=',log_file_path)
        log_content, test_results = read_log_file(log_file_path, objective)
        feedback_message = generate_failure_message_from_results(test_results, log_file_path, cot_count)
        
        #print('*** From test_generation coverage_percentage=',coverage_percentage)
        #print('feedback_message=',feedback_message)
        if feedback_message == "passed":
            print("****test_passed****")
            # Save the cleaned_code into the dictionary with cot_count as the key
            generated_test_dict[cot_count] = {
                'generated_test': cleaned_code,
                'covered_lines': covered_lines
            }

            if coverage_percentage == "":
                print("converage percentage empty, so setting value 0.0 ***")
                coverage_percentage = 0.0
            if float(coverage_percentage) < 100.0: # Means that the generated test passes
                print("ENTERED ***")
                feedback_message, total_uncovered_lines = generate_low_coverage_message_from_results(test_results, log_file_path, cot_count, covered_lines, all_changed_line_numbers_list, coverage_percentage, total_uncovered_lines)
                if len(total_uncovered_lines) == 0: # Means that multiple tests together passes the test
                    selected_tests, covered_lines_set, count_selected_tests_that_covers_all_tests, covered_percentage =  collect_minimal_set_test(generated_test_dict, all_changed_line_numbers_list) 

                    covered_percentage = calculate_coverage_percentage(all_changed_line_numbers_list, total_uncovered_lines) # This is the actual coverage happened by all the generated tests
                    end_time = time.time()
                    elapsed_time = end_time - float(start_time)
                    print("***** YESS, multiple generated test can make 100.0% coverage, covered_percentage=",all_changed_line_numbers_list, total_uncovered_lines , covered_percentage)
                    fail_to_generate_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, str(cot_count), dynamic_trace, covered_percentage, count_selected_tests_that_covers_all_tests, covered_lines_set, elapsed_time)
                    break
        elif feedback_message == "NA":
            feedback_message = "</instructions>Your previously generated test method is not correct. Please give a correct changed test method.</instructions>"

        if test_results['passed'] > 0 and coverage_percentage == 100.0 and  (test_results['assertion_errors'] == 0 and test_results['failed'] == 0 and test_results['errors'] == 0):
            test_refine_cc = True

        cot_count += 1
        time.sleep(3)
    #collect_minimal_set_test(generated_test_dict, changed_line_numbers) 
    #print(f"Refinement_dict at cot_count {cot_count}: {generated_test_dict}")
    return generated_test_dict

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
    #fm_file_path = row['fm_filename']
    #fm_name = row['fm_method']
    #changed_fm_code = row['changed_fm']
    #error_type = row['test_pass/fail']
    #coverage_percentage = row['coverage_percentage']
    if not is_valid_fm_code(changed_fm_code): #pd.isna(changed_fm_code) or changed_fm_code == "NA":
        return None
    #return proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, error_type, coverage_percentage
    return proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, error_type, coverage_percentage, old_unit_test_body, new_test_lines

if __name__ == "__main__":
    file_path = sys.argv[1] #Results/Combined_result_of_fm_and_tests.csv
    objective = sys.argv[2] #CC (Code Coverage) or Refine_AF (Assertion Failure)
    file_name = file_path.split('/')[-1]
    df = pd.read_csv(file_path)

    outputDir = "Results"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)
  
    #slice_type="Static" 
    #slice_type="Dynamic" 
    #slice_type="NA" 
    slice_type = sys.argv[3]
    #slice_file_to_repair = "Results/Generated_"+slice_type+"_Slices_to_"+objective+".csv"
    slice_file_to_repair = "Results/Generated_"+slice_type+"_Slices_to_"+objective+".csv"

    # Open the CSV file and create a writer object
    with open(slice_file_to_repair, mode='w', newline='') as csvfile:
        slice_csv_writer = csv.writer(csvfile)
        slice_csv_writer.writerow(['proj_name', 'unit_test_name', 'fm_name', 'slice_for_context'])  # Write the header
        
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
            print( proj_name, test_file_path, unit_test_name, fm_file_path, fm_name)
            csv_file_path = "Results/Combined_result_of_fm_and_tests.csv" 
            data = read_csv_to_dict(csv_file_path)
            #print(data.head(10))

            #fm_lines, test_lines = get_fm_line_num(data, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name)

            changed_fm_code = changed_fm_code.strip()
            if changed_fm_code.startswith('"') and changed_fm_code.endswith('"'):
                changed_fm_code = changed_fm_code[1:-1].strip()
            unit_test_body = get_function_code(test_file_path, unit_test_name)
            #fm_lines = hack_into_sut(changed_fm_code, fm_file_path, fm_name, fm_lines) #added the change into CUT by removing existing method code
            #diff_fm, changed_line_numbers, diff_fm_with_line_numbers = collect_git_diff(fm_file_path, "../test_analysis/projects/"+proj_name, proj_name) 
            #print('changed_line_numbers=', changed_line_numbers)
            #print("diff_fm=", diff_fm)
            #print("********diff_fm_with_line_numbers=", diff_fm_with_line_numbers)
            #exit()
            after_adding_old_test_start_line, after_adding_old_test_end_line = hack_into_test(old_unit_test_body, test_file_path, unit_test_name, new_test_lines)
            cot_count = 0 
            threshold_to_cot = 10
            reproduce_result_file = "Results/Reproduce_test_outcome.csv"
            
            dynamic_trace = "" 
            start_time = time.time()
            #if slice_type == "Dynamic" or slice_type == "Static_And_Dynamic":
            coverage_percentage, dynamic_trace, covered_lines = run_test("To-reproduce-only", fm_file_path, fm_name, "fm_lines", unit_test_name, test_file_path, reproduce_result_file, proj_name, str(cot_count), "claude", "See-Previous", "Reproduce_CC",error_type,"","","","","","",start_time) # AIM is to introduces the changed_fm in CUT. dynamic_trace only contains content when it is Reproduce_CC or Reproduce_AF
            #coverage_percentage, dyn, covered_lines = run_test(cleaned_code, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective, error_type, diff_fm_with_line_numbers, changed_fm_code, "", "", org_unit_test_name, changed_line_numbers) #Here dyn is dynamic trace which will be empty
            #log_file = "test_run_logs_after_fm_changed/log_"+proj_name+"_"+unit_test_name+"_"+fm_name+"_Reproduce-CC_claude_0" 
            #feedback_message = f"The current test method covers {coverage_percentage}% of the focal method's lines. However, this does not achieve 100% coverage. Please modify the test method to ensure it fully covers the focal method, reaching 100% code coverage."
            #print('*** dynamic_trace=', dynamic_trace)
            #exit()
            feedback_message = ""
            #claude_result_file = "Results/Claude3-5_690_tests_with_Refined_Tests_Meth_CC_Updated.csv"
            claude_result_file = "Results/Claude3-5_690_tests_with_Refined_Tests_Meth_CC_with_"+slice_type+"_slice_with_updated_prompt_1_node8_after_data_clean_with_time.csv"
            claude = "Claude"
            refine_test_with_claude_to_improve_cc(claude, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code, "fm_lines", feedback_message, diff_fm_with_line_numbers, objective, threshold_to_cot, slice_csv_writer, dynamic_trace, claude_result_file, slice_type, changed_line_numbers, diff_fm, str(start_time))
            exit()

