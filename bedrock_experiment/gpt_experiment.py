import openai
import pandas as pd
import boto3
import sys
import os
import json
import time
import csv
from prompt_engineering import generate_promt_for_change_curation_to_reduce_cc, generate_promt_for_change_curation_to_test_fail
from modify_python_file import hack_into_sut
from change_curation_helper import get_function_code, check_llm_response, run_test, parse_test_log, extract_failure_reasons, fail_to_get_changed_fm, read_log_file

def query_gpt(prompt, temperature=0, top_p=0.9):
    # Set up OpenAI API key
    #openai.api_key = api_key

    # Create the payload for OpenAI's API
    payload = {
        #"model": "gpt-4",  # Update to the desired model version
        #model="gpt-3.5-turbo-0125",  # Adjust if necessary
        "model":"gpt-4o-mini-2024-07-18",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": temperature,
        "top_p": top_p
    }

    # Invoke the model using OpenAI's API
    response = openai.ChatCompletion.create(**payload)

    # Extract the text response from the API response
    text_response = response["choices"][0]["message"]["content"]

    return text_response

if  __name__ == "__main__":

    file_path = sys.argv[1] #https://github.com/UT-SE-Research/Predict-Flakies-Paper/blob/master/scripts/data/victim.csv
    openai.api_key = "sk-proj-rphBYFI8kCa1t3ACErdOT3BlbkFJYU0B9SUqKdAEnWHUliVP" 

    file_name = file_path.split('/')[-1]
    df = pd.read_csv(file_path)
    #print(filename)
    for index, row in df.iterrows():
        #print(f"Processing row {index}:")
        #print(f"Project Name: {row['proj_name']}")
        proj_name = row['proj_name'] 
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
        print("-----\n")
        outputDir = "Results"
        if not os.path.exists(outputDir):
            os.makedirs(outputDir, exist_ok=True)
        unit_test_body = get_function_code(test_file_path, unit_test_name)
        #print("**************")
        test_pass = False
        reduced_cc = False
        chain_count_cc = 0
        log_content = ""
        feedback = ""
        threshold_to_try = 5
        gpt_result_file = "Results/GPT_690_tests_with_Changed_FM_CC.csv"
        while not test_pass and not reduced_cc:
            if chain_count_cc > threshold_to_try:
                fail_to_get_changed_fm(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, "aim_to_reduce_coverage", gpt_result_file, str(chain_count_cc))
                break
            else:
                if chain_count_cc > 0: # if test_error found
                    prompt_to_reduce_code_coverage = generate_promt_for_change_curation_to_reduce_cc(test_file_path, test_file_content, unit_test_name, test_lines, fm_file_path, fm_file_content, fm_name, fm_lines, feedback, log_content)
                else:
                    prompt_to_reduce_code_coverage = generate_promt_for_change_curation_to_reduce_cc(test_file_path, test_file_content, unit_test_name, test_lines, fm_file_path, fm_file_content, fm_name, fm_lines, feedback)
            #print(prompt_to_reduce_code_coverage)
            #exit()         
            
            with open("GPT_prompt.csv", mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(prompt_to_reduce_code_coverage) 

            response = query_gpt(prompt_to_reduce_code_coverage)
            print(response) 
            #if response: 
            #    response_content = response['choices'][0]['message']['content']
            #
            #    print("RESPONSE CONTENT =============================")
            #    print(response_content)
                
            #Checking if the generated output is in the correct format
            #==========================================================
            cleaned_code = check_llm_response(response)
            if cleaned_code == "incomplete_changed_fm":
                #print('=======go and will ask to generate prompt again==========')
                feedback="Your previously generated changed focal method is incomplete. Please give a complete changed focal method."
                continue
            elif cleaned_code != "":
                response = cleaned_code 
            #==========================================================

            #exit() 
            hack_into_sut(response, fm_file_path, fm_name, fm_lines)  

            run_test(response, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, "aim_to_reduce_coverage", gpt_result_file, proj_name, str(chain_count_cc),"GPT")
            #look for logs, then will decide 
            test_results = read_log_file("test_run_logs_after_fm_changed/log_"+proj_name+"_"+unit_test_name+"_aim_to_reduce_coverage_GPT_"+str(chain_count_cc))
            
            if test_results:
                print("Test Results Summary:")
                print(f"Passed: {test_results['passed']}")
                print(f"Failed: {test_results['failed']}")
                print(f"Errors: {test_results['errors']}")
                print(f"Skipped: {test_results['skipped']}")
            if test_results['passed'] > 0:
                test_pass = True
                reduced_cc = True
            else:
                chain_count_cc += 1 
                fail_reason = extract_failure_reasons(log_content)
                feedback=f"Your previously generated changed focal method is not making test pass. Here is the test outcome: ``` {fail_reason} ```"
            time.sleep(5)
            #exit()
