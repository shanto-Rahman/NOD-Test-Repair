# For Benchmark Creation

```shell
python3 find_focal_method_using_claude.py ../test_analysis/Results/airtable-python-wrapper_function_block.csv

/mnt/efs/people/urshanto/change_aware_utg/test_analysis/Results/airtable-python-wrapper_function_block.csv
```
## To know the number of unique tests,
```shell
cut -d',' -f1-2 Results/airtable-python-wrapper_function_block.csv  | sort -u | wc -l
```

I get the Results/Combined_result_of_fm_and_tests.csv using the following command.
```shell
bash find_test_case_line.sh focal_method_statistics/Results

python3 curate_change_in_fm.py Results/Combined_result_of_fm_and_tests.csv AF

The tests for which we don't get any assertion failure. This will output different types of errors including assertion_error if found.
python3 curate_change_in_fm.py Results/not_assertion_error_or_attribute_errors.csv AF

python3 gpt_experiment.py Results/Combined_result_of_fm_and_tests.csv # This is to get the changed fm

To combine fm line numbers and test case line number, run the following command.

bash find_test_case_line.sh focal_method_statistics/Results/

```  

# For Technique

## For test refinement,
```shell
python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF NA # without slice

python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF Dynamic # Dynamic trace

python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF Static # Static trace

python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF Tool-Static

python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF Tool-Dynamic

python3 test_refinement.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Refine_AF Tool-Static-And-Dynamic
```

## For test generation,
```shell
python3 test_generation.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv Refine_CC NA # without slice
python3 test_generation.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv Refine_CC Static # with static slice
python3 test_generation.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv Refine_CC Dynamic # with dynamic slice
python3 test_generation.py data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv Refine_CC Static_And_Dynamic # with dynamic slice
```

Assertion fail not found for the following,
Results/tests_AF_failed.csv (426)

To parse result, run the following command.
python3 extract_unsuccessful_AF_tests.py l


To parse the repair test result:

python3 parse_test_refinement_output.py Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF.csv Results/Claude3-5_690_tests_with_Changed_Focal_Meth_AF.csv

To get the repaired tests example and the diff:
python3 git_diff_show.py Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF_Updated.csv

To get the failure category:
python3 log_parse.py

python3 parse_test_refinement_output.py Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF_Updated.csv Results/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv Results/Combined_result_of_fm_and_tests.csv 
Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF_Updated.csv


## For collecting real_tests, we run the following command

python3 collect_real_tests.py

python3 test_refinement_real_data.py data/assertion_error_real_data.csv Refine_AF NA
