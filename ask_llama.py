import os
import sys
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import random

# Pick one of the valid tokens directly or use an env var
token_random = random.choice(["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"])
HF_TOKEN = os.getenv("HF_TOKEN", token_random)  # Replace with real token or set env var

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

# Detect device and dtype
use_cuda = torch.cuda.is_available()
dtype = torch.bfloat16 if use_cuda else torch.float32
device_map = "auto" if use_cuda else None

# Load tokenizer and model
print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=dtype,
    device_map=device_map,
    token=HF_TOKEN
)

# Create generator pipeline
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    pad_token_id=tokenizer.eos_token_id,
)




data_file = sys.argv[1] 
# read the csv using pandas
subject = pd.read_csv(data_file, header=None) # header is in the format of Git,Sha,Test-Name,Python-Version,Category. But there is no header in the csv file
# pick the first row
subject = subject.iloc[0]

git_repo = subject[0]
project_name = subject[0].split("/")[-1]
sha = subject[1]
test_name = subject[2]
python_version = subject[3]
category = subject[4]

generic_log_name = f"{project_name}_{test_name.replace('::', '_').replace('/', '_').replace('.py', '').replace('.', '_')}"

method_bodies_file= f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/pretrained_data/{generic_log_name}.csv"
failure_log = f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/logs/{generic_log_name}/fail"
# file inside failure_log (only one file is there)
try: 
    failure_log_file = os.listdir(failure_log)[0]
except IndexError:
    print(f"Failure log directory is empty: {failure_log}")
    sys.exit(1)

failure_log_file = os.path.join(failure_log, failure_log_file)
# read the failure log file
with open(failure_log_file, "r") as f:
    failure_log = f.read()

method_bodies_file_df = pd.read_csv(method_bodies_file) # Filename,Method,Body,level

method_bodies = ""
test_code = ""

for index, row in method_bodies_file_df.iterrows():
    # check if the method is same as that mentioned by test_name
    generic_name_temp = row['Method'].replace('::', '_').replace('/', '_').replace('.py', '').replace('.', '_')
    print(f"generic_name_temp: {generic_name_temp}")

    if generic_log_name.endswith(generic_name_temp):
        # if yes, then add the method body to the test_code
        test_code += f"Test: {row['Filename']}/{row['Method']}\n"
        test_code += f"{row['Body']}\n"
        test_code += "\n"
        continue


    method_bodies += f"Method: {row['Filename']}/{row['Method']}\n"
    method_bodies += f"{row['Body']}\n"
    method_bodies += "\n"




# Generate a test response
prompt = f'I have the following {category} flaky tests, which passes and fails non-determinstically. When the test fails, we get the following failure-log starting with “#Failure”.  Along with these information, I am giving “#Code-Under-Tests that are executed” this contains all the methods that are executed during the test-run. Your task is  to modify the code-under-test, that can lead to the given test failure consistently? Your output should be within <Output> tag. Do not change the semantics of the test-code. \n#Failure\n{failure_log}\n#Code-Under-Tests\n{method_bodies}\n#Test-code\n{test_code}'
# prompt = "How are you? Give me max 5 words answer"
print(f"Prompt: {prompt}")
print("Generating response...")

response = generator(prompt, temperature=0.01, num_return_sequences=1, return_full_text=False)
print(response[0]['generated_text'])

# exit(0)

# get the size of the response in terms of number of tokens
num_tokens = len(tokenizer.encode(response[0]['generated_text']))
num_input_tokens = len(tokenizer.encode(prompt))

results_dir = f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/llama_results/{generic_log_name}.txt"
# Save the response to a file
with open(results_dir, "w") as f:
    f.write(f"size of input tokens: {num_input_tokens}\n")
    f.write(f"size of response tokens: {num_tokens}\n")
    f.write(response[0]['generated_text'])























# # Input data
# data_file = sys.argv[1]
# subject = pd.read_csv(data_file, header=None).iloc[0]

# git_repo = subject[0]
# project_name = subject[0].split("/")[-1]
# sha = subject[1]
# test_name = subject[2]
# python_version = subject[3]
# category = subject[4]

# generic_log_name = f"{project_name}_{test_name.replace('::', '_').replace('/', '_').replace('.py', '').replace('.', '_')}"
# method_bodies_file = f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/pretrained_data/{generic_log_name}.csv"
# failure_log_dir = f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/logs/{generic_log_name}/fail"

# # Load failure log
# try:
#     failure_log_file = os.path.join(failure_log_dir, os.listdir(failure_log_dir)[0])
#     with open(failure_log_file, "r") as f:
#         failure_log = f.read()
# except IndexError:
#     print(f"Failure log directory is empty: {failure_log_dir}")
#     sys.exit(1)

# # Load methods
# method_bodies_df = pd.read_csv(method_bodies_file)
# method_bodies = ""
# test_code = ""

# for _, row in method_bodies_df.iterrows():
#     generic_name_temp = row['Method'].replace('::', '_').replace('/', '_').replace('.py', '').replace('.', '_')
#     if generic_log_name.endswith(generic_name_temp):
#         test_code += f"Test: {row['Filename']}/{row['Method']}\n{row['Body']}\n\n"
#     else:
#         method_bodies += f"Method: {row['Filename']}/{row['Method']}\n{row['Body']}\n\n"

# # Simple prompt for now
# prompt = "How are you? Give me max 5 words answer"
# print(f"Prompt: {prompt}")
# print("Generating response...")

# response = generator(prompt, temperature=0.01, num_return_sequences=1, return_full_text=False)
# print(response[0]['generated_text'])
# print(response)
# exit(0)

# # Save response
# num_tokens = len(tokenizer.encode(response[0]['generated_text']))
# num_input_tokens = len(tokenizer.encode(prompt))

# results_dir = f"/scratch/tbaral/NOD-Test-Repair/NOD-Test-Repair/llama_results/{generic_log_name}.txt"
# with open(results_dir, "w") as f:
#     f.write(f"size of input tokens: {num_input_tokens}\n")
#     f.write(f"size of response tokens: {num_tokens}\n")
#     f.write(response[0]['generated_text'])
