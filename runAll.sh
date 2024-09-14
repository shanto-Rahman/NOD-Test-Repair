#For getting the focal methods for tests using jaccard, run the first 3 commands. This will also give you the test statistics, and the output will be ${proj_name}_focal_method_with_api_similarity.csv 
currentDir=$(pwd)
cd test_analysis 
bash collect_tests.sh ../data/data.csv
cd $currentDir

#For getting the focal method names using Claude, run the following two commands.
cd bedrock_experiment 
bash run.sh ../data/data.csv

#Now to combine the results of both Jaccard and Claude, run the following commands. The output will be Results/combined_complexity_result.csv
cd focal_method_statistics
#bash collect_focal_method_statistics.sh ../Results/Static_Analysis_and_Claude_comparison.csv # Aim is to search if the focal method class truely exists or not
bash collect_focal_method_statistics.sh ../../test_analysis/Results/Updated_1079_tests_with_Focal_Methods.csv
bash fm_statistics.sh Results/FM_details.csv 
