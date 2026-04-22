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
        #echo "$proj_name_only; ${proj_name_only}-${testName}-FlakeDelay-Run-1-*.txt"
        #log_search_csv=""

        #if [[ $2 == "flakerake_new" ]]; then 
        #    log_search_csv="../Results/failure_log_new_tests.csv"
        #elif [[ $2 == "flakerake" ]]; then #will read failure message from, and save that into a txt file similar to the name of idoft unique_failures_10K_reruns_flakerake_775.csv
        #    log_search_csv="../Results/unique_failures_10K_reruns_flakerake_775.csv"
        #elif [[ $2 == "idoft" ]]; then #../Results/unique_failures_10K_reruns_181_unique_only.csv
        #    log_search_csv="../Results/unique_failures_10K_reruns_181_unique_only.csv"
        #fi
        log_search_csv="../Results/merged_failures.csv"
        echo "python3 find_failure_message_and_save.py "$id" "$slug_org" "$sha" "$module_org" "$testName" "$log_search_csv" "$module_with_dot" "$proj_name_only""
        python3 find_failure_message_and_save.py "$id" "$slug_org" "$sha" "$module_org" "$testName" "$log_search_csv" "$module_with_dot" "$proj_name_only" # It outputs $id_$module_with_dot_$testName_stacktrace.txt
        if [[ $module_org == "." ]]; then
            fail_log_csv_name="logs/${id}_${proj_name_only}_${testName}_stacktrace.csv"
        else
            fail_log_csv_name="logs/${id}_${module_with_dot}_${testName}_stacktrace.csv"
        fi
        #fi
        #else
        #    if [[ $2 == "idoft" ]]; then
        #        fail_log_csv_name=$(find logs -name "${module_with_dot}-${testName}-FlakeDelay-Run-1-*.txt") #Java-WebSocket-org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario8-FlakeDelay-Run-1-3200.txt
        #    else # $2 = flakerake
        #       python3 find_failure_message_and_save.py "$id" "$slug_org" "$sha" "$module_org" "$testName" "../Results/unique_failures_10K_reruns_flakerake_775.csv" "$module_with_dot" "$proj_name_only" # It outputs $id_$module_with_dot_$testName_stacktrace.txt
        #        fail_log_csv_name="logs/${id}_${module_with_dot}_${testName}_stacktrace.csv"
        #    fi
        #fi
        echo "new csv = $fail_log_csv_name"
        ##python3 generating_reproducing_script.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot 
        ##python3 generating_reproducing_script.py traces/${filename}_executed_with_call_depth.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot 
        #python3 generating_reproducing_script.py traces/${filename}_executed_with_call_depth.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot 
        #python3 generating_reproducing_script.py traces/${filename}_executed_with_static_call_depth.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot 
        echo "python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot" #"$2"
        #python3 generating_reproducing_script.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "embeddingOnly" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        #python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gemini" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        python3 generating_reproducing_config.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot #> ${id}_log.txt
        echo "I am here"
        #python3 barebone_llm.py traces/${filename}_executed_method_bodies.csv "tmp" "traces" "gpt" traces/${filename}_test_code.csv "$fail_log_csv_name" ${slug_org} $sha ${module_org} $testName_with_dot $2
        exit

    done < $1
