# @zijwan
import boto3
import time
import datetime
import json 
from botocore.config import Config
import importlib
from langchain_aws import ChatBedrock
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
import re
#export AWS_DEFAULT_REGION=us-east-1

#region_name='us-west-2' #is for Claude3.0
region_name='us-east-1' # is for Claude3.5
#role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
role_arn = "arn:aws:iam::852483370298:role/bedrock_access_share_with_intern"
session_name = "BedrockSession"


class BedrockClientWithAutoRefresh:
    def __init__(self, role_arn, session_name, region_name):
        self.role_arn = role_arn
        self.session_name = session_name
        self.region_name = region_name
        self.session = boto3.Session()
        self.sts_client = self.session.client('sts', region_name=region_name)
        self.bedrock_client = None
        self.expiration = None
        self.refresh_credentials()

    def refresh_credentials(self):
        #print('authorizing')
        assumed_role = self.sts_client.assume_role(
            RoleArn=self.role_arn,
            RoleSessionName=self.session_name,
            DurationSeconds=12*60*60
        )
        credentials = assumed_role['Credentials']
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region_name
        )
        self.expiration = credentials['Expiration']
        #print(f'current expiration: {self.expiration}')

    def make_bedrock_call(self, api_call_function, *args, **kwargs):
        if self.expiration is None or datetime.datetime.now(datetime.timezone.utc) > self.expiration - datetime.timedelta(minutes=10):
            self.refresh_credentials()
        return api_call_function(self.bedrock_client, *args, **kwargs)


def query_claude_3(client, prompt: str): 
    # change it to the API you want
    payload = {
        "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        #"modelId":"anthropic.claude-3-sonnet-20240229-v1:0",
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

class Claude(object):
    def __init__(self, bedrock_client, session_memory, model = "sonnet", temperature = 0.4, top_k = 250, top_p = 0.4):
        models = {
            "v2": "anthropic.claude-v2:1",
            "haiku": "anthropic.claude-3-haiku-20240229-v1:0",
            #"sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "opus": "anthropic.claude-3-opus-20240229-v1:0",   # Not available for internal usage :(
            "sonnet" : "anthropic.claude-3-5-sonnet-20240620-v1:0"
        }
        params = {
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "stop_sequences": ["\n\nHuman"]
        }

        self.bedrock_client = bedrock_client
        self.model_name = models[model]
        self.params = params
        self.llm = ChatBedrock(model_id=self.model_name, model_kwargs=self.params, client=self.bedrock_client.bedrock_client, verbose=False)
        self.memory = session_memory
        self.chain_with_history = RunnableWithMessageHistory(self.llm, self.get_session_history)
    
    # Conversation History
    def get_session_history(self, session_id):
        if session_id not in self.memory:
            self.memory[session_id] = ChatMessageHistory()
            #print('session_memory=',self.memory[session_id])
        return self.memory[session_id]
    
    def extract_failure_message_content(self, prompt_string, category):
        # Use regular expressions to extract content inside <failure_message> tags
        if category == "prompt":
            match = re.search(r"<failure_message>(.*?)</failure_message>", prompt_string, re.DOTALL)
            return match.group(1).strip() if match else prompt_string
        elif category == "code":
            match = re.search(r"<repaired_test_method>(.*?)</repaired_test_method>", prompt_string, re.DOTALL)
            code = match.group(1).strip() if match else prompt_string
            #print("match of generated_code=", code)
            return f'"""{code}"""'
    
    def remove_additional_kwargs(self, session_history):
        # Remove additional_kwargs from HumanMessage and AIMessage
        for message in session_history.messages:
            if hasattr(message, 'additional_kwargs'):
                del message.additional_kwargs
    
    def remove_metadata(self, session_history):
        for message in session_history.messages:
            if hasattr(message, 'response_metadata'):
                del message.response_metadata
            if hasattr(message, 'usage_metadata'):
                del message.usage_metadata
 

    def extract_static_content(self, prompt_string):
        # Extract the static content of the message
        match = re.search(r"</failure_message>(.*)</data>", prompt_string, re.DOTALL)
        return match.group(1).strip() if match else ""

    # Used for change curation, and test Fix
    def infer_using_claude(self, prompt_string, chain_of_thought=False, session_id="1", max_retry=10000):
        retry = 0
        while(retry < max_retry):
            try:         
                session_history = self.get_session_history(session_id)
                '''last_human_message = None
                for message in reversed(session_history.messages):
                    if isinstance(message, HumanMessage):
                        last_human_message = message
                        break

                if last_human_message:
                    if isinstance(last_human_message, HumanMessage):

                        # Extract the content of the last HumanMessage
                        human_content = last_human_message.content
                        #print("***********NOW GOING TO remove redundant stuff") 
                        last_human_message.content = modified_content'''

                #print(f"Session History before adding new message: {session_history.messages}")

                if chain_of_thought:
                    response = self.chain_with_history.invoke({"prompt": prompt_string},
                    config={"configurable": {"session_id": session_id}}
                    ).content.strip()  #self.chain_with_history.invoke(prompt_string, config={"configurable": {"session_id": "1"}}).content.strip()
                else:
                    response = self.llm.invoke(prompt_string).content.strip()
                gen_code = self.extract_failure_message_content(response, category="code")
                #print('generated_test=', gen_code)
                self.remove_additional_kwargs(session_history)
                self.remove_metadata(session_history)

                #print(f"Session History for {session_id} after adding response: {session_history.messages}")
                return response
            except Exception as e:
                if 'ThrottlingException' in str(e):
                    print("Throttling Exception: retrying after waiting 4 seconds...")
                    retry = retry + 1
                    time.sleep(4)
                elif 'ExpiredTokenException' in str(e):
                    print("Token is expired, refreshing credentials...")
                    return 'ExpiredTokenException'
                else:
                    print("Error while running inference: " + str(e))
                    raise e
        
        if retry >= max_retry:
            print(f"Still receiving Throttling Exception after {retry} retries")
            raise e

    # Used for change curation, and test Fix
    def generate_static_slice_using_claude(self, prompt_string, chain_of_thought=False, session_id="2", max_retry=10000):
        retry = 0
        while(retry < max_retry):
            try:         
                session_history = self.get_session_history(session_id)
                '''last_human_message = None
                for message in reversed(session_history.messages):
                    if isinstance(message, HumanMessage):
                        last_human_message = message
                        break

                if last_human_message:
                    if isinstance(last_human_message, HumanMessage):

                        # Extract the content of the last HumanMessage
                        human_content = last_human_message.content
                        last_human_message.content = modified_content'''
                        #print('last_message.content=',last_human_message.content)

                #print(f"Session History before adding new message: {session_history.messages}")
                #print('prompt=', prompt_string)
                if chain_of_thought:
                    response = self.chain_with_history.invoke({"prompt": prompt_string},
                    config={"configurable": {"session_id": session_id}}
                    ).content.strip()  #self.chain_with_history.invoke(prompt_string, config={"configurable": {"session_id": "1"}}).content.strip()
                else:
                    response = self.llm.invoke(prompt_string).content.strip()
                gen_code = self.extract_failure_message_content(response, category="code")
                #print('gen_code=',gen_code)
                # Clean up session history
                #self.remove_additional_kwargs(session_history)
                #self.remove_metadata(session_history)

                #print(f"Session History for {session_id} after adding response: {session_history.messages}")
                #print('response=',response)
                #print("********")
                return response
            except Exception as e:
                if 'ThrottlingException' in str(e):
                    print("Throttling Exception: retrying after waiting 4 seconds...")
                    retry = retry + 1
                    time.sleep(4)
                elif 'ExpiredTokenException' in str(e):
                    print("Token is expired, refreshing credentials...")
                    return 'ExpiredTokenException'
                else:
                    print("Error while running inference: " + str(e))
                    raise e
        
        if retry >= max_retry:
            print(f"Still receiving Throttling Exception after {retry} retries")
            raise e
# Infer Claude for unit tests
#def get_and_save_claude_response(prompt, session_memory, chain_of_thought=False):
#    # Use the provided session_memory or create a new one if not provided
#    print(f"****BEFORE: Session memory = {session_memory}")
#    bedrock_client = BedrockClientWithAutoRefresh(role_arn, session_name, region_name)
#    claude = Claude(bedrock_client, session_memory)
#    answer = claude.infer_using_claude(prompt, chain_of_thought) 
#    print(answer)
#    exit()
#    return answer
