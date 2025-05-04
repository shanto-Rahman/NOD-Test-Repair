#!/bin/bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi
while read line
    do
        if [[ ${line} =~ ^\# ]]; then
            echo "Line starts with Hash $line"
            continue
        fi
        slug_org=$(echo $line | cut -d',' -f1)
        slug=${slug_org//\//_}
        sha=$(echo $line | cut -d',' -f2)
        module_org=$(echo $line | cut -d',' -f3)

        module=${module_org//\//_}
        testName_with_dot=$(echo $line | cut -d',' -f4)
        testName="${testName_with_dot%.*}#${testName_with_dot##*.}"

        filename="${slug}_${module}_${testName}"
        if [[ $module_org == "." ]]; then
            fail_log_csv_name=$(find logs -name "${slug}-${testName}-FlakeDelay-Run-1-*.txt") #Java-WebSocket-org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario8-FlakeDelay-Run-1-3200.txt
        else
            fail_log_csv_name=$(find logs -name "${module}-${testName}-FlakeDelay-Run-1-*.txt") #Java-WebSocket-org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario8-FlakeDelay-Run-1-3200.txt
        fi

       #chunk=$( sed -n '/Running org\.apache\.uniffle\.common\.rpc\.GrpcServerTest/,/Tests run: 1/p' $fail_log_csv_name)
       #echo $chunk
       # capture
       #chunk=$( sed -n '/Running org\.apache\.uniffle\.common\.rpc\.GrpcServerTest/,/Tests run: 1/p' "$fail_log_csv_name" )

       ## print with newlines intact:
       #printf '%s\n' "$chunk"
       ## or simply:
       #echo "$chunk"

       #exit


        python3 generating_reproducing_script.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot 
        #echo "python3 generating_reproducing_script.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "logs/tmp_failure.csv" ${slug_org} $sha ${module_org} $testName_with_dot" 
        exit

        #python3 generating_reproducing_script.py traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_executed_method_bodies.csv "tmp"  "traces" "gpt" traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest\#testGrpcExecutorPool_test_code.csv "logs/tmp_failure.csv" ${slug_org} $sha ${module_org} $testName_with_dot
    done < $1
