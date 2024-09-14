if [[ $1 == "" ]]; then 
    echo "$1 - give the input.csv with (nl/nlighten/prometheus/tomcat/TomcatServletMetricsFilter#118~nl/nlighten/prometheus/tomcat/TomcatServletMetricsFilter#118[100])"
    #echo "$2 - test assertion line number (TomcatServletMetricsFilterTest#30)"
    exit
fi
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
inputProj=$currentDir"/projects"
Results="$currentDir/Results-Barrier" 
Yielding_dir="$currentDir/YIELDING_Point_StackTrace"
logs_dir="$currentDir/logs"
if [ ! -d "$Results" ];then
    mkdir "$Results"
fi
if [ ! -d "$inputProj" ]; then
    mkdir "$inputProj"
fi
if [ ! -d "$Yielding_dir" ];then
    mkdir "$Yielding_dir"
fi
if [ ! -d "$logs_dir" ]; then
    mkdir "$logs_dir"
fi
echo "slug,sha,module,testname,boundary-point,barrier-point,threshold,time" >> "$Results/Result.csv"
while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    elif [[ $(echo $line | grep "Not-Found-Boundary" | wc -l) -gt 0 ]]; then
        echo "Not found any boundary"
        continue
    fi
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    testClassName=$(echo $testName | cut -d'#' -f1 | rev | cut -d'.' -f1 | rev)
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)

    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
        cd $inputProj/$slug
        git checkout ${sha}
    else
        cd $inputProj/$slug
    fi
    
    if [[ $slug == "Alluxio/alluxio" ]]; then
        surefire_exists=0
    else
        surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)
    fi
    JMVNOPTIONS=""
    if [[ "$slug" == "doanduyhai/Achilles" ]]; then
        sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
    elif [[ $slug == "apache/dubbo" ]]; then
        JMVNOPTIONS="-pl dubbo-dependencies-bom"
    fi
    if [[ $slug == "Accenture/mercury" ]]; then
        mvn install -pl $module -am -Dmaven.test.skip=true
    else
        mvn clean install -pl $module -am -DskipTests
    fi
    bash $currentDir"/agent-pom-modify/modify-project.sh" $inputProj/$slug $surefire_exists "barrier"
    
    #For taking the last boundary
    #last_boundary_item=$(echo $line | rev | cut -d';' -f2 | rev)
    boundaries=$(echo $line | cut -d',' -f5)
    boundary_count=$(echo "$boundaries" | grep -o ";" | wc -l)
    if [[ $boundary_count -eq 0 ]]; then
        boundary_count=1 #I am doing this just to forcefully execute the following for block when multiple boundary does not exits. Because when a single boundary exists, it doesn't have any semicolon (;).
    fi

    if [[ $slug,$sha,$module,$testName == "elasticjob/elastic-job-lite,a7042cf4872d784d619e4560cdfa0f92b0311965,elasticjob-infra/elasticjob-infra-common,org.apache.shardingsphere.elasticjob.infra.concurrent.ElasticJobExecutorServiceTest#assertCreateExecutorService" ]]; then #special case
        echo -n "$(echo $line | cut -d',' -f1-5),org.apache.shardingsphere.elasticjob.infra.concurrent#57" >> "$Results/Result.csv" # Look for runable meth in test-class (Will automate)
    fi
    #for (( boundary_index=1; boundary_index<=${boundary_count}; boundary_index=$((boundary_index+1)) )); do 
    for (( boundary_index=${boundary_count}; boundary_index>=0; boundary_index=$((boundary_index-1)) )); do 
        boundary_item=$(echo $boundaries | cut -d';' -f${boundary_index})
        upper_boundary=$(echo $boundary_item | cut -d'~' -f2 | cut -d'[' -f1 | sed 's/\//./g') #Taking the first boundary
        delay=$(echo $boundary_item | cut -d'~' -f2 | cut -d'[' -f2 | cut -d']' -f1) #Taking the first boundary
        if [[ $upper_boundary == *"Test"* ]]; then
            echo "I am in the test method"
            echo $upper_boundary
            echo $line >> "$Results/Boundary-exists-in-test-code.csv"
            bash $currentDir/downward_mvn_run.sh $module $testName ${upper_boundary} $currentDir $line $delay 1
            continue
        fi
        start=$(date +%s.%N)
        #echo "index=$boundary_index,boundary=$boundary_item **"
        bash "$currentDir/collect_stacktrace.sh" $module $testName $delay $currentDir $upper_boundary "${JMVNOPTIONS}" &> "$logs_dir/stacktrce_log_${testName}"
        if [ -f  "$Yielding_dir/$testName" ]; then
            bash $currentDir/run_mvn_test_with_yield_and_cut.sh "$Yielding_dir/$testName" $module $testName ${upper_boundary} $currentDir $line $delay 1 "${JMVNOPTIONS}" &> $currentDir/tmp-log
            flag=$(echo $(grep -r "flag=" $currentDir/tmp-log) | cut -d'=' -f2)

            echo "***flag==$flag"
            if [[ $flag -eq 0 ]]; then # This means that previous update at threshold=1 doesn't work
                # Now we will monitor the execution of the boundary location; then that count we will pass as part of our threshold
                mvn test ${JMVNOPTIONS} -pl $module -Dtest="$testName" -DexecutionMonitor="flag" -Ddelay=$delay -DCodeToIntroduceVariable=$upper_boundary -DYieldingPoint=""  &> log-occurance  
                echo $upper_boundary
                num_of_times_the_boundary_code_is_executed=$(grep -r "#execution=" "$module/ExecutionMonitor.txt" | cut -d'=' -f2)
                bash $currentDir/run_mvn_test_with_yield_and_cut.sh "$Yielding_dir/$testName" $module $testName ${upper_boundary} $currentDir $line $delay ${num_of_times_the_boundary_code_is_executed} "${JMVNOPTIONS}"  &> $currentDir/tmp-log
                flag1=$(echo $(grep -r "flag=" $currentDir/tmp-log) | cut -d'=' -f2)
                echo "***flag1=$flag1"
            fi
        fi
        end=$(date +%s.%N)
        take=$(echo "scale=2; ${end} - ${start}" | bc)
        rm "$Yielding_dir/already_yielding_point.csv"
        if [ $flag -eq 1 ]; then
            echo ",$take" >> $Results/Result.csv
            break
        elif [ $flag1 -eq 1 ]; then
            echo ",$take" >> $Results/Result.csv
            break
        else 
            echo "($line,not-works),$take" >> $Results/Result.csv
        fi
        #check=$((check + 1))
        take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    done

    cd $currentDir
    rm -rf ${inputProj}/${rootProj}
done < $1
