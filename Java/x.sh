#bash runAll.sh ../data/talank_with_test_id_idoft.csv results/ "static"
#bash runAll.sh ../data/tmp.csv results/ "dynamic"
#bash search_for_failure_reproducing.sh ../data/talank_with_test_id_idoft.csv idoft
#bash runAll.sh ../data/talank_with_test_id_flakerake.csv results/ 
#bash search_for_failure_reproducing.sh ../data/talank_with_test_id_flakerake.csv flakerake
#bash runAll.sh results/Tests_found_from_flakerake_isolated_reruns.csv results/
#bash search_for_failure_reproducing.sh results/Tests_found_from_flakerake_isolated_reruns.csv results/

#bash runAll.sh ../data/new_flaky_rows.csv results/
#bash search_for_failure_reproducing.sh ../data/new_flaky_rows.csv idoft
#../results/Tests_found_from_flakerake_isolated_reruns.csv results/


#bash runAll.sh ../data/talank_with_test_id_idoft_corrected.csv results/
#bash search_for_failure_reproducing.sh ../data/talank_with_test_id_idoft_corrected.csv idoft


bash runAll.sh ../Results/uniq_flakerake_not_found_in_idoft.csv results/
bash search_for_failure_reproducing.sh ../Results/uniq_flakerake_not_found_in_idoft.csv flakerake

RQ2
 bash rq2.sh results/gpt.csv results idoft
