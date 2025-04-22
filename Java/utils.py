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
#from huggingface_hub import login


# Function to check if a token contains at least one English letter
def contains_english_letter(token):
    return bool(re.search(r'[a-zA-Z]', token))

def filter_tokens(sorted_token_attributions):
    # Remove 'Ġ' prefix and filter out non-English tokens
    filtered_token_attributions = []
    unique_tokens = set()  # ✅ Track unique tokens

    for token, score in sorted_token_attributions:
        cleaned_token = token.lstrip("Ġ").lstrip(".").lstrip("_")  # ✅ First, remove 'Ġ'
        
        # ✅ Ensure the token contains at least one English letter AND is longer than 1 character
        if contains_english_letter(cleaned_token) and len(cleaned_token) > 1:
            if cleaned_token not in unique_tokens:  # ✅ Ensure uniqueness
                unique_tokens.add(cleaned_token)
                filtered_token_attributions.append((cleaned_token, score))
 
            if len(unique_tokens) == 20:
                break
    # Print filtered top-20 tokens
    print("\n✅ Filtered Top-20 Tokens (Only English Letters, No 'Ġ' Prefix):")
    for token, score in filtered_token_attributions:  # Get only top 20 tokens
        print(f"Token: {token}, Attribution Score: {score:.4f}")
    
    top_20_tokens = [token for token, _ in filtered_token_attributions[:20]]

    # If you need to return the cleaned list:
    return top_20_tokens

def forward_func(inputs, attention_mask, model):
    """Forward function to return logits for attribution."""
    outputs = model(inputs, attention_mask=attention_mask, return_dict=True)
    return outputs.logits[:, -1, :]  # Get logits for the last token


def predict(inputs, attention_mask, model, target_token):
    """Forward pass for IG. Returns logits for classification."""
    outputs = model(inputs.long(), attention_mask=attention_mask, return_dict=True)
    return outputs.logits[:, -1, :] #outputs.logits[:, -1, :].max(dim=-1).values  # Return logits for last token

stopwords = {"<|im_start|>", "<|im_end|>", ";", "()", "=", "(", ")", ".", ",", "Ċ", "Ġ", "Ġ<", "Ġ>" , "void", "_" }

def clean_token(token):
    return re.sub(r"^[^a-zA-Z]+", "", token)  # Remove leading non-letters


#def interpret_with_ig_codellama(prompt, tokenizer, model, model_inputs, predicted_tokens, test_data):
#    input_ids = model_inputs["input_ids"]
#    attention_mask = model_inputs["attention_mask"]  # ✅ Ensure this is defined
#
#    lig = LayerIntegratedGradients(forward_func, model.model.embed_tokens)
#    # ✅ Identify Token Indices for test_data (Test Code)
#    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
#    tokenized_test_code = tokenizer.tokenize(test_data)  # Tokenize test_code separately
#
#    # ✅ Convert Input IDs to Tokenized Text
#    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
#    print('tokenized_prompt=', tokenized_prompt)
#    #exit()
#    # 🔹 Locate the "Test:" marker in tokenized input
#    test_start_index = -1
#    for i in range(len(tokenized_prompt) - 2): 
#        if tokenized_prompt[i] == '_Test' and (tokenized_prompt[i + 1] == ':'):
#            test_start_index = i + 2  # Move past "Test:"
#            break
#
#    if test_start_index == -1: 
#        print("❌ Error: 'Test:' not found in tokenized input! Computing for all tokens.")
#        test_start_index = 0  # Default to full prompt
#        test_end_index = len(tokenized_prompt)
#    else:
#        # 🔹 Locate "@Test"
#        for i in range(test_start_index, len(tokenized_prompt) - 1): 
#            if tokenized_prompt[i] == '_@' and tokenized_prompt[i + 1] == 'Test':
#                test_start_index = i  # Adjust start index
#                break
#
#        # 🔹 Find the end of the test method (closing '}')
#        test_end_index = -1
#        for i in range(test_start_index, len(tokenized_prompt)):
#            if tokenized_prompt[i] == '}':
#                test_end_index = i + 1  # Include '}'
#                break
#
#        if test_end_index == -1: 
#            test_end_index = len(tokenized_prompt)  # If no '}', take full remaining tokens
#
#    filtered_tokens_attributions = []
#    MAX_TEST_LENGTH = 1024  # ✅ Truncate large test functions
#    print('test_end_index - test_start_index=',test_end_index - test_start_index)
def interpret_with_ig_codellama(prompt, tokenizer, model, model_inputs, predicted_tokens, test_data):
    input_ids = model_inputs["input_ids"]
    attention_mask = model_inputs["attention_mask"]  # ✅ Ensure this is defined

    lig = LayerIntegratedGradients(forward_func, model.model.embed_tokens)
    
    # ✅ Convert Input IDs to Tokenized Text
    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
    print('tokenized_prompt=', tokenized_prompt)

    # 🔹 Locate the "Test:" marker in tokenized input
    test_start_index = -1
    for i in range(len(tokenized_prompt) - 1):  # No need for -2
        if tokenized_prompt[i] == '▁Test' and tokenized_prompt[i + 1] == ':':
            test_start_index = i + 2  # Move past "Test:"
            break

    if test_start_index == -1: 
        print("❌ Error: 'Test:' not found in tokenized input! Computing for all tokens.")
        test_start_index = 0  # Default to full prompt
        test_end_index = len(tokenized_prompt)
    else:
        # 🔹 Locate "@Test"
        for i in range(test_start_index, len(tokenized_prompt) - 1): 
            if tokenized_prompt[i] == '▁@' and tokenized_prompt[i + 1] == 'Test':
                test_start_index = i  # Adjust start index
                break

        # 🔹 Find the end of the test method (closing '}')
        test_end_index = -1
        for i in range(test_start_index, len(tokenized_prompt)):
            if tokenized_prompt[i] == '▁}':  # Match tokenized version
                test_end_index = i + 1  # Include '}'
                break

        if test_end_index == -1: 
            test_end_index = len(tokenized_prompt)  # If no '}', take full remaining tokens

    print(f"📌 Test starts at token index: {test_start_index}, ends at: {test_end_index}")
    MAX_TEST_LENGTH = 1024  # ✅ Truncate large test functions
    if test_end_index - test_start_index < MAX_TEST_LENGTH:
        if len(predicted_tokens.shape) > 1:
            target_token = predicted_tokens[0, -1].item()  # Last token
        else:
            target_token = predicted_tokens.item()  # Scalar

        attributions = lig.attribute(input_ids, target=target_token,     additional_forward_args=(attention_mask, model), n_steps=1)
            
        # ✅ Normalize attributions for better visualization
        attributions = attributions.sum(dim=-1).squeeze(0).cpu().detach().numpy()
        attributions = (attributions - attributions.min()) / (attributions.max() - attributions.min() + 1e-6)
        # ✅ Get the tokens and attributions only within the test_code range
        filtered_tokens = tokenized_prompt[test_start_index:test_end_index]
        filtered_tokens = [clean_token(token) for token in filtered_tokens]  # Clean tokens 
        filtered_attributions = attributions[test_start_index:test_end_index]

        filtered_tokens_attributions = [(token, attribution) for token, attribution in zip(filtered_tokens, filtered_attributions) if token not in stopwords]

        # Sort tokens based on attributions
        #sorted_tokens = sorted(zip(filtered_tokens_attributions, attributions), key=lambda x: x[1], reverse=True)
        sorted_tokens = sorted(filtered_tokens_attributions, key=lambda x: x[1], reverse=True)
        # ✅ Free up memory
        del attributions
        torch.cuda.empty_cache()
    else:
        sorted_tokens = []
    return sorted_tokens 


def interpret_with_ig_gemma7b(prompt, tokenizer, model, model_inputs, predicted_tokens, test_data):
    input_ids = model_inputs["input_ids"]
    attention_mask = model_inputs["attention_mask"]  # ✅ Ensure this is defined

    lig = LayerIntegratedGradients(forward_func, model.model.embed_tokens)
    # ✅ Identify Token Indices for test_data (Test Code)
    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
    tokenized_test_code = tokenizer.tokenize(test_data)  # Tokenize test_code separately

    # ✅ Convert Input IDs to Tokenized Text
    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
    print('tokenized_prompt=', tokenized_prompt)
    #exit()
    # 🔹 Locate the "Test:" marker in tokenized input
    test_start_index = -1
    for i in range(len(tokenized_prompt) - 2): 
        if tokenized_prompt[i] == 'Test' and (tokenized_prompt[i + 1] == ':'):
            test_start_index = i + 2  # Move past "Test:"
            break

    if test_start_index == -1: 
        print("❌ Error: 'Test:' not found in tokenized input! Computing for all tokens.")
        test_start_index = 0  # Default to full prompt
        test_end_index = len(tokenized_prompt)
    else:
        # 🔹 Locate "@Test"
        for i in range(test_start_index, len(tokenized_prompt) - 1): 
            if tokenized_prompt[i] == '@' and tokenized_prompt[i + 1] == 'Test':
                test_start_index = i  # Adjust start index
                break

        # 🔹 Find the end of the test method (closing '}')
        test_end_index = -1
        for i in range(test_start_index, len(tokenized_prompt)):
            if tokenized_prompt[i] == '}':
                test_end_index = i + 1  # Include '}'
                break

        if test_end_index == -1: 
            test_end_index = len(tokenized_prompt)  # If no '}', take full remaining tokens

    filtered_tokens_attributions = []
    MAX_TEST_LENGTH = 1024  # ✅ Truncate large test functions
    print('test_end_index - test_start_index=',test_end_index - test_start_index)
    #exit()
    if test_end_index - test_start_index <= MAX_TEST_LENGTH:
        attributions = lig.attribute(input_ids, target=predicted_tokens[0, 0].item(),     additional_forward_args=(attention_mask, model), n_steps=1)
            
        # ✅ Normalize attributions for better visualization
        attributions = attributions.sum(dim=-1).squeeze(0).cpu().detach().numpy()
        attributions = (attributions - attributions.min()) / (attributions.max() - attributions.min() + 1e-6)
        # ✅ Get the tokens and attributions only within the test_code range
        filtered_tokens = tokenized_prompt[test_start_index:test_end_index]
        filtered_tokens = [clean_token(token) for token in filtered_tokens]  # Clean tokens 
        filtered_attributions = attributions[test_start_index:test_end_index]

        filtered_tokens_attributions = [(token, attribution) for token, attribution in zip(filtered_tokens, filtered_attributions) if token not in stopwords]

        # Sort tokens based on attributions
        #sorted_tokens = sorted(zip(filtered_tokens_attributions, attributions), key=lambda x: x[1], reverse=True)
        sorted_tokens = sorted(filtered_tokens_attributions, key=lambda x: x[1], reverse=True)
        # ✅ Free up memory
        del attributions
        torch.cuda.empty_cache()
    else:
        sorted_tokens = []
    return sorted_tokens 


import gc
def interpret_with_ig_qwen(prompt, tokenizer, model, model_inputs, predicted_tokens, test_data, ml_technique):

    input_ids = model_inputs["input_ids"]
    attention_mask = model_inputs["attention_mask"]  # ✅ Ensure this is defined
    if input_ids.shape[0] > 1:
        print('multiple examples are runnning.....')
    if ml_technique == "deep_seek_coder" or ml_technique == "llama3_8b" or ml_technique == "qwen":
        MAX_TOKENS = 512  # Reduce to 512 tokens
        input_ids = input_ids[:, :MAX_TOKENS]
        attention_mask = attention_mask[:, :MAX_TOKENS]
 
    lig = LayerIntegratedGradients(forward_func, model.model.embed_tokens)
    # ✅ Identify Token Indices for test_data (Test Code)
    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
    tokenized_test_code = tokenizer.tokenize(test_data)  # Tokenize test_code separately

    # ✅ Convert Input IDs to Tokenized Text
    tokenized_prompt = tokenizer.convert_ids_to_tokens(input_ids[0])
    print('tokenized_prompt=', tokenized_prompt)
    #exit()
    # 🔹 Locate the "Test:" marker in tokenized input
    test_start_index = -1
    for i in range(len(tokenized_prompt) - 2): 
        if tokenized_prompt[i] == 'ĠTest' and (tokenized_prompt[i + 1] == ':' or tokenized_prompt[i + 1] == ':Ċ'):
            test_start_index = i + 2  # Move past "Test:"
            break

    if test_start_index == -1: 
        print("❌ Error: 'Test:' not found in tokenized input! Computing for all tokens.")
        test_start_index = 0  # Default to full prompt
        test_end_index = len(tokenized_prompt)
    else:
        # 🔹 Locate "@Test"
        for i in range(test_start_index, len(tokenized_prompt) - 1): 
            if tokenized_prompt[i] == 'Ġ@' and tokenized_prompt[i + 1] == 'Test':
                test_start_index = i  # Adjust start index
                break

        # 🔹 Find the end of the test method (closing '}')
        test_end_index = -1
        for i in range(test_start_index, len(tokenized_prompt)):
            if tokenized_prompt[i] == '}':
                test_end_index = i + 1  # Include '}'
                break

        if test_end_index == -1: 
            test_end_index = len(tokenized_prompt)  # If no '}', take full remaining tokens

    print(f"📌 Test starts at token index: {test_start_index}, ends at: {test_end_index}")
    filtered_tokens_attributions = []
    MAX_TEST_LENGTH = 1200  # ✅ Truncate large test functions
    print('test_end_index - test_start_index=',test_end_index - test_start_index)
    #exit()
    if test_end_index - test_start_index <= MAX_TEST_LENGTH:
        torch.cuda.empty_cache()  # Free unused GPU memory
        gc.collect()
        with torch.cuda.amp.autocast():
            attributions = lig.attribute(input_ids, target=predicted_tokens[0, 0].item(),     additional_forward_args=(attention_mask, model), n_steps=1)
            
        # ✅ Normalize attributions for better visualization
        attributions = attributions.sum(dim=-1).squeeze(0).cpu().detach().numpy()
        attributions = (attributions - attributions.min()) / (attributions.max() - attributions.min() + 1e-6)
        # ✅ Get the tokens and attributions only within the test_code range
        filtered_tokens = tokenized_prompt[test_start_index:test_end_index]
        filtered_tokens = [clean_token(token) for token in filtered_tokens]  # Clean tokens
        filtered_attributions = attributions[test_start_index:test_end_index]

        filtered_tokens_attributions = [(token, attribution) for token, attribution in zip(filtered_tokens, filtered_attributions) if token not in stopwords]

        # Sort tokens based on attributions
        #sorted_tokens = sorted(zip(filtered_tokens_attributions, attributions), key=lambda x: x[1], reverse=True)
        sorted_tokens = sorted(filtered_tokens_attributions, key=lambda x: x[1], reverse=True)
        # ✅ Free up memory
        del attributions
        torch.cuda.empty_cache()
    else:
        sorted_tokens = []
    return sorted_tokens 



#====================================================
#====================================================
#login(token="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")
def init_setup(technique, data_name):
    # specify GPU
    device = torch.device("cuda")
    #device = torch.device("cpu")
    ml_technique=technique.split("-")[0]
    #input_data, target_data, output_layer, dataset_category = preprocess_data(dataset_path, technique)
    dataset_category = "Flakicat"
    output_layer = 6 # Flakicat

    where_data_comes = data_name.split("-")[0] 
    os.makedirs(f"{where_data_comes}-result", exist_ok=True)
    return device, ml_technique, dataset_category, output_layer, where_data_comes

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
    model_name = "Qwen/Qwen2-7B-Instruct"

    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        #trust_remote_code=True
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
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    auto_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    ).cuda()
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
