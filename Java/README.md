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
