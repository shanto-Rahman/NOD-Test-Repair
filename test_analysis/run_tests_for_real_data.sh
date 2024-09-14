#!/usr/bin/env bash
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the data file (eg. Results/850_tests.csv or 1079 tests.csv)" 
    exit
fi

python3 making_csv_with_intended_col.py $1

currentDir=$(pwd)

inputProj=$currentDir"/projects"
outputDir="out"
if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

if [ ! -d "logs" ] 
then
    mkdir "logs"
fi

if [ ! -d "Results" ] 
then
    mkdir "Results"
fi
count=0

outputFile="$currentDir/Results/Real_tests_with_Focal_Methods.csv"
echo "#proj_name,git_link,python_file_path,test_method_name,claude_result,Static_Analysis_Result,fm_source_file_by_static_analysis,Findings,All_Api_List,fm_source_file_by_dynamic_analysis,covered_methods,coverage_percentage,test_pass/fail" >> "$outputFile"

while read line
do 
   
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with the hash $line"
        continue
    fi
    proj=$(echo $line |cut -d',' -f1)
    echo $proj
    git_link=$(echo $line |cut -d',' -f2)
    test_full_path=$(echo $line |cut -d',' -f4) #| rev| cut -d'/' -f1-2 | rev) 
    #path_after_project="${test_full_path#*$proj}"
    test_class_name=$(echo "$test_full_path" | sed -n "s|.*$proj/\(.*\)|\1|p")
    
    test_method=$(echo $line |cut -d',' -f5)
    focal_method=$(echo $line |cut -d',' -f7)
    new_commit=$(echo $line |cut -d',' -f8)
    #jaccard_focal_method=$(echo $line |cut -d',' -f6 | cut -d'#' -f1)
    #jaccard_focal_method_argument=$(echo $line |cut -d',' -f6 | cut -d'#' -f2)

    git clone $git_link $inputProj/$proj

    cd $inputProj/$proj
    git checkout $new_commit
    #python3 $currentDir/modify_tox_to_get_cov.py
    if [[ $proj == "graphene-django" ]]; then
        tox -e py39 -- "graphene-django/"${test_class_name}::${test_method}

    elif [[ $proj == "h11" ]]; then 

        tox -e py39 -- "h11/"${test_class_name}::${test_method} > "$currentDir/logs/log_${proj}_${test_method}"

    elif [[ $proj == "cssselect" ]]; then
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir/logs/log_${proj}_${test_method}" 2>&1

    elif [[ $proj == "eemeter" ]]; then
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir/logs/log_${proj}_${test_method}" 2>&1
    else
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir/logs/log_${proj}_${test_method}" 2>&1
    fi
    #Now I will collect all the python files available in the coverage file 
    #echo "jaccard focal meth=,${jaccard_focal_method}"
    #output=$(python3 $currentDir/collect_coverage_info.py ${jaccard_focal_method})
    #echo "output from bash= $output"
    ##python3 parse_code_coverage.py     

    ## Split the output into filename and covered methods
    #file_name=$(echo $output | cut -d '#' -f 1)
    #covered_percentage=$(echo $output | rev | cut -d '#' -f 1 | rev)
    #covered_methods=$(echo $output | cut -d '#' -f 2- | cut -d'#' -f1)
    #
    ## Use the output in your Bash script
    #echo "Filename: $file_name"
    #echo "Covered Methods: $covered_methods"
    #echo "covered_percentage: $covered_percentage"

    #tox -e py312  | tee $currentDir/logs/log_$proj
    count_pass=$(grep "passed" "$currentDir/logs/log_${proj}_${test_method}" | wc -l)
    #echo $count_pass
    if [[ ${count_pass} -gt 0 ]]; then
        #echo $proj,$git_link,$test_class_name,$test_method,$count_pass >> "$currentDir/Results/Passed_Proj_test.csv" 
        echo "$line,test_pass" >> "$outputFile" 
    else
        count_skipped=$(grep "skipped" "$currentDir/logs/log_${proj}_${test_method}" | wc -l)
        if [[ ${count_skipped} -gt 0 ]]; then
            echo "$line,test_skip" >> "$outputFile"
        else
            echo "$line,test_fail" >> "$outputFile"
        fi
    fi    
    #exit
    #echo $(pwd)
    #rm "coverage.xml" 
    #rm "testreport/report.json"
    #git checkout "tox.ini"
    cd $currentDir
    #exit
    #rm -rf $inputProj/$proj
done < "Results/Part_Real_Tests.csv"


