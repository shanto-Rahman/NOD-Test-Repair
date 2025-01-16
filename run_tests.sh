#!/usr/bin/env bash
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
coverage_Dir="$currentDir/coverages"
if [ ! -d "$coverage_Dir" ]; then
    mkdir ${coverage_Dir}
fi

inputProj=$currentDir"/projects"
if [ ! -d "projects" ]; then
    mkdir ${inputProj}
fi

logs="$currentDir/logs"
if [ ! -d "$currentDir/logs" ]; then
    mkdir "$currentDir/logs"
fi
Results="$currentDir/Results"
if [ ! -d "$Results" ] 
then
    mkdir "$Results"
fi

echo "proj_name,sha,test-name" >> "$Results/Test_Run_Result.csv"


while IFS= read -r line
    do
    test_failure=0
    test_pass=0
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    git_link=$(echo $line | cut -d',' -f6)
    sha=$(echo $line | cut -d',' -f7)
    test_name_with_classname=$(echo $line | cut -d',' -f1)
    test_name_only=$(echo $test_name_with_classname | rev | cut -d':' -f1 | rev)
    rootProj=$(echo "$git_link" | rev | cut -d/ -f 2| rev)
    subProj=$(echo "$git_link" | rev | cut -d/ -f 1 | rev)
    if [[ ! -d ${inputProj}/${subProj} ]]; then
        echo "not found ${inputProj}/${subProj}"
        continue
    #    echo git clone "$git_link" $inputProj/$subProj
    #    git clone "$git_link" $inputProj/$subProj
    fi
    cd "$inputProj/$subProj"
    echo "$inputProj/$subProj"
    git checkout ${sha}
    python3 $currentDir/modify_tox_to_get_cov.py
    #tox_ini_found=$(find . -name "tox.ini"| wc -l)
    #if [[ $tox_ini_found -gt 0 ]]; then
    #    echo "${git_link},$sha" >> "$Results/Tox_found.txt"
    #    cd $currentDir 
    #else
    #     echo "${git_link},$sha" >> "$Results/Tox_not_found.txt"
    #     cd $currentDir
    #     rm -rf ${inputProj}/${subProj} 
    #fi
    for i in {1..800}; do  

        #echo $(pwd)
        #echo "pytest $test_name_with_classname"
        #pytest ${test_name_with_classname}  > "$logs/${test_name_only}_$i.txt"
        #echo "tox -e py36 -- ${test_name_with_classname}"
        tox -e py36 -- ${test_name_with_classname}  > "$logs/${test_name_only}_$i.txt"
        failure_count=$(grep -c '1 failed' "$logs/${test_name_only}_$i.txt")
        echo "Failure_count=$failure_count"
        if [[ $failure_count -gt 0 ]]; then
            test_failure=1
            echo "${git_link},${sha},${test_name_with_classname},test_failure,$i" >> "$Results/Test_Run_Result_tox_Compiled.csv"
            echo "I get the test failure"
            mv coverage.xml "$coverage_Dir/${test_name_only}_$i.xml"
        else
            test_pass=1
            echo "${git_link},${sha},${test_name_with_classname},test_pass,$i" >> "$Results/Test_Run_Result_tox_Compiled.csv"
            mv coverage.xml "$coverage_Dir/${test_name_only}_$i.xml"
        fi
        if [[ $test_pass -eq 1 && $test_failure -eq 1 ]]; then
            echo "${git_link},${sha},${test_name_with_classname},both_test_fail_and_test_pass,above" >> "$Results/Test_Run_Result_tox_Compiled.csv"
            break
        fi
    done 
    git checkout "tox.ini" 
    cd $currentDir
    exit
done < $1 
