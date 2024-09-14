import csv
import re


def save_complexities_to_file(proj_name, git_link, complexities, output_filename):
    base_path, suffix = output_filename.split('_cyclomatic', 1) #Results/airtable-python_wrapper_cyclomatic_complexity.csv into Results/airtable-python_wrapper and _cyclomatic_complexity.csv
    with open(output_filename, 'w') as file:
        file.write(f'proj_name,git_link,file_name,test_method,cyclomatic_complexity,line_number,start_line,end_line\n')
        for file_path, name, complexity, line_number, start_line_no, end_line_no in complexities:
            file.write(f'{proj_name},{git_link},{file_path},{name},{complexity},{line_number},[{start_line_no},{end_line_no}]\n')
    

def save_test_method_body(proj_name, git_link, file_path, function_blocks):
    print("file_path=",file_path)
    base_path, suffix = file_path.split('_focal', 1) #Results/airtable-python_wrapper_cyclomatic_complexity.csv into Results/airtable-python_wrapper and _cyclomatic_complexity.csv
    with open(base_path+"_function_block.csv", 'w', newline='', encoding='utf-8') as file:
        #print('I am from base_path+function_block', base_path+"_function_block.csv")
        writer = csv.writer(file, quoting=csv.QUOTE_ALL, delimiter=',')
        # Write the header row
        writer.writerow(['proj_name','git_link','file_name', 'test_method', 'test_method_block'])
        for file_path, function_name, function_body in function_blocks:
            writer.writerow([proj_name, git_link, file_path, function_name, function_body])

def save_dependencies_to_file(proj_name, git_link, dependencies, output_filename):
    with open(output_filename, 'w') as file:
        file.write(f"Proj_name,File_name,method,args,types,internal_calls,external_calls,api_calls,branch_count,branch_type\n")
        for file_path, methods in dependencies.items():
            for method, deps in methods.items():
                internal_count = len(deps['internal_calls'])
                external_count = len(deps['external_calls'])
                api_count = len(deps['api_calls'])
                arg_count = deps['arg_count']
                sanitized_arg_types = [arg_type.replace(',', ';') for arg_type in deps['arg_types']]
                arg_types = '#'.join(sanitized_arg_types)  
                branch_count = deps['branch_count']
                sanitized_branch_types = [branch_type.replace(',', ';') for branch_type in deps['branch_types']]
                branch_types = '#'.join(sanitized_branch_types) if sanitized_branch_types else 'None'
                file.write(f"{proj_name},{git_link},{file_path},{method},{arg_count},{arg_types},{internal_count},{external_count},{api_count},{branch_count},{branch_types}\n")

