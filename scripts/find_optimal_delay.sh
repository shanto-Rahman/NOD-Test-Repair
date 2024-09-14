currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
inputProj=$currentDir"/projects"

while read line
do
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    thread_id=$(echo $line | cut -d',' -f5)
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)

    tt_file=$(echo $testName | sed 's;\[;\\[;g')
    if [[ $module != "." ]]; then
       projName=$(sed 's;/;.;g' <<< $module-$tt_file)
    else
        projName=$(sed 's;/;.;g' <<< $subProj-$tt_file)
    fi

    comma_count=$(echo $line | tr -cd , | wc -c)
    comma_count=$((comma_count + 1))
    regionId=0
    flag=0
    echo -n "$slug,$sha,$module,$testName,$thread_id" >> $2
    for (( i=6; i<=${comma_count}; i=$((i+2)) )); do
        echo "within for loop"
        allFailureLines=()
        regionId=$((regionId + 1))
        locations=$(echo $line | cut -d',' -f${i})
        time_index=$((i+1))
        time=$(echo $line | cut -d',' -f${time_index})
        delay=$(echo $locations | cut -d "[" -f2 | cut -d "]" -f1)
        beforeParentheses=$(echo $locations | cut -d'(' -f1)
        beforeDelay=$(echo $locations | cut -d'[' -f1)
        lineNum=$(echo $locations | cut -d':' -f2 | cut -d')' -f1)
        className=$(echo $beforeParentheses | rev | cut -d'/' -f2- | rev)
        methodName=$(echo $beforeParentheses | rev | cut -d'/' -f1 | rev)
        combined_location="$className#$lineNum"
        if [[ -f "$currentDir/Locations/${projName}-Root" ]]; then
            rm "$currentDir/Locations/${projName}-Root"
        fi
        echo "${combined_location}:$testName" >> "$currentDir/Locations/${projName}-Root"
        cd $inputProj/$slug
        reduce_percentage=0.9
        while [ $delay -gt 100 ]; do
            updated_delay_in_float=$(echo "scale=1; $delay * $reduce_percentage" | bc)
            updated_delay=$(printf '%.0f' "$updated_delay_in_float")
            echo "$updated_delay from finding optimal delay"
            echo "$currentDir/Locations/${projName}-Root"
            mvn test -pl $module -Dtest=$testName  -Ddelay=$updated_delay  -Dlocations="$currentDir/Locations/${projName}-Root" >  "$currentDir/logs/checking_optimal_delay.txt"
            if [[ -f "StackTrace-$testName.txt" ]]; then
                rm "StackTrace-$testName.txt"
            fi
            bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/checking_optimal_delay.txt")
            if [[ $bugCount -eq 0 ]]; then
                flag=1
                echo -n ",$beforeDelay[$delay],$time" >> $2
                break
            else
                delay=$updated_delay
            fi
        done
        if [ $flag -eq 0 ]; then
            echo -n ",$beforeDelay[$delay],$time" >> $2
        fi
     done
     echo "" >> $2
done < $1
