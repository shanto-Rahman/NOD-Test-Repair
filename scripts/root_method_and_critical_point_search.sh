#!/bin/bash
#bash mvn-run-and-find-stack-trace.sh data_list/data.csv Results/output.csv
if [[ $1 == "" || $2 == "" ]]; then
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

if [ ! -d "$currentDir/Linkage" ]; then
    mkdir "$currentDir/Linkage"
fi
linkage=0

process_results() {
   local delay=$1
   local item_location=$2
   local outputFile=$3
   local threadId=$4
   local projName=$5
   local tt_file=$6
   local from_updated_delay=$7

   bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/$projName-FlakeDelay.txt")
   linkageError=$(grep -r "java.lang.LinkageError" "$currentDir/logs/$projName-FlakeDelay.txt" | wc -l)

   if [[ $linkageError -gt 0 ]]; then
       linkage=$((linkage + 1))
       cp  "$currentDir/logs/$projName-FlakeDelay.txt" "$currentDir/Linkage/$projName-FlakeDelay-$linkage.txt"
       return 0
   fi  

   if [ $bugCount -gt 0 ]; then
       echo -n ",$item_location,Fail,$delay" >> "$outputFile"
       className=$(echo $item_location | cut -d'#' -f1)
       lineNumber=$(echo $item_location | cut -d'#' -f2)
       searchKey="$threadId,$className.*:$lineNumber"
       stack_trace_location=$(find "$currentDir/Locations" -name "StackTrace-${tt_file}.txt")
       rootLine=$(grep -r $searchKey "$stack_trace_location" | head -1)
       if [[ $rootLine == "" ]]; then
           return
       fi  
       rootLine=$(echo $rootLine | sed 's/[(]/=/g')
       rootLine=$(echo $rootLine | sed 's/[)]/!/g')
       rootLine=$(echo $rootLine | sed 's/\$/</g')
       rootLine="$rootLine[${delay}]"
	   if [[ $from_updated_delay != "" ]]; then
	      return 2
       else 
          return 1
	   fi
   else
      return 3
   fi

}

echo "Module-Name,SHA,Module,Test-Name,FlakeDelay-Run1(1=Bug-Found: 0=Not-Found),FlakeDelay-Run1-Time-Required(sec)" >> "$outputFile"
while IFS= read -r line
    do
    if [ ! -d "$currentDir/logs" ]; then
        mkdir "$currentDir/logs"
    fi
    
    if [ ! -d "$currentDir/Locations/Line" ]; then
        mkdir -p "$currentDir/Locations/Line"
    fi

    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
    all_locations=($(echo $line | cut -d',' -f6)) # Multiple root location can be found by delta-debugging.
    echo "${all_locations}"
    IFS=';' read -ra locations <<< "${all_locations}"
    location_count=${#locations[@]}
    echo $location_count
    delay=$(echo $line | rev | cut -d',' -f1 | rev)
    rootLine=""
    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi

    cd $inputProj/$slug
    git checkout ${sha}

    if [[ "$slug" == "doanduyhai/Achilles" ]]; then
        sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
    else
        echo "Slug is not for Achilles."
    fi

    if [[ $slug == "Accenture/mercury" ]]; then
        mvn install -pl $module -am -Dmaven.test.skip=true
    else
        mvn install -pl $module -am -DskipTests
    fi

    echo -n "${slug},${sha},${module},${testName}" >> "$outputFile"
    tt_file=$(echo $testName | sed 's;\[;\\[;g')
    
    if [[ $module != "." ]]; then
       projName=$(sed 's;/;.;g' <<< $module-$tt_file)
    else
        projName=$(sed 's;/;.;g' <<< $subProj-$tt_file)
    fi
    location_to_inject_delay=""
    if [[ -f "$currentDir/Locations/$projName" ]]; then #Removing Location file is in previous run it exists
        rm "$currentDir/Locations/$projName"
        rm "$currentDir/Locations/already_covered_line-${projName}"
        rm "$currentDir/Locations/stackTraced-parsed-${projName}"
    fi
    start=$(date +%s.%N)
    for ((i=1; i<=${location_count}; i++)); do  #Is used if multiple location makes test fail (this comes from it's prior step)
        class_name_with_dollar_sign=$(echo ${all_locations} | cut -d';' -f $i)
        line_number=$(echo ${class_name_with_dollar_sign} | cut -d'#' -f2)
        class_name_without_dollar_sign=$(echo ${class_name_with_dollar_sign} | cut -d'#' -f1) 
        location_to_inject_delay=$class_name_without_dollar_sign"#"$line_number
        echo "$location_to_inject_delay:$testName" >> "$currentDir/Locations/$projName"
        #echo "$location_to_inject_delay:$testName" >> "$currentDir/Locations/already_covered_line-${projName}"
    done
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)
    if [[ "$slug,$sha" == "Alluxio/alluxio,78c063ae181279d81cbc0808a684864a8c8b311c" ]]; then
        surefire_exists=0
    fi
    bash $currentDir"/agent-pom-modify/"modify-project.sh $inputProj/$slug $surefire_exists "boundaryPoint"
    iteration=0
    arr=()
    stack_trace="false"

    #Running the location with delay to get initial stacktrace
    bash $currentDir/mvn-run-and-find-stack-trace.sh $(pwd) $currentDir ${delay} $testName $projName $module "$currentDir/Locations/$projName" "1st"  #running test
    bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/$projName-FlakeDelay.txt")
    linkageError=$(grep -r "java.lang.LinkageError" "$currentDir/logs/$projName-FlakeDelay.txt" | wc -l)

    if [[ $linkageError -gt 0 ]]; then
       linkage=$((linkage + 1))
       cp  "$currentDir/logs/$projName-FlakeDelay.txt" "$currentDir/Linkage/$projName-FlakeDelay-$linkage.txt"
       continue
    fi
    if [ $bugCount -gt 0 ]; then # Assumption is that the test should fail. Because this line comes from delta-debugging which makes test fail consistently
        echo  -n  ",Beginning-Location(count=${location_count}),$location_to_inject_delay,Fail,${delay}" >> "$outputFile"
        #Following check is only for checking if required files exists or not.
        if [ -s "$currentDir/Locations/StackTrace-${tt_file}.txt" ]; then #Check if a file is exists and non-empty
             bash "$currentDir/parse-stack-trace.sh" "$currentDir/Locations/StackTrace-${tt_file}.txt" 1 "$projName" #This creates a row for each stackStrace(before END)
            if [ ! -s $(find "$currentDir/Locations" -name "stackTraced-parsed-$projName") ]; then  # Will break if stackTrace-parsed file not exists
                stack_trace="true"
                break
            fi
        fi
    else
       echo "$line,This minimized location is not a good one. Go back and run minimizer." >> "$currentDir/Results-Boundary/Root-Method-All-Tests.csv" 
       continue
    fi
    while read line_for_each_stacktrace # For each line from my "$currentDir/Locations/stackTraced-parsed-$projName"; One line may contain multiple locations
    do
        commaCount_from_stacktrace=$(echo ${line_for_each_stacktrace} | tr -cd , | wc -c)
        thread_index=$((commaCount_from_stacktrace+1))
        for ((j=1; j<=${commaCount_from_stacktrace}; j++)); #each item from a stacktrace
        do

            item_location=$(echo ${line_for_each_stacktrace} | cut -d',' -f $j)
            java_class_name=$(echo ${item_location} | cut -d'#' -f1 | rev | cut -d'/' -f1 | rev | cut -d'$' -f1) # if dollar sign exists

            not_in_library_code=$(find . -name "${java_class_name}.java" | wc -l)
            if [[ $not_in_library_code -eq 0 ]]; then
                continue
            fi
            threadId=$(echo ${line_for_each_stacktrace} | cut -d',' -f $thread_index)
            echo "${item_location}:$testName" > "$currentDir/Locations/Line/$projName-$threadId-$j"
            exists=$(grep -r "${item_location}:$testName" "$currentDir/Locations/already_covered_line-${projName}" | wc -l)
            echo "exists=$exists, $item_location"
            if [ $exists -eq 0 ]; then  # If the test does not run with that location before
                echo "${item_location}:$testName" >> "$currentDir/Locations/already_covered_line-${projName}"
                bash $currentDir/mvn-run-and-find-stack-trace.sh $(pwd) $currentDir $delay $testName $projName $module "$currentDir/Locations/Line/$projName-$threadId-$j"  
                process_results $delay $item_location "$outputFile" $threadId $projName $tt_file
                process_res_result=$? #to get the function's exit code
                echo $item_location >> "$currentDir/tmp"
                #echo "returned res= ${process_res_result}"
                if [[ $process_res_result -eq 0 ]]; then #Linkage error check
                    break 
                elif [[ $process_res_result -eq 3 ]]; then
                    MAX_DELAY=51200
                    updated_delay=$((delay * 2))
                    echo "updated_delay="$updated_delay
                    while [ $updated_delay -le $MAX_DELAY ]; do 
                        bash $currentDir/mvn-run-and-find-stack-trace.sh $(pwd) $currentDir $updated_delay $testName $projName $module "$currentDir/Locations/Line/$projName-$threadId-$j"
                        echo "******$item_location, delay=$updated_delay" >> "$currentDir/tmp"
                        process_results $updated_delay $item_location "$outputFile" $threadId $projName $tt_file "need_to_increase_delay"
                        process_res_result=$?

						if [[ ${process_res_result} -eq 2 ]]; then #2 means failure occurs
							break

                        else #3 means no failure
                            if [ $updated_delay -eq $MAX_DELAY ]; then #IF no bug found and it reaches to the MAX_DELAY, break, otherwise update the delay with the same loctaion
                                echo -n ",$item_location,Pass,${updated_delay}" >> "$outputFile"
                                break
                            fi
                            updated_delay=$(( updated_delay*2))
                        fi
                    done
                    if [ $(find "$currentDir/Locations/Line"  -name "$projName-$threadId-$j" | wc -c) -gt 0 ];then # This is just to make space free by deleting file
                       rm $(find "$currentDir/Locations/Line"  -name "$projName-$threadId-$j")
                    fi
                fi
            fi
        done # END: each item from a stacktrace
        echo "rootLine=$rootLine"
        if [[ ! -z $rootLine  ]]; then # Aim is to check arr. If rootLine doesn't exist in arr, I will add that item.
			item_found_in_arr="false"
            echo "****************$rootLine****" 
            for root in "${arr[@]}"
            do
                if [[ "$root"  == "$rootLine" ]]; then  # SAME item found. TEST required ??
					item_found_in_arr="true"
                    break
                fi
            done
            if [[ "$item_found_in_arr" == "false" ]]; then
               arr+=("$rootLine")

            fi
        fi
    done < "$currentDir/Locations/stackTraced-parsed-$projName"
    echo -n ",Final Result=>" >> $outputFile
    #testName_replace_with_dot=$(echo $tt_file |sed 's/\#/./g')
    result_file_name="Results-Boundary/${tt_file}-Result.csv" 
    if [[ -f "$currentDir/$result_file_name" ]]; then
        rm "$currentDir/$result_file_name"
    fi
    echo -n "${slug},${sha},${module},${testName}" >> "$currentDir/$result_file_name"

    len="${#arr[@]}"
    if [[ $len -gt 0 ]]; then # Now printing each array item into the outputFile
        for root in "${arr[@]}"
        do
            everything_is_fine=1 
            root=$(echo $root | sed 's/=/(/g')
            root=$(echo $root | sed 's/!/)/g')
            root=$(echo $root | sed 's/</\$/g')
            echo -n ",$root" >> "$outputFile"
            delay=$(echo $root | cut -d',' -f3)
            echo -n ",$root" >> "$currentDir/${result_file_name}"
        done
    else #if [[ ${stack_trace} == "false" ]]; then #considering that we do not find any stack_trace, or I mean onno kono location er jonno ei test ta fail kore nai
        ### Need to find a method name that contains a line
        echo ${location_to_inject_delay} > "$currentDir/logs/org_loc.txt"
        echo "content of org_loc=${location_to_inject_delay}"
        ln=$(echo ${location_to_inject_delay} | cut -d'#' -f2) #split line number
        cn=$(echo ${location_to_inject_delay} | cut -d'#' -f1) #split class name
        cnOnly=$(echo $cn | rev | cut -d'/' -f1 | rev)
        #For gettting the method name of that class and line
        mvn test -pl $module -Dtest=$testName -DsearchForMethodName="$currentDir/logs/org_loc.txt" > "$currentDir/logs/search-for-method-name-$tt_file" 
        containing_method_name=$(grep -r "CONTAINING-METHOD-NAME" "$currentDir/logs/search-for-method-name-$tt_file"| head -1 | cut -d'=' -f2 )
        build_classname_method="$cn/${containing_method_name}($cnOnly/java:$ln)"
        echo $containing_method_name
        echo "HOW ??************ $build_classname_method"
        echo -n ",,${build_classname_method}[${delay}]" >> "$currentDir/$result_file_name" #One extra comma added intentionally to keep result file consistent, If we do not get thread ID
        #rm "$currentDir/logs/org_loc.txt"
    fi

    end=$(date +%s.%N)
    take=$(echo "scale=2; ${end} - ${start}" | bc)
    take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    echo ",$take" >>   "$currentDir/$result_file_name"
    cat  "$currentDir/${result_file_name}" >> "$currentDir/Results-Boundary/Root-Method-All-Tests.csv" #To copy each test's result in one file (Result-All.csv)
    cd $inputProj
    echo "" >> "$outputFile"
    #rm -rf "$rootProj"
    
    cd $currentDir
    rm "$currentDir/Locations/Root-*"
    rm -rf "$currentDir/Locations/Line"
    #rm -rf "$currentDir/logs"
    #exit
#for finding the boundaries within the method

    if [[ -f "$currentDir/Results-Boundary/${tt_file}_with_optimalDelay.csv" ]]; then
        rm "$currentDir/Results-Boundary/${tt_file}_with_optimalDelay.csv"
    fi

    if [[ -f "Results-Boundary/Boundary-${tt_file}-Result.csv"  ]]; then
        rm "Results-Boundary/Boundary-${tt_file}-Result.csv" 
    fi

    #bash find_optimal_delay.sh "$currentDir/${result_file_name}" "$currentDir/Results-Boundary/${tt_file}_with_optimalDelay.csv"
    bash analyzeRootMethod.sh "${result_file_name}" "Results-Boundary/Boundary-${tt_file}-Result-without-delay-optimization.csv" 
done < $1    
#bash analyzeRootMethod.sh "$currentDir/Results/Root-Method-All-Tests-$3.csv" "Results/Boundary-$3"

