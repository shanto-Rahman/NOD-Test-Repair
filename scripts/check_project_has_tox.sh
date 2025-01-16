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
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    git_link=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    rootProj=$(echo "$git_link" | rev | cut -d/ -f 2| rev)
    subProj=$(echo "$git_link" | rev | cut -d/ -f 1 | rev)
    if [[ ! -d ${inputProj}/${subProj} ]]; then
        echo "not found ${inputProj}/${subProj}"
        #continue
        echo git clone "$git_link" $inputProj/$subProj
        git clone "$git_link" $inputProj/$subProj
        if [ $? -ne 0 ]; then
            echo "$git_link" >> "$Results/not_found_proj.csv"
            continue
        else
            echo "Git clone succeeded"
        fi
    fi
    cd "$inputProj/$subProj"
    echo "$inputProj/$subProj"
    git checkout ${sha}
    echo $(pwd)
    tox_ini_found=$(find . -name "tox.ini"| wc -l)
    if [[ $tox_ini_found -gt 0 ]]; then
        echo "TOX found"
        echo "${git_link},$sha" >> "$Results/Tox_found_idoft_dataset.csv"
        cd $currentDir 
    else

         echo "TOX notfound"
         echo "${git_link},$sha" >> "$Results/Tox_not_found_idoft_dataset.csv"
         cd $currentDir
         rm -rf ${inputProj}/${subProj} 
    fi
    #exit
done < $1 
