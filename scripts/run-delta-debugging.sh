#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - full path of the Locations for a test"
    echo "arg3 - Result-Dir"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
inputProj=$currentDir"/projects-For-Delta"

if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

if [ ! -d "$currentDir/logs" ] 
then
    mkdir "$currentDir/logs"
fi
Results="$3"
if [ ! -d "$currentDir/$Results" ] 
then
    mkdir "$currentDir/$Results"
fi


if [ ! -d "$currentDir/Delta-Debug/Delta-logs" ] 
then
    mkdir -p "$currentDir/Delta-Debug/Delta-logs"
fi

min_number() {
    printf "%s\n" "$@" | sort -g | head -n1
}
count=0
MAX=25601
final_delay=0
final_file_name=""
delta_debug()
{
    local array_name="$1[@]"
    local n=$2
    local elements=("${!array_name}")
    local delay=$3
    local flag=$4   # This is flag to indicate whether we are trying to tweak the delay time; 0 means we are not plaing with delay time, 1 means we are
    count=$((count+1))
    echo "STARTING ELEMENTS: ${elements[*]}"
    len=${#elements[@]}
    echo "*********** len = $len"
    if [ $len -lt $n ]
    then
        echo -n  ",${elements[*]}" >> "$currentDir/$resultFileName"
        end_time=$(date +%s.%N)
        take=$(echo "scale=2; ${end_time} - ${start}" | bc)
        take=$(echo $take | awk '{printf("%.2f\n", $1) }')
        echo -n "[delay=$delay:Time=${take}]" >> "$currentDir/$resultFileName"
        return $elements
    fi
    chunkSize=$len/$n;
    chunks=()
    for (( i=1; i<$len; i=$((i+chunkSize)))) 
        do
         chunkIndices=()
         otherChunkIndices=()
         endpoint="$(min_number  $len $((i + chunkSize -1)))"
         echo "$i  $endpoint"
         chunkIndices=($(seq $i $((endpoint))))
         
         otherChunkIndices_part_1=($(seq 1 $((i-1)) ))
         otherChunkIndices_part_2=($(seq $((endpoint+1)) $len))
         otherChunkIndices+=("${otherChunkIndices_part_1[@]}" "${otherChunkIndices_part_2[@]}" )
        
        ## For otherChunk
        otherChunk=()
        for j in "${otherChunkIndices[@]}"
        do
            if [ ! -z $j ];
            then
                #echo ${j}
                #echo ${elements[$((j-1))]}
                otherChunk+=(${elements[$((j-1))]})
                #echo ${otherChunk[*]}
            fi
        done
        for elem in "${otherChunk[@]}"
        do
            if [ ! -z $elem ];
            then
                sed -n "$elem"p $resultLocationsFile >> "$currentDir/Delta-Debug/Delta-Debug-${projName}/otherChunk-$count-$i.txt"
            fi
        done

        timeout 2h mvn test -pl $module -Dlocations=$currentDir/"Delta-Debug/Delta-Debug-${projName}/otherChunk-$count-$i.txt" -Dconcurrentmethods=${concurrentMethodListFile}  -Dwhitelist=${whitelistFile} -Dtest=$testName -Ddelay=${delay} > "$currentDir/Delta-Debug/Delta-logs/$projName-otherChunk-$count-$i.txt"
        local bugCountOtherChunk=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/Delta-Debug/Delta-logs/$projName-otherChunk-$count-$i.txt")
        if [ $bugCountOtherChunk -gt 0 ]; then
           delta_debug otherChunk 2 ${delay} 0 # send it as array
           final_delay=$delay
           final_file_name="otherChunk-$count-$i.txt"
           return
        fi

        ## For Chunk
        chunk=()
        for j in "${chunkIndices[@]}"
        do
            if [ ! -z $j ];
            then
                chunk+=(${elements[$((j-1))]})
            fi
        done
        for elem in "${chunk[@]}"
        do
            if [ ! -z $elem ];
            then
                sed -n "$elem"p $resultLocationsFile >> "$currentDir/Delta-Debug/Delta-Debug-${projName}/chunk-$count-$i.txt"
            fi
        done

        timeout 2h mvn test -pl $module -Dlocations=$currentDir/"Delta-Debug/Delta-Debug-${projName}/chunk-$count-$i.txt" -Dconcurrentmethods=${concurrentMethodListFile}  -Dwhitelist=${whitelistFile} -Dtest=$testName -Ddelay=${delay} > "$currentDir/Delta-Debug/Delta-logs/$projName-chunk-$count-$i.txt"

        local bugCountChunk=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/Delta-Debug/Delta-logs/$projName-chunk-$count-$i.txt")
        if [ $bugCountChunk -gt 0 ]; then
           delta_debug chunk 2 ${delay} 0 # send it as array
           final_delay=$delay
           final_file_name="chunk-$count-$i.txt"
           return
        fi
    done


    # Before going further breaking into parts, if delay is still less than the maximum allowed, we try to play with the delay tim
    if [[ ${delay} -lt ${MAX} ]]; then
        echo "until going to maxdelay $delay"
        echo -n  ",${elements[*]}" >> "$currentDir/$resultFileName"
        end_time=$(date +%s.%N)
        take=$(echo "scale=2; ${end_time} - ${start}" | bc)
        take=$(echo $take | awk '{printf("%.2f\n", $1) }')
        echo -n "[delay=$delay:Time=${take}]" >> "$currentDir/$resultFileName"
        start=$(date +%s.%N)
        delta_debug elements $n $((delay*2)) 1
        final_delay=$delay
        return
    fi

    if [[ ${flag} == 1 && ${delay} -eq ${MAX} ]]; then
        return
    fi

    if [ $len -lt $((n*2)) ]
    then
        delta_debug elements $len ${delay} 0
        return 
    else 
        delta_debug elements $((n*2)) ${delay} 0
        return
    fi

}

while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    rootProj=$(echo "$slug" |cut -d/ -f 1)
    subProj=$(echo "$slug" |cut -d/ -f 2)
    testName_for_file_name=$(echo $testName |sed 's;\[;\\[;') #adding slash if square bracket exits
    result_file_name_per_test=$(echo $testName_for_file_name |sed 's;\\;.;')
    resultFileName="${Results}/${result_file_name_per_test}.csv"

    if [ -f "$(find $currentDir/$2 -name "whitelist-*-${testName_for_file_name}.txt")" ]; then
        whitelistFile="$(find $currentDir/$2 -name "whitelist-*-${testName_for_file_name}.txt")"
        
        if [ -f "$(find $currentDir/$2 -name "ConcurrentMethodsWhiteList-*-${testName_for_file_name}.txt")" ]; then
            concurrentMethodListFile="$(find $currentDir/$2 -name "ConcurrentMethodsWhiteList-*-${testName_for_file_name}.txt")"

            if [ -f "$(find $currentDir/$2 -name "Locations-*-${testName_for_file_name}-FlakeDelay-Run-1-*")" ]; then
                
                if [[ ! -d ${inputProj}/${rootProj} ]]; then
                    git clone "https://github.com/$slug" $inputProj/$slug
                fi
                
                cd $inputProj/$slug
                git checkout ${sha}

                if [[ "$slug" == "doanduyhai/Achilles" ]]; then
                    sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
                else
                    echo "Strings are not equal."
                fi  

                echo -n "${slug}" >> "$currentDir/$resultFileName"
                echo -n ",${sha}" >> "$currentDir/$resultFileName"
                echo -n ",${module}" >> "$currentDir/$resultFileName"
                echo -n ",${testName}" >> "$currentDir/$resultFileName"

                surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)
                
                cd $currentDir"/agent-pom-modify"
                bash modify-project.sh "$inputProj/$slug" $surefire_exists "minimizer"
                echo "currentDir= $(pwd), slug=$inputProj/$slug"
                cd $inputProj/$slug

                if [[ $slug == "Accenture/mercury" ]]; then
                    mvn install -pl $module -am -Dmaven.test.skip=true
                else
                    mvn install -pl $module -am -DskipTests
                fi
                #exit
                if [[ $module != "." ]]; then
                    projName=$(sed 's;/;.;g' <<< $module-$testName)
                 else   
                    projName=$(sed 's;/;.;g' <<< $subProj-$testName)
                fi
                #1st Run, To Find concurent method list
                #Locations-Java-WebSocket-org.java_websocket.issues.Issue256Test#runReconnectBlockingScenario4-TSVD-Run5-100.txt
                 mkdir -p "$currentDir/Delta-Debug/Delta-Debug-${projName}"


                resultLocationsFile="$(find $currentDir/$2 -name "Locations-*-${testName_for_file_name}-FlakeDelay-Run-1-*")"         
                filename="${resultLocationsFile%.*}"
                startingDelay=${filename//*-}
                
                locationCount=$(wc -l < $resultLocationsFile)	
                arr=($(seq 1 $locationCount))
                echo "Seq size= ${#arr[@]} "
                
                full_start=$(date +%s.%N)
                start=$(date +%s.%N)
                delta_debug arr 2 $startingDelay 0 
                full_end=$(date +%s.%N)
                take=$(echo "scale=2; ${full_end} - ${full_start}" | bc)
                take=$(echo $take | awk '{printf("%.2f\n", $1) }')
                echo  -n  ",${take}" >> "$currentDir/$resultFileName"
                echo "" >> "$currentDir/$resultFileName"
            fi
          fi
     fi

   cd $currentDir

    bash $currentDir/find-actual-line-to-delay-inject.sh "$currentDir/$resultFileName" $currentDir/$2
done < $1

