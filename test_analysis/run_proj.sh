#!/usr/bin/env bash
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the data file (eg. data_with_sha.csv)"
    exit
fi

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
while read line
do 
   
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with the hash $line"
        continue
    fi
    proj=$(echo $line |cut -d',' -f1)
    echo $proj
    git_link=$(echo $line |cut -d',' -f2)
    sha=$(echo $line |cut -d',' -f3)
   
    git clone $git_link $inputProj/$proj
    cd $inputProj/$proj
    git checkout $sha
    tox -e py39 | tee $currentDir/logs/log_$proj
    count_pass=$(grep "passed" $currentDir/logs/log_$proj | wc -l)
    echo $count_pass
    if [[ ${count_pass} -gt 0 ]]; then
        echo $proj,$git_link,$count_pass >> $currentDir/Results/Passed_Proj.csv
    fi    
    cd $currentDir
    #exit
    #rm -rf $inputProj/$proj
done < $1


