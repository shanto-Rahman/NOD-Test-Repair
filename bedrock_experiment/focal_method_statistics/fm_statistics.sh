#$1 = Results/FM_details.csv

if [[ -f "Results/properties_of_fm.csv" ]]; then
    rm "Results/properties_of_fm.csv" 
fi
while read proj_line
do

    if [[ ${proj_line} =~ ^\# ]]; then
        echo "Line starts with Hash ${proj_line}"
        continue
    fi
    proj=$(echo $proj_line | cut -d',' -f1)
    test_name=$(echo $proj_line | cut -d',' -f2)
    fm=$(echo $proj_line | cut -d',' -f3)
    fm_first_covered_line=$(echo $proj_line | cut -d',' -f4)
    fm_filename=$(echo $proj_line | cut -d',' -f5)
    test_filename=$(echo $proj_line | cut -d',' -f6) # We also need to keep the test_filename because one test may exists into multiple test files
    #dirname=$(echo $proj_line | cut -d',' -f5)
    #echo "python3 method_statistics.py $proj filename=${fm_filename}, fm=$fm test_name=$test_name, test_filename=$test_filename"
    #
    if [[ $fm_filename != "" ]]; then
        echo "I am one"
        python3 method_statistics.py $proj $fm_filename $fm $test_name $test_filename ${fm_first_covered_line}
    fi
    #exit
done < $1
