if [[ $1 == "" || $2 == "" ]]; then 
    echo "($1 - give the module)"
    echo "($2 - give the testName)"
    echo "$3 - delay amount"
    echo "$4 - currentDir"
    echo "$5 -Code-to-introduce-variable"
    exit
fi

module=$1
testName=$2
delay=$3
currentDir=$4
upper_boundary=$5
JMVNOPTIONS="$6"
#echo $upper_boundary
#echo "upper_boundary=$upper_boundary"
echo "mvn test $JMVNOPTIONS -pl $module -Dtest="$testName" -DstackTraceCollect="flag" -Ddelay=$delay -DCodeToIntroduceVariable=${upper_boundary}"
mvn test $JMVNOPTIONS -pl $module -Dtest="$testName" -DstackTraceCollect="flag" -Ddelay=$delay -DCodeToIntroduceVariable=${upper_boundary} 
if [[ -f  "$currentDir/YIELDING_Point_StackTrace/$testName" ]]; then
    rm  "$currentDir/YIELDING_Point_StackTrace/$testName"
fi
xml_file=$(find "$module/target/surefire-reports/" -name "TEST-*.xml")
all_stacktrace_arr=($(grep -r ".java:" "$xml_file"))
echo ${all_stacktrace_arr[@]}
for item in ${all_stacktrace_arr[@]}; do
echo "item=$item"
    if [[ $item == "at" ]]; then
        continue
    elif [[ $item == "&amp" ]]; then
        continue
    elif [[ $item == "0)even#0" ]]; then
        continue
    elif [[ $item == "Method)" ]]; then
        continue
    fi
    class_name=$(echo $item | cut -d'(' -f1 | rev | cut -d'.' -f2- | rev)
    line_num=$(echo $item | cut -d':' -f2 | cut -d')' -f1)
    flag=0
    # Need to search if the clas_name exists in the blacklist or not
    while read line 
    do
        if [[ "$class_name" == "$line"* ]]; then
            echo "ENTERED**"
            flag=1
            break
        fi
    done < "$currentDir/../barrierSearch-core/src/main/resources/blacklist.txt"
    if [[ $flag == 0 ]]; then
        if [[ $line_num =~ ^[0-9]+$ ]]; then
            echo "$class_name#$line_num" >> "$currentDir/YIELDING_Point_StackTrace/$testName"
        fi
    fi
done

