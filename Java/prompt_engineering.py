
def generate_prompt(failure_log_df, code_under_test_meths, test_meth_code_df ):
    prompt = f"""
    I have an async-wait flaky test that sometimes passes and fails unpredictably timing-related issues—most commonly asynchronous waits.

    When the test fails, it produces the following failure log:

    #Failure
    {failure_log_df}

    Below is the code that is executed during the test run:

    #Code-Under-Test
    {code_under_test_meths}
    
    And here is the test code itself:
    
    #Test-Code
    {test_meth_code_df}
    
    Analyze the Code-Under-Test and pinpoint the single method whose logic must be altered to reliably reproduce the test failure. To do this, insert a deliberate delay (e.g. a Thread.sleep) at the precise point in that method’s body so that the timing-related issue causes the test to fail every time.
    **Return only that modified method’s source**, wrapped exactly like:
    
    Output **only** the modified method wrapped in
    
    <Output>
        ...
    </Output>
    """
    definitions = """You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code."""

    return prompt, definitions
