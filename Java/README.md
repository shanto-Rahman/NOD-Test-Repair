Run command:

```shell
bash runAll.sh ../data/talank_with_test_id_idoft_corrected.csv Result/
```

```shell
export OPENAI_API_KEY="YOUR_KEY_HERE"
bash search_for_failure_reproducing.sh ../data/all_82_tests.csv "idoft"
```

To collect the agreement between models, we run the following command.

```shell
 bash run_to_get_top10_methods.sh ../data/all_82_tests.csv Result/ > log
```

For collecting location after adding sequential delay, run the following command.
```shell
python3 wrapper_for_sequential_delay_injection_to_check_each_embedding_model.py 
```

For check the nondeterminism in embeddings, we do the following experiment.
```shell
python3 matching_embeddings_to_check_non_determinism.py "llama"
```

To analyze the results, for example how many on average gpt calls happened, how many test runs on average needed
```shell
python3 analyze_result.py results/tdrepro.csv 
```

To match the failure log, run the following command
```shell
 bash find_failure_match.sh ../data/all_82_tests.csv "idoft"
 ```
To run barebone gpt model to show it's not data-leakaged, run the following command.
```shell
bash s.sh ../data/all_82_tests.csv Result/
```
clone the project

Run the test, collect the failure. So collecting the failure, we might need to run flakesync.

modify the pom.xml to add jacoco and surefire plugin (mvn test -pl common -Dtest=org.apache.uniffle.common.rpc.GrpcServerTest#testGrpcExecutorPool)
java -jar jacococli.jar report common/target/jacoco.exec \
  --classfiles common/target/classes \
    --sourcefiles common/src/main/java \
      --xml common/target/coverage.xml

Collect the code-coverage and methods using jacoco and tree-sitter (Run collect_executed_meths.py, and collect_method_body.py)


tree-sitter-languages==1.10.2
tree-sitter==0.21.3



bash runAll.sh ../data/tmp.csv Result/
bash search_for_failure_reproducing.sh ../data/tmp.csv X

python3 generating_reproducing_script.py traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_method_bodies.csv "tmp"  "traces" "qwen" traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_test_code.csv "logs/tmp_failure.csv"

#python3 generating_reproducing_script.py traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_methods_with_call_labels.csv "tmp"  "traces" "deep_seek_coder" traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_test_code.csv "logs/tmp_failure.csv"

python3 generating_reproducing_script.py traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_method_bodies.csv "tmp"  "traces" "qwen" traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_test_code.csv "logs/tmp_failure.csv"

python3 generating_reproducing_script.py traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_method_bodies.csv "tmp"  "traces" "gpt" traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_test_code.csv "logs/tmp_failure.csv" apache/incubator-uniffle a2b9c17b common org.apache.uniffle.common.rpc.GrpcServerTest.testGrpcExecutorPool

pip install torch

# For Requirements

```python -m pip list --not-required --format=freeze > requirements.txt```
