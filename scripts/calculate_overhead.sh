if [[ $1 == "" ]]; then
    echo "give fixed test's file name(e.g.,Result/Final-Fix-Result.csv) "
    exit
fi
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
inputProj=$currentDir"/projects"
Results="$currentDir/Result"
#Yielding_dir="$currentDir/YIELDING_Point_StackTrace"
logs_dir="$currentDir/logs"
if [ ! -d "$Results" ];then
    mkdir "$Results"
fi
if [ ! -d "$inputProj" ]; then
    mkdir "$inputProj"
fi
if [ ! -d "$logs_dir" ]; then
    mkdir "$logs_dir"
fi

echo "slug,sha,module,testname,boundary,yield-point,threshold,Runtime-Normal,Runtime-With-Patches,Overhead" >> "$Results/Overhead.csv"

while read line
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
    upper_boundary_loc=$(echo $line | cut -d',' -f5 | cut -d'~' -f2 | cut -d'[' -f1 | sed 's/\//./g') 
    delay=$(echo $line | cut -d',' -f5 | cut -d'~' -f2 | cut -d'[' -f2 | cut -d']' -f1) 
    yield_loc=$(echo $line | cut -d',' -f6)
    threshold=$(echo $line | cut -d',' -f7)
    echo $upper_boundary_loc
    
    if [[ ! -d ${inputProj}/${rootProj} ]]; then
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
    mvn clean install -pl $module -am -DskipTests

    start=$(date +%s.%N)
    mvn test -pl $module -Dtest="$testName" 
    end=$(date +%s.%N)
    runtime_normal=$(echo "scale=3; ${end} - ${start}" | bc)

    bash $currentDir"/agent-pom-modify/modify-project.sh" $inputProj/$slug $surefire_exists
    mvn clean install -pl $module -am -DskipTests

    start=$(date +%s.%N)
    echo "$upper_boundary_loc"
    timeout 3m mvn test -pl $module -Dtest="$testName" -DOverheadCalculate="flag" -DCodeToIntroduceVariable=$upper_boundary_loc -DYieldingPoint="$yield_loc" -Dthreshold="$threshold"  &> "$logs_dir/log_${testName}_overhead"
    end=$(date +%s.%N)
    runtime_with_flakysync=$(echo "scale=3; ${end} - ${start}" | bc)
    Overhead=$(bc <<< "scale=3; $runtime_with_flakysync / $runtime_normal")
    echo "$slug,$sha,$module,$testName,$upper_boundary_loc,$yield_loc,$threshold,$runtime_normal,$runtime_with_flakysync,$Overhead " >> "$Results/Overhead.csv"
    cd $currentDir
    rm -rf $inputProj/$rootProj
done < $1
