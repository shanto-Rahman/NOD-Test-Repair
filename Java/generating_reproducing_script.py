import time
import csv
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import sys
from utils import set_seed, setup_logging, seed_worker, qwen_model_define, parse_category_and_token_list, init_setup, contains_english_letter,  deep_seek_coder_model_define, llama3_8b_model_define, codegemma7b_model_define, gemma2b_model_define, gemma7b_model_define
import pandas as pd
import os
import numpy as np
import json
from sklearn.metrics import confusion_matrix, classification_report
import re
from collections import Counter
import torch.nn.functional as F
#from Testing_gemma_7b_categorization import parse_generated_output_to_get_category
#from Testing_gemma_2b_categorization  import identify_test_category
import transformers 
from prompt_engineering import generate_prompt
import torch
import openai

login(token="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")

def gpt_score_finder(prompt, definition, max_retries=1):
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": definition},
                    {"role": "user", "content": prompt}
                ],
                #temperature=1,
            )
            return response
        except openai.error.APIError as e:
            # Check if it's a server-side error (500, 502, 503, etc.)
            if hasattr(e, 'response') and e.response.status_code >= 500:
                print(f"Server error ({e.response.status_code}). Retrying in {initial_wait * (2 ** retry_count)} seconds.")
                time.sleep(initial_wait * (2 ** retry_count))  # Exponential backoff
                retry_count += 1
            else:
                print(f"API error: {str(e)}")
                raise  # Re-raise the exception for non-server-side errors or if retries are exhausted
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error: {str(e)}")
            raise 
    print("Max retries reached, unable to complete request.")
    return None 

def gpt_output_calculate(test_code, ml_technique, code_under_test_meths, failure_log):
    prompt, definition = generate_prompt(failure_log, code_under_test_meths, test_code)
    response = gpt_score_finder(prompt, definition)
    if response: 
        response_content = response['choices'][0]['message']['content']
        
        print("RESPONSE CONTENT =============================")
        print(response_content)
    
        #scores = response_content.split()
        #print("SCORES:")
        #print(scores)
 
    

def give_test_data_in_chunks_qwen(test_meth_code_df, tokenizer, model, device, ml_technique, code_under_test_meths, failure_log_df):
    max_length = 1024
    n = 1  # len(x_test) / batch_size
    preds_chunks = None
    paired_data = []
    total_preds = []
    category_token_map = {}  # Dictionary to store tokens per category
    count = 0
    top_tokens_per_test = []
    #categories, MAX_LENGTH = categories_defination_and_tokenizers_max_length()
    MAX_LENGTH = 2048
    model.eval()  # Set the model to evaluation mode
    prompt = f"""
    I have an async-wait flaky test that sometimes passes and fails unpredictably.
    When the test fails, it produces the following failure log:
    #Failure
    {failure_log_df}

    Below is the code that is executed during the test run:    
    #Code-Under-Test
    {code_under_test_meths}
    
    And here is the test code itself:
    
    #Test-Code
    {test_meth_code_df}
    
    Your task is to modify the code under test so that the test fails consistently, as shown in the failure log. Do not change the test code itself. Ensure that the modifications do not alter the intended behavior of the code under test, except to make the failure reproducible.
    
    Please provide your modified code within the following format:
    
    <Output>
    Modified_code:
    <Your modified code here>
    </Output>
    """
    definitions = """You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code."""
    
    messages = [
        {"role": "system", "content": definitions},
        {"role": "user", "content": prompt}
    ]
    print(messages)
    
    text = tokenizer.apply_chat_template(
           messages,
           tokenize=False,
           add_generation_prompt=True
    )

    model_inputs = tokenizer([text], return_tensors="pt",
        max_length=MAX_LENGTH,  # Truncate long inputs
            truncation=True
    ).to(model.device)

    outputs = model.generate(
            **model_inputs,
            max_new_tokens=500,
            eos_token_id=tokenizer.eos_token_id,
            do_sample=False,  # Use deterministic sampling
            temperature=0,  # Slightly lower temperature for more focused predictions
            return_dict_in_generate=True,  # Return full output including attention
            #output_attentions=True  # Capture attention weights
        )
    #print(outputs.keys())
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, outputs.sequences)
    ]
    changed_code = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    print(changed_code)
    exit()

    return "" #, category_token_map, top_tokens_per_test


def give_test_data_in_chunks_deep_seek_coder(x_test_nparray, tokenizer, model, batch_size, device, fold, y_test_nparray, ml_technique): 
    x_test_df = pd.DataFrame(x_test_nparray)
    y_test_df = pd.DataFrame(y_test_nparray, columns=['category'])  # Convert to DataFrame
    print(y_test_df)
    n = 1  # len(x_test) / batch_size
    preds_chunks = None
    paired_data = []
    total_preds = []
    top_tokens_per_test = []
    category_token_map = {}  # Dictionary to store tokens per categoy
    count = 0
    categories, MAX_LENGTH = categories_defination_and_tokenizers_max_length()

    MAX_LENGTH = 1600  # Or 8192, based on your model
    model.eval()  # Set the model to evaluation mode
    #for index, row in x_test_df.iterrows():
    for index, (test_data, actual_label) in enumerate(zip(x_test_df['full_code'], y_test_df['category'])):
        print("****fold=", fold)
        definitions = f"""You are an expert at identifying flaky tests. Flaky tests are tests that pass and fail non-deterministically for the same code. You are given a test with the category, and you have to tell me how 
check whether it is flaky or not. If it is flaky, you have to identify the type of flakiness and classify into one of the following categories or just say Not Flaky: 
        1. Async wait: The test execution makes an asynchronous call and does not properly wait for the result of the call to be available before proceeding. This can lead to non-deterministic test outcomes. 
        2. Concurrency: Test non-determinism is due to different threads interacting in a non-desirable manner (but not due to asynchronous calls from the Async Wait category), e.g., due to data races, atomicity violations, or deadlocks. 
        3. Time: Relying on the system time introduces non-deterministic failures, e.g., a test may fail when the midnight changes in the UTC time zone. Some tests also fail due to the precision by which time is reported as it can vary from one platform to another. 
        4. Unordered collection: In general, when iterating over unordered collections (e.g., sets), the code should not assume that the elements are returned in a particular order. If it does assume, the test outcome can become non-deterministic as different executions may have a different order.
        5. Test Order dependent test: The test depends on the order of execution of other tests. If the order changes, the test outcome may change. 
        6. Not Flaky: The test is not flaky due to the above reasons."""
        #test_data = row['full_code']

        prompt = f"""
        Classify the given test as one of the following categories: Async wait or Concurrency or Time or Unordered collection or Order dependent test or non-flaky.
        Test:
        {test_data}                        
        **Output Format (MUST follow this format exactly):**
        ```
        Category: <one of the six categories above>
        ``` 
        """

        messages = [
            #{"role": "system", "content": definitions},
            {"role": "user", "content": prompt}
        ]
        #model_inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", padding=True,  max_length=MAX_LENGTH, truncation=True).to(model.device)
        formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True, max_length=MAX_LENGTH, truncation=True).to(model.device)


        input_ids = model_inputs["input_ids"]
        attention_mask = model_inputs["attention_mask"]
        # tokenizer.eos_token_id is the id of <｜end▁of▁sentence｜>  token
        outputs = model.generate(
            #inputs, 
            #input_ids=input_ids,
            #attention_mask=attention_mask,
            **model_inputs,
            max_new_tokens=50, 
            do_sample=False, 
            top_k=50, 
            top_p=0.95, 
            temperature=0.8,
            num_return_sequences=1, 
            pad_token_id=tokenizer.pad_token_id,  # Set pad_token_id explicitly
            eos_token_id=tokenizer.eos_token_id,
            output_attentions=True  # Capture attention weights
        )
        #output_category = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)

        print(outputs)
        # Check if "sequences" exists in outputs
        if isinstance(outputs, torch.Tensor):
            print("outputs is a torch.tensor")
            sequences = outputs  # If `outputs` is a tensor, use it directly
            # Extract generated tokens from outputs (excluding input tokens)
            generated_tokens = outputs[:, input_ids.shape[1]:]  # Slice out the new tokens
            
            # Decode the generated tokens
            output_text = tokenizer.decode(generated_tokens[0].tolist(), skip_special_tokens=True).strip()
            
            print("Decoded Output:", output_text)

        print("Raw model output:", output_text)

        category = parse_category_and_token_list(output_text)
        print("category=", category)

        output_category_lower = category.lower()
        #Calculating IG
        top_token_list = collect_token_list_by_applying_ig(model_inputs, prompt, tokenizer, model, test_data, ml_technique)

        # Print only the tokens (no scores)
        print("\n✅ Top-20 Tokens Based on Attribution Scores:")
        print(top_token_list)

        category_value = categories.get(output_category_lower, 6)  # Return -1 if category not found
        print('category_value=')
        print(category_value)
        total_preds.append(category_value)
        top_tokens_per_test.append(top_token_list)

        if category_value not in category_token_map:
            category_token_map[category_value] = []  # Initialize empty list if not exists

        if top_token_list:
            category_token_map[category_value].extend(top_token_list)  # Append tokens for the category
        else:
            category_token_map[category_value] = []  # Store empty list for large test cases

        print("\nFinal Category-Token Map:", category_token_map)
        #exit()
    #return total_preds, category_token_map
    return total_preds, category_token_map, top_tokens_per_test

def run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, failure_log_csv):
    device, ml_technique, dataset_category, output_layer, where_data_comes = init_setup(technique, data_name_dir)
    
    if ml_technique == "qwen":
        print('I am qwen')
        model_name, tokenizer, auto_model = qwen_model_define()
    elif ml_technique == "llama3_8b":
        model_name, tokenizer, auto_model = llama3_8b_model_define()
    elif ml_technique == "deep_seek_coder":
        model_name, tokenizer, auto_model = deep_seek_coder_model_define()
    elif ml_technique == "gpt":
         #openai.api_key = "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"
    else:
        print('model name not correct')
        exit()
    execution_time = time.time()
    print("Start time of the experiment", execution_time)
    #no_splits = 10 # For FlakiCat=4, IDOFT=10
    TN = FP = FN = TP = 0
    project_group = 0
    total_execution_time = 0
    #no_split = 5
    global_category_token_map = {}
    predictions_per_project_group = {}
    ground_truth_per_project_group = {}
    tokens_per_project_group = {}
    Org_test_per_project_group = {}
    #print(len(input_data))

    test_meth_code_df = pd.read_csv(test_code_csv) #read_data(test_code_csv)
    failure_log_df = pd.read_csv(failure_log_csv)
    test_code = test_meth_code_df.iloc[0] 
    failure_log = failure_log_df.iloc[0]

    df = pd.read_csv(
        dataset_path,
            quoting=csv.QUOTE_ALL,
                encoding='utf-8',
                    engine='python'
                    )
    code_under_test_meths = df['Body'].tolist()

    #pd.read_csv(dataset_path['Body'])
    print(failure_log)
    print(test_code)
    #model = auto_model

    if ml_technique == "qwen":
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_qwen(test_code, tokenizer, auto_model, device, ml_technique, code_under_test_meths, failure_log)
 
            #X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
            print('***************** All preds=')
            print(preds)
    

    elif ml_technique == "llama3_8b":
        #model_name, tokenizer, auto_model = llama3_8b_model_define()
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_llama3_8b(X_test, tokenizer, auto_model, batch_size, device, project_group, test_y.numpy(), ml_technique)
    elif ml_technique == "deep_seek_coder":
        #model_name, tokenizer, auto_model = deep_seek_coder_model_define()
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_deep_seek_coder(X_test, tokenizer, auto_model, batch_size, device, project_group, test_y.numpy(), ml_technique)
    elif ml_technique == "gpt":
        gpt_output_calculate(test_code, ml_technique, code_under_test_meths, failure_log)
    else:
        print('no model name found')

    #predictions_per_project_group[f"Fold_{project_group}"] = preds
    #tokens_per_project_group[f"Fold_{project_group}"] = top_tokens_per_test
    #ground_truth_per_project_group[f"Fold_{project_group}"] = test_y
    #Org_test_per_project_group[f"Fold_{project_group}"] = X_test

    ## Merge tokens from the current project_group into the global category-token map
    #for category, tokens in category_token_map.items():
    #    if category not in global_category_token_map:
    #        global_category_token_map[category] = []  # Initialize list if category not present
    #    global_category_token_map[category].extend(tokens)  # Append tokens from current project_group

    #cr=classification_report(test_y, preds)
    #print(type(cr))
    #parse_cr(cr, technique, str(project_group))
    #
    #with open(where_data_comes+"-result/classification_report_"+str(project_group)+"project_groups_"+str(project_group), "a") as file:
    #    file.write("Fold="+str(project_group)+"\n")
    #    file.write(cr)
    #    file.write("\n")
    #
    #cm = confusion_matrix(test_y, preds)
    ##print(cm)
    #
    #with open(where_data_comes+"-result/confusion_matrix_"+str(project_group)+"project_groups_"+str(project_group), "a") as file:
    #    file.write("Fold="+str(project_group)+"\n")
    #    file.write(np.array2string(cm))
    #    file.write("\n")
    
    #tn, fp, fn, tp = confusion_matrix(test_y, preds, labels=[0, 1]).ravel()
    #TN = TN + tn
    #FP = FP + fp
    #FN = FN + fn
    #TP = TP + tp
    print("delete model")
    del model
    torch.cuda.empty_cache()
    
    #project_group = project_group+1

    #exit()
    #**Merging & Saving is done AFTER the loop**
    '''df_predictions = pd.DataFrame.from_dict(predictions_per_project_group, orient="index").transpose()
    df_tokens = pd.DataFrame.from_dict(tokens_per_project_group, orient="index").transpose()
    
    
    # Rename columns
    df_predictions.columns = [f"Predictions_{col}" for col in df_predictions.columns]
    df_tokens.columns = [f"Tokens_{col}" for col in df_tokens.columns]
    
    # Merge both DataFrames
    df_combined = pd.concat([df_predictions, df_tokens], axis=1)
    
    # Save to CSV
    df_combined.to_csv(where_data_comes+"-result/"+ml_technique+".csv", index=False)    
    print("\nPredictions and tokens saved to llama.csv")'''
    # Initialize empty list to store reshaped data
    reshaped_data = []
    
    # Iterate over each fold
    for fold in predictions_per_project_group.keys():  # Example: "Fold_1", "Fold_2", ...
        preds = predictions_per_project_group[fold]
        tokens = tokens_per_project_group[fold]
        ground_truths = ground_truth_per_project_group[fold]
        org_test = Org_test_per_project_group[fold]
    
        # Iterate over all samples in this fold
        for test_code, pred, token_list, gt in zip(org_test, preds, tokens, ground_truths):
            reshaped_data.append({
                "test_code": test_code,
                "Prediction": pred,
                "Ground_Truth": int(gt.item()) if isinstance(gt, torch.Tensor) else int(gt),
                "Token_List": token_list
            })
    
    # Convert reshaped data to DataFrame
    df_final = pd.DataFrame(reshaped_data)
    
    # Save to CSV
    csv_path = f"{where_data_comes}-result/{ml_technique}.csv"
    df_final.to_csv(csv_path, index=False)
    
    print("\nPredictions and tokens saved to", csv_path)
    exit()


    top_10_tokens_per_category = {}
    for category, tokens in global_category_token_map.items():
        token_counts = Counter(tokens).most_common(10)  # Get top-10 most frequent tokens
        top_10_tokens_per_category[category] = token_counts  # Store as (token, count) pairs

    # Convert to DataFrame for better visualization
    df_token_per_cat = pd.DataFrame.from_dict(
        {category: dict(tokens) for category, tokens in top_10_tokens_per_category.items()},
        orient="index"
    ).transpose()
    
    #df_token_per_cat = pd.DataFrame.from_dict(top_5_tokens_per_category, orient='index').transpose()
    # Display result
    # Print the result in a readable format
    print("\nTop-10 Tokens Per Category:")
    for category, tokens in top_10_tokens_per_category.items():
        #print(f"Category {category}: {tokens}")
        print(f"Category {category}:")
        for token, count in tokens:
            print(f"  - {token}: {count}")

def initialize_environment(seed_value):
    """Initializes the environment by setting the seed and configuring logging."""
    set_seed(seed_value)  # Set the seed for reproducibility
    setup_logging()  # Setup standardized logging

if __name__ == "__main__":
    dataset_path = sys.argv[1] #traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_methods_with_call_labels.csv
    results_file = sys.argv[2] #
    data_name_dir = sys.argv[3] #traces
    technique = sys.argv[4] #deep-seek
    test_code_csv = sys.argv[5] #deep-seek
    fail_log_csv = sys.argv[6] #deep-seek
    initialize_environment(42)
    run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, fail_log_csv)
