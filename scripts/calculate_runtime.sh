#$1=data_list/input.csv
#$2="Results-Barrier/Final-Fix-Result.csv"
result="Results-Barrier/Runtime-Result.csv"
echo "slug,sha,module,testname,Minimizer,Root-Meth,Boundary,crit_point,barrier_point" >> $result
rm $result
while read line
do
	
  if [[ ${line} =~ ^\# ]]; then
      echo "Line starts with Hash $line"
      continue
  fi
  test_name=$(echo $line | cut -d',' -f4 | sed 's;\[;\\[;g' |sed 's;\\;.;')
  echo -n "$line" >> "$result"
  if [[ ! -f "Results-Minimizer/${test_name}.csv" ]]; then
  	echo -n ",NA" >> "$result"
  else
  	echo -n "," >> "$result"
  fi
  
  if [[ ! -f "Results-Boundary/${test_name}-Result.csv" ]]; then
  	echo -n ",NA" >> "$result"
  else
  	echo -n "," >> "$result"
  fi
  
  if [[ ! -f "Results-Boundary/Boundary-${test_name}-Result-without-delay-optimization.csv" ]]; then
  	echo -n ",NA" >> "$result"
  else
  	echo -n "," >> "$result"
  fi
  #echo "" >> "Check.csv"
  #continue
  
  runtime_for_minimization=$(rev "Results-Minimizer/${test_name}.csv" | cut -d',' -f1 | rev) #last item is runtime 
  runtime_for_root_method=$(rev "Results-Boundary/${test_name}-Result.csv" | cut -d',' -f1 | rev) #last item is runtime 
  runtime_for_boundary=$(rev "Results-Boundary/Boundary-${test_name}-Result-without-delay-optimization.csv" | cut -d',' -f1 | rev)
  runtime_for_crit_search=$(echo "$runtime_for_minimization" + "$runtime_for_root_method" + "$runtime_for_boundary" | bc) 
  echo "crit search time=$runtime_for_minimization"
  echo "crit search time=$runtime_for_root_method"
  echo "crit search time=$runtime_for_boundary"
  echo "crit search time=$runtime_for_crit_search"
  
  repair_res=$(grep -r "${test_name}" $2)
  echo $repair_res
  runtime_for_barrier=$(echo $repair_res| rev | cut -d',' -f1 | rev)
  echo $runtime_for_barrier
  echo "$runtime_for_crit_search,$runtime_for_barrier" >> $result
  #exit
done < $1
