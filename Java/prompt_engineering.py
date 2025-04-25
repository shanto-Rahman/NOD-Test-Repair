
def generate_prompt(failure_log_df, code_under_test_meths, test_meth_code_df ):
    prompt = f"""
    You are an expert Java developer diagnosing async-wait flakiness. 

    I will give you:  
    1. A non-deterministic test failure log  
    2. The full code under test  
    3. The async-wait test code  

    Your job is to find a location from a method in the code under test where inserting a deliberate delay (e.g. `Thread.sleep(...)`) will force the test to fail every time.  You can start injecting delay from 500 to 5000 milliseconds.

<Input>
    <Failure>  
        {failure_log_df}  
    </Failure>  

    <Code-Under-Test>  
        {code_under_test_meths}  
    </Code-Under-Test>  

    <Test-Code>  
        {test_meth_code_df}  
    </Test-Code>  
</Input>

   Analyze the Code-Under-Test and pinpoint the single method whose logic must be altered to reliably reproduce the test failure. To do this, insert a deliberate delay (e.g. a Thread.sleep) at the precise point in that method’s body so that the timing-related issue causes the test to fail every time.
    
    Return **only** the modified method wrapped in
    
    <Output>
        ...
    </Output>
    """
    definitions = """You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code. Always obey these rules exactly:
    1. Never output Markdown fences (```java``` etc).
    2. Wrap your answer **only** in `<Output>` and `</Output>`, with no extra text before or after.
    3. Inside those tags, output the full modified method source."""

    return prompt, definitions
