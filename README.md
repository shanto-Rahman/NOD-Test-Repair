```shell
pip install gitpython
pip install toml
```



```shell
python3 run_tests_in_venv.py data/proj_name_with_test_with_correct_virtualenv_create_python38.csv
python3 data_preparation.py results/Combined_Result.csv 
```
This outputs "data/extracted_tests.csv".

For getting the flaky-test category, run the following command:

```
python3 llama3_8b_categorization.py data/extracted_tests.csv  "llama" "category_prediction" "NA"
```

Run the script `run_tests_in_venv_talank.py` to run the tests while generating traces, covered method lists, and method bodies.
Line traces will be in the dir `line_traces`
function traces will be in the dir `function_traces`
method lists will be in the dir `method_lists` it will be a csv file with the columns `filename,method,level`. So, you can find the methodname for specific levels here. This file will be used eventually to get method bodies. You can add additional filter in the script `run_tests_in_venv_talank.py` in line 987 if you want to keep filter by levels