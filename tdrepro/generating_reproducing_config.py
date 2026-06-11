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
from prompt_engineering import generate_prompt, generate_prompt_for_library_meth
import torch
import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ChatMessageHistory
from helper import get_line_range, find_api_match_with_flakerake
from modify_java_file import inject_sleep_before_line
from heuristics import rank_methods_by_similarity, clustering_methods, rank_methods_by_llm_embedding_similarity
from token_processing import count_prompt_tokens

CURRENT_DIR = os.getcwd()
MODEL_NAME = "gpt-4.1" #"gpt-5.5-pro" #gpt-4o

def hf_login_once():
    if os.environ.get("HF_ALREADY_LOGGED_IN") == "1":
        return
    token = os.environ["HUGGINGFACE_HUB_TOKEN"]
    login(token=token, add_to_git_credential=True)  # runs once, caches
    os.environ["HF_ALREADY_LOGGED_IN"] = "1"

def extract_gemini_text(response):
    if response is None:
        print("DEBUG: response is None")
        return ""

    # Print raw structure so we see what's inside
    print("DEBUG: raw response object:", repr(response))
    candidates = getattr(response, "candidates", None)
    print("DEBUG: candidates:", candidates)

    # Try the usual path: first candidate → first part → text
    try:
        if candidates:
            first_cand = candidates[0]
            print("DEBUG: first candidate:", first_cand)
            content = getattr(first_cand, "content", None)
            print("DEBUG: content:", content)
            parts = getattr(content, "parts", None) if content else None
            print("DEBUG: parts:", parts)

            if parts:
                first_part = parts[0]
                print("DEBUG: first_part:", first_part)

                # object-style: part.text
                if hasattr(first_part, "text"):
                    print("DEBUG: first_part.text:", first_part.text)
                    return (first_part.text or "").strip()

                # dict-style: {"text": "..."}
                if isinstance(first_part, dict) and "text" in first_part:
                    print("DEBUG: first_part['text']:", first_part["text"])
                    return (first_part["text"] or "").strip()

        # Fallback: try response.text if SDK exposes it
        t = getattr(response, "text", None)
        print("DEBUG: fallback response.text:", t)
        if isinstance(t, str):
            return t.strip()

    except Exception as e:
        print("DEBUG: Error while extracting text:", e)

    return ""


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

'''def gemini_score_finder(messages, max_retries=3, initial_wait=2, sleep_on_success=10):
    retry_count = 0
    #response = client.models.generate_content(
    #model="gemini-2.5-flash",   # ✅ use one of the listed models
    #contents="USER: Hello Gemini!",
    #config=types.GenerateContentConfig(
    #    temperature=0.2,
    #    max_output_tokens=50,
    #    ),
    #)

    #print(response.text)
    #exit()

    #converted_messages = [
    #    {"role": m["role"], "parts": [m["content"]]}
    #    for m in messages
    #]
    prompt = "\n".join(
              f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
              for m in messages
          )
    print("prompt=",prompt)
    print("END of Prompt***")
    while retry_count < max_retries:
        try:
            response = client.models.generate_content(
                #model="gemini-2.5-flash",
                model="gemini-2.5-pro",
                contents=prompt, #converted_messages,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=7300,
                ),
            )
            response_content = extract_gemini_text(response)
            print("RESPONSE ========")
            print(response_content)
            time.sleep(sleep_on_success)
            return response_content

        except Exception as e:
            # Gemini doesn't differentiate APIError subclasses the same way as OpenAI
            err_msg = str(e)
            if "500" in err_msg or "503" in err_msg or "unavailable" in err_msg.lower():
                wait_time = initial_wait * (2 ** retry_count)
                print(f"Server error. Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(f"API error: {err_msg}")
                raise

    print("Max retries reached. Returning None.")
    return None'''

'''def gpt_score_finder_5(messages, max_retries=5, initial_wait=2, sleep_on_success=2):
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                #model="gpt-5.5-pro",
                model="gpt-4.1",
                messages=messages,
                temperature=0.0,
                max_tokens=2000
            )

            time.sleep(sleep_on_success)

            return response

        except openai.error.RateLimitError as e:
            wait_time = initial_wait * (2 ** retry_count)

            print(
                f"Rate limit error. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)
            retry_count += 1

        except openai.error.APIError as e:

            status_code = None

            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code

            if status_code is not None and status_code >= 500:

                wait_time = initial_wait * (2 ** retry_count)

                print(
                    f"Server error ({status_code}). "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)
                retry_count += 1

            else:
                print(f"API error: {str(e)}")
                raise

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

    print("Max retries reached. Returning None.")
    return None'''

def gpt_score_finder(messages, max_retries=3, initial_wait=2, sleep_on_success=5):
    retry_count = 0
    #print("messages=", messages)
    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                #model="gpt-4o-mini",
                model=MODEL_NAME,
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
    before, after = test.rsplit('.', 1)
    test_with_hash = f"{before}#{after}"
    try:
        print("./run_test.sh", slug, module, test, tag, "logs-to-reproduce")
        result_run = subprocess.run(
            ["./run_test.sh", slug, module, test, tag, "logs-to-reproduce"],
            check=True, text=True, capture_output=True
        )
        out = result_run.stdout.strip()
        firstLine = out.splitlines()[0]  # "Failure not found." or "Failure found."
        failed = (firstLine == "Failure found.")
        #return failed, None, (out if failed else None)
        return failed, CURRENT_DIR +"/logs-to-reproduce/" + test_with_hash + "-con-after-changedCode-"+tag+".txt"
    except subprocess.CalledProcessError as e:
        print("run_test.sh failed with exit code", e.returncode)
        print("--- stdout ---"); print(e.stdout)
        print("--- stderr ---"); print(e.stderr)

        # Inspect produced log to decide if it was a failure
        currentDir_when_exception_occurs = os.getcwd()
        log_file = (currentDir_when_exception_occurs + "/logs-to-reproduce/" +
                    f"{test_with_hash}-con-after-changedCode-{tag}.txt")
        print("log file name=", log_file)
        log_text = None
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                log_text = f.read()
        if has_errors_or_failures(log_file):
            print("Found Errors: 1 or Failures: 1")
            # Will check if the failure is the one that we desired
            return True, log_file
        else:
            print("No Errors: 1 or Failures: 1")
            return False, log_file

def append_token_row(csv_path, slug, module, test, token_count):
    p = Path(csv_path)
    is_new = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["slug", "module", "test", "token_count"])
        w.writerow([slug, module, test, token_count])


'''def gemini_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, dataset_path,  slug, module, test, filtered_df, retry_count = 0):
    max_retries = 5
    tried_methods = set()

    prompt, definition = generate_prompt(failure_log, filtered_df, test_code)
    print("prompt=", prompt)
    messages = [
        {"role": "system", "content": definition},
        {"role": "user",   "content": prompt}
    ]
    prompt_tokens = count_prompt_tokens(messages, model="gpt-4o")
    token_csv_path = str(Path("results") / "prompt_token_counts.csv")
    append_token_row(token_csv_path, slug, module, test, prompt_tokens)
    while retry_count < max_retries:
        response_content = gemini_score_finder(messages)
        if not response_content: 
            break

        #response_content = response['choices'][0]['message']['content']

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
                print(f"Class: {class_name}, Method: {method_name}, Descriptor: {descriptor}, Line: {line_number}, Code: {code_line}")
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
    return "NA", str(retry_count), "Failure not found"'''

def log_similarity_check(failure_log_file, test_run_log_file, test):
    #print("failure_log type:", type(failure_log_file))
    #print("test_run_log type:", type(test_run_log_file))
    #print("test type:", type(test))
    print("failure_log value:", failure_log_file)
    print("test_run_log value:", test_run_log_file)
    print("test value:", test)

    result = subprocess.check_output(
        ["python3", CURRENT_DIR + "/log_similarity_init.py", str(failure_log_file), str(test_run_log_file), str(test)],
            text=True
            ).strip()
    if "MisMatched" in result:
        return False
    else:
        print(f"{result} Matched Failure found.") 
        return True

def get_messages(definition, prompt):
    messages = [
        {"role": "system", "content": definition},
        {"role": "user",   "content": prompt}
    ]
    prompt_tokens = count_prompt_tokens(messages, model=MODEL_NAME)
    token_csv_path = str(Path("results") / "prompt_token_counts.csv")
    append_token_row(token_csv_path, slug, module, test, prompt_tokens)
    return messages, prompt_tokens

def parse_gpt_response(response, messages, retry_count): 
    if not response: 
        return ""

    response_content = response['choices'][0]['message']['content']

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


    os.makedirs("tdrepro_gpt_responses", exist_ok=True)

    file_path = f"tdrepro_gpt_responses/{test}.txt"
    print("saving to =", file_path)
    with open(file_path, "a") as f:
        f.write(f"\n\n===== RETRY {retry_count} =====\n")
        f.write(response_content)
        f.write("\n==============================\n")

    return meth_code #, messages

def gpt_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, meth_body_csv,  slug, module, test, filtered_df, failure_log_csv, libraries_df, retry_count = 0):

    lib_retry_count = 0 
    max_retries = 2
    lib_max_retries = 2

    tried_methods = set()
    lib_tried_methods = set()

    prompt, definition = generate_prompt(failure_log, filtered_df, test_code)
    messages, prompt_tokens = get_messages(definition, prompt)

    '''while retry_count < max_retries:
        response = gpt_score_finder(messages)
        #meth_code, messages = parse_gpt_response(response, messages)
        meth_code = parse_gpt_response(response, messages, retry_count)

        # Suppose meth_code is your multiline string as shown above
        for idx, line in enumerate(meth_code.strip().splitlines(), start=1):
            print("**** index=", idx, ",Processing line:", line)
            line = line.strip()
            if not line:
                continue  # skip empty lines
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
                failure_happened_and_log_matched = True
                if class_path_list:
                    failure_count = 0
                    first_failed, test_run_log = run_once(0, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx)
                    if not first_failed:
                        print("First run: no failure; skipping additional runs.")
                        print("Only 0/1 runs failed. Not considering as valid failure.")
                    else:
                       # First run failed → run 4 more times (total 5)
                        failure_count = 1
                        # Will check the logs 
                        log_similar = log_similarity_check(failure_log_csv, test_run_log, test)
                        #print("org failure_log=", failure_log)
                        #print("test_run_log=", test_run_log)
                        #exit()
                        if not log_similar:
                            print("failure log does not match.")
                            failure_happened_and_log_matched = False
                        else:
                            for run_id in range(1, 5):
                                _failed, test_run_log = run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx)
                                log_similar = log_similarity_check(failure_log_csv, test_run_log, test)
                                if log_similar and _failed: #run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx):
                                    #Call the function to check the log match 
                                    failure_count += 1
                                else:
                                    print("failure log does not match.")
                                    failure_happened_and_log_matched = False
                                    #Call to the GPT that log does not match, so find a different location
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
        if not failure_happened_and_log_matched:
            feedback = (
                f"Your previous suggestion did not reproduce the same failure.\n"
                f"Here is what is already tried:\n"
                f"Method: {method_name}\n"
                f"Location(s):\n{meth_code}\n\n"
                f"Please suggest a new location for delay injection in a different method, "
                f"or a different location within a method that has not already been tried so that the original failure is reproduced. "
                f"Do not repeat any of the previous suggestions."
                f"Sometimes, choosing lines from methods that are shorter and have simpler logic can help isolate the failure more effectively and improve reproducibility."
            )
        else:
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
        retry_count += 1'''
        #continue
    
    lib_prompt, lib_definitions = generate_prompt_for_library_meth(failure_log, filtered_df, test_code, libraries_df)
    lib_messages, lib_prompt_tokens = get_messages(lib_definitions, lib_prompt)



    while lib_retry_count < lib_max_retries:
        lib_response = gpt_score_finder(lib_messages)
        #meth_code, messages = parse_gpt_response(response, messages)
        lib_meth_code = parse_gpt_response(lib_response, lib_messages, lib_retry_count)

        # Suppose meth_code is your multiline string as shown above
        for idx, line in enumerate(lib_meth_code.strip().splitlines(), start=1):
            print("**** index=", idx, ",Processing line:", line)
            line = line.strip()
            if not line:
                continue  # skip empty lines
            with open("metadata/Suggested_Delay_Injected_lines.csv", mode="a", newline="") as f:
                print("Tried lines")
                writer = csv.writer(f)
                writer.writerow([slug, module, test, line])
            
            #Will call FlakeSync to inject delay at the beginning of that method; will return the log; then will check the log outcome, if same failure, will stop, otherwise next line
            failure_happened_and_log_matched = True
            #if class_path_list:
            #    failure_count = 0
            #    first_failed, test_run_log = run_once(0, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx)
            #    if not first_failed:
            #        print("First run: no failure; skipping additional runs.")
            #        print("Only 0/1 runs failed. Not considering as valid failure.")
            #    else:
            #       # First run failed → run 4 more times (total 5)
            #        failure_count = 1
            #        # Will check the logs 
            #        log_similar = log_similarity_check(failure_log_csv, test_run_log, test)
            #        #print("org failure_log=", failure_log)
            #        #print("test_run_log=", test_run_log)
            #        #exit()
            #        if not log_similar:
            #            print("failure log does not match.")
            #            failure_happened_and_log_matched = False
            #        else:
            #            for run_id in range(1, 5):
            #                _failed, test_run_log = run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx)
            #                log_similar = log_similarity_check(failure_log_csv, test_run_log, test)
            #                if log_similar and _failed: #run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx):
            #                    #Call the function to check the log match 
            #                    failure_count += 1
            #                else:
            #                    print("failure log does not match.")
            #                    failure_happened_and_log_matched = False
            #                    #Call to the GPT that log does not match, so find a different location
            #            if failure_count >=3:
            #                print(f"Failure found in {failure_count}/5 runs.")
            #                return line, f"{retry_count}_{idx}", "Failure found."
            #            else:
            #                print("Only {failure_count}/5 runs failed. Not considering as valid failure.") 
            #else:
            #    print(f"[ERROR] Could not locate class source file for: {class_name}")
        tried_method_list = "\n".join(f"{i+1}. {m[0]}" for i, m in enumerate(lib_tried_methods))
        if not failure_happened_and_log_matched:
            lib_feedback = (
                f"Your previous suggestion did not reproduce the same failure.\n"
                f"Here is what is already tried:\n"
                f"Location(s):\n{lib_meth_code}\n\n"
                f"Please suggest a new method for delay injection "
                f"so that the original failure is reproduced. "
                f"Do not repeat any of the previous suggestions."
            )
        else:
            lib_feedback = (
                f"Your previous suggestion did not reproduce the failure.\n"
                f"Here is what is already tried:\n"
                f"Location(s):\n{lib_meth_code}\n\n"
                f"Please suggest a new location for delay injection. "
                f"Do not repeat any of the previous suggestions."
            )
        lib_messages.append({"role": "user", "content": lib_feedback}) 
        lib_retry_count += 1


    print("lib_prompt=", lib_prompt)

    print("*****lib_def=",lib_definitions)

    print("*** lib_count=", lib_retry_count)
    
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

def read_library_txt(file_path):
    # Read top 100 lines
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()][:100]

    # Put into DataFrame
    libraries_df = pd.DataFrame(lines, columns=["method"])

    print(libraries_df.head())
    print("Total rows:", len(libraries_df))
    return libraries_df

def filter_csv_by_concurrent_methods(csv_file, method_list_file, output_csv):
    df = pd.read_csv(csv_file) 

    # Read concurrent methods from text file
    with open(method_list_file, "r") as f:
        concurrent_methods = {
            line.strip()
            for line in f
            if line.strip()
        }

    # If no concurrent methods found, return entire CSV
    if not concurrent_methods:
        print("Concurrent method file is empty. Returning all rows.")

        df.to_csv(output_csv, index=False)

        print(f"Rows returned: {len(df)}")
        print(f"Saved to: {output_csv}")
        return df

    # Build matching key
    df["MethodKey"] = (
        df["Class"].str.replace(".", "/", regex=False)
        + "."
        + df["Method"]
        + df["Descriptor"]
    )

    # Keep only matched rows
    matched_df = df[df["MethodKey"].isin(concurrent_methods)]

    # Remove helper column if desired
    matched_df = matched_df.drop(columns=["MethodKey"])

    # Save
    matched_df.to_csv(output_csv, index=False)

    print(f"Matched rows: {len(matched_df)}")
    print(f"Saved to: {output_csv}")

    return matched_df

def run_experiment(meth_body_csv, results_file, data_name_dir, model_name, test_code_csv, failure_log_csv, slug, module, test, library_meth_file, proj_conc_meth_file):
    device, ml_technique = init_setup(model_name, data_name_dir)
    
    if ml_technique == "qwen":
        print('I am qwen')
        model_name, tokenizer, auto_model = qwen_model_define()
    elif ml_technique == "llama3_8b":
        model_name, tokenizer, auto_model = llama3_8b_model_define()
    elif ml_technique == "deep_seek_coder":
        model_name, tokenizer, auto_model = deep_seek_coder_model_define()
    elif ml_technique == "gpt":
        openai.api_key = os.environ["OPENAI_API_KEY"]
    elif ml_technique == "gemini":
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        #gemini_api_key="AIzaSyDmFFCseLDxPkgXnGsbSSjomfG2LkiQcIU"
    execution_time = time.time()
    print("Start time of the experiment", execution_time)
    #TN = FP = FN = TP = 0
    project_group = 0
    libraries_df = read_library_txt(library_meth_file)

    #Here I will remove the methods if those are not in the concurrent-method list 
    conc_meth_details_df = filter_csv_by_concurrent_methods(meth_body_csv, proj_conc_meth_file, "output.csv") 
    print("printing top-10 meths=", conc_meth_details_df.head(10))
    
    #print("test_code_csv=", test_code_csv)
    test_meth_code_df = pd.read_csv(test_code_csv) #read_data(test_code_csv)

    failure_log_df = pd.read_csv(failure_log_csv)
    test_code = test_meth_code_df.iloc[0] 
    failure_log = failure_log_df.iloc[0]
    df = pd.read_csv(meth_body_csv, quoting=csv.QUOTE_ALL, encoding='utf-8', engine='python')

    print("test_code_csv=",test_code_csv, ",meth_body_csv=", meth_body_csv) 
    test_df = pd.read_csv(test_code_csv)
    #method_df = pd.read_csv(meth_body_csv)

    #df_with_cluster = clustering_methods(method_df)
    #print("***************")
    #df_with_cluster.to_csv("M.csv", index=False)
    #print(df_with_cluster)
    embed_model_name = "gpt2" #"codebert" #"llama" #"tf-idf" #"gpt2" #"llama" #"qwen" #"codebert" #"qwen"  #"llama" #"qwen"

    os.makedirs("metadata/embedings", exist_ok=True)
    csv_that_saved_embedding = "metadata/embedings/"+test+"_"+embed_model_name+"_embeddings.csv"
    #csv_that_saved_embedding = "metadata/embedings_ablation_0_100/"+test+"_"+embed_model_name+"_embeddings.csv"
    embedding_required_to_generate =  True #False
    if embedding_required_to_generate:
        ranked_df = rank_methods_by_llm_embedding_similarity(test_df, conc_meth_details_df, failure_log_df, embed_model_name)
        print(ranked_df)
        ranked_df.to_csv(csv_that_saved_embedding, index=False)
    else:
        print("loading embedding", csv_that_saved_embedding)
        ranked_df = pd.read_csv(csv_that_saved_embedding)
        print(ranked_df)
   

    #TO-DO: Hopefully the following way of ranking the ranked_df will be removed
    '''ranked_df["LineSpan"] = ranked_df["LineRange"].apply(
        lambda x: int(x.split("-")[1]) - int(x.split("-")[0]) + 1 if "-" in x else 0
    )

    ranked_df["HasBody"] = ranked_df["Body"].apply(is_non_empty_body)
    ranked_df["IsSynchronized"] = ranked_df["Body"].apply(is_synchronized_signature)
    ranked_df["CoverageFloat"] = ranked_df["Coverage %"].str.rstrip('%').astype(float)'''

    depth_filtered_df = ranked_df.head(10) #Collecting 10 methods from the top
    print(len(depth_filtered_df))
    #exit()

    '''with open("metadata/meta_data.csv", mode="a", newline="") as f: #Just to see how many are in that depth_filtered_df (although it will always be 10)
        print("I AM from metadata")
        writer = csv.writer(f)
        writer.writerow([slug, module, test, len(depth_filtered_df)])'''

    code_under_test_meths = depth_filtered_df['Body'].tolist()
    lineRange = depth_filtered_df['LineRange'].tolist()
    
    depth_filtered_df.to_csv("metadata/Depth_filtered_df.csv", index=False)
    print(failure_log)
    print(test_code)

    if ml_technique == "qwen":
        with torch.no_grad():
            preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_qwen(test_code, tokenizer, auto_model, device, ml_technique, code_under_test_meths, lineRange, failure_log)
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
            line_to_inject_delay, cot_count, test_output = gpt_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, meth_body_csv,  slug, module, test, depth_filtered_df, failure_log_csv, libraries_df)
            print("line_to_inject_delay=", line_to_inject_delay, ", cot_count=", cot_count, ", test_output=", test_output)
    elif ml_technique == "gemini":
            line_to_inject_delay, cot_count, test_output = gemini_output_calculate(test_code, ml_technique, code_under_test_meths, lineRange, failure_log, meth_body_csv,  slug, module, test, depth_filtered_df)
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
    meth_body_csv = sys.argv[1] #traces/TooTallNate_Java-WebSocket_._org.java_websocket.issues.Issue580Test\#runNoCloseBlockingTestScenario0_executed_method_bodies.csv
    results_file = sys.argv[2] #
    data_name_dir = sys.argv[3] #traces
    model_name = sys.argv[4] 
    test_code_csv = sys.argv[5] 
    fail_log_csv = sys.argv[6]
    slug = sys.argv[7] 
    sha = sys.argv[8] 
    module = sys.argv[9] 
    test = sys.argv[10] 
    library_meth_file = sys.argv[11] #conc_executed_methods/classified/org.apache.hadoop.hbase.stargate.client.TestRemoteAdmin.testDeleteTable-ResultMethods-library-methods.txt
    proj_meth_file = sys.argv[12] #conc_executed_methods/classified/org.apache.hadoop.hbase.stargate.client.TestRemoteAdmin.testDeleteTable-ResultMethods-library-methods.txt
    #data_is_from_which_csv = sys.argv[11] 
    initialize_environment(42)

    start_time = time.time()
    #print(type(big_block_fail_log))
    line_to_inject_delay, cot_count, test_output = run_experiment(meth_body_csv, results_file, data_name_dir, model_name, test_code_csv, fail_log_csv, slug, module, test, library_meth_file, proj_meth_file)
    end_time = time.time()
    duration_in_seconds = end_time - start_time
    #print("duration=", duration)
    #minutes, seconds = divmod(duration, 60)

    save_result(slug, sha, module, test, line_to_inject_delay, cot_count, test_output, duration_in_seconds)
