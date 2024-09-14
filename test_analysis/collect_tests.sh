if [[ $1 == "" ]]; then
    echo "Give csv (data/data.csv)"
fi

proj_dir="Projects"
if [[ ! -d $proj_name ]]; then
    mkdir $proj_dir
fi

currentDir=$(pwd)

inputProj=$currentDir"/projects"
outputDir="out"
if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

logDir="${currentDir}/logs"
if [ ! -d $logDir ] 
then
    mkdir "$logDir"
fi

result="${currentDir}/Results"
if [ ! -d $result ] 
then
    mkdir "$result"
fi

count_proj=0
while read line
do
    count_proj=$((count_proj +1))
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi

    proj=$(echo $line |cut -d',' -f1)
    echo $proj
    git_link=$(echo $line |cut -d',' -f2)
    git clone $git_link $inputProj/$proj
    python3 inject_into_tox_ini.py $inputProj/$proj #Modify tox.ini to gather the tests
    if [[ $proj == "graphene-django" ]]; then
        cd "$inputProj/${proj}/graphene_django/"

    elif [[ $proj == "h11" ]]; then
        cd "$inputProj/${proj}/h11/"

    elif [[ $proj == "json-rpc" ]]; then
        cd "$inputProj/${proj}/jsonrpc/"

    elif [[ $proj == "parsimonious" ]]; then
        cd "$inputProj/${proj}/parsimonious/"

    elif [[ $proj == "pytest-pylint" ]]; then
        cd "$inputProj/${proj}/pytest_pylint/"

    elif [[ $proj == "queuelib" ]]; then
        cd "$inputProj/${proj}/queuelib/"

    elif [[ $proj == "supervisor" ]]; then
        cd "$inputProj/${proj}/supervisor/"
    else
        cd $inputProj/$proj
    fi 
    ##cp ${currentDir}/list_pytest_tests.py .
    ##exit
    cp ${currentDir}/gather_tests.py .
    #tox -e gather_tests #to run the test
    ##To get the complexity of each method 
    python3 $currentDir/analyze_tests.py  "$result/${proj}"  "$git_link"
    cd $currentDir
    #exit
    #rm -rf $inputProj/$proj
    #if [[ $count_proj == 2 ]]; then
    #    exit
    #fi
done < $1
