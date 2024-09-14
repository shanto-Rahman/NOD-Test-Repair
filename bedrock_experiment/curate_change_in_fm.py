import pandas as pd
import boto3
import sys
import os
import json
import time
from access_in_claude import BedrockClientWithAutoRefresh, query_claude_3, Claude
from save_result import claude_result_changed_fm_save_to_file
from prompt_engineering import generate_promt_for_change_curation_to_reduce_cc, generate_promt_for_change_curation_to_test_fail
from modify_python_file import hack_into_sut
from change_curation_helper import get_function_code, get_function_code_fm, check_llm_response, run_test, parse_test_log, extract_failure_reasons, fail_to_get_changed_fm, read_log_file
import csv
import re

region_name='us-east-1' # is for Claude3.5
#role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
session_name = "BedrockSession"


def extract_lines_with_context(log_file_path):
    extracted_lines = []  # List to store extracted lines

    with open(log_file_path, 'r') as log_file:
        previous_line = ""
        for line in log_file:
            stripped_line = line.lstrip()
            if stripped_line.startswith('E') and (len(stripped_line) == 1 or stripped_line[1].isspace()):
                if previous_line.lstrip().startswith('>') and (len(previous_line.lstrip()) == 1 or previous_line.lstrip()[1].isspace()):
                    extracted_lines.append(previous_line.strip())  # Store previous line
                extracted_lines.append(stripped_line.strip())  # Store current line
            previous_line = line  # Update previous_line for next iteration

    return extracted_lines

def data_from_row(row):
    #print('row=',row)
    proj_name = row['proj_name'] 
    if proj_name.strip().startswith('#'):
        #continue
        return None

    fm_file_path = row['fm_filename']
    test_file_path = row['test_filename']
    unit_test_name = row['test_method']
    fm_name = row['fm_method']
    fm_lines = row['fm_line_num']
    test_lines = row['test_line_num']
    with open(fm_file_path, 'r') as file:
        fm_file_content = file.read()
    with open(test_file_path, 'r') as file:
        test_file_content = file.read()

    return proj_name, test_file_path, unit_test_name, test_lines, fm_file_path, fm_name, fm_lines, fm_file_content, test_file_content


def generate_feedback_from_results_af(test_results, log_file_path, cot_count, feedback, assert_af):
    log_content = extract_lines_with_context(log_file_path)
    print("AF Test Results Summary:")
    print(f"SyntaxError: {test_results['syntax_errors']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Assertion error: {test_results['assertion_errors']}")
    if test_results['syntax_errors'] > 0:
        cot_count += 1
        feedback=f"<feedback>The changes you previously made to the focal method is making syntax error. Please correct your changes to ensure the test AssertionError occurs.<log>{log_content}</log> </feedback>" 
    elif test_results['assertion_errors'] > 0: #or test_results['failed'] > 0 or test_results['errors'] > 0:
        print("AF Test Results Summary:")
        print(f"Assertion Errors: {test_results['assertion_errors']}")
        assert_af = True
    elif test_results['passed'] > 0:
        cot_count += 1
        feedback=f"<feedback>The changes you previously made to the focal method is making test pass. Please correct your changes to ensure the test AssertionError occurs. </feedback>"
    else:
        cot_count += 1
        feedback=f"<feedback>The changes you previously made to the focal method is making test error. Please correct your changes to ensure the test AssertionError occurs.<log>{log_content}</log> </feedback>"

    #print(feedback) 
    return feedback, cot_count, assert_af

def generate_feedback_from_results_cc(test_results, log_file_path, cot_count, feedback, test_pass, reduced_cc, coverage_percentage):
    #print('log_file_path=', log_file_path, ',coverage_percentage=',coverage_percentage)
    log_content = extract_lines_with_context(log_file_path)
    if test_results:
        print("CC Test Results Summary:")
        print(f"Passed: {test_results['passed']}")
        print(f"Failed: {test_results['failed']}")
        print(f"Errors: {test_results['errors']}")
        print(f"Skipped: {test_results['skipped']}")
    if test_results['failed'] > 0 or test_results['errors'] > 0 or test_results['skipped'] > 0: 
        cot_count += 1 
        print('test failure happened ***, cot_count=', cot_count)
        #fail_reason = extract_failure_reasons(log_content)
        feedback=f"<feedback>The changes you previously made to the focal method are causing the test error. Please correct your changes to ensure the test passes while minimizing the code coverage by the provided test code. <failure_log> {log_content} </failure_log> </feedback>"
    elif test_results['passed']:
        if coverage_percentage == "":
            reduced_cc = True
            print('Not 100% coverage means empty=', type(coverage_percentage), ",", coverage_percentage ) 
        #check the code coverage difference from the original #../test_analysis/Results/1072_tests_with_Focal_Methods_with_code_coverage.csv 
        #check_coverage_difference()  
        test_pass = True
    
    return feedback, cot_count, test_pass, reduced_cc

def save_fm_logs(prompt, response):
    with open("fm_prompt.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([prompt])
        writer.writerow("*******************") 

    with open("fm_claude_response.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow("************Code to put into SUT**************")
        writer.writerow([response]) 

def check_cc_coverage(coverage_percentage, cot_count, feedback):
    if coverage_percentage: 
        cot_count += 1 
        print('100%_coverage_percentage=', cot_count)
        feedback="<feedback>The changes you previously made is 100% covered by the given unit test. Please make your changes to ensure the test passes while minimizing the code coverage by the provided test code.<Goal>Is to reduce code coverage</Goal></feedback>"
    return feedback, cot_count

def initialization():
    #test_pass = False
    #reduced_cc = False
    #assert_af = False
    test_pass = reduced_cc = assert_af = attribute_error = type_error = name_error = value_error = False
    return test_pass, reduced_cc, assert_af, attribute_error, type_error, name_error, value_error

def collect_prompt_or_check_break_condition_reaches_af(cot_count, threshold_to_cot, assert_af, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, unit_test_body, fm_body):
    if cot_count > threshold_to_cot: 
        if not assert_af:
            fail_to_get_changed_fm(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, str(cot_count)) # save into the result file if we are unsuccessful
        return "Cot_count_exceed_Threshold"
    elif assert_af:
        return "assert_fail_found"
    else:
        print('Coming back to generate prmpt again ...:unit_test_name=', unit_test_name,fm_name)
        prompt = generate_promt_for_change_curation_to_test_fail(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_body, fm_file_content, fm_name, fm_lines, feedback)
        return prompt

def collect_prompt_or_check_break_condition_reaches_cc(cot_count, threshold_to_cot, test_pass, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, unit_test_body, fm_body, reduced_cc):
    if cot_count > threshold_to_cot: # last number e giyeo pass hote pare
        if not test_pass:
            fail_to_get_changed_fm(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, "aim_to_reduce_coverage", claude_result_file, str(cot_count)) # save into the result file that we are failed
        #print('cot_count exceeds threshold_to_cot****')
        return "Cot_count_exceed_Threshold"
    elif test_pass and reduced_cc:
        print('Both test_pass and reduced_cc ***')
        return "test_pass_and_reduced_cc"
    else:
        #print('**** PROMPT ****')
        #print('**** cot_count = ', cot_count, ', threshold_to_cot=', threshold_to_cot)
        if cot_count == 0:
            prompt = generate_promt_for_change_curation_to_reduce_cc(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_body, fm_file_content, fm_name, fm_lines, feedback)
        else:
            print('cot_count>0: feedback=', feedback)
            prompt = feedback
        return prompt

if __name__ == "__main__":
    file_path = sys.argv[1] #Results/Combined_result_of_fm_and_tests.csv
    objective = sys.argv[2] #CC (Code Coverage) or AF (Assertion Failure)
    file_name = file_path.split('/')[-1]
    df = pd.read_csv(file_path)

    outputDir = "Results"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)
    
    for index, row in df.iterrows():
        session_memory = {}
        # Initialize the Bedrock client
        bedrock_client = BedrockClientWithAutoRefresh(role_arn, session_name, region_name)
        claude = Claude(bedrock_client, session_memory)
        row_data = data_from_row(row)
        if row_data is None:
            continue
        proj_name, test_file_path, unit_test_name, test_lines, fm_file_path, fm_name, fm_lines, fm_file_content, test_file_content = row_data

        unit_test_body = get_function_code(test_file_path, unit_test_name)
        fm_body = get_function_code_fm(fm_file_path, fm_name, fm_lines) #added the change into CUT by removing existing method code
        test_pass, reduced_cc, assert_af, attribute_error, type_error, name_error, value_error = initialization()

        cot_count = 0 #chain of thought
        log_content = ""
        feedback = ""
        threshold_to_cot = 3
        while True:
            if objective == "CC":
                claude_result_file = "Results/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv"
                prompt=collect_prompt_or_check_break_condition_reaches_cc(cot_count,threshold_to_cot, test_pass, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, unit_test_body, fm_body, reduced_cc)
                #print('prompt***=', prompt)
                if prompt == "Cot_count_exceed_Threshold":
                    #print('========CC cot count exceed threshold ========')
                    break 
                elif prompt == "test_pass_and_reduced_cc":
                    print("========Entering test_pass_and_reduced_cc")
                    break

            elif objective == "AF":
                claude_result_file = "Results/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv"
                prompt=collect_prompt_or_check_break_condition_reaches_af(cot_count,threshold_to_cot, assert_af, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, unit_test_body, fm_body)
                if prompt == "Cot_count_exceed_Threshold" or prompt == "assert_fail_found":
                    break 

            #if cot_count > 0: # if test_error found and not crossed the threshold_to_cot
                #print('Going to call COT')
            response = claude.infer_using_claude(prompt, True) # This is the changed_code, True is for cot
            #else:
            #    response = claude.infer_using_claude(prompt) # This is the changed_code

            #Checking if the generated output is in the correct format
            #==========================================================
            cleaned_code, changes_types = check_llm_response(response, "fm")
            if cleaned_code == "incomplete_changed_fm": # looking if tag exists or not
                cot_count += 1 
                #print('incomplete***, cot_count=', cot_count)
                feedback="</feedback>Your previously generated changed focal method is incomplete. Please give a complete changed focal method.</feedback>"
                continue
            elif cleaned_code != "":
                response = cleaned_code 
            #==========================================================
            hack_into_sut(response, fm_file_path, fm_name, fm_lines)  
            log_file_path =  "test_run_logs_after_fm_changed/log_"+proj_name+"_"+unit_test_name+"_"+fm_name+"_"+objective+"_claude_"+str(cot_count)
            print('log_file_name=', log_file_path)
            if objective == "CC":
                coverage_percentage = run_test(response, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective)
                feedback, cot_count = check_cc_coverage(coverage_percentage, cot_count, feedback)

            elif objective == "AF":
                #log_file_path =  "test_run_logs_after_fm_changed/log_"+proj_name+"_"+unit_test_name+"_"+fm_name+"_"+objective+"_claude_"+str(cot_count)
                run_test(response, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective) 
            
            save_fm_logs(prompt, response)
            log_content, test_results = read_log_file(log_file_path, objective) 
 
            if objective == "CC":
                feedback, cot_count, test_pass, reduced_cc = generate_feedback_from_results_cc(test_results, log_file_path, cot_count, feedback, test_pass, reduced_cc, coverage_percentage)  
            elif objective == "AF":
                #print('calling to get feedback **********************')
                feedback, cot_count, assert_af = generate_feedback_from_results_af(test_results, log_file_path, cot_count, feedback, assert_af)

            time.sleep(5)
              
        #exit()

