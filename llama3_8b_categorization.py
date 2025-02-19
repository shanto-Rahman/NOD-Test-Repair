import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import sys
from open_source_models import set_seed, setup_logging, seed_worker, train, evaluate, parse_cr, llama3_8b_model_define, parse_category_and_token_list
from utils import extract_first_failure_log, extract_open_source_model_output, extract_open_source_model_output_categpory
import pandas as pd
import os
import numpy as np
import json
from sklearn.metrics import confusion_matrix, classification_report
import re
from collections import Counter
from parsing_test_code_info import extract_test_function
from prompt_engineering import generate_prompt_without_any_slice_for_flaky_test_category


#login(token="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")
login(token="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")

timeStart = time.time()

def detection_flaky_test_category(model, proj_name, test_file_path, unit_test_name, failure_message, objective, threshold_to_cot, static_slice_csv_writer, dynamic_trace, claude_result_file, slice_type, start_time, tokenizer, row_index, model_name_arg, unit_test_body):
    device = torch.device("cuda")
    cot_count = 0
    found_category = False
    log_content = ""
    cannot_go_to_next_cot = False
    while True:
        if objective == "category_prediction":
            if cot_count > threshold_to_cot or cannot_go_to_next_cot:
                if not found_category:
                    end_time = time.time()
                    # Calculate the elapsed time
                    elapsed_time = end_time - float(start_time)
                    #fail_to_refine_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, objective, claude_result_file, str(cot_count), dynamic_trace, elapsed_time) # save into the result file if we are unsuccessful
                    print('Failed in finding correct test category ****')
                    break
            if found_category:
                break
            if cot_count == 0:
                if slice_type == "Static": #Will Collect Static Trace
                    #static_slices = generate_static_slice(prompt_static_slices)
                    #print(static_slices)
                    #match_tag = re.search(r'<relevant_program_slice>(.*?)</relevant_program_slice>', static_slices, re.DOTALL)
                    #static_slice_for_context = ""
                    #if match_tag:
                    #    static_slice_for_context = match_tag.group(1).strip()
                    #static_slice_csv_writer.writerow([proj_name, unit_test_name, fm_name, static_slice_for_context])
                    #prompt = generate_prompt_with_static_slices_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, fm_file_path, fm_file_content, changed_fm_code, fm_name, fm_lines, failure_message, diff_fm, static_slice_for_context)
                    print("Static")
                    
                elif slice_type == "Dynamic":
                    print("Will generate the prompt using the dynamic_trace")
                    #prompt = generate_prompt_with_dynamic_traces_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body, unit_test_name, test_lines, failure_message, diff_fm, dynamic_trace)
                else: #No slicing, Tool (OurTechnique)
                    system_definition, prompt = generate_prompt_without_any_slice_for_flaky_test_category(test_file_path, unit_test_body, unit_test_name, failure_message)
            else: # If cot_count > 0
                prompt = failure_message
            print("*** PROMPT=", prompt)
            cleaned_code, cannot_go_to_next_cot = extract_open_source_model_output_categpory(system_definition, prompt, model, device, tokenizer, cot_count, row_index, model_name_arg, unit_test_name, objective)
            #Need to again renaming the test_method name
            print('cleaned_code=',cleaned_code)
            exit()
            if cleaned_code == "":
                if cot_count == 0:
                    failure_message += f"""<human-message>{system_definition}{prompt}</human-message> <AI-message> </AI-message> </instruction>Your previously generated test method is incomplete. Please give a complete changed test method.</instruction>"""
                else:
                    failure_message += f"""</instruction>Your previously generated test method is incomplete. Please give a complete changed test method.</instruction>"""

                cot_count += 1
                continue
            hack_into_test(cleaned_code, test_file_path, unit_test_name, test_lines)
            diff_test, changed_line_numbers_in_fm, diff_in_fm_with_line_numbers = collect_git_diff(test_file_path, "../test_analysis/projects/"+proj_name, proj_name)
            log_file_path = f"test_run_logs_after_fm_changed/log_{proj_name}_{unit_test_name}_{fm_name}_{objective}_{model_name_arg}_{cot_count}"
            changes_types = "changes_type_NA" 
            run_test(cleaned_code, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), model_name_arg, str(changes_types), objective, error_type, diff_fm, changed_fm_code, diff_test, dynamic_trace, "", "", start_time)

            log_content, test_results = read_log_file(log_file_path, objective)
            failure_message = generate_failure_message_from_results(test_results, log_file_path, cot_count, slice_type, fm_file_content, changed_fm_code, diff_fm, test_file_content, unit_test_body, failure_message, unit_test_name, fm_name, dynamic_trace, system_definition, prompt, cleaned_code)
            #print('=========failure_message=',failure_message)
            if failure_message == "":
                print("Empty-Failure Found, Means test pass *****")
                #exit()
            #print(test_results['passed'],  test_results['assertion_errors'], test_results['failed'], test_results['errors'], test_results["syntax_errors"])
            if test_results['passed'] > 0 and  (test_results['assertion_errors'] == 0 and test_results['failed'] == 0 and test_results['errors'] == 0):
                assert_refine_af = True

            cot_count += 1
            time.sleep(2)  # Sleep for 2 seconds (or adjust as necessary)
            #exit()
        
        time.sleep(5)


def data_from_row(row):
    git_proj = row['git_proj'] 

    if git_proj.strip().startswith('#'):
        return None 
    sha = row['sha']
    test_file_path = row['test_file_path']
    test_name = row['test_name']
    test_code = row['test_code']
    start_line = row['start_line']
    end_line = row['end_line']
    #print("row['test_name']=", row['test_name'])
    #test_file_path, test_name = row['test_name'].split("::", 1)
    #print(test_file_path, test_name)
    return git_proj, sha, test_file_path, test_name, test_code, start_line, end_line

if __name__ == "__main__":
    #model_weights_path = sys.argv[2]
    #results_file = sys.argv[3]
    #data_name = sys.argv[4]
    #technique = sys.argv[5]
    #initialize_environment(42)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #pythpn3 llama3_8b_categorization.py data/extracted_tests.csv  llama category_prediction NA
    dataset_path = sys.argv[1] #extracted_tests.csv
    model_name_arg = sys.argv[2] #llama
    objective = sys.argv[3] #category_prediction/ reproducing_failure/ test_repair
    slice_type = sys.argv[4] #NA/ Static/ Dynamic
    threshold_to_cot = 4
    log_dir = os.path.join(script_dir, "logs")

    if model_name_arg  == "deep_seek_coder":
        model_name, tokenizer, auto_model = deep_seek_coder_model_define()
        result_file = "Results/DeepSeekCoder_V2_Instruct_tests_with_Refined_Tests_Meth_AF_with_"+slice_type+"_slice_with_updated_prompt_with_changed_with_runtime.csv"
    elif model_name_arg  == "codellama":
        model_name, tokenizer, auto_model = codellama_7b_instruct_model_define()
        result_file = "Results/Codellama_34b_tests_with_Refined_Tests_Meth_AF_with_"+slice_type+"_slice_with_updated_prompt_with_changed_with_runtime.csv"
    elif model_name_arg  == "llama":
        model_name, tokenizer, auto_model = llama3_8b_model_define()
        result_file = "Results/Llama3_8b_tests_with_Refined_Tests_Meth_AF_with_"+slice_type+"_slice_with_updated_prompt_with_changed_with_runtime.csv"

    #output_data = []  # List to store extracted data
    df = pd.read_csv(dataset_path)
    for index, row in df.iterrows():
        row_data = data_from_row(row)
        if row_data is None:
            continue
        git_proj, sha, test_file_path, test_name, test_code, start_line, end_line = row_data
        proj_name = git_proj.split("/")[-1]
        log_file_name = log_dir +"/"+ proj_name+"_"+test_file_path.replace(".py", "").replace("/", "_")+"_"+test_name.replace("::", "_").replace("/", "_")+".log"
        print(log_file_name)
        print(proj_name)
        print(test_file_path)
        print(test_name)
        fail_logs = extract_first_failure_log(log_file_name)
        #Collecting Dynamic Trace
        dynamic_trace = ""
        slice_csv_writer = ""

        #STEP-1: Ask LLM to know the category of the flaky test
        definition, prompt = generate_prompt_without_any_slice_for_flaky_test_category(test_file_path, test_code, test_name, fail_logs)
        print('definition+prompt=', definition+prompt)
        start_time = time.time()
        detection_flaky_test_category(auto_model, proj_name, test_file_path, test_name, fail_logs, objective, threshold_to_cot, slice_csv_writer, dynamic_trace, result_file, slice_type, str(start_time), tokenizer, index, model_name_arg, test_code) 
        exit()

        #print("projects/"+proj_name+"/"+test_file_path)
        #run_experiment()
        #test_code, start_line, end_line = extract_test_function("projects/"+proj_name+"/"+test_file_path, test_name)
        #print('test_code=', test_code)
        #print('start_line=', start_line)
        #print('end_line=', end_line)
    #    # Append the extracted information into a dictionary
    #    output_data.append({
    #        "git_proj": git_proj,
    #        "test_file_path": test_file_path,
    #        "test_name": test_name,
    #        "test_code": test_code,
    #        "start_line": start_line,
    #        "end_line": end_line
    #    })

    #output_df = pd.DataFrame(output_data)
    ## Save to CSV
    #output_csv_path = "extracted_tests.csv"
    #output_df.to_csv(output_csv_path, index=False)  
    #exit()

    #run_experiment(dataset_path, model_weights_path, results_file, data_name, technique)
