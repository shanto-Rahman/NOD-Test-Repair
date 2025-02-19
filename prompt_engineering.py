import textwrap
import re
import random
import string

def generate_prompt_without_any_slice_for_flaky_test_category(test_file_path, unit_test_body, test_name, failure_message): 
    definition = f"""
    <instructions>
        You are analyzing a software testing expert. A flaky test is a test that non-determinstically passes and fails in different runs. You have the following information:
        1. The failing unit test case is provided in the `<unit_test>` tag.
        2. The error message or failure output from the test is given in the `<failure_message>` tag.
        Your job is to mention what type of flaky test this test is.
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
    </data>"""
    #print("user_prompt=",user_prompt)
    return definition, user_prompt
