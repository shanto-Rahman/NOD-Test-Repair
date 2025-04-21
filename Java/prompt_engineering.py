
def generate_prompt(failure_log_df, code_under_test_meths, test_meth_code_df ):
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

    return prompt, definitions
