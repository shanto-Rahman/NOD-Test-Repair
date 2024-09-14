#!/bin/bash
### INPUT-TooTallNate/Java-WebSocket,fa3909c391195178ccf5a92d4ac342a30ae247c8,.,org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario0,39,org/java_websocket/client/WebSocketClient/run(WebSocketClient/java:420),3200
if [[ $1 == "" || $2 == ""  ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Results/output.csv)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
outputFile="$currentDir/$2"

if [ ! -d "${inputProj}" ];then
    mkdir ${inputProj}
fi

if [ ! -d "$currentDir/Results-Boundary" ]; then
    mkdir "$currentDir/Results-Boundary"
fi

#echo "Slug,SHA,Module,Test-Name,Lower-Bound~Upper-Bound[Delay],Anywhere-of-method(1)/portion-of-method(0),RegionId,reaches_to_end(If reaches end then TRUE, otherwise FALSE)" >> "$outputFile"

inject_delay_beginning() {
    local file_name="$1"
    local delay=$3
    while read rangeLineAll
    do
        methodNameToInjectDelay=$(echo $rangeLineAll | cut -d'#' -f4) # 
        #echo "methodNameToInjectDelay=  $methodNameToInjectDelay"
        rangeLine=$(echo $rangeLineAll | cut -d'#' -f1-3)
        echo $rangeLine
        #For injecting delay at the beginning of a method visitCode 
        lower_line=$(echo $rangeLine | cut -d'-' -f1)
        class_name=$(echo ${lower_line} | cut -d'#' -f1)
        lower_line_num=$(echo ${lower_line} | cut -d'#' -f2)
        echo "${class_name}#$lower_line_num"  > "$currentDir/Locations/Root-${projName}-$lower_line_num.txt"
        mvn test -pl $module -Dlocations="$currentDir/Locations/Root-${projName}-$lower_line_num.txt" -DmethodNameForDelayAtBeginning="$methodNameToInjectDelay" -Dtest=$testName -Ddelay=${delay} > "$currentDir/logs/Root-Beginning-log-${projName}-$delay.txt"
        local bug_count=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/Root-Beginning-log-${projName}-$delay.txt")
        if [ ${bug_count} -gt 0 ]; then 
            echo "EROOR / Failure Found at the beginning***********************************"
            beginning_fail="true"
            begin_line_name=$(cat "$currentDir/Locations/Root-${projName}-${lower_line_num}.txt")  #"$currentDir/Locations/Root-${projName}-$i.txt"
        else
            echo "*** NO EROOR / Failure Found at the beginning"
            #rm "$currentDir/logs/Root-Beginning-log-${projName}-$delay.txt"
        fi
    done < ${file_name}
}
reaches_to_end_with_fail=0
declare -A myCluster
sequential_debug() {
#INPUT-org/apache/http/impl/nio/reactor/SessionInputBufferImpl#154-org/apache/http/impl/nio/reactor/SessionInputBufferImpl#233#readLine
    allFailureLines=()
    local file_name="$1"
    local delay=$3
    cluster=1
    while read rangeLineAll
    do
        seq_error_found=0
        rangeLine=$(echo $rangeLineAll | cut -d'#' -f1-3)
        #echo $rangeLine
        lower_line=$(echo $rangeLine | cut -d'-' -f1)
        class_name=$(echo ${lower_line} | cut -d'#' -f1)
        lower_line_num=$(($(echo ${lower_line} | cut -d'#' -f2))) #Removing Adding 1 because inject_delay_beginning() 
        upper_line=$(echo $rangeLine | cut -d'-' -f2)
        upper_line_num=$(echo ${upper_line} | cut -d'#' -f2)
        upper_boundary=$upper_line_num 
        echo "lower_line_num=${lower_line_num}; and upper_line_num=${upper_line_num};"
        for (( j=${lower_line_num}; j<=${upper_line_num}; j=$((j+1)) )); do
            echo "${class_name}#$j"  > "$currentDir/Locations/Root-${projName}-$j.txt"

            mvn test -pl $module -Dlocations="$currentDir/Locations/Root-${projName}-$j.txt" -Dtest=$testName -Ddelay=${delay} > "$currentDir/logs/Root-log-${projName}-$j-$delay.txt"
            delay_inject_in_true_line=$(grep -r "HI-DELAYING=" "$currentDir/logs/Root-log-${projName}-$j-$delay.txt" | wc -l)
            if [[ $delay_inject_in_true_line -eq 0 ]]; then 
                continue 
            fi
            echo "***I am sequential jjj=$j"
            local bug_count=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/Root-log-${projName}-$j-$delay.txt")
            if [ ${bug_count} -gt 0 ]; then 
                echo "Sequential EROOR / Failure Found at Line $j"
                seq_error_found=$cluster
                line_name=$(cat "$currentDir/Locations/Root-${projName}-$j.txt")  #"$currentDir/Locations/Root-${projName}-$i.txt"
                allFailureLines+=($(echo $line_name | cut -d':' -f1))
                reaches_to_end_with_fail=$j
            else
                if [[ ${#allFailureLines[@]} -gt 0 ]]; then
                    if [[ $seq_error_found -gt 0 ]]; then
                        echo "STORING into myCluster for Line $j and map, ${allFailureLines[@]}"
                        myCluster["$cluster"]=${allFailureLines[@]}
                        allFailureLines=()
                        cluster=$((cluster + 1))
                    fi
                fi
            fi
            rm "$currentDir/logs/Root-log-${projName}-$j-$delay.txt"
        done
        if [[ ! -v myCluster["$cluster"] ]] ; then # This one is for end boundary fails. Because at that the else block will not execute
          if [[ ${#allFailureLines[@]} -gt 0 ]]; then
            echo "End fails..."
            myCluster["$cluster"]=${allFailureLines[@]}
          fi
        fi

        if [[ ${#myCluster[@]} -eq 0 ]]; then # This indicates that injecting delay anywhere of the method makes the test fail
            echo "The map is empty"
            #myCluster["$cluster"]=${allFailureLines[@]}
        fi
    done < ${file_name}
}

while IFS= read -r line
    do

    if [[ ${line} =~ ^\# ]]; then
        #echo "Line starts with Hash $line"
        continue
    fi

    if [ ! -d "$currentDir/logs" ]; then
        mkdir "$currentDir/logs"
    fi
    
    if [ ! -d "$currentDir/Locations" ]; then
        mkdir "$currentDir/Locations"
    fi

    reaches_to_end="FALSE"
    flag_full_method=0
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
  
    if [[ $module != "." ]]; then
       projName=$(sed 's;/;.;g' <<< $module-$testName)
    else
        projName=$(sed 's;/;.;g' <<< $subProj-$testName)
    fi
    if [[ ! -d ${inputProj}/${rootProj} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
        cd $inputProj/$slug
        git checkout ${sha} 

        if [[ "$slug" == "doanduyhai/Achilles" ]]; then
            sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
        fi

        if [[ $slug == "Accenture/mercury" ]]; then
            mvn install -pl $module -am -Dmaven.test.skip=true
        else
            mvn install -pl $module -am -fn -DskipTests
        fi
        surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)
        bash $currentDir"/agent-pom-modify/"modify-project.sh $inputProj/$slug $surefire_exists "boundaryPoint"
        
    else # Expecting that if the project already exists, then our agent snapshot is also added in the pom.xml. Hence, I am not modifyng pom.xml anymore
        cd $inputProj/$slug
    fi

    comma_count=$(echo $line | tr -cd , | wc -c)
    comma_count=$((comma_count + 1))
    regionId=0
    start_time=$(date +%s.%N)
    for (( i=6; i<=${comma_count}; i=$((i+2)) )); do
        allFailureLines=()
        regionId=$((regionId + 1))
        #loc_index=$i
        locations=$(echo $line | cut -d',' -f${i})
        delay=$(echo $locations | cut -d "[" -f2 | cut -d "]" -f1 )
        beforeParentheses=$(echo $locations | cut -d'(' -f1)
        className=$(echo $beforeParentheses | rev | cut -d'/' -f2- | rev)
        methodName=$(echo $beforeParentheses | rev | cut -d'/' -f1 | rev)
        #echo $methodName
        combined_location="$className#$methodName"
        echo "*****combined location= $combined_location"
   
        beginning_fail="false"
        end_fail="false"

        if [[ -f "$currentDir/Locations/${projName}-Root" ]]; then
            rm "$currentDir/Locations/${projName}-Root"
        fi
        echo "${combined_location}:$testName" >> "$currentDir/Locations/${projName}-Root"
        #The following command is to call agent/ to generate all the statements in a method
        mvn test -pl $module -DrootMethod="$currentDir/Locations/${projName}-Root" -DmethodOnly="$methodName" -Dtest=$testName -Ddelay=$delay >  "$currentDir/logs/RootMethodAllStatement-log-$projName" #generated outputfile=all-location-in-a-method
        savedLocation=$(find -name "MethodStartAndEndLine.txt")
        if [[  -s $savedLocation ]]; then
            cp $savedLocation "$currentDir/Results-Boundary/"
            locationCount=$(wc -l < "$savedLocation")	
            echo "locationCount===>$locationCount"
            arr=($(seq 1 $locationCount))

            inject_delay_beginning "$currentDir/Results-Boundary/MethodStartAndEndLine.txt" 1 $delay 
            if [[ "${beginning_fail}" =~ "true" ]]; then # that means async wait
                echo "*************beginning fail true=$begin_line_name"
                allFailureLines+=$begin_line_name
            fi    
            sequential_debug "$currentDir/Results-Boundary/MethodStartAndEndLine.txt" 1 $delay #search for a region
            #flag_full_method=0
            #echo "I am setting 0"
            
            cd $inputProj
            echo "Work with myCluster======="
            
            totalKeys=${#myCluster[@]}
            echo "totalKeys=$totalKeys" 

            echo -n "${slug},${sha},${module},${testName}," >> "$outputFile"
            keys=("${!myCluster[@]}")
            sorted_keys=($(printf '%s\n' "${keys[@]}" | sort -n))
    
            if [[ $totalKeys -gt 0 ]]; then
                for key in "${sorted_keys[@]}"; do 
                    echo "Key: $key"
                    valuesArr=("${myCluster[$key]}")
                    echo "KEY and Value pair=$key, ${valuesArr[@]}" 
                    #echo "All failure lines==="
                    echo "${valuesArr[@]}"
                    first_item=$(echo ${valuesArr[@]} | cut -d' ' -f1)
                    end_item=$(echo ${valuesArr[@]} | rev | cut -d' ' -f1 | rev)
                    echo "first_item and end_item= $first_item and $end_item"
                    if [ $totalKeys -eq 1 ]; then # JUST to see if injecting delay anywhere in the code makes my test fail
                        bndary=$((upper_boundary - 1)) # 1 is reduced from locationCount because the end boundary might be losing bracket. 
                        if [[ $reaches_to_end_with_fail == "$bndary" ]]; then # This check is needed at the time of fixing, because if a test's fails if we add delay at the end boundary, then we will ignore thos;  #myCluster is onl updated from Sequential, So, if it is equal to 1, it may be only one line or the full-code
                            echo "reached to end, and beginning fails=${beginning_fail}"
                            reaches_to_end="TRUE"
                            if [[ "${beginning_fail}" =~ "true" ]]; then
                                flag_full_method=1 # IF by sequential_debug, it can reach to the end of line and if beginning is also true, that means injecting delay into an
                                echo -n "${first_item}~${end_item}[${delay}]"  >> "$outputFile"
                            else # This one will be running if only end makes test fail (e.g., Issue677Test)
                                echo -n "${first_item}~${end_item}[${delay}]"  >> "$outputFile"
                            fi
                        else
                            echo -n "$first_item~$end_item[${delay}]"  >> "$outputFile"
                        fi

                    else #If only beginning delay making test fail
                        if [ $end_item == "" ]; then
                            echo -n "${first_item}~${first_item}[${delay}];"  >> "$outputFile"
                        else # This one will be running if 
                            echo -n "${first_item}~${end_item}[${delay}];"  >> "$outputFile"
                        fi
                        flag_full_method=0
                    fi
                done 

            else
                if [[ "${beginning_fail}" =~ "true" ]]; then # only beginning fails
                    echo -n "$begin_line_name~$begin_line_name[${delay}]" >> "$outputFile"
                    flag_full_method=0
                    totalKeys=1
                else # Not Found boundary because this block will ony be executed if totalKeys equals to 0 and not beginning fails happen
                    echo -n "Not-Found-Boundary"  >> "$outputFile"
                    flag_full_method=-100
                fi
            fi

            if [[ ${flag_full_method} -gt -100 ]]; then
                echo -n ",${flag_full_method},$totalKeys,$reaches_to_end" >> $outputFile #
            fi

            #echo "All failure lines==="
            #echo "${allFailureLines[@]}"
            #if [ $flag_full_method -eq 1 ] ; then
            #    echo "${slug},${sha},${module},${testName},${allFailureLines[0]}~${allFailureLines[-1]}[${delay}],${flag_full_method},$regionId,$reaches_to_end" >> "$outputFile"
            #fi
            #elif [[ "${beginning_fail}" =~ "true" ]]; then
            #    echo "CHECKING==$begin_line_name"
        else
            echo "Start and End Line of the method not found, $line"
        #exit
        fi
        cd $currentDir
        echo "$(pwd) NOW GOING to remove rootProj========= $rootProj"
        #rm -rf "$inputProj/$rootProj"
    
        unset myCluster
    done

    end_time=$(date +%s.%N)
    take=$(echo "scale=2; ${end_time} - ${start_time}" | bc)
    echo ",$take" >> $outputFile
    rm -rf "$inputProj/$rootProj"
    #rm -rf "$currentDir/logs"
    #rm -rf "$currentDir/Locations"
    cd $currentDir
done < $1    
