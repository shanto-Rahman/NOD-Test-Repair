import logging
import numpy as np
import torch
import random
from transformers import AdamW, AutoTokenizer, AutoModel, AutoConfig, T5Tokenizer, T5ForConditionalGeneration, T5EncoderModel, RobertaTokenizer, AutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import json
import os
import venv
from git import Repo
#from huggingface_hub import login

#login(token="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")

# ---------------- Step 1: Clone the GitHub Repository ----------------
def proj_clone(proj_name, sha, projects_dir):
    repo_url = "https://github.com/"+proj_name
    repo_name = proj_name.split("/")[-1]
    repo_path = os.path.join(projects_dir, repo_name)  # Clone inside projects directory
    
    if not os.path.exists(repo_path):
        print("Cloning repository...")
        Repo.clone_from(repo_url, repo_path)
    
    repo = Repo(repo_path)
    try:
        repo.git.checkout(sha)
        print(f"Successfully checked out commit")
    except Exception as e:
        print(f"Failed to checkout commit")
        exit(1)
    return repo, repo_path

def extract_failure_log(log_text):
    """Extracts the failure log starting from the 'FAILURES' section."""
    match = re.search(r"== FAILURES ==", log_text)
    
    if match:
        failure_start_index = match.start()  # Get the start index of the failure section
        return log_text[failure_start_index:]  # Extract everything from the failure section onward
    
    return None 

def extract_first_failure_log(log_file):
    """Extracts the logs of the first failing test run from a log file."""
    first_failure_run = None
    logs = []
    capture = False

    with open(log_file, "r", encoding="utf-8") as file:
        for line in file:
            # Detect the test run start
            if line.startswith("=== Test Run "):
                if first_failure_run is not None:
                    break  # Stop capturing after first failure is completely logged
                test_run_number = int(line.split()[3].split("/")[0])  # Extract test run number
                logs = [line]  # Start new log capture
                capture = True
                continue
            
            if capture:
                logs.append(line)
            
            # Detect a failure
            if "FAILED" in line and first_failure_run is None:
                first_failure_run = test_run_number  # Store first failure run number
            
    if first_failure_run is None:
        return "No test failures found."

    fail_run_log = f"📄 \n\n" + "".join(logs)
    fails_txt_only = extract_failure_log(fail_run_log)
    return fails_txt_only #f"📄 \n\n" + "".join(logs)


def extract_open_source_model_output(system_definition, prompt, model, device, tokenizer, cot_count, row_index, model_name_arg, unit_test_name):
    messages = []
    model.eval() 
    if model_name_arg == "deep_seek_coder":
        if cot_count == 0:
            messages = [
                {"role": "system", "content": system_definition},
                {"role": "user", "content": prompt}
            ]
        else:
            messages = [{"role": "user", "content": prompt}] 
        input_texts = [msg["content"] for msg in messages]  # Extract 'content' part
        print("**** message to model=",input_texts)
        inputs = tokenizer(input_texts, return_tensors="pt", padding=True, truncation=True).to(model.device)

    elif model_name_arg == "llama":
        if cot_count == 0:
            messages = [
                {"role": "system", "content": system_definition},
                {"role": "user", "content": prompt}
            ]
        else:
            messages = [{"role": "user", "content": prompt}] 
        
        input_texts = [msg["content"] for msg in messages]  # Define input_texts here
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        #print("inputs=", inputs)
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
        input_ids = inputs
    elif model_name_arg == "codellama":
        if cot_count == 0:
            messages = system_definition + prompt
        else:
            messages = prompt #[{"role": "user", "content": prompt}]
        
        input_texts = messages #[msg["content"] for msg in messages]  # Extract 'content' part
        inputs = tokenizer(input_texts, return_tensors="pt").to(model.device)

    #print("**** message to model=",input_texts)
    #inputs = tokenizer(input_texts, return_tensors="pt").to(model.device)
    # Calculate the total number of tokens in input_texts
    total_input_tokens = sum([len(tokenizer.encode(text)) for text in input_texts])
    if model_name_arg == "deep_seek_coder" or  model_name_arg == "codellama":
        input_ids = inputs["input_ids"]
    if input_ids.shape[1] > 2048:
        return "", True

    print('***input_ids.shape=',input_ids.shape)
    #attention_mask = inputs["attention_mask"]
    if isinstance(inputs, dict) and "attention_mask" in inputs:
        attention_mask = inputs["attention_mask"]
    else:
        # Handle the absence of attention_mask for llama
        attention_mask = None
    outputs = generate_open_source_model_output(model, input_ids, attention_mask, tokenizer, model_name_arg) # this function is responsible for generating the model's output

    decoded_outputs = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
    decoded_output_token_sizes = [len(tokenizer.encode(decoded_output)) for decoded_output in decoded_outputs]
    print("cot_count=",cot_count,",Total tokens in input_texts:", total_input_tokens, ",row_index=", row_index)
    print('Len of decoded_outputs=', decoded_output_token_sizes)
    print("generated_decoded_outputs=",decoded_outputs)
    #exit()
    cleaned_code = ""
    for i, output in enumerate(decoded_outputs):
        print(f"**** Output {i+1}: {output}")    
        # Remove system_definition and prompt from the output if they're present
        if system_definition in output:
            output = output.replace(system_definition, "").strip()
        if prompt in output:
            output = output.replace(prompt, "").strip()
        print("generated output=", output)
        # Extract Python code block
        match = re.search(r'```python(.*?)```', output, re.DOTALL)
        if match:
            cleaned_code = match.group(1).strip()
            cleaned_code = re.sub(r'def \s*(\w+)\s*\(', f'def {unit_test_name}(', cleaned_code)
            print(f"Python Block {i+1}:\n{cleaned_code}\n")
            #print(f"Python Block {i+1}:\n{cleaned_code}\n")
        else:
            print(f"No Python code block found in Output {i+1}")
    # Clear GPU memory after each iteration to avoid memory accumulation
    torch.cuda.empty_cache()
    gc.collect() 
    # Delete tensors explicitly to free memory
    del inputs, input_ids, attention_mask, outputs, decoded_outputs
    if model_name_arg == "deep_seek_coder" and total_input_tokens >= 1500:
        return cleaned_code, True # Cannot proceed with the COT 
    return cleaned_code, False 


def generate_open_source_model_output(model, input_ids, attention_mask, tokenizer, model_name_arg):
    if model_name_arg == "deep_seek_coder":
        with torch.no_grad():  # Avoid storing gradients during inference
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=2048, 
                do_sample=False, 
                top_k=50, 
                top_p=0.95, 
                temperature=0.8,
                num_return_sequences=1, 
                pad_token_id=tokenizer.pad_token_id,  # Set pad_token_id explicitly
                eos_token_id=tokenizer.eos_token_id )

    elif model_name_arg == "llama":
        with torch.no_grad():  # Avoid storing gradients during inference
            model = model.float()
            outputs = model.generate(
                input_ids=input_ids,
                #attention_mask=attention_mask,
                max_new_tokens=2048,
                #max_length=25,
                eos_token_id=tokenizer.eos_token_id,
                do_sample=False,
                temperature=0.8,
                top_p=1, 
            )
    return outputs

def extract_category(decoded_output):
    if isinstance(decoded_output, list):
        decoded_output = " ".join(decoded_output)

    decoded_output = decoded_output.replace('`', '').strip()
    print('***DECODED_OUTPUT=',repr(decoded_output))
    #match = re.search(r"<Category>\s*(.*?)\s*</Category>", decoded_output, re.DOTALL)
    match = re.search(r"<Category>\s*([^<>]+?)\s*</Category>", decoded_output)


    print('***Match=',match)
    if match:
        category_name = match.group(1).strip()  # Remove leading/trailing whitespace
        print(f"\n✅ Extracted Category: {category_name}")
        return category_name
    else:
        print("\n⚠️ No <Category> tag found!")
        return None


def extract_open_source_model_output_categpory(system_definition, prompt, model, device, tokenizer, cot_count, row_index, model_name_arg, unit_test_name, objective):
    messages = []
    model.eval() 
    if model_name_arg == "deep_seek_coder":
        if cot_count == 0:
            messages = [
                {"role": "system", "content": system_definition},
                {"role": "user", "content": prompt}
            ]
        else:
            messages = [{"role": "user", "content": prompt}] 
        input_texts = [msg["content"] for msg in messages]  # Extract 'content' part
        print("**** message to model=",input_texts)
        inputs = tokenizer(input_texts, return_tensors="pt", padding=True, truncation=True).to(model.device)

    elif model_name_arg == "llama":
        if cot_count == 0:
            messages = [
                {"role": "system", "content": system_definition},
                {"role": "user", "content": prompt}
            ]
            #print('****message=',messages)
        else:
            messages = [{"role": "user", "content": prompt}] 
        
        input_texts = [msg["content"] for msg in messages]  # Define input_texts here
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        #print("inputs=", inputs)
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
        input_ids = inputs

    #print("**** message to model=",input_texts)
    #inputs = tokenizer(input_texts, return_tensors="pt").to(model.device)
    # Calculate the total number of tokens in input_texts
    total_input_tokens = sum([len(tokenizer.encode(text)) for text in input_texts])
    if model_name_arg == "deep_seek_coder":
        input_ids = inputs["input_ids"]
    if input_ids.shape[1] > 2048:
        return "", True

    print('***input_ids.shape=',input_ids.shape)
    #attention_mask = inputs["attention_mask"]
    if isinstance(inputs, dict) and "attention_mask" in inputs:
        attention_mask = inputs["attention_mask"]
    else:
        # Handle the absence of attention_mask for llama
        attention_mask = None
    outputs = generate_open_source_model_output(model, input_ids, attention_mask, tokenizer, model_name_arg) # this function is responsible for generating the model's output

    decoded_outputs = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
    decoded_output_token_sizes = [len(tokenizer.encode(decoded_output)) for decoded_output in decoded_outputs]
    print("cot_count=",cot_count,",Total tokens in input_texts:", total_input_tokens, ",row_index=", row_index)
    print('Len of decoded_outputs=', decoded_output_token_sizes)
    #print("****generated_decoded_outputs=",decoded_outputs)
    category_name = ""
    if objective == "category_prediction":
        category_name = extract_category(decoded_outputs)
        print('*************category_name=',category_name)

    exit()
    #cleaned_code = ""
    #for i, output in enumerate(decoded_outputs):
    #    print(f"**** Output {i+1}: {output}")    
    #    # Remove system_definition and prompt from the output if they're present
    #    if system_definition in output:
    #        output = output.replace(system_definition, "").strip()
    #    if prompt in output:
    #        output = output.replace(prompt, "").strip()
    #    print("generated output=", output)
    #    # Extract Python code block
    #    match = re.search(r'```python(.*?)```', output, re.DOTALL)
    #    if match:
    #        cleaned_code = match.group(1).strip()
    #        cleaned_code = re.sub(r'def \s*(\w+)\s*\(', f'def {unit_test_name}(', cleaned_code)
    #        print(f"Python Block {i+1}:\n{cleaned_code}\n")
    #        #print(f"Python Block {i+1}:\n{cleaned_code}\n")
    #    else:
    #        print(f"No Python code block found in Output {i+1}")
    ## Clear GPU memory after each iteration to avoid memory accumulation
    #torch.cuda.empty_cache()
    #gc.collect() 
    ## Delete tensors explicitly to free memory
    #del inputs, input_ids, attention_mask, outputs, decoded_outputs
    #if model_name_arg == "deep_seek_coder" and total_input_tokens >= 1500:
    #    return cleaned_code, True # Cannot proceed with the COT 
    return cleaned_code, False 


