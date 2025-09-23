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
        #echo " python3 match_top10_methods.py metadata/embedings/${testName_with_dot}_qwen_embeddings.csv metadata/embedings/${testName_with_dot}_llama_embeddings.csv metadata/embedings/${testName_with_dot}_bigbird_embeddings.csv metadata/embedings/${testName_with_dot}_codebert_embeddings.csv" -o "${testName_with_dot}_out.csv"
        python3 match_top10_methods.py "metadata/embedings/${testName_with_dot}_qwen_embeddings.csv" "metadata/embedings/${testName_with_dot}_llama_embeddings.csv" "metadata/embedings/${testName_with_dot}_bigbird_embeddings.csv" "metadata/embedings/${testName_with_dot}_codebert_embeddings.csv" -o "${testName_with_dot}_agreement.csv"
    exit
    done < $1
