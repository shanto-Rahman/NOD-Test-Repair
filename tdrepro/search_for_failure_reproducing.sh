#!/bin/bash
#bash search_for_failure_reproducing.sh ../data/all_142_tests.csv
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    #echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi

while read line
    do
        if [[ ${line} =~ ^\# ]]; then
            echo "Line starts with Hash $line"
            continue
        fi
        id=$(echo $line | cut -d',' -f1)
        slug_org=$(echo $line | cut -d',' -f2)
        slug=${slug_org//\//_}
        sha=$(echo $line | cut -d',' -f3)
        module_org=$(echo $line | cut -d',' -f4)

        module_with_dot=${module_org//\//.}
        module_with_underscore=${module_org//\//_}
        #testName_with_dot=$(echo $line | cut -d',' -f5)
        testName=$(echo $line | cut -d',' -f5) #"${testName_with_dot%.*}#${testName_with_dot##*.}"
        testName_with_dot="${testName//#/.}"

        filename="${slug}_${module_with_underscore}_${testName}"
        #if [[ $module_org == "." ]]; then
        #echo "module name is DOT ***"
        proj_name_only=$(echo $slug_org | cut -d'/' -f2)
	    #executed_methods/classified/org.apache.hadoop.hbase.stargate.client.TestRemoteAdmin.testDeleteTable-ResultMethods-library-methods.txt
	    library_meth_list=$(find "conc_executed_methods/classified" -name ${testName_with_dot}-ResultMethods-library-methods.txt) #Conc method list
	    proj_meth_list=$(find "conc_executed_methods/classified" -name ${testName_with_dot}-ResultMethods-project-methods.txt) #Conc method list
        log_search_csv="../Results/merged_failures.csv"
        echo "python3 find_failure_message_and_save.py "$id" "$slug_org" "$sha" "$module_org" "$testName" "$log_search_csv" "$module_with_dot" "$proj_name_only""
        python3 find_failure_message_and_save.py "$id" "$slug_org" "$sha" "$module_org" "$testName" "$log_search_csv" "$module_with_dot" "$proj_name_only" # It outputs $id_$module_with_dot_$testName_stacktrace.txt
        if [[ $module_org == "." ]]; then
            fail_log_csv_name="logs/${id}_${proj_name_only}_${testName}_stacktrace.csv"
        else
            fail_log_csv_name="logs/${id}_${module_with_dot}_${testName}_stacktrace.csv"
        fi
        echo "new csv = $fail_log_csv_name"

        echo "python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot ${library_meth_list} ${proj_meth_list}"
        #python3 generating_reproducing_script.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "embeddingOnly" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        #python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gemini" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot ${library_meth_list} ${proj_meth_list} #> ${id}_log.txt
        echo "I am here"
        #python3 barebone_llm.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        exit

    done < $1
