if [[ $1 == "" ]]; then
    echo "give argument (e.g., ../data/data.csv)"
    exit
fi

rm "Results/Static_Analysis_and_Claude_comparison.csv"

while read proj_line; do 
    if [[ ${proj_line} =~ ^\# ]]; then
        echo "Line starts with Hash ${proj_line}"
        continue
    fi
    proj=$(echo $proj_line | cut -d',' -f1)
    echo $proj
    python3 find_focal_method_using_claude.py ../test_analysis/Results/${proj}_function_block.csv # For Claude result
    if [[ -f "unable_focal_meth.csv" ]]; then
        rm "unable_focal_meth.csv"
    fi
    res=$(grep -r "Unable to determine the focal method" "Results/${proj}_function_block.csv") 
    #echo $res > "unable_focal_meth.csv"
    while read -r line ; do
        echo "$line" >> "unable_focal_meth.csv"
        # your code goes here
    done < <(grep "Unable to determine the focal method" "Results/${proj}_function_block.csv")
    bash compare_results_between_statistical_analysis_and_claude.sh unable_focal_meth.csv "../test_analysis/Results/${proj}_focal_method_with_api_similarity.csv" "Results/${proj}_function_block.csv"
done < $1
python3 parse_result.py "Results/Static_Analysis_and_Claude_comparison.csv"
