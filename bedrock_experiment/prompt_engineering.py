import textwrap

def collect_static_slice_prompt(focal_method_file_content, changed_fm_code, diff_focal_method, test_file_content, unit_test_body, failure_log, test_name, fm_name):
    prompt = f""" 

<instructions> 
    You are analyzing a program where a unit test that previously passed is now failing due to changes in the *focal method* it was testing. You have the following information:

    1. The failing unit test case is provided in the `<unit_test>` tag.
    2. The error message or failure output from the test is given in the `<failure_message>` tag.
    3. The modified version of the focal method is included in the `<modified_focal_method>` tag.
    4. The specific changes made to the focal method are detailed in the `<focal_method_diff>` tag.
    5. The entire class file containing the focal method is provided in the `<focal_file>` tag.
    
    Your task is to:
    
    1. Identify and return only the relevant code context from the focal file, excluding the modified focal method itself. This context should be related to the focal method (e.g., any class or method that is used or called by the focal method) and could be useful in fixing the test. You may return one or more code slices, each enclosed in `<context-1>`, `<context-2>`, etc., and all enclosed within the `<relevant_program_slice>` tag.

</instructions>

<data> 
    <failure_message>
{failure_log}
    </failure_message>

    <code_under_test> 
        <focal_file>
{focal_method_file_content}
        </focal_file>
        <modified_focal_method, name={fm_name}>
{changed_fm_code}
        </modified_focal_method>
        <focal_method_diff> 
{diff_focal_method} 
        </focal_method_diff>
    </code_under_test>

    <unit_test name={test_name}>
{unit_test_body}
    </unit_test>
</data>
    """
    return prompt


def generate_promt_for_change_curation_to_reduce_cc(test_file_path, test_file_content, test_name, test_body, test_lines, focal_method_file_path, focal_method_body, focal_method_file_content, focal_method_name, focal_method_lines, feedback):

    prompt_to_reduce_code_coverage = f"""You are provided with a unit test and a corresponding focal method within a codebase.
   
<instructions> 
    1. The goal is described in the <goal> tag: 
       <goal>
         a. Locate the focal method and the unit test based on the provided file paths, names, and line numbers.
         b. Introduce as many changes as you can in the given focal method to reduce code coverage with test pass.
       </goal>
    2. The changes might be in the following ways:
      <changes>
          <variable>Add, modify, or delete variables.</variable>
          <statement>Add, delete, or modify statements.</statement>
          <api_change>Make API changes.</api_change>
          <type_change>Change variable or parameter types.</type_change>
          <parameter_change>Modify method parameter names.</parameter_change>
          <parameter_immutable>Make parameters immutable.</parameter_immutable>
          <abstraction>Abstract methods.</abstraction>
          <exception_handling>Add try blocks.</exception_handling>
          <modifier>Change access modifiers.</modifier> 
          <branch>Introduce new branches.</branch>
          <condition>Change conditions.</condition>
          <loop>Introduce new or change existing loops.</loop>
          <refactoring>Refactor code for quality and maintainability.</refactoring>
          <logging>Add, modify, or remove logging statements.</logging>
          <annotations>Add or modify annotations or decorators.</annotations>
          <documentation>Add or modify docstrings and comments.</documentation>
          <data_structures>Change the data structures used.</data_structures>
          <control_flow>Change the flow of control.</control_flow>
          <method_extraction>Extract new methods from existing ones.</method_extraction>
          <performance_optimization>Optimize code for performance.</performance_optimization>
          <security_enhancements>Add or modify security-related code.</security_enhancements>
          <dependency_injection>Introduce or modify dependency injection.</dependency_injection>
          <error_handling>Enhance error handling and exception management.</error_handling>
          <configuration>Modify configuration parameters or settings.</configuration>
          <concurrency>Introduce concurrency or parallelism.</concurrency>
          <state_management>Change how state is managed or stored.</state_management>
          <validation>Add or modify data validation logic.</validation>
          <cleanup>Add cleanup code or ensure proper resource management.</cleanup>
          <other>Make any other changes that seem natural to a developer.</other>
      </changes>

     <constraints>
         a. The changed code should be compilable, and logically consistent.
         b. The test must pass.
         c. Changes should be natural; do not suggest blocks like `if False:` or `if True:`.
     </constraints>

    3. Return only the changed focal method in <changed_focal_method> tags. Outside of <changed_focal_method> tag, specify the changes you have made with the proper tags, enclosed with the <changes_type> tag.
    4. Wrap the response <changed_focal_method> and <changes_type> into <root> tag to ensure well-formed XML.
</instructions>

<data> 
    <code_under_test>
        <focal_method_class reason="context">
            <source_code>
{focal_method_file_content}
            </source_code>
        </focal_method_class>
    
        <focal_method name={focal_method_name} lines={focal_method_lines}>
            <source_code>
{focal_method_body}
            </source_code>
        </focal_method>
    </code_under_test>

        <test_class reason="context">
            <source_code>
{test_file_content}
            </source_code>
        </test_class>
    <unit_test name={test_name} lines={test_lines}>
        <source_code>
{test_body}
        </source_code>
    </unit_test>
</data>

    """
    return feedback+prompt_to_reduce_code_coverage


def generate_promt_for_change_curation_to_test_fail(test_file_path, test_file_content, test_body, test_name, test_lines, focal_method_file_path, focal_method_body, focal_method_file_content, focal_method_name, focal_method_lines, feedback):
    # Prompt to make the test fail
    prompt_to_make_assertion_failure = textwrap.dedent(f"""
   <instructions> 
    1. You are provided with a unit test and a corresponding focal method within a codebase. You are also provided the full source code of the class that contains the focal method and unit test, respectively. The full source code for focal method and unit test are given for more context. 

    The goal is described in the <goal> tag: 
       <goal>
    Introduce as many changes as you can in the given focal method to make assertion fails.
       </goal>
    2. The changes might be in the following ways:
      <changes>
          <statement>Add, delete, or modify statements.</statement>
          <api_change>Make API changes.</api_change>
          <type_change>Change variable or parameter types.</type_change>
          <parameter_change>Modify method parameter names.</parameter_change>
          <parameter_immutable>Make parameters immutable.</parameter_immutable>
          <abstraction>Abstract methods.</abstraction>
          <exception_handling>Add try blocks.</exception_handling>
          <modifier>Change access modifiers.</modifier> 
          <branch>Introduce new branches.</branch>
          <condition>Change conditions.</condition>
          <loop>Introduce new or change existing loops.</loop>
          <refactoring>Refactor code for quality and maintainability.</refactoring>
          <logging>Add, modify, or remove logging statements.</logging>
          <annotations>Add or modify annotations or decorators.</annotations>
          <documentation>Add or modify docstrings and comments.</documentation>
          <data_structures>Change the data structures used.</data_structures>
          <control_flow>Change the flow of control.</control_flow>
          <method_extraction>Extract new methods from existing ones.</method_extraction>
          <performance_optimization>Optimize code for performance.</performance_optimization>
          <security_enhancements>Add or modify security-related code.</security_enhancements>
          <dependency_injection>Introduce or modify dependency injection.</dependency_injection>
          <error_handling>Enhance error handling and exception management.</error_handling>
          <configuration>Modify configuration parameters or settings.</configuration>
          <concurrency>Introduce concurrency or parallelism.</concurrency>
          <state_management>Change how state is managed or stored.</state_management>
          <validation>Add or modify data validation logic.</validation>
          <cleanup>Add cleanup code or ensure proper resource management.</cleanup>
          <change_return>Changing return values to incorrect ones.</change_return>
          <alter_condition>Altering logical conditions so they fail.</alter_condition>
          <revome_critical_functionality>Removing critical functionality that the test relies on.</revome_critical_functionality>
          <variable>Add, modify, or delete variables.</variable>
          <other>Make any other changes that seem natural to a developer.</other>
      </changes>

     <constraints>
         a. The changed code should be compilable, and logically consistent.
         b. The test assertion must fail.
         c. Consider edge cases, boundary conditions, and different input scenarios to ensure comprehensive testing.
         d. Changes should be natural; do not suggest blocks like `if False:` or `if True:`.
         e. Initialize any required objects and set up test data, if necessary.
     </constraints>

    3. Return only the changed focal method in <changed_focal_method> tags. Outside of <changed_focal_method> tag, specify the changes you have made with the proper tags, enclosed with the <changes_type> tag.
    4. Wrap the response of both <changed_focal_method> and <changes_type> tags into <root> tag to ensure well-formed XML.
</instructions>


<data> 
    <code_under_test>
        <focal_method_class reason="context">
            <source_code>
{focal_method_file_content}
            </source_code>
        </focal_method_class>
    
        <focal_method name={focal_method_name} lines={focal_method_lines}>
            <source_code>
{focal_method_body}
            </source_code>
        </focal_method>
    </code_under_test>

        <test_class reason="context">
            <source_code>
{test_file_content}
            </source_code>
        </test_class>
    <unit_test name={test_name} lines={test_lines}>
        <source_code>
{test_body}
        </source_code>
    </unit_test>
</data>
    """)
    #print(prompt_to_make_assertion_failure)
    return feedback+prompt_to_make_assertion_failure


def generate_prompt_without_any_slice_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, failure_message, diff_focal_method):    

    prompt_to_make_assertion_failure = f"""
    <instructions>
        You are analyzing a software testing situation. A unit test case that previously passed is now failing due to an update in the *focal method* it was testing. You have the following information:

        1. The failing unit test case is provided in the `<unit_test>` tag.
        2. The error message or failure output from the test is given in the `<failure_message>` tag.
        3. The changed focal method is given in the `<changed_focal_method>` tag.

        Your task is to:

        1. Repaire the test method, ensuring it covers the changes made in the focal method. 
            a. Wrap your repaired test in `<repaired_test_method>` tag.
            b. Mention the changes you made using `<modification_type>` tag.
            c. Ensure the entire response, `<repaired_test_method>` and `<modification_type>` tags are wrapped in a `<root>` tag to maintain well-formed XML.
        2. Follow the constraints provided under the `<constraints>` tag while fixing/updating the test.
    </instructions>
    
    <constraints>
        1. The repaired test must pass.
        2. Ensure that your suggested code does not introduce any other errors.
    </constraints>
    
    <data>
        <changed_focal_method>
    {changed_fm_code}
        </changed_focal_method>
        <unit_test name={test_name}>
    {unit_test_body}
        </unit_test>
        <failure_message>
    {failure_message}
        </failure_message>
    </data>
    """
    return prompt_to_make_assertion_failure



def generate_prompt_with_dynamic_traces_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, failure_message, diff_focal_method, dynamic_trace):

    prompt_to_make_assertion_failure = f"""
    <instructions>
        You are analyzing a software testing situation. A unit test case that previously passed is now failing due to an update in the *focal method* it was testing. You have the following information:

        1. The failing unit test case is provided in the `<unit_test>` tag.
        2. The error message or failure output from the test is given in the `<failure_message>` tag.
        3. A diff showing how the focal method was changed is given in the `<diff_focal_method>` tag.
        4. Additional context information that you can *optionally* use to analyze with `<optional_focal_method_context>` tag. This context comes from dynamic traces, showing the Python filenames, methods, and line numbers that were executed during the test.

        Your task is to:

        1. Repaire the test method, ensuring it covers the changes made in the focal method. Optionally, you can use the <optional_focal_method_context> to analyze the failure.
            a. Wrap your repaired test in `<repaired_test_method>` tag.
            b. Mention the changes you made using `<modification_type>` tag.
            c. Ensure the entire response, `<repaired_test_method>` and `<modification_type>` tags are wrapped in a `<root>` tag to maintain well-formed XML.
        2. Follow the constraints provided under the `<constraints>` tag while fixing/updating the test.
    </instructions>
    
    <constraints>
        1. The repaired test must pass.
        2. Ensure that your suggested code does not introduce any other errors.
    </constraints>
    
    <data>
        <diff_focal_method>
    {diff_focal_method}
        </diff_focal_method>
        <optional_focal_method_context>
    {dynamic_trace}
        </optional_focal_method_context>
        <unit_test name={test_name}>
    {unit_test_body}
        </unit_test>
        <failure_message>
    {failure_message}
        </failure_message>
    </data>
    """

    return prompt_to_make_assertion_failure



def generate_prompt_with_static_slices_for_test_repair_that_was_failed(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, failure_message, diff_focal_method, context_slice):

    prompt_to_make_assertion_failure = f"""
    <instructions>
        You are analyzing a software testing situation. A unit test case that previously passed is now failing due to an update in the *focal method* it was testing. You have the following information:

        1. The failing unit test case is provided in the `<unit_test>` tag.
        2. The error message or failure output from the test is given in the `<failure_message>` tag.
        3. A diff showing how the focal method was changed is given in the `<diff_focal_method>` tag.
        4. Additional context information that you can *optionally* use to analyze with `<optional_focal_method_context>` tag.  This context comes from static analysis of the focal method and may include relevant classes or methods.

        Your task is to:

        1. Repaire the test method, ensuring it covers the changes made in the focal method. Optionally, you can use the <optional_focal_method_context> to analyze the failure.
            a. Wrap your repaired test in `<repaired_test_method>` tag.
            b. Mention the changes you made using `<modification_type>` tag.
            c. Ensure the entire response, `<repaired_test_method>` and `<modification_type>` tags are wrapped in a `<root>` tag to maintain well-formed XML.
        2. Follow the constraints provided under the `<constraints>` tag while fixing/updating the test.
    </instructions>
    
    <constraints>
        1. The repaired test must pass.
        2. Ensure that your suggested code does not introduce any other errors.
    </constraints>
    
    <data>
        <diff_focal_method>
    {diff_focal_method}
        </diff_focal_method>
        <optional_focal_method_context>
    {context_slice}
        </optional_focal_method_context>
        <unit_test name={test_name}>
    {unit_test_body}
        </unit_test>
        <failure_message>
    {failure_message}
        </failure_message>
    </data>
    """

    return prompt_to_make_assertion_failure



def generate_prompt_without_slice_that_had_less_cc(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, feedback, diff_focal_method_with_line_number, changed_line_numbers, diff_fm):
    #Question: Should we hope for getting code-coverage 100% or increasing the code-coverage?
    # The focal method can or cannot be the the modified one. It may happen that the original focal method has less code coverage. That's why we are saying we are improving test code coverage

    prompt_to_increase_cc = f"""
        <instructions>
            You are working on software testing. You have a focal method that was changed in the code. Your job is to create a new test to execute the changed lines of the method.
    
            1. The changed focal method is provided in the <diff_focal_method> tag.
               a. This tag displays the differences in the method, with added lines marked by a + sign at the beginning of each line and deleted lines marked by a - sign.
               b. Lines that remain unchanged are not preceded by any symbol.
            2. Only updated lines of focal method are shown in the `<only_updated_lines_in_focal_method>` tag. Each line starts with the line number at the beginning.
            3. You are also given the changed line numbers in the `<changed_line_numbers>` tag, indicating the lines that must be covered by the new test.
            4. There is an existing test in the `<similar_unit_test>` tag that provides context on how the original focal method was tested before it was changed. Use this test to understand the context and how the focal method was used.
    
            Your task is to:
    
            1. Write a new test that will execute primarily on the changes made to the focal method when running the test, and ensure that the test passes.
                a. Put your new test method inside the `<generated_test_method>` tag.
                b. Write the name of your new test inside the `<generated_test_name>` tag.
                c. Describe the changes you made inside the `<generation_type>` tag.
                d. Wrap the `<generated_test_method>`, `<generated_test_name>`, and `<generation_type>` tags in a `<root>` tag to make sure the XML is correct.
            2. Follow the rules in the `<constraints>` tag when creating the test.
        </instructions>
    
        <constraints>
            1. The new test must pass.
            2. Make sure the code does not create any new errors.
            3. Avoid using if-else conditions in the new test method.
        </constraints>
    
        <data>
            <diff_focal_method>
    {diff_fm}
            </diff_focal_method>

            <only_updated_lines_in_focal_method>
    {diff_focal_method_with_line_number}
            </only_updated_lines_in_focal_method>

            <changed_line_numbers>
    {changed_line_numbers}
            </changed_line_numbers>

            <similar_unit_test>
    {unit_test_body}
            </similar_unit_test>
        </data>
        """

    return prompt_to_increase_cc


def generate_prompt_with_dynamic_trace_that_had_less_cc(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, feedback, diff_focal_method_with_line_number,changed_line_numbers,context_slice, diff_fm):
    #Question: Should we hope for getting code-coverage 100% or increasing the code-coverage?
    # The focal method can or cannot be the the modified one. It may happen that the original focal method has less code coverage. That's why we are saying we are improving test code coverage

    prompt_to_increase_cc = f"""
    <instructions>
        You are analyzing a software testing situation. You have a focal method that was changed in the code. Your job is to create a new test for changed lines of the method.
    
            1. The specific changes of focal method are shown in the `<diff_focal_method>` tag. Each line starts with the line number at the beginning.
            2. You are also given the changed line numbers in the `<changed_line_numbers>` tag, indicating the lines that must be covered by the new test.
            3. There is an existing test in the `<similar_unit_test>` tag that provides context on how the original focal method was tested before it was changed. Use this test to understand the context and how the focal method was used.
            4. Additional context information that you can *optionally* use to analyze with `<optional_focal_method_context>` tag. This context comes from dynamic traces of the code that might be relevant for this test.
    
            Your task is to:
    
            1. Write a new test that focuses primarily on the changes made to the focal method. You don’t need to mandatorily cover the statements that weren't changed.
                a. Put your new test method inside the `<generated_test_method>` tag.
                b. Write the name of your new test inside the `<generated_test_name>` tag.
                c. Describe the changes you made inside the `<generation_type>` tag.
                d. Wrap the `<generated_test_method>`, `<generated_test_name>`, and `<generation_type>` tags in a `<root>` tag to make sure the XML is correct.
            2. Follow the rules in the `<constraints>` tag when creating the test.
        </instructions>
    
        <constraints>
            1. The new test must pass.
            2. Make sure the code does not create any new errors.
            3. Avoid using if-else conditions in the new test method.
        </constraints>
    
        <data>
            <diff_focal_method>
    {diff_fm}
            </diff_focal_method>

            <changed_line_numbers>
    {changed_line_numbers}
            </changed_line_numbers>

            <similar_unit_test>
    {unit_test_body}
            </similar_unit_test>

            <optional_focal_method_context>
    {context_slice}
            </optional_focal_method_context>
        </data>
    """


    return prompt_to_increase_cc


def generate_prompt_with_static_slice_that_had_less_cc(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, feedback, diff_focal_method_with_line_number, changed_line_numbers, context_slice, diff_fm):
    #Question: Should we hope for getting code-coverage 100% or increasing the code-coverage?
    # The focal method can or cannot be the the modified one. It may happen that the original focal method has less code coverage. That's why we are saying we are improving test code coverage
    prompt_to_increase_cc = f""" 
        <instructions>
            You are working on software testing. You have a focal method that was changed in the code. Your job is to create a new test for changed lines of the method.
    
            1. The specific changes of focal method are shown in the `<diff_focal_method>` tag. Each line starts with the line number at the beginning.
            2. You are also given the changed line numbers in the `<changed_line_numbers>` tag, indicating the lines that must be covered by the new test.
            3. There is an existing test in the `<similar_unit_test>` tag that provides context on how the original focal method was tested before it was changed. Use this test to understand the context and how the focal method was used.
            4. Additional context information that you can *optionally* use to analyze with `<optional_focal_method_context>` tag. This context comes from static slices of the code that might be relevant for this test.
    
            Your task is to:
    
            1. Write a new test that focuses primarily on the changes made to the focal method. You don’t need to mandatorily cover the statements that weren't changed.
                a. Put your new test method inside the `<generated_test_method>` tag.
                b. Write the name of your new test inside the `<generated_test_name>` tag.
                c. Describe the changes you made inside the `<generation_type>` tag.
                d. Wrap the `<generated_test_method>`, `<generated_test_name>`, and `<generation_type>` tags in a `<root>` tag to make sure the XML is correct.
            2. Follow the rules in the `<constraints>` tag when creating the test.
        </instructions>
    
        <constraints>
            1. The new test must pass.
            2. Make sure the code does not create any new errors.
            3. Avoid using if-else conditions in the new test method.
        </constraints>
    
        <data>
            <diff_focal_method>
    {diff_fm}
            </diff_focal_method>

            <changed_line_numbers>
    {changed_line_numbers}
            </changed_line_numbers>

            <similar_unit_test>
    {unit_test_body}
            </similar_unit_test>

            <optional_focal_method_context>
    {context_slice}
            </optional_focal_method_context>
        </data>
    """
    return prompt_to_increase_cc


def generate_prompt_with_both_static_and_dynamic_trace_that_had_less_cc(test_file_path, test_file_content, unit_test_body,  test_name, test_lines, focal_method_file_path, focal_method_file_content, changed_fm_code, focal_method_name, focal_method_lines, feedback, diff_focal_method_with_line_number,changed_line_numbers,static_slice, diff_fm, dynamic_slice):
    #Question: Should we hope for getting code-coverage 100% or increasing the code-coverage?
    # The focal method can or cannot be the the modified one. It may happen that the original focal method has less code coverage. That's why we are saying we are improving test code coverage

    prompt_to_increase_cc = f"""
    <instructions>
        You are analyzing a software testing situation. You have a focal method that was changed in the code. Your job is to create a new test for changed lines of the method.
    
            1. The specific changes of focal method are shown in the `<diff_focal_method>` tag. Each line starts with the line number at the beginning.
            2. You are also given the changed line numbers in the `<changed_line_numbers>` tag, indicating the lines that must be covered by the new test.
            3. There is an existing test in the `<similar_unit_test>` tag that provides context on how the original focal method was tested before it was changed. Use this test to understand the context and how the focal method was used.
            4. You are provided with additional context information, which you can optionally use for analysis under the `<optional_focal_method_context>` tag. This includes both the static and dynamic traces of the code, which may be relevant to this test.
    
            Your task is to:
    
            1. Write a new test that focuses primarily on the changes made to the focal method. You don’t need to mandatorily cover the statements that weren't changed.
                a. Put your new test method inside the `<generated_test_method>` tag.
                b. Write the name of your new test inside the `<generated_test_name>` tag.
                c. Describe the changes you made inside the `<generation_type>` tag.
                d. Wrap the `<generated_test_method>`, `<generated_test_name>`, and `<generation_type>` tags in a `<root>` tag to make sure the XML is correct.
            2. Follow the rules in the `<constraints>` tag when creating the test.
        </instructions>
    
        <constraints>
            1. The new test must pass.
            2. Make sure the code does not create any new errors.
            3. Avoid using if-else conditions in the new test method.
        </constraints>
    
        <data>
            <diff_focal_method>
    {diff_fm}
            </diff_focal_method>

            <changed_line_numbers>
    {changed_line_numbers}
            </changed_line_numbers>

            <similar_unit_test>
    {unit_test_body}
            </similar_unit_test>

            <optional_focal_method_context>
            <static_trace>
    {static_slice}
            </static_trace>
            <dynamic_trace>
    {dynamic_slice}
            </dynamic_trace>
            </optional_focal_method_context>
        </data>
    """

    return prompt_to_increase_cc
