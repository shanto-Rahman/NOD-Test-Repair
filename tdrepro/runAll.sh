#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi
#baseline_all_flaky_tests_after_10k_runs.csv

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
trace_dir="$currentDir/traces"
outputDir="$2"
trace_collection_way="$3"

if [ ! -d "$currentDir/$outputDir" ] 
then
    mkdir "$currentDir/$outputDir"
fi

if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

if [ ! -d "$currentDir/logs" ] 
then
    mkdir "$currentDir/logs"
fi

if [ ! -d "$trace_dir" ] 
then
    mkdir "$trace_dir"
fi

test_specific_stat="$currentDir/$outputDir/Test-Specific-Stat.csv"
echo "Project-Name,SHA,Module,Test-Name,Failure-Found,Runtime,#Thread" > "$currentDir/$outputDir/Isolation-Result.csv"

echo "Project-Name,SHA,Module,Test-Name,Total-Executed-Meth,Total-tokens" >> "$test_specific_stat"
while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    id=$(echo $line | cut -d',' -f1)
    slug=$(echo $line | cut -d',' -f2)
    sha=$(echo $line | cut -d',' -f3)
    module=$(echo $line | cut -d',' -f4)

    testName=$(echo $line | cut -d',' -f5) #"${testName_with_dot%.*}#${testName_with_dot##*.}"
    testName_with_dot="${testName//#/.}"
    #testName_with_dot=$(echo $line | cut -d',' -f5)
    #package_class_name=$(echo $testName_with_dot| rev | cut -d'.' -f2- | rev)
    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    echo "$testName"
    testClass="$(echo $testName_with_dot | rev | cut -d'.' -f2 | rev)"
    #echo "$testClass"
    

    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi
    
    cd $inputProj/$slug
    git checkout ${sha}

	JMVNOPTIONS=""
    if [[ "$slug" == "doanduyhai/Achilles" ]]; then
        git stash 
        sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
        sed -i '/<plugin>/,/<\/plugin>/ {
         /<groupId>org.apache.felix<\/groupId>/ {
           N
           /<artifactId>maven-bundle-plugin<\/artifactId>/ {
             a\
             <version>${felix.version}</version>
           }
         }
       }' pom.xml

    elif [[ "$slug" == "spring-projects/spring-boot" ]]; then
        git stash 
        sed -i 's~http://repo.string.io~https://repo.spring.io~g' pom.xml


    elif [[ $slug == "apache/dubbo" ]]; then
        JMVNOPTIONS="-pl dubbo-dependencies-bom"

    elif [[ $slug == "apache/httpcore" ]]; then
       git stash
       sed -i '/<build>/,/<\/build>/ {
       /<plugins>/a\
         <plugin>\n\
           <groupId>org.apache.maven.plugins</groupId>\n\
           <artifactId>maven-surefire-plugin</artifactId>\n\
           <version>2.22.1</version>\n\
         </plugin>
     }' pom.xml
 
    fi  
    echo -n "${slug},${sha},${module},${testName}" >> "$currentDir/$outputDir/Isolation-Result.csv"
    
    if [[ $module != "." ]]; then
        projName=$(sed 's;/;.;g' <<< $module-$testName)
    else   
        projName=$(sed 's;/;.;g' <<< $subProj-$testName)
    fi
    
    if [[ $slug == "Accenture/mercury" ]]; then
        mvn install -pl $module -am -Dmaven.test.skip=true
    else
        mvn install -pl $module -am -DskipTests
    fi
    slug_with_underscore="${slug//\//_}"
    module_with_underscore="${module//\//_}"
    echo "$slug_with_underscore"

    cd $inputProj/$slug
    #cp whitelist.txt "$currentDir/Locations/whitelist-$projName.txt"
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)

    cd $currentDir"/agent-pom-modify" 
    #echo "bash modify-project.sh $inputProj/$slug $surefire_exists "minimizer""
    
    bash modify-project.sh $inputProj/$slug "jacoco"
    cd $inputProj/$slug
    mvn clean install -pl $module -am -DskipTests
    mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$currentDir/logs/$testName-con.txt"

    mvn edu.utexas.ece:flakesync-maven-plugin:1.0-SNAPSHOT:concurrentfind -Dflakesync.testName=$testName -pl $module

    cp $module/.flakesync/${testName_with_dot}-ResultMethods.txt "$currentDir/executed_methods/"
    python3 $currentDir/classify_methods_multimodule.py "$projectRoot" "$currentDir/executed_methods/${testName_with_dot}-ResultMethods.txt"
    exit

     
    cp $currentDir/jacococli.jar .
    echo "cp $currentDir/jacococli.jar $(pwd)"

    #java -jar jacococli.jar report $module/target/jacoco.exec \
    #  --classfiles $module/target/classes \
    #    --sourcefiles $module/src/main/java \
    #      --xml $module/target/coverage.xml
    # Assume this is the root of your multi-module project
    CLASSFILES=""
    SOURCEFILES=""
    
    for mod in $(find . -name target -type d -prune); do
      base_module=$(dirname "$mod")

       #echo "mod=$mod"
       #echo "class dir=$mod/classes"
       #echo "source dir=$base_module/src/main/java"
       if [ -d "$mod/classes" ]; then
           echo "classes exists"
       else
           echo "classes missing"
       fi
       

      if [[ "$slug" == "doanduyhai/Achilles" && "$base_module" == ./integration-test-* && "$base_module" != ./$module ]]; then
        continue
      fi

      if [ -d "$mod/classes" ]; then
        CLASSFILES+="--classfiles $mod/classes "
      fi

      if [ -d "$base_module/src/main/java" ]; then
        SOURCEFILES+="--sourcefiles $base_module/src/main/java "

      elif [ "$slug" == "zxing/zxing" ]; then
        if [ -d "$base_module/src" ]; then
          echo "sources exists"
        else
          echo "sources missing"
        fi
        SOURCEFILES+="--sourcefiles $base_module/src "
        CLASSFILES+="--classfiles $base_module/build "
      fi
    done
      java -jar jacococli.jar report $module/target/jacoco.exec \
        $CLASSFILES \
        $SOURCEFILES \
        --xml $module/target/coverage.xml

      #echo "java -jar jacococli.jar report $module/target/jacoco.exec \
      #  $CLASSFILES \
      #  $SOURCEFILES \
      #  --xml $module/target/coverage.xml"

      #executed_methods_count_and_total_token_count=$(
    #fi
    #echo python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug"
    python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug" 
    #)
    #executed_methods=$(echo "$executed_methods_count_and_total_token_count" | cut -d'=' -f2 | cut -d':' -f1 | tr -d ' ')
    #total_tokens_desc=$(echo "$executed_methods_count_and_total_token_count" | cut -d'=' -f3 | tr -d ' ')

    test_class_full_path=$(find $module -name "${testClass}.java")
    echo "test_class_full_path=$test_class_full_path"

    if [[ $testName == "io.undertow.websockets.jsr.test.JsrWebSocketServer08Test#testErrorHandling" || $testName == "io.undertow.websockets.jsr.test.JsrWebSocketServer13Test#testErrorHandling" ]]; then #These classes extend JsrWebSocketServer07Test.java, and the actual method is JsrWebSocketServer07Test.java
        test_class_full_path="websockets-jsr/src/test/java/io/undertow/websockets/jsr/test/JsrWebSocketServer07Test.java"
    elif [[ $testName == "uk.co.flax.luwak.matchers.TestPartitionMatcher#testParallelSlowLog" || $testName == "uk.co.flax.luwak.matchers.TestParallelMatcher#testParallelSlowLog" ]]; then
        test_class_full_path="luwak/src/test/java/uk/co/flax/luwak/matchers/ConcurrentMatcherTestBase.java"
    elif [[ $testName == "com.github.kagkarlsson.scheduler.compatibility.HsqlCompatibilityTest#test_compatibility" ]]; then
        test_class_full_path="src/test/java/com/github/kagkarlsson/scheduler/compatibility/CompatibilityTest.java"
    elif [[ $testName == "com.google.zxing.pdf417.decoder.ec.ErrorCorrectionTestCase#testTooManyErrors" ]]; then
        test_class_full_path="core/test/src/com/google/zxing/pdf417/decoder/ec/ErrorCorrectionTestCase.java"
    fi
    
    #echo "python3 $currentDir/collect_test_meth_body.py "$module" "$testName" "$slug" "$test_class_full_path" $currentDir"
    python3 $currentDir/collect_test_meth_body.py "$module" "$testName" "$slug" "$test_class_full_path" $currentDir #) # Might need if later we want to do the repair
    #echo $(pwd)

    #exit
    #echo "matched_calls===$matched_calls"

    #python3 $currentDir/collect_method_body.py "$module" "$testName" "$slug"
    #all_dependent_modules_including_the_main_module=$(find . -type d -name target | sed 's|/target||' | sed 's|^\./||' | sort -u)  #$(find . -type d -name target | sed 's|/target||' | sort -u)
    #all_dependent_modules_including_the_main_module=$(find . -type d -name target -prune | sed 's|/target$||' | sed 's|^\./||' | sort -u)
    readarray -t modules_array < <(find . -type d -name target -prune | sed 's|/target$||' | sed 's|^\./||' | sort -u)


    #echo $all_dependent_modules_including_the_main_module

    result=$(python3 $currentDir/collect_method_body.py $module   "$testName" "$slug" "${modules_array[@]}")

    echo " python3 $currentDir/collect_method_body.py $module $testName $slug ${modules_array[@]}"
    #echo "result=$result"
    executed_methods=$(echo "$result" | cut -d'=' -f2 | cut -d':' -f1)
    total_tokens=$(echo "$result" | cut -d'=' -f3)

    echo "Executed methods: $executed_methods"
    echo "Total tokens:      $total_tokens"
    #exit


    echo "$slug,$sha,$module,$testName,$executed_methods,$total_tokens" >> $test_specific_stat
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv" "$trace_dir/"
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "$trace_dir/"
    base_package=$(python3 $currentDir/finding_base_package.py "$trace_dir/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv")
    #echo "$base_package"
    cd $inputProj/$slug
    #exit
    if [[ $trace_collection_way == "static" ]]; then
        git stash
        #git checkout $(find -name "*.java")
        rm -rf $(find -name "target")
        #rm test-classes.jar 
        rm -rf merged_classes/
        rm merged-all-classes.jar
        echo "" >> "$currentDir/$outputDir/Isolation-Result.csv"
    fi
    cd $currentDir

    #if [[ $trace_collection_way == "dynamic" ]]; then
    #    python3 ff.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_dynamic_calltrace.txt "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_call_depth.csv"

    #elif [[ $trace_collection_way == "static" ]]; then
    #    python3 mapping_static_callgraph_to_executed_meth.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_callgraphs.csv "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_static_call_depth.csv"

    #    echo "python3 mapping_static_callgraph_to_executed_meth.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_callgraphs.csv "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_static_call_depth.csv""

    #fi
    #exit
done < $1
#bash  $currentDir/run-delta-debugging.sh "$currentDir/$outputDir/Isolation-Result.csv" "Locations/" "Results-Minimizer"

