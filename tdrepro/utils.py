import os
import logging
import numpy as np
import torch
import random
from transformers import AdamW, AutoTokenizer, AutoModel, AutoConfig, T5Tokenizer, T5ForConditionalGeneration, T5EncoderModel, RobertaTokenizer, AutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import json
import pandas as pd

import os
from pathlib import Path
#from huggingface_hub import login

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


def find_class_file(class_name, slug, module):
    """  
    Find a .java file using its fully-qualified class name, searching the
    ENTIRE project directory (not just the given module) - since a class
    may live in a different module than the one currently being tested.
 
    Matches any file whose path ends with the class's package path, which
    works regardless of the project's source layout (src/main/java,
    source/, javasrc/, or no prefix at all).
 
    Args:
        class_name: Fully-qualified class name, e.g.
                     "org.java_websocket.AbstractWebSocket".
                     Inner classes (Outer$Inner) are handled by stripping
                     to the outer class, since only it has its own file.
        slug:       Project directory name, e.g. "TooTallNate/Java-WebSocket".
                     The project lives at projects/<slug>.
        module:     Kept for signature compatibility / logging only - not
                     used to scope the search, since the class may live
                     outside the given module.
 
    Returns:
        A list containing a single matched path as a string, or [] if
        nothing was found. Deterministic across runs (sorted matches).
    """
    class_name = class_name.split('$')[0]  # strip inner-class suffix
    rel_path = class_name.replace('.', '/') + '.java'
    simple_name = class_name.split('.')[-1]
 
    project_root = Path(f"projects/{slug}")
 
    # --- Tier 1: exact package path, anywhere in the project ---
    candidates = sorted(project_root.glob(f"**/{rel_path}"), key=str)
 
    # --- Tier 2: fallback - simple name only, anywhere in the project ---
    if not candidates:
        print("***Multiple filename matched found*****")
        candidates = sorted(project_root.glob(f"**/{simple_name}.java"), key=str)
 
    if not candidates:
        print(f"No match found for {class_name} (slug={slug}, module={module})")
        return []
 
    if len(candidates) > 1: 
        print(f"WARNING: multiple matches for {class_name}: {candidates}")

    print(str(candidates[0]))

    return [str(candidates[0])]


# Function to check if a token contains at least one English letter
def contains_english_letter(token):
    return bool(re.search(r'[a-zA-Z]', token))

#====================================================
#====================================================
#login(token="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")
def init_setup(technique):
    # specify GPU
    device = torch.device("cuda")
    #device = torch.device("cpu")
    ml_technique=technique.split("-")[0]
    #input_data, target_data, output_layer, dataset_category = preprocess_data(dataset_path, technique)
    #dataset_category = "Flakicat"
    #output_layer = 6 # Flakicat

    #where_data_comes = data_name.split("-")[0] 
    #os.makedirs(f"{where_data_comes}-result", exist_ok=True)
    return device, ml_technique

def extract_test_method_names(csv_file, output_file):
    """
    Extracts test method names from Java test methods in a CSV file.
    
    Args:
    - csv_file (str): Path to the input CSV file.
    - output_file (str): Path to save the extracted method names.
    """

    # Load CSV
    df = pd.read_csv(csv_file)

    # Regex pattern to extract method names after `@Test public void `
    #method_pattern = re.compile(r'@Test\s+void\s+(\w+)\s*\(')
    method_pattern = re.compile(r'(?:@Test\s+)?(?:public\s+)?void\s+(\w+)\s*\(')

    # Extract method names
    df["test_method_name"] = df["full_code"].apply(lambda code: method_pattern.findall(code)[0] if method_pattern.findall(code) else None)

    # Save extracted method names
    df[["test_method_name"]].to_csv(output_file, index=False)

    print(f"Extracted test method names saved to: {output_file}")
    print(df[["test_method_name"]].head())  # Preview the extracted method names

def parse_category_and_token_list(output_category):
    """Parses the model output to extract the category and tokens."""

    # Regular expressions to extract category and tokens
    category_match = re.search(r"Category:\s*(.+)", output_category)
    tokens_match = re.search(r"Tokens:\s*(\[[^\]]+\])", output_category)

    category = category_match.group(1).strip() if category_match else "Unknown"
    tokens = tokens_match.group(1).strip() if tokens_match else "[]"

    # Convert tokens string to a Python list
    try:
        tokens_list = json.loads(tokens)
    except json.JSONDecodeError:
        tokens_list = []

    return category #, tokens_list

# sett seed for data_loaders for output reproducibility
def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    numpy.random.seed(worker_seed)
    random.seed(worker_seed)


def set_seed(seed_value=42):
    """Sets seed for reproducibility."""
    np.random.seed(seed_value)
    torch.manual_seed(seed_value)
    random.seed(seed_value)
    torch.cuda.manual_seed_all(seed_value) # if you are using CUDA

def setup_logging():
    """Sets up the logging format and level."""
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.INFO)


# setting the seed for reproducibility, same seed is set to ensure the reproducibility of the result
'''def set_deterministic(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)                    
    torch.cuda.manual_seed(seed)               
    torch.cuda.manual_seed_all(seed)           
    torch.backends.cudnn.deterministic = True '''

def codebert_model_define():	
    model_name = "microsoft/codebert-base"
    model_config = AutoConfig.from_pretrained(model_name, return_dict=False, output_hidden_states=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    auto_model = AutoModel.from_pretrained(model_name, config=model_config)	
    return model_name, tokenizer, auto_model

def codet5_model_define():
    model_name = "Salesforce/codet5-small"
    tokenizer = RobertaTokenizer.from_pretrained(model_name)
    auto_model = T5ForConditionalGeneration.from_pretrained(model_name)

    return model_name, tokenizer, auto_model


def t5_small_model_define():	
    model_name = "t5-small"
    #try with codet5 instead of t5
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    auto_model = T5EncoderModel.from_pretrained(model_name)
    model_config = T5ForConditionalGeneration.from_pretrained(model_name).config

    return model_name, tokenizer, auto_model


def gemma2b_model_define():	
    model_name = "google/gemma-2b-it"
    auto_model = AutoModelForCausalLM.from_pretrained(
        "google/gemma-2b-it",
        #device_map="auto",
        torch_dtype=torch.bfloat16
    ).cuda()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    #auto_model = AutoModelForCausalLM.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def gemma7b_model_define():	
    model_name = "google/gemma-7b-it"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    #auto_model = AutoModelForCausalLM.from_pretrained(model_name)
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        #device_map="cuda",
        torch_dtype=torch.bfloat16
    ).cuda()

    return model_name, tokenizer, auto_model

def codegemma7b_model_define():	
    model_name = "google/codegemma-7b-it"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16
    ).cuda()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

#def llama3_8b_model_define():	
#    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
#    auto_model = AutoModelForCausalLM.from_pretrained(
#        model_name,
#        torch_dtype=torch.bfloat16,
#        low_cpu_mem_usage=True
#    ).cuda()
#    tokenizer = AutoTokenizer.from_pretrained(model_name)
#    return model_name, tokenizer, auto_model

def codellama_7b_instruct_model_define():
    model_name = "codellama/CodeLlama-13b-Instruct-hf"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16
        #device_map="auto",
    ).cuda()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def mistral_model_define():
    model_name = "mistralai/Ministral-8B-Instruct-2410"

    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
        use_auth_token=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    return model_name, tokenizer, auto_model

def qwen_model_define():
    # model_name = "Qwen/Qwen2-7B-Instruct"
    # model_name = "Qwen/Qwen3-235B-A22B-Instruct-2507"
    model_name = "Qwen/Qwen2.5-Coder-14B-Instruct"

    print("Loading the Qwen/Qwen3-235B-A22B-Instruct-2507 model. This may take a while...")
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
        use_auth_token=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def deep_seek_coder_model_define():	
    #model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
    #model_name = "deepseek-ai/deepseek-llm-67b-chat"
    #model_name = "deepseek-ai/deepseek-coder-33b-base"
    #model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    #model_name = "deepseek-ai/deepseek-coder-7b-instruct-v1.5"
    #model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
    model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16
        ).cuda()
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    return model_name, tokenizer, auto_model

def llama3_8b_model_define():
    print("*"*50)
    print("llama 3 8b has been defined")
    print("*"*50)
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"

    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16
    ).cuda()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def llama3_3_70b_model_define():
    print("*"*50)
    print("llama 3.3 70b has been defined")
    print("*"*50)

    # username = os.getenv("USER")
    # os.makedirs(f"/scratch/{username}/offload", exist_ok=True)

    model_name = "meta-llama/Llama-3.3-70B-Instruct"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto"
        # offload_folder=f"/scratch/{username}/offload"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def llama3_70b_model_define():	
    model_name = "meta-llama/Meta-Llama-3-70B-Instruct"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto"
        #low_cpu_mem_usage=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model_name, tokenizer, auto_model


def llama_7b_model_define():	
    model_name = "meta-llama/Llama-2-7b-chat-hf"
    #llama-3b-instruct (json form; https://github.com/1rgs/jsonformer); Will ask to generate the json of the category. We can add a little bit descriptions of each category, and the flaky test in general.
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    #tokenizer = AutoTokenizer.from_pretrained(model_name)
    #tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, padding_side='max_length', truncation=True, pad_token_id=50256)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, truncation=True)
    tokenizer.pad_token_id = tokenizer.encode(tokenizer.pad_token)[0]
    return model_name, tokenizer, auto_model


def fmt_gpu_mem_info(gpu_id=0, brief=True) -> str:
    import torch.cuda.memory

    if torch.cuda.is_available():
        report = ""
        t = torch.cuda.get_device_properties(gpu_id).total_memory
        c = torch.cuda.memory.memory_reserved(gpu_id)
        a = torch.cuda.memory_allocated(gpu_id)
        f = t - a

        report += f"[Allocated {a} | Free {f} | Cached {c} | Total {t}]\n"
        if not brief:
            report += torch.cuda.memory_summary(device=gpu_id, abbreviated=True)
        return report
    else:
        return f"CUDA not available, using CPU"
