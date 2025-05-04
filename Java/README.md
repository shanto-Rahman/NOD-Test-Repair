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
