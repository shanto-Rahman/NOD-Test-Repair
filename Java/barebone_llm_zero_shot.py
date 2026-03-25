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
from typing import Optional, List, Tuple  # and List, Dict, Optional, Any as needed
import time, threading

#login(token="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")

import re

def hf_login_once():
    if os.environ.get("HF_ALREADY_LOGGED_IN") == "1":
        return
    token = os.environ["HUGGINGFACE_HUB_TOKEN"]
    login(token=token, add_to_git_credential=True)  # runs once, caches
    os.environ["HF_ALREADY_LOGGED_IN"] = "1"


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

def has_errors_or_failures(path):
    with open(path, 'r') as f:
        text = f.read()
    return 'Errors: 1' in text or 'Failures: 1' in text

def gpt_score_finder(messages, max_retries=3, initial_wait=2, sleep_on_success=5, max_tokens=1000):
    #tokens_needed = estimate_request_tokens(messages, max_tokens)
    #tpm_throttle(tokens_needed)
    retry_count = 0
    #print("messages=", messages)
    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                #model="gpt-4o",
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens
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

    if slug == "zxing/zxing":
        print("zxing ....")
        candidate_roots = [
            Path(f"projects/{slug}/{module}/src"),
        ]
        search_patterns = [
            f"**/src/{rel_path}",
        ]
    else:
        candidate_roots = [
            Path(f"projects/{slug}/{module}/src/main/java"),
        ]
        search_patterns = [
            f"**/src/main/java/{rel_path}",
        ]

    # Step 1: Check in the given module
    for root in candidate_roots:
        main_path = root / rel_path
        if main_path.exists():
            return [str(main_path)]

    # Step 2: Search all modules under projects/<slug>/
    base_dir = Path(f"projects/{slug}")
    candidates = []
    for pattern in search_patterns:
        candidates.extend(base_dir.glob(pattern))

    # ---- fallback for unqualified class names like "State" ----
    #if not candidates and "." not in class_name:
    #    candidates = list(base_dir.glob(f"**/{class_name}.java"))
    # Fallback for unqualified class names like "State"
    if not candidates and "." not in class_name:
        local_candidates = list(Path(f"projects/{slug}/{module}").glob(f"**/{class_name}.java"))
        if local_candidates:
            candidates = local_candidates
        else:
            candidates = list(base_dir.glob(f"**/{class_name}.java"))

    print("All candidates before filtering:", candidates)

    if candidates:
        return [str(candidates[0])]
 
    return []

#def find_class_file(class_name, slug, module):
#    # Convert class name to relative path
#    rel_path = class_name.replace('.', '/') + '.java'
#    print("class_name=", class_name)
#    # Step 1: Check in the given module
#    main_path = Path(f"projects/{slug}/{module}/src/main/java/{rel_path}")
#    if main_path.exists():
#        return str(main_path)
#
#    # Step 2: Search all modules under projects/<slug>/
#    base_dir = Path(f"projects/{slug}")
#    #candidates = list(base_dir.glob(f"**/src/main/java/**/{class_name}.java"))
#    candidates = list(base_dir.glob(f"**/src/main/java/**/{rel_path}"))
#    print("All candidates before filtering:", candidates)
#
#    return candidates

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


def gpt_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, dataset_path,  slug, module, test, filtered_df, retry_count = 0):
    max_retries = 1
    tried_methods = set()
   
    prompt, definition = generate_prompt(failure_log, filtered_df, test_code)

    #print("prompt=", prompt)
    messages = [
        {"role": "system", "content": definition},
        {"role": "user",   "content": prompt}
    ]
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
            retry_count = 0
            feedback = (
                f"Your previous response did not include the </Output> tag. Please enclose your answer between <Output> and </Output> tags.\n")
            messages.append({"role": "user", "content": feedback})
            continue
        print("**meth_code=", meth_code)
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
        retry_count += 1
        #continue
    return "NA", str(retry_count), "Failure not found"
   
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


def run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, failure_log_csv, slug, module, test, module_with_underscore_by_replace_slash):
    device, ml_technique, dataset_category, output_layer, where_data_comes = init_setup(technique, data_name_dir)
    
    if ml_technique == "qwen":
        print('I am qwen')
        model_name, tokenizer, auto_model = qwen_model_define()
    elif ml_technique == "llama3_8b":
        model_name, tokenizer, auto_model = llama3_8b_model_define()
    elif ml_technique == "deep_seek_coder":
        model_name, tokenizer, auto_model = deep_seek_coder_model_define()
    elif ml_technique == "gpt":
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
    #csv_that_saved_embedding = "metadata/embedings/"+test+"_"+embed_model_name+"_embeddings.csv"
    slug_with_underscore = slug.replace("/", "_")
    print("slug, module, test=", slug, module_with_underscore_by_replace_slash, test)
    test_with_hash = test.rsplit('.', 1)[0] + '#' + test.rsplit('.', 1)[1]
    csv_that_contains_all_methods = "traces/" + slug_with_underscore + "_" + module_with_underscore_by_replace_slash + "_" + test_with_hash + "_executed_method_bodies.csv" 
    print("csv_that_contains_all_methods=", csv_that_contains_all_methods)
    #csv_that_contains_all_methods = traces/TooTallNate_Java-WebSocket_._org.java_websocket.issues.Issue256Test#runReconnectBlockingScenario0_executed_method_bodies.csv 
    '''embedding_required_to_generate =  False
    if embedding_required_to_generate:
        ranked_df = rank_methods_by_llm_embedding_similarity(test_df, df_with_cluster, failure_log_df, embed_model_name)
        print(ranked_df)
        ranked_df.to_csv(csv_that_saved_embedding, index=False)
    else:
        print("loading embedding", csv_that_saved_embedding)
        ranked_df = pd.read_csv(csv_that_saved_embedding)
        print(ranked_df)'''
    
    depth_filtered_df = pd.read_csv(csv_that_contains_all_methods)
    #depth_filtered_df = df.head(120) # First 100 methods
    #SAMPLE_SIZE = 500
    #depth_filtered_df = df.head(500) #sample(n=SAMPLE_SIZE, random_state=42).reset_index(drop=True) #Random 100 methods
    #print("len=",len(df))
    print(len(depth_filtered_df))
    #exit()

    with open("metadata/meta_data.csv", mode="a", newline="") as f:
        print("I AM from metadata")
        writer = csv.writer(f)
        writer.writerow([slug, module_with_underscore_by_replace_slash, test, len(depth_filtered_df)])
    code_under_test_meths = depth_filtered_df['Body'].tolist()
    lineRange = depth_filtered_df['LineRange'].tolist()
    
    os.makedirs("metadata/barebone", exist_ok=True)
    depth_filtered_df.to_csv("metadata/barebone/"+test+"Depth_filtered_df.csv", index=False)
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
    file_path = "results/barebone-gpt4-result_zero_shot.csv"
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
    module_with_underscore_by_replace_slash = module.replace('/', '_')
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
    line_to_inject_delay, cot_count, test_output = run_experiment(dataset_path, results_file, data_name_dir, technique, test_code_csv, fail_log_csv, slug, module, test, module_with_underscore_by_replace_slash)
    end_time = time.time()
    duration_in_seconds = end_time - start_time
    save_result(slug, sha, module, test, line_to_inject_delay, cot_count, test_output, duration_in_seconds)
