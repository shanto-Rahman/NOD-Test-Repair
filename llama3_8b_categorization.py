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

#def give_test_data_in_chunks(x_test_nparray, tokenizer, model, batch_size, device, fold, y_test_nparray): #BERT
#    #max_length = 1024; 128
#    max_length = 1024
#    x_test_df = pd.DataFrame(x_test_nparray)
#    n = 1 #len(x_test) / batch_size
#    preds_chunks = None
#    paired_data = []
#    model.eval()
#    total_attributions = []
#    total_tokens = []
#    top_tokens_per_test = []
#    total_preds = []
#    vis_data_records_ig = []
#    category_token_map = {}  # Dictionary to store tokens per category
#
#    count = 0
#
#    categories = {
#    "async wait": 0,
#    "concurrency": 1,
#    "time": 2,
#    "unordered collection": 3,
#    "order dependent test": 4,
#    "not flaky": 5
#    }
#
#    y_test_df = pd.DataFrame(y_test_nparray, columns=['category'])  # Convert to DataFrame
#    #for index, row in x_test_df.iterrows():
#    for index, (test_data, actual_label) in enumerate(zip(x_test_df['full_code'], y_test_df['category'])):
#        #test_data = row['full_code']
#        prompt = f"""
#        Classify the given test as one of the following categories: **Async wait, Concurrency, Time, Unordered collection, Order dependent test, or Not Flaky**.
#        
#        **Test:**
#        {test_data}                        
#        
#        **Output Format (MUST follow this format exactly):**
#        ```
#        Category: <one of the six categories above>
#        Tokens: ["token1", "token2", "token3", "token4", "token5"]
#        ```
#        
#        **Important Rules:**
#        - Category: Choose exactly one from the given list.
#        - Tokens:
#            - Provide exactly **5 tokens**.
#            - Each token must be **a single atomic unit** (one word, number, or symbol).
#            - **Do NOT include dots (`.`), spaces, or compound words**.  
#            - **Example of valid tokens:** `"Thread"`, `"sleep"`, `"1000"`, `";"`, `"wait"`  
#            - **Example of INVALID tokens (DO NOT use these!):** `"Thread.sleep"`, `"e.execute"`, `"this.method"`, `"Thread start"`
#
#        **Example of Expected Output:**
#        ```
#        Category: Concurrency
#        Tokens: ["Thread", "lock", "synchronized", "race", "volatile"]
#        ```
#
#        **Example of INVALID Output (DO NOT produce this format!):**
#        ```
#        Category: Concurrency
#        Tokens: ["Thread.sleep", "e.execute", "Thread.start", "race condition", "lock()"]
#        ```
#        """
#        definitions = f"""You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code. You are given a test, and you have to check whether it is flaky or not. If it is flaky, you have to identify the type of flakiness and classify into one of the following categories or just say Not Flaky: 
#        1. Async wait: The test execution makes an asynchronous call and does not properly wait for the result of the call to be available before proceeding. This can lead to non-deterministic test outcomes. 
#        2. Concurrency: Test non-determinism is due to different threads interacting in a non-desirable manner (but not due to asynchronous calls from the Async Wait category), e.g., due to data races, atomicity violations, or deadlocks. 
#        3. Time: Relying on the system time introduces non-deterministic failures, e.g., a test may fail when the midnight changes in the UTC time zone. Some tests also fail due to the precision by which time is reported as it can vary from one platform to another. 
#        4. Unordered collection: In general, when iterating over unordered collections (e.g., sets), the code should not assume that the elements are returned in a particular order. If it does assume, the test outcome can become non-deterministic as different executions may have a different order. 
#        5. Test Order dependent test: The test depends on the order of execution of other tests. If the order changes, the test outcome may change. 
#        6. Not Flaky: The test is not flaky due to the above reasons."""
#        messages = [
#        {"role": "system", "content": definitions}, #I can specify the output format as the json
#        {"role": "user", "content": prompt},
#        ]
#       
#        input_ids = tokenizer.apply_chat_template(
#            messages,
#            add_generation_prompt=True,
#            return_tensors="pt"
#        ).to(model.device)
#
#        terminators = [
#            tokenizer.eos_token_id,
#            tokenizer.convert_tokens_to_ids("<|eot_id|>")
#        ]
#        
#        outputs = model.generate(
#            input_ids=input_ids,
#            #attention_mask=attention_mask,
#            max_new_tokens=50,
#            #max_length=25,
#            eos_token_id=tokenizer.eos_token_id,
#            do_sample=False,
#            temperature=0.8,
#            top_p=1,
#        )
#        response = outputs[0][input_ids.shape[-1]:]
#        output_category = tokenizer.decode(response, skip_special_tokens=True)
#        print('output_category=',output_category)
#        category, tokens = parse_category_and_token_list(output_category)
#        print("Extracted Category:", category)
#        print("Extracted Tokens:", tokens)
#
#        #output_category_lower = output_category.lower()
#        category_value = categories.get(category.lower().strip(), 6)  # Return -1 if category not found
#        print(category_value)
#    
#        total_preds.append(category_value)
#        top_tokens_per_test.append(tokens)
#
#        # Store tokens in dictionary
#        #if category_value != -1:  # Valid category
#
#        if category_value == actual_label:
#            if category_value not in category_token_map:
#                category_token_map[category_value] = []  # Initialize empty list if not exists
#            category_token_map[category_value].extend(tokens)  # Append tokens for the category
#            print("\nFinal Category-Token Map:", category_token_map)
#
#    return total_preds, category_token_map, top_tokens_per_test
#
#
#def preprocess_data(dataset_path, technique):
#    which_dataset=technique.split("-")[1]
#    where_data_comes=data_name.split("-")[0]
#    dataset_category=technique.split("-")[1]
#    
#    df = pd.read_csv(dataset_path)
#    input_data = df['full_code'] # use the 'full_code' column to run Flakify using the full code instead of pre-processed code
#    #print(len(input_data))
#    out_layer=""
#    target_data = ""
#    if which_dataset == "Flakicat":
#        print("It is Flakicat")
#        out_layer = 6 # if Flakicat dataset
#        target_data = df['category']
#    
#    elif which_dataset == "IDoFT_6Cat":
#        out_layer = 7 # if Flakicat dataset
#        target_data = df['category']
#    
#    elif dataset_category == "IDoFT_2Cat":
#        out_layer=2
#        target_data = df['flaky'] # For multi-class
#    return input_data, target_data, out_layer, dataset_category
#
#def run_experiment(dataset_path, model_weights_path, results_file, data_name, technique):
#    # specify GPU
#    #device = torch.device("cuda")
#    device = torch.device("cpu")
#    #print(torch.cuda.is_available())  # This should return True if CUDA is available
#
#    input_data, target_data, output_layer, dataset_category= preprocess_data(dataset_path, technique)
#    where_data_comes = data_name.split("-")[0]
#
#    model_name, tokenizer, auto_model = llama3_8b_model_define()
#
#    execution_time = time.time()
#    print("Start time of the experiment", execution_time)
#    #no_splits = 10 # For FlakiCat=4, IDOFT=10
#    TN = FP = FN = TP = 0
#    fold_number = 0
#    total_execution_time = 0
#    no_split = 5
#    #print(len(input_data))
#    global_category_token_map = {}
#    predictions_per_fold = {}
#    tokens_per_fold = {}
#
#    for fold in range(no_split):
#        print('fold_number=',fold)
#
#        if os.path.exists("Flakicat_Categorization-result/score_fold"+str(fold)+"_Class.txt"):
#            os.remove("Flakicat_Categorization-result/score_fold"+str(fold)+"_Class.txt")
#        fit_time=0
#        bert_flag=0
#        total_execution_time = 0
#        feature_extraction_time=0
#        #total_execution_time_for_feature_extraction = 0
#        print(" NOW IN FOLD NUMBER", fold)
#    
#        X_train_df = pd.read_csv(data_name+'/data_splits/X_train_fold'+str(fold)+'.csv')
#        Y_train_df = pd.read_csv(data_name+'/data_splits/y_train_fold'+str(fold)+'.csv')
#    
#        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'deadcode_perturbation_Most_important_features.csv')
#        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'printStatement_perturbation_Most_important_features.csv')
#        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'variableDeclare_perturbation_Most_important_features.csv')
#        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'multiLine_comment_perturbation_Most_important_features.csv')
#        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'singleLine_comment_perturbation_Most_important_features.csv')
#        print(data_name+'/data_splits/X_test_fold'+str(fold)+'.csv')
#        X_test_df = pd.read_csv(data_name+'/data_splits/X_test_fold'+str(fold)+'.csv')
#        Y_test_df = pd.read_csv(data_name+'/data_splits/y_test_fold'+str(fold)+'.csv')
#        #print(len(X_test_df))
#        #print(len(Y_test_df))
#        #exit()
#    
#        X_test = X_test_df['full_code']
#        y_test = Y_test_df['category']
#    
#        X_train = X_train_df['full_code']
#        y_train = Y_train_df['category']
#   
#        #tokenizer_instance = Tokenizer(tokenizer)
#        #tokens_train = tokenizer_instance.tokenize_training_data(X_train)
#        #tokens_test = tokenizer_instance.tokenize_test_data(X_test)
#
#        #Y_train = pd.DataFrame(y_train)
#        y_test = pd.DataFrame(y_test)
#    
#        #Y_train.columns = ['which_tests']
#        y_test.columns = ['which_tests']
#    
#        # convert labels of train, validation and test into tensors
#        #train_y = torch.tensor(Y_train['which_tests'].values)
#        test_y = torch.tensor(y_test['which_tests'].values)
#    
#        #tensor_converter = TensorConverter()
#        #train_seq, train_mask = tensor_converter.convert_train_to_tensors(tokens_train)
#        #test_seq, test_mask = tensor_converter.convert_test_to_tensors(tokens_test)
#
#        # create data_loaders for train and validation dataset
#        batch_size = 1
#
#        #data_loader_factory = DataLoaderFactory(batch_size, seed_worker)
#        #train_dataloader = data_loader_factory.create_train_loader(train_seq, train_mask, train_y)
#        #print(X_test.head(5))
#        #print(test_y.head(5))
#
#        model = auto_model
#        
#        # push the model to GPU
#        #model = model.to(device)
#    
#        print(f"Expected number of predictions: {len(X_test)}")  # Should be 137
#        print(f"Actual number of labels (test_y): {len(y_test)}")   # Is 135, should be 137
#        with torch.no_grad():
#            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks(X_test, tokenizer, model, batch_size, device, fold, test_y.numpy())
#            print('All preds=')
#            print(preds)
#            print(top_tokens_per_test)
#        predictions_per_fold[f"Fold_{fold}"] = preds
#        tokens_per_fold[f"Fold_{fold}"] = top_tokens_per_test
#        #exit()
#    
#        
#        # Merge tokens from the current fold into the global category-token map
#        for category, tokens in category_token_map.items():
#            if category not in global_category_token_map:
#                global_category_token_map[category] = []  # Initialize list if category not present
#            global_category_token_map[category].extend(tokens)  # Append tokens from current fold
#
#        cr=classification_report(test_y, preds)
#        print(type(cr))
#        parse_cr(cr, technique, str(fold))
#    
#        with open(where_data_comes+"-result/classification_report_"+str(no_split)+"folds_"+str(fold), "a") as file:
#            file.write("Fold="+str(fold)+"\n")
#            file.write(cr)
#            file.write("\n")
#    
#        cm = confusion_matrix(test_y, preds)
#        #print(cm)
#    	
#        with open(where_data_comes+"-result/confusion_matrix_"+str(no_split)+"folds_"+str(fold), "a") as file:
#            file.write("Fold="+str(fold)+"\n")
#            file.write(np.array2string(cm))
#            file.write("\n")
#    
#        tn, fp, fn, tp = confusion_matrix(test_y, preds, labels=[0, 1]).ravel()
#        TN = TN + tn
#        FP = FP + fp
#        FN = FN + fn
#        TP = TP + tp
#        print("delete model")
#        del model
#        torch.cuda.empty_cache()
#        #exit()    
#        fold = fold+1
#
#    #**Merging & Saving is done AFTER the loop**
#    df_predictions = pd.DataFrame.from_dict(predictions_per_fold, orient="index").transpose()
#    df_tokens = pd.DataFrame.from_dict(tokens_per_fold, orient="index").transpose()
#    
#    # Rename columns
#    df_predictions.columns = [f"Predictions_{col}" for col in df_predictions.columns]
#    df_tokens.columns = [f"Tokens_{col}" for col in df_tokens.columns]
#    
#    # Merge both DataFrames
#    df_combined = pd.concat([df_predictions, df_tokens], axis=1)
#    
#    # Save to CSV
#    df_combined.to_csv("llama.csv", index=False)    
#    print("\nPredictions and tokens saved to llama.csv")
# 
#    top_10_tokens_per_category = {}
#    for category, tokens in global_category_token_map.items():
#        token_counts = Counter(tokens).most_common(10)  # Get top-10 most frequent tokens
#        top_10_tokens_per_category[category] = token_counts  # Store as (token, count) pairs
#
#    # Convert to DataFrame for better visualization
#    df_token_per_cat = pd.DataFrame.from_dict(
#        {category: dict(tokens) for category, tokens in top_10_tokens_per_category.items()},
#        orient="index"
#    ).transpose()
#    
#    #df_token_per_cat = pd.DataFrame.from_dict(top_5_tokens_per_category, orient='index').transpose()
#    # Display result
#    # Print the result in a readable format
#    print("\nTop-10 Tokens Per Category:")
#    for category, tokens in top_10_tokens_per_category.items():
#        #print(f"Category {category}: {tokens}")
#        print(f"Category {category}:")
#        for token, count in tokens:
#            print(f"  - {token}: {count}")
#
#
#def initialize_environment(seed_value):
#    """Initializes the environment by setting the seed and configuring logging."""
#    set_seed(seed_value)  # Set the seed for reproducibility
#    setup_logging()  # Setup standardized logging
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
            cleaned_code, cannot_go_to_next_cot = extract_open_source_model_output_categpory(system_definition, prompt, model, device, tokenizer, cot_count, row_index, model_name_arg, unit_test_name)
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
