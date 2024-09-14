if [[ $1 == "" ]]; then
    echo "give the input file to get test_name"
    exit
fi
while read line
do

if [[ ${line} =~ ^\# ]]; then
    echo "Line starts with Hash $line"
    continue
fi
test_name=$(echo $line | cut -d',' -f4 | sed 's;\[;\\[;g' |sed 's;\\;.;')

start_time=$(date +%s.%N)
#bash delay_injection_and_minimized_locations.sh $1
bash root_method_and_critical_point_search.sh Results-Minimizer/${test_name}_Actual_Location.csv tmp
#bash barrier_point_search.sh Results-Boundary/Boundary-${test_name}-Result-without-delay-optimization.csv
end_time=$(date +%s.%N)

take=$(echo "scale=2; ${end_time} - ${start_time}" | bc)
take=$(echo $take | awk '{printf("%.2f\n", $1) }')
echo $line,$take >> Total_Time.csv 
done < $1
