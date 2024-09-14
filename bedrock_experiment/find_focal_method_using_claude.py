import pandas as pd
import boto3
import sys
from access_in_claude import BedrockClientWithAutoRefresh
from save_result import claude_result_save_to_file
import os

region_name='us-west-2' # is for Claude3.0
role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
session_name = "BedrockSession"
bedrock_client = BedrockClientWithAutoRefresh(role_arn, session_name, region_name)

MODEL_IDS = [
    #"amazon.titan-text-express-v1",
    #"amazon.titan-text-lite-v1",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    #"anthropic.claude-3-haiku-20240307-v1:0",
    #"meta.llama3-70b-instruct-v1:0",
    #"mistral.mistral-large-2402-v1:0",
    #"mistral.mixtral-8x7b-instruct-v0:1",
    #"mistral.mistral-7b-instruct-v0:2",
    ]

def invoke_bedrock_model(client, id, prompt, max_tokens=2000, temperature=0, top_p=0.9):
    response = ""
    try:
        response = client.converse(
            modelId=id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "temperature": temperature,
                "maxTokens": max_tokens,
                "topP": top_p
            }
        )
    except Exception as e:
        print(e)
        result = "Model invocation error"
    try:
        result = response['output']['message']['content'][0]['text'] #\
        #+ '\n--- Latency: ' + str(response['metrics']['latencyMs']) \
        #+ 'ms - Input tokens:' + str(response['usage']['inputTokens']) \
        #+ ' - Output tokens:' + str(response['usage']['outputTokens']) + ' ---\n'
        return result
    except Exception as e:
        print(e)
        result = "Output parsing error"
    return result


def query_claude_3(client, prompt: str):
    # change it to the API you want
    payload = {
        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ]
                }
            ]
        }
    }

    # Convert the payload to bytes
    body_bytes = json.dumps(payload['body']).encode('utf-8')

    response = client.invoke_model(
        body=body_bytes,
        contentType=payload['contentType'],
        accept=payload['accept'],
        modelId=payload['modelId']
    )
    response_body = response['body'].read().decode('utf-8')
    text_response = json.loads(response_body)["content"][0]["text"]
    return text_response

if __name__ == "__main__":
    #prompt = sys.argv[1] #("What is the capital of Italy?")
    file_path = sys.argv[1] #("What is the capital of Italy?")
    file_name = file_path.split('/')[-1]
    #print(filename)

    df = pd.read_csv(file_path)
    outputDir = "Results"
    if not os.path.exists(outputDir):
        print('Making output dir')
        os.makedirs(outputDir, exist_ok=True)
    if os.path.exists("Results/"+file_name):
        os.remove("Results/"+file_name)
    print(len(df))
    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Access columns by name
        proj_name = row['proj_name']
        git_link = row['git_link']
        test_file_name = row['file_name']
        test_method = row['test_method']
        function_block = row['test_method_block']
        prompt = f"""Unit tests are designed to test specific methods or functions within a codebase. The focal method(s) are the methods or functions being tested in a particular unit test case. To identify the focal method(s), you can leverage the following. 1. Unit test method names: Typically, unit test method names follow a naming convention that includes the name of the method being tested (e.g., test_add for testing the add method). 2. Assertions: The assertions within the unit test case often involve calling the method being tested and checking the expected output or behavior. 3. Method calls: The unit test case may directly call the method being tested within  its setup or test methods.  Given the following unit test code: 
        Test:
        {function_block}
        Carefully analyze the unit test method names, assertions, and method calls within the provided code. Identify the focal method(s) being tested by leveraging these cues. Return only the method name(s)(api_calls no class name) with the number of arguments within that method calls separated by hash (for example test_add#3, here 3 is the number of arguments), without any additional text or explanation. You may encounter unit tests that test multiple methods or cases where it is difficult to determine the focal method(s) based on the provided code alone. In such cases, you can return Unable to determine the focal method(s) or provide your best guess separated by commas."""

        #print(f'{prompt}\n')
        #prompt="Can you tell me what is the capital of Bangladesh?"
        #print(f'{prompt}\n')
        for model_id in MODEL_IDS:
            response = bedrock_client.make_bedrock_call(invoke_bedrock_model, model_id, prompt)
            print(f'Response= {response}')
            apis = [api.strip() for api in response.split(',')]
            #print(type(response))
            for api in apis:
                print(api)
                #print(f'Model: {model_id}\n{response}')
                claude_result_save_to_file(outputDir+"/"+file_name, proj_name, git_link, test_file_name, test_method, api)
                break
    #exit()
