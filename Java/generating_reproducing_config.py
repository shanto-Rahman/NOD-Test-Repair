import time
import subprocess
from sentence_transformers import SentenceTransformer
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
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ChatMessageHistory
from helper import get_line_range, find_api_match_with_flakerake
from modify_java_file import inject_sleep_before_line
from heuristics import rank_methods_by_similarity, clustering_methods, rank_methods_by_llm_embedding_similarity
from token_processing import count_prompt_tokens

#login(token="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")
def hf_login_once():
    if os.environ.get("HF_ALREADY_LOGGED_IN") == "1":
        return
    token = os.environ["HUGGINGFACE_HUB_TOKEN"]
    login(token=token, add_to_git_credential=True)  # runs once, caches
    os.environ["HF_ALREADY_LOGGED_IN"] = "1"


def has_errors_or_failures(path):
    with open(path, 'r') as f:
        text = f.read()
    return 'Errors: 1' in text or 'Failures: 1' in text

def top_n_common_scan_second_first(ranked_df1, ranked_df2, key_col="Body", n=25):
    """
    Scan ranked_df2 first, picking entries also in ranked_df1[key_col].
    Returns the first n common entries in the order they appear in ranked_df2.
    """
    # Build a lookup set of keys from df1
    set1 = set(ranked_df1[key_col])

    common_keys = []
    for key in ranked_df2[key_col]:
        if key in set1:
            common_keys.append(key)
            if len(common_keys) >= n:
                break

    # Now filter and reorder ranked_df2 by those keys
    common_df = (
        ranked_df2
        .set_index(key_col)       # index by the key
        .loc[common_keys]         # pick only those keys, in order of df2
        .reset_index()            # turn the index back into a column
    )
    return common_df

def gpt_score_finder(messages, max_retries=3, initial_wait=2, sleep_on_success=5):
    retry_count = 0
    #print("messages=", messages)
    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                #model="gpt-4o-mini",
                model="gpt-4o",
                messages=messages,
                temperature=0.2,
                max_tokens=1000
            )
            time.sleep(sleep_on_success)  # Optional: avoid hammering the API
            return response
        except openai.error.APIError as e:
            # Check if it's a server-side error (500, 502, 503, etc.)
            if hasattr(e, 'response') and e.response.status_code >= 500:
                #time.sleep(initial_wait * (2 ** retry_count))  # Exponential backoff
                wait_time = initial_wait * (2 ** retry_count)
                print(f"Server error ({e.response.status_code}). Retrying in {initial_wait * (2 ** retry_count)} seconds.")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(f"API error: {str(e)}")
                raise  # Re-raise the exception for non-server-side errors or if retries are exhausted
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error: {str(e)}")
            raise

    print("Max retries reached. Returning None.")
    return None 

import os
from pathlib import Path

def find_class_file(class_name, slug, module):
    # Convert class name to relative path
    rel_path = class_name.replace('.', '/') + '.java'
    print("class_name=", class_name)
    # Step 1: Check in the given module
    main_path = Path(f"projects/{slug}/{module}/src/main/java/{rel_path}")
    if main_path.exists():
        return str(main_path)

    # Step 2: Search all modules under projects/<slug>/
    base_dir = Path(f"projects/{slug}")
    #candidates = list(base_dir.glob(f"**/src/main/java/**/{class_name}.java"))
    candidates = list(base_dir.glob(f"**/src/main/java/**/{rel_path}"))
    print("All candidates before filtering:", candidates)

    # Step 3: Filter out matches from the given module itself

    #if module != ".":
    #    module_path = (base_dir / module).resolve()
    #    candidates = [c for c in candidates if module_path not in c.resolve().parents]
    #for c in candidates:
    #    if c.exists():
    #        print(f"[INFO] Found class file: {c}")
    #        return str(c)
    #print("Filtered candidates:", candidates)  # <-- Add this line

    # Step 4: Return the first alternative match (if any)
    #if candidates:
    #    print(f"[INFO] Class {class_name} not found in {module}, using {candidates[0]}")
    #    return str(candidates[0])

    #print(f"[WARN] Class {class_name} not found in any module.")
    #exit()
    
    return candidates

# Filter out methods with empty or trivial bodies
def is_non_empty_body(body):
    code_lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
    return len(code_lines) > 1  # >1 to ensure at least one actual code line beyond signature

def is_synchronized_signature(body):
    lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
    for line in lines:
        if line.startswith("@"):
            continue  # Skip annotations like @Override
        return "synchronized" in line
    return False


def run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx):
    inject_sleep_before_line(class_path_list, line_number, method_name, descriptor, code_line)
    tag = f"{retry_count}_{idx}_{run_id}"
    try:
        print("./run_test.sh", slug, module, test, tag)
        result_run = subprocess.run(
            ["./run_test.sh", slug, module, test, tag],
            check=True, text=True, capture_output=True
        )
        out = result_run.stdout.strip()
        print("***out****", out)
        firstLine = out.splitlines()[0]  # "Failure not found." or "Failure found."
        return (firstLine == "Failure found.")
    except subprocess.CalledProcessError as e:
        print("run_test.sh failed with exit code", e.returncode)
        print("--- stdout ---"); print(e.stdout)
        print("--- stderr ---"); print(e.stderr)

        # Inspect produced log to decide if it was a failure
        currentDir_when_exception_occurs = os.getcwd()
        before, after = test.rsplit('.', 1)
        test_with_hash = f"{before}#{after}"
        log_file = (currentDir_when_exception_occurs + "/logs-to-reproduce/" +
                    f"{test_with_hash}-con-after-changedCode-{tag}.txt")
        print("log file name=", log_file)
        if has_errors_or_failures(log_file):
            print("Found Errors: 1 or Failures: 1")
            return True
        else:
            print("No Errors: 1 or Failures: 1")
            return False

def append_token_row(csv_path, slug, module, test, token_count):
    p = Path(csv_path)
    is_new = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["slug", "module", "test", "token_count"])
        w.writerow([slug, module, test, token_count])

def gpt_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, dataset_path,  slug, module, test, filtered_df, retry_count = 0):
    max_retries = 5
    tried_methods = set()

    #call a method to check if any api call happened which is the same as api found by flakerake paper
    #../data/flakerake-timing-related-apis.txt
    #find_api_match_with_flakerake(filtered_df, "../data/flakerake-timing-related-apis.txt") 
    #exit()
    #print("filtered_df=", filtered_df.head(2))
    #print("filtered_df columns=", filtered_df.columns)

    '''all_clusters = sorted(filtered_df["Cluster"].unique())
    for cluster_id in {1..1}:
        print(f"\nTrying Cluster {cluster_id}")
        cluster_df = filtered_df[filtered_df["Cluster"] == cluster_id].head(10)

        #Making code_under_test_meths with the Class
        code_under_test_meths = "\n\n".join(
        f"// Class: {row['Class']}, Method: {row['Method']}\n{row['Body']}"
        for _, row in cluster_df.iterrows()
        )'''

    prompt, definition = generate_prompt(failure_log, filtered_df, test_code)
    #print("definition=", definition)

    print("prompt=", prompt)
    messages = [
        {"role": "system", "content": definition},
        {"role": "user",   "content": prompt}
    ]
    prompt_tokens = count_prompt_tokens(messages, model="gpt-4o")
    #print()
    # save token count
    #if token_csv_path is None:
    token_csv_path = str(Path("results") / "prompt_token_counts.csv")
    append_token_row(token_csv_path, slug, module, test, prompt_tokens)
    while retry_count < max_retries:
        #print("messages=", messages)
        response = gpt_score_finder(messages)

        if not response: 
            break

        response_content = response['choices'][0]['message']['content']

        print("RESPONSE CONTENT =============================")
        print(response_content)
        messages.append({"role": "assistant", "content": response_content})

        if "</Output>" in response_content:
            m = re.search(r"<Output>\s*(.*?)\s*</Output>", response_content, re.DOTALL)
            if m:
                meth_code = m.group(1)
            else:
                meth_code = "No code found" #response_content
        else:
            meth_code = "</Output> not found" #response_content
        print("**meth_code=", meth_code)
        # Suppose meth_code is your multiline string as shown above
        for idx, line in enumerate(meth_code.strip().splitlines(), start=1):
            print("**** index=", idx, ",Processing line:", line)
            line = line.strip()
            if not line:
                continue  # skip empty lines
            # Example: split into parts
            # Format: Class:Method:Descriptor:LineNumber (ActualCodeLine)
            m = re.match(r"^(.*?):(.*?):(.*?):(\d+)\s+\((.*)\)$", line)
            if m:
                class_name = m.group(1)
                method_name = m.group(2)
                descriptor = m.group(3)
                line_number = int(m.group(4))
                code_line = m.group(5)
                #print(f"Class: {class_name}, Method: {method_name}, Descriptor: {descriptor}, Line: {line_number}, Code: {code_line}")
                class_simple_name = class_name.split('.')[-1]  # Get class name (e.g., HeaderExchangeHandler)
                class_name = class_simple_name.split('$')[0]
                print(f"===Class name after split: {class_name}", ",line=", line_number)
                #print("class_name, slug, module=", class_name, slug, module)

                with open("metadata/Suggested_Delay_Injected_lines.csv", mode="a", newline="") as f:
                    print("Tried lines")
                    writer = csv.writer(f)
                    writer.writerow([slug, module, test, class_name, line_number,code_line])
                class_path_list = find_class_file(class_name, slug, module)
                #print("**** class_path=", class_path)

                if class_path_list:
                    failure_count = 0
                    first_failed = run_once(0, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx)
                    if not first_failed:
                        print("First run: no failure; skipping additional runs.")
                        print("Only 0/1 runs failed. Not considering as valid failure.")
                    else:
                       # First run failed → run 4 more times (total 5)
                        failure_count = 1
                        for run_id in range(1, 5):
                            if run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx):
                                failure_count += 1
                        if failure_count >=3:
                            print(f"Failure found in {failure_count}/5 runs.")
                            return line, f"{retry_count}_{idx}", "Failure found."
                        else:
                            print("Only {failure_count}/5 runs failed. Not considering as valid failure.") 
                else:
                    print(f"[ERROR] Could not locate class source file for: {class_name}")
            else:
                print("Line did not match expected format:", line)
        tried_method_list = "\n".join(f"{i+1}. {m[0]}" for i, m in enumerate(tried_methods))
        feedback = (
            f"Your previous suggestion did not reproduce the failure.\n"
            f"Here is what is already tried:\n"
            f"Method: {method_name}\n"
            f"Location(s):\n{meth_code}\n\n"
            f"Please suggest a new location for delay injection in a different method, "
            f"or a different location within a method that has not already been tried. "
            f"Do not repeat any of the previous suggestions."
            f"Sometimes, choosing lines from methods that are shorter and have simpler logic can help isolate the failure more effectively and improve reproducibility."
        )
        messages.append({"role": "user", "content": feedback}) 
        retry_count += 1
        #continue
    return "NA", str(retry_count), "Failure not found"
   
def give_test_data_in_chunks_qwen(test_meth_code_df, tokenizer, model, device, ml_technique, code_under_test_meths, line_ranges, failure_log_df):
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
    #print(messages)
    
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
    #exit()

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

import re

def extract_block(path, test):
    test_class = test.rsplit('.', 1)[0]
    start_re = re.compile(fr"Running {test_class}")
    end_re   = re.compile(r"There are test failures")
    drop_re  = re.compile(r'^\s*at\s+(org\.junit|org\.apache\.maven\.surefire|java.base)')
    buf = []

    in_block = False

    with open(path) as f:
        for line in f:
            if not in_block and start_re.search(line):
                in_block = True
            if in_block:
                if end_re.search(line):
                    break
                if drop_re.match(line):
                    continue

                buf.append(line.rstrip("\n"))
                # print(line, end="")

    # if the stacktrace contains "Time elapsed: __ s(ec)" then remove that part
    buf = [re.sub(r'Time\s+elapsed:?\s*\d+(?:\.\d+)?\s*(?:s|sec)\b', '', line) for line in buf]


    # # also remove the "Total time:  11.854 s" and "Finished at: 2024-01-30T16:00:00" from the stacktrace
    buf = [re.sub(r'Total time: \s+\d+\.\d+ s', '', line) for line in buf]
    buf = [re.sub(r'Finished at:\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?', '', line) for line in buf]

    return buf


def run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, failure_log_csv, slug, module, test):
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
        openai.api_key = os.environ["OPENAI_API_KEY"]
    #else:
    #    print('model name not correct')
    #    exit()
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

    print("test_code_csv=", test_code_csv)
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


    print("test_code_csv=",test_code_csv, ",dataset_path=", dataset_path) 
    test_df = pd.read_csv(test_code_csv)
    method_df = pd.read_csv(dataset_path)

    df_with_cluster = clustering_methods(method_df)
    print("***************")
    df_with_cluster.to_csv("M.csv", index=False)
    #print(df_with_cluster)
    embed_model_name = "gpt2" #"codebert" #"llama" #"tf-idf" #"gpt2" #"llama" #"qwen" #"codebert" #"qwen"  #"llama" #"qwen"
    csv_that_saved_embedding = "metadata/embedings/"+test+"_"+embed_model_name+"_embeddings.csv"
    embedding_required_to_generate =  False
    if embedding_required_to_generate:
        ranked_df = rank_methods_by_llm_embedding_similarity(test_df, df_with_cluster, failure_log_df, embed_model_name)
        print(ranked_df)
        ranked_df.to_csv(csv_that_saved_embedding, index=False)
    else:
        print("loading embedding", csv_that_saved_embedding)
        ranked_df = pd.read_csv(csv_that_saved_embedding)
        print(ranked_df)
    
    ranked_df["LineSpan"] = ranked_df["LineRange"].apply(
        lambda x: int(x.split("-")[1]) - int(x.split("-")[0]) + 1 if "-" in x else 0
    )

    ranked_df["HasBody"] = ranked_df["Body"].apply(is_non_empty_body)
    ranked_df["IsSynchronized"] = ranked_df["Body"].apply(is_synchronized_signature)
    ranked_df["CoverageFloat"] = ranked_df["Coverage %"].str.rstrip('%').astype(float)
    #ranked_df["SimilarityFloat"] = ranked_df["similarity"].astype(float)
    #ranked_df["SimilarityFloat"] = ranked_df["combined_sim"].astype(float)
    #threshold = ranked_df["SimilarityFloat"].quantile(0.90)
    #print("threshold=", threshold) 
    # Filter by LineSpan < 30, then get top 20
    #depth_filtered_df = ranked_df[ #(ranked_df["LineSpan"] <= 30) & 
    #                              (ranked_df["HasBody"]) &  (ranked_df["CoverageFloat"] >= 90.0) & (ranked_df["SimilarityFloat"] > threshold) & 
    #                              (~ranked_df["IsSynchronized"])] #.head(30)
    depth_filtered_df = ranked_df.head(10) #Collecting 10 methods from the top
    print(len(depth_filtered_df))
    #exit()

    with open("metadata/meta_data.csv", mode="a", newline="") as f:
        print("I AM from metadata")
        writer = csv.writer(f)
        writer.writerow([slug, module, test, len(depth_filtered_df)])
    code_under_test_meths = depth_filtered_df['Body'].tolist()
    lineRange = depth_filtered_df['LineRange'].tolist()
    
    depth_filtered_df.to_csv("metadata/Depth_filtered_df.csv", index=False)
    print(failure_log)
    print(test_code)

    if ml_technique == "qwen":
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_qwen(test_code, tokenizer, auto_model, device, ml_technique, code_under_test_meths, lineRange, failure_log)
 
            #X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
            print('***************** All preds=')
            print(preds)
    
    elif ml_technique == "llama3_8b":
        #model_name, tokenizer, auto_model = llama3_8b_model_define()
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_llama3_8b(X_test, tokenizer, auto_model, batch_size, device, project_group, test_y.numpy(), ml_technique)

        del auto_model
        torch.cuda.empty_cache()
    elif ml_technique == "deep_seek_coder":
        #model_name, tokenizer, auto_model = deep_seek_coder_model_define()
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_deep_seek_coder(X_test, tokenizer, auto_model, batch_size, device, project_group, test_y.numpy(), ml_technique)
    elif ml_technique == "gpt":
            line_to_inject_delay, cot_count, test_output = gpt_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, dataset_path,  slug, module, test, depth_filtered_df)
            print("line_to_inject_delay=", line_to_inject_delay, ", cot_count=", cot_count, ", test_output=", test_output)
    else:
        print('no model name found=',ml_technique)
        line_to_inject_delay = "Embedding-Only"
        cot_count = "Embedding-Only"
        test_output = "Embedding-Only"

    #if ml_technique != "gpt" or ml_technique != " embeddingOnly":
    #    print(ml_technique)
    #    print("delete model")
    #    del auto_model
    #    torch.cuda.empty_cache()
    #    exit()

    return line_to_inject_delay, cot_count, test_output 
    #return changed_code_output_to_get_fail, java_file_path, method_name, line_range, cot_count, test_output


def initialize_environment(seed_value):
    """Initializes the environment by setting the seed and configuring logging."""
    set_seed(seed_value)  # Set the seed for reproducibility
    setup_logging()  # Setup standardized logging

def save_result(slug, sha, module, test, line_to_inject_delay, cot_count, test_output, seconds): 
    #Saving result for reproducing failure
    #with open("results/gpt.csv", "a", newline="") as fw:
    file_path = "results/tdrepro.csv"
    write_header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
    with open(file_path, "a", newline="") as fw:
        writer = csv.writer(fw)
        if write_header:
            writer.writerow(["proj_name","sha","module","test_name","changed_code_to_get_fail", "file", "method", "line_range", "cot_count"])

        if test_output == "Failure found.":
            writer.writerow([
                slug,
                sha,
                module,
                test,
                line_to_inject_delay,  # This is the code change to inject delay
                cot_count,
                seconds
            ])
        else:
            writer.writerow([
                slug,
                sha,
                module,
                test,
                "",
                "10",
                seconds
            ])
if __name__ == "__main__":
    dataset_path = sys.argv[1] #traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_methods_with_call_labels.csv
    results_file = sys.argv[2] #
    data_name_dir = sys.argv[3] #traces
    technique = sys.argv[4] 
    test_code_csv = sys.argv[5] 
    fail_log_csv = sys.argv[6]
    slug = sys.argv[7] 
    sha = sys.argv[8] 
    module = sys.argv[9] 
    test = sys.argv[10] 
    data_is_from_which_csv = sys.argv[11] 
    initialize_environment(42)
    if data_is_from_which_csv == "idoft":
        filtered_fail_log_txt = extract_block(fail_log_csv, test)
        base, _ = os.path.splitext(fail_log_csv)
        fail_log_csv = f"{base}.csv"

        cleaned_fail_log = [line for line in filtered_fail_log_txt if line.strip()]

        # 2) drop lines that are just “[INFO]” (with optional spaces)
        info_only = re.compile(r'^\[INFO\]\s*$')
        cleaned_fail_log = [line for line in cleaned_fail_log if not info_only.match(line)]
        print("fail cleaned=", cleaned_fail_log)

        #big_block = "\n".join(filtered_fail_log_txt)
        big_block_fail_log = "\n".join(cleaned_fail_log)

        with open(fail_log_csv, "w", newline="") as fw:
            writer = csv.writer(fw,
                            delimiter=",",
                            quoting=csv.QUOTE_MINIMAL)      # wrap everything in quotes
            writer.writerow(["Failure"])
            writer.writerow([big_block_fail_log]) 

    start_time = time.time()
    #print(type(big_block_fail_log))
    line_to_inject_delay, cot_count, test_output = run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, fail_log_csv, slug, module, test)
    end_time = time.time()
    duration_in_seconds = end_time - start_time
    #print("duration=", duration)
    #minutes, seconds = divmod(duration, 60)

    save_result(slug, sha, module, test, line_to_inject_delay, cot_count, test_output, duration_in_seconds)
