#$1=unable_focal_meth.csv
#$2=../test_analysis/Results/airtable-python-wrapper_focal_method_with_api_similarity.csv
if [[ ! -f "Results/Static_Analysis_and_Claude_comparison.csv" ]]; then
    #rm "Results/Static_Analysis_and_Claude_comparison.csv"
    #echo "python_file_path,test_method_name,claude_result,Static_Analysis_Result,Static_Analysis_Score(Jaccard_score)" >> "Results/Static_Analysis_Finds_but_Not_Claude.csv"
    echo "#proj_name,git_link,python_file_path,test_method_name,claude_result,Static_Analysis_Result,Focal_method_Class_name,Findings,All_Api_List" >> "Results/Static_Analysis_and_Claude_comparison.csv" 
fi

#while read line 
#do 
#
#	proj_name=$(echo $line | cut -d',' -f1)
#	git_link=$(echo $line | cut -d',' -f2)
#	file_path=$(echo $line | cut -d',' -f3)
#	test_method_name=$(echo $line | cut -d',' -f4)
#	suggested_focal_meth_by_claude=$(echo $line | cut -d',' -f5)
#	search_result_into_jaccard_similarity=$(grep -r "${proj_name},${git_link},${file_path},${test_method_name}," $2 |cut -d',' -f5-)
#	echo $search_result_into_jaccard_similarity
#	#exit
#        echo "$line,$search_result_into_jaccard_similarity" >> "Results/Static_Analysis_Finds_but_Not_Claude.csv"
#	#
#done < $1


while read line 
do 
	## To measure how many are common ##
	proj_name=$(echo $line | cut -d',' -f1)
	git_link=$(echo $line | cut -d',' -f2)
	file_path=$(echo $line | cut -d',' -f3)
	test_method_name=$(echo $line | cut -d',' -f4)
	suggested_focal_meth_by_claude=$(echo $line | cut -d',' -f5 |cut -d'#' -f1)
	suggested_focal_meth_by_jaccard_similarity=$(grep -r "${file_path},${test_method_name}," $2 |cut -d',' -f5 | cut -d'#' -f1)
	class_name_of_suggested_focal_meth=$(grep -r "${file_path},${test_method_name}," $2 |cut -d',' -f6)
	all_focal_meth_by_jaccard_similarity=$(grep -r "${file_path},${test_method_name}," $2 |cut -d',' -f8-)
        echo "$(grep -r "${file_path},${test_method_name}," $2 |cut -d',' -f8-)"
	if [[ $suggested_focal_meth_by_claude ==  $suggested_focal_meth_by_jaccard_similarity ]]; then
            echo $line,$suggested_focal_meth_by_jaccard_similarity,$class_name_of_suggested_focal_meth,"Matched",$all_focal_meth_by_jaccard_similarity >>  "Results/Static_Analysis_and_Claude_comparison.csv"
        else 
            echo $line,$suggested_focal_meth_by_jaccard_similarity,$class_name_of_suggested_focal_meth,"MisMatched",$all_focal_meth_by_jaccard_similarity >>  "Results/Static_Analysis_and_Claude_comparison.csv" #Static_Analysis_Finds_but_Not_Claude.csv"
	fi
done < $3
