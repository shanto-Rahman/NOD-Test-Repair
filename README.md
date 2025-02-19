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
