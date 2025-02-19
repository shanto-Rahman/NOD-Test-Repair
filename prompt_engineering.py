import textwrap
import re
import random
import string

def generate_prompt_without_any_slice_for_flaky_test_category(test_file_path, unit_test_body, test_name, failure_message): 
    #definition = f"""
    #<instructions>
    #    You are a software flaky test expert. A flaky test is a test that non-determinstically passes and fails in different runs. You have the following information:
    #    1. The failing unit test case is provided in the `<unit_test>` tag.
    #    2. The error message or failure output from the test is given in the `<failure_message>` tag.
    #    Your job is to mention what type of flaky test this test is.
    #    Your task is to mention the flaky test category using <Category> tag. 
    #</instructions>
    #"""

    ##For example, you can metion a test as async-wait or concurrency or time or resource or random or anything else by observing the test code and the failure message.
    #user_prompt = f"""
    #<data>
    #    <unit_test>
    #{unit_test_body}
    #    </unit_test>
    #    <failure_message>
    #{failure_message}
    #    </failure_message>
    #</data>"""
    #print("user_prompt=",user_prompt)
    definition = f"""
    <instructions>
        You are an expert in detecting and classifying flaky tests. 
        A flaky test is a test that exhibits non-deterministic behavior, 
        meaning it passes and fails across different test runs without code changes.
    
        You will be provided with:
        1. The failing unit test case enclosed in the `<unit_test>` tag.
        2. The corresponding failure message or error output within the `<failure_message>` tag.
    
        Your task is to analyze the provided information and **identify the category of flaky test** it belongs to. 
        Please respond only with the identified category enclosed in a `<Category>` tag.
    </instructions>
    """
    
    user_prompt = f"""
    <data>
        <unit_test>
    {unit_test_body}
        </unit_test>
        <failure_message>
    {failure_message}
        </failure_message>
    </data>
    """
    return definition, user_prompt
