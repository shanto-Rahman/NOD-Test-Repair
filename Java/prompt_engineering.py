import textwrap
import re
import random
import string

def format_code_under_test(df):
    """Format the code-under-test DataFrame for LLM prompt."""
    code_blocks = []
    for _, row in df.iterrows():
        line_range = row.get('LineRange', '')
        if '-' in str(line_range):
            start, end = map(int, str(line_range).split('-'))
        else:
            start, end = 1, 1  # fallback
        
        # Split method body into lines and add file line numbers
        body_lines = str(row['Body']).split('\n')
        numbered_body = "\n".join(
            f"{start + i}: {line}" for i, line in enumerate(body_lines)
        )

        block = (
            f"Class: {row['Class']}\n"
            f"Method: {row['Method']}\n"
            f"Descriptor: {row.get('Descriptor', '')}\n"
            f"LineRange: {row.get('LineRange', '')}\n"
            f"Body:\n{numbered_body}\n"
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
2. Up to 10 code-under-test methods, each with Class, Method, Descriptor, LineRange, and source code, ranked by similarity to the test code. Each method body line is prefixed with its actual file line number.
3. The test code itself.

Your task:
- Carefully analyze each provided method and identify the **single most likely location** before which injecting a deliberate delay (e.g., Thread.sleep(...)) would consistently trigger the test failure.
- Output a ranked list (most likely first) of up to 10 locations, each in the following format:
    Class:Method:Descriptor:FileLineNumber (ActualCodeLine)
- The FileLineNumber is the actual line number in the source file, as shown before each line in the method body.
- The ActualCodeLine should be the exact code at that line, shown inside parentheses.
- You must analyze the full method body and logic to decide the most probable statement.
- **Do NOT output the full method source or any other text.**

**Rules:**
1. Never choose a location inside any `synchronized {{ ... }}` block or lock context.
2. Output a ranked list of up to 10 locations, each formatted as:
   Class:Method:Descriptor:FileLineNumber (ActualCodeLine)
3. Do NOT output the full method source or any other text.
4. Wrap your answer **only** in <Output> and </Output>, with no extra text before or after.
5. End your answer with </Output>.
6. Only suggest injecting a delay before the start of a complete Java statement, not in the middle of a multi-line statement or expression.
7. Never suggest a line that is a continuation of the previous line (e.g., lines starting with '.', ',', or inside parentheses).

<Input>
    <Failure>
{failure_log_str}
    </Failure>
    <Code-Under-Test>
{code_under_test_str}
    </Code-Under-Test>
    <Test-Code>
{test_code_str}
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
"""

    return prompt, definitions
