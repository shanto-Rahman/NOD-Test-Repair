import textwrap
import re
import random
import string

def format_code_under_test(df):
    """Format the code-under-test DataFrame for LLM prompt."""
    code_blocks = []
    for _, row in df.iterrows():
        block = (
            f"Class: {row['Class']}\n"
            f"Method: {row['Method']}\n"
            f"Descriptor: {row.get('Descriptor', '')}\n"
            f"LineRange: {row.get('LineRange', '')}\n"
            f"Body:\n{row['Body']}\n"
            "-----"
        )
        code_blocks.append(block)
    return "\n".join(code_blocks)

def generate_prompt(failure_log_df, code_under_test_meths_ranked_df, test_meth_code_df):
    code_under_test_str = format_code_under_test(code_under_test_meths_ranked_df)
    failure_log_str = str(failure_log_df.iloc[0]) if hasattr(failure_log_df, "iloc") else str(failure_log_df)
    test_code_str = str(test_meth_code_df.iloc[0]) if hasattr(test_meth_code_df, "iloc") else str(test_meth_code_df)
    prompt = f"""
You are an expert Java developer specializing in diagnosing async-wait flakiness in tests.

You will be provided with:
1. A non-deterministic test failure log.
2. Up to 10 code-under-test methods, each with Class, Method, Descriptor, LineSpan, and source code, ranked by similarity to the test code.
3. The test code itself.

Your task:
- Carefully analyze each provided method and identify the **single most likely location** in each where injecting a deliberate delay (e.g., Thread.sleep(...)) would consistently trigger the test failure.
- For each location, output the following information in a ranked list (most likely first):
    - Class name
    - Method name
    - Descriptor
    - Line number for delay injection
    - The full modified method source with the delay injected at the chosen location (preferably near the beginning or middle, not at the end, and always wrapped in a try-catch for InterruptedException).

**Rules:**
1. Never choose a location inside any `synchronized { ... }` block or lock context.
2. Output a ranked list of up to 10 locations, each formatted as:
   - Class:Method:Descriptor:LineNumber
   - The full modified method source (with injected delay)
3. Wrap your answer **only** in `<Output>` and `</Output>`, with no extra text before or after.

<Input>
    <Failure>
{failure_log_str}
    </Failure>
    <Code-Under-Test>
{code_under_test_str}
    </Code-Under-Test>
    <Test-Code>
{test_meth_code_df}
    </Test-Code>
</Input>

<Output>
   ...
</Output>
"""
    definitions = """You are an expert at identifying flaky tests and analyzing their type. Flaky tests are tests that pass and fail non-deterministically for the same code. Always obey these rules exactly:
1. Never choose a location inside any `synchronized { … }` block or lock context.
2. In the output, write Class:Method:Descriptor:LineNumber, where Class is the class name, Method is the method name, Descriptor is the method descriptor, and LineNumber is the line number where you would inject the delay.
3. Output a ranked list of locations, maximum 10.
4. Wrap your answer **only** in `<Output>` and `</Output>`, with no extra text before or after.
5. Inside those tags, output the full modified method source for each location."""

    return prompt, definitions, code_under_test_str
