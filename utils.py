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

    return category, tokens_list

def parse_cr(cr, ml_technique, fold):
    total_weighted_avg_scores=[0, 0, 0]
    total_support=0
    weighted_avg_arrays_list=[]
    category_dict={}

    lines = cr.strip().split('\n')
    # parse the class names and metrics
    classes = []
    metrics = []
    for line in lines[2:-4]:  # skip the first 2 and last 3 lines
        t = line.strip().split()
        classes.append(t[0])
        key=t[0]
        values=[float(x) for x in t[1:]]

        with open("../flaky-test-categorization/without_adversarial_per_Category_Evaluation_"+ml_technique+".txt", "a") as file:
            file.write(fold+":"+key+":" + str(values))
            file.write("\n")

        metrics.append(values)
        if key in category_dict:
            existing_values=category_dict[key]
            updated_values=[existing_values[k] + (values[k]*values[-1]) for k in range(len(values)-1)]
            updated_values.append(existing_values[-1] + values[-1]) #This is for adding support
            category_dict[key] = updated_values
        else:
            initial_val = [(values[i]*values[-1]) for i in range(len(values)-1)]
            initial_val.append(values[-1])
            category_dict[key] = initial_val

    
    print('metrics=',metrics)
    third_last_line = lines[-3].strip().split()

    accuracy = [float(x) for x in third_last_line[1:]]

    second_last_line = lines[-2].strip().split()
    macro_avg = [float(x) for x in second_last_line[2:]]

    # parse the overall scores
    last_line = lines[-1].strip().split()
    weighted_avg = [float(x) for x in last_line[2:]]
    # print the results
    print('Classes:', classes)

    total_weighted_avg_scores =  [ total_weighted_avg_scores[idx] + (weighted_avg[idx] * weighted_avg[-1]) for idx in range(3)] 
    total_support +=weighted_avg[-1]

    with open("../flaky-test-categorization/without_adversarial_weighted_avg_for_cv_"+ml_technique+".txt", "a") as file: # Once I get the result, need to divide by 10
        file.write(fold+",")
        file.write(str(weighted_avg))
        file.write("\n")
    return category_dict

def get_evaluation_scores(tn, fp, fn, tp):
    print("get_score method is defined")
    if(tp == 0):
        accuracy = (tp+tn)/(tn+fp+fn+tp)
        Precision = 0
        Recall = 0
        F1 = 0
    else:
        accuracy = (tp+tn)/(tn+fp+fn+tp)
        Precision = tp/(tp+fp)
        Recall = tp/(tp+fn)
        F1 = 2*((Precision*Recall)/(Precision+Recall))
    return accuracy, F1, Precision, Recall

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

# train the model
def train(model, train_dataloader, cross_entropy, device, optimizer):
    model.train()
    #total_loss, total_accuracy = 0, 0
    # empty list to save model predictions
    #total_preds = []

    # iterate over batches
    for step, batch in enumerate(train_dataloader):

        # push the batch to gpu
        batch = [r.to(device) for r in batch]

        sent_id, mask, labels = batch

        # clear previously calculated gradients
        model.zero_grad()
        preds = model(sent_id, mask)
        loss = cross_entropy(preds, labels)
        # add on to the total loss
        #total_loss = total_loss + loss.item()
        # backward pass to calculate the gradients
        loss.backward()
        # progress update after every 50 batches.
        if step % 50 == 0 and not step == 0:
            print('  Batch {:>5,}  of  {:>5,}.'.format(step, len(train_dataloader)))
            print('loss=',loss.item())
        # clip the the gradients to 1.0. It helps in preventing the exploding gradient problem
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1)
        # update parameters
        optimizer.step()
        # model predictions are stored on GPU. So, push it to CPU
        #preds = preds.detach().cpu().numpy()
        # append the model predictions
        #total_preds.append(preds)
    # compute the training loss of the epoch
    #avg_loss = total_loss / len(train_dataloader)
    # reshape the predictions in form of (number of samples, no. of classes)
    #total_preds = np.concatenate(total_preds, axis=0)
    # returns the loss and predictions
    #return avg_loss, total_preds

def evaluate(model, val_dataloader, cross_entropy, device):

    print("\nEvaluating..")
    # deactivate dropout layers
    model.eval()

    total_loss, total_accuracy = 0, 0

    # empty list to save the model predictions
    total_preds = []
    total_labels = []

    # iterate over batches
    for step, batch in enumerate(val_dataloader):

        # Progress update every 50 batches.
        if step % 50 == 0 and not step == 0:

            # Calculate elapsed time in minutes.
            # elapsed = format_time(time.time() - t0)

            # Report progress.
            print('  Batch {:>5,}  of  {:>5,}.'.format(
                step, len(val_dataloader)))

        # push the batch to gpu
        batch = [t.to(device) for t in batch]

        sent_id, mask, labels = batch

        # deactivate autograd
        with torch.no_grad():

            # model predictions
            preds = model(sent_id, mask)

            # compute the validation loss between actual and predicted values
            loss = cross_entropy(preds, labels)

            total_loss = total_loss + loss.item()

            preds = preds.detach().cpu().numpy()
            labels = labels.detach().cpu().numpy()

            total_preds.append(preds)
            total_labels.append(labels)

    # compute the validation loss of the epoch
    avg_loss = total_loss / len(val_dataloader)

    # reshape the predictions in form of (number of samples, no. of classes)
    total_preds = np.concatenate(total_preds, axis=0)
    total_labels = np.concatenate(total_labels, axis=0)

    return avg_loss, total_preds, total_labels

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
