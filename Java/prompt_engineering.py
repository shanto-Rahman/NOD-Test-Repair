def generate_prompt(failure_log_df, code_under_test_meths, test_meth_code_df ):
    prompt = f"""
    You are an expert Java developer diagnosing async-wait flakiness. 

    I will give you:  
    1. A non-deterministic test failure log  
    2. The full code-under-test-methods pre-selected and ranked by cosine similarity to the test code, each labeled with its Class and Method name 
    3. The async-wait test code  

    Your job is to find a location in one of the provided methods where inserting a deliberate delay (e.g. Thread.sleep(...)) between 5000 and 10000 milliseconds will consistently trigger the test failure. Avoid placing the delay at the very end of the method, as that is less likely to affect program behavior. Prefer injecting the delay near the **Beginning* or in the **Middle** of the method logic. When injecting delay, always wrap it in a try-catch block that handles InterruptedException.

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

   Analyze the Code-Under-Test and pinpoint the single method whose logic must be altered to reliably reproduce the test failure. 
 
    Return **only** the modified method wrapped in
    
    <Output>
        ...
    </Output>
    """
    definitions = """You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code. Always obey these rules exactly:
    1. Never choose a location inside any `synchronized { … }` block or lock context.
    2. Never output Markdown fences (```java``` etc).
    3. Wrap your answer **only** in `<Output>` and `</Output>`, with no extra text before or after.
    4. Inside those tags, output the full modified method source."""

    return prompt, definitions
