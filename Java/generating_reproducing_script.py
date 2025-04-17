
from utils import set_seed, setup_logging, seed_worker, train, evaluate, parse_cr, qwen_model_define, parse_category_and_token_list, init_setup, contains_english_letter, filter_tokens, forward_func, predict, deep_seek_coder_model_define, llama3_8b_model_define, codegemma7b_model_define, gemma2b_model_define, gemma7b_model_define, interpret_with_ig_qwen, interpret_with_ig_gemma7b, codellama_7b_instruct_model_define, interpret_with_ig_codellama

login(token="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")

def run_experiment(dataset_path, model_weights_path, results_file, data_name_dir, technique):
    device, ml_technique, dataset_category, output_layer, where_data_comes = init_setup(technique, data_name_dir)
    
    if ml_technique == "qwen":
        print('I am qwen')
        model_name, tokenizer, auto_model = qwen_model_define()
    elif ml_technique == "gemma7b":
        model_name, tokenizer, auto_model = gemma7b_model_define() 
    elif ml_technique == "gemma2b":
        model_name, tokenizer, auto_model = gemma2b_model_define()
    elif ml_technique == "codegemma":
        model_name, tokenizer, auto_model = codegemma7b_model_define()
    elif ml_technique == "llama3_8b":
        model_name, tokenizer, auto_model = llama3_8b_model_define()
    elif ml_technique == "deep_seek_coder":
        model_name, tokenizer, auto_model = deep_seek_coder_model_define()
    elif ml_technique == "codellama":
        model_name, tokenizer, auto_model =  codellama_7b_instruct_model_define()
    else:
        print('model name not correct')
        exit()
    execution_time = time.time()
    print("Start time of the experiment", execution_time)
    #no_splits = 10 # For FlakiCat=4, IDOFT=10
    TN = FP = FN = TP = 0
    project_group = 0
    total_execution_time = 0
    #no_split = 5
    global_category_token_map = {}
    predictions_per_project_group = {}
    ground_truth_per_project_group = {}
    tokens_per_project_group = {}
    Org_test_per_project_group = {}
    #print(len(input_data))

    # Get all train-test file pairs from the directory
    train_files = sorted([f for f in os.listdir(data_name_dir) if f.startswith("train_") and f.endswith(".csv")])
    test_files = sorted([f for f in os.listdir(data_name_dir) if f.startswith("test_") and f.endswith(".csv")])

    for train_file, test_file in zip(train_files, test_files):
        project_group +=1
        if project_group == 5:
            break

        if os.path.exists("Flakicat_Categorization-result/score_project_group"+str(project_group)+"_Class.txt"):
            os.remove("Flakicat_Categorization-result/score_project_group"+str(project_group)+"_Class.txt")
        fit_time=0
        bert_flag=0
        total_execution_time = 0
        feature_extraction_time=0
        #total_execution_time_for_feature_extraction = 0
        print(" NOW IN FOLD NUMBER", project_group)
    
        '''X_train_df = pd.read_csv(data_name+'/data_splits/X_train_project_group'+str(project_group)+'.csv')
        Y_train_df = pd.read_csv(data_name+'/data_splits/y_train_project_group'+str(project_group)+'.csv')
    
        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'deadcode_perturbation_Most_important_features.csv')
        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'printStatement_perturbation_Most_important_features.csv')
        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'variableDeclare_perturbation_Most_important_features.csv')
        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'multiLine_comment_perturbation_Most_important_features.csv')
        #X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'singleLine_comment_perturbation_Most_important_features.csv')
        X_test_df = pd.read_csv(data_name+'/data_splits/X_test_project_group'+str(project_group)+'.csv')
        Y_test_df = pd.read_csv(data_name+'/data_splits/y_test_project_group'+str(project_group)+'.csv')'''
        X_train_df, Y_train_df, X_valid_df, Y_valid_df, X_test_df, Y_test_df = read_data(data_name_dir, project_group)

        print(len(X_test_df))
        print(len(Y_test_df))
        print(X_test_df)
        #X_test_df.to_csv('XX.csv', index=False)
        #test_name_at_83 = X_test_df.iloc[83]["full_code"]  # Replace "test_name" with the actual column name

        #print(test_name_at_83)
        #exit()
    
        X_test = X_test_df['full_code']
        y_test = Y_test_df['category']
    
        X_train = X_train_df['full_code']
        y_train = Y_train_df['category']
   
        #Y_train = pd.DataFrame(y_train)
        y_test = pd.DataFrame(y_test)
    
        #Y_train.columns = ['which_tests']
        y_test.columns = ['which_tests']
    
        # convert labels of train, validation and test into tensors
        #train_y = torch.tensor(Y_train['which_tests'].values)
        test_y = torch.tensor(y_test['which_tests'].values)
    
        # create data_loaders for train and validation dataset
        batch_size = 1

        model = auto_model
        
         
        if ml_technique == "qwen":
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_qwen(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
                print('***************** All preds=')
                print(preds)
        
        elif ml_technique == "gemma7b":
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_gemma7b(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
                print('***************** All preds=')
                print(preds)

        elif ml_technique == "gemma2b":
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_gemma2b(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)

        elif ml_technique == "codegemma":
            #model_name, tokenizer, auto_model = codegemma7b_model_define()
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_codegemma(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)

        elif ml_technique == "llama3_8b":
            #model_name, tokenizer, auto_model = llama3_8b_model_define()
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_llama3_8b(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
        elif ml_technique == "deep_seek_coder":
            #model_name, tokenizer, auto_model = deep_seek_coder_model_define()
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_deep_seek_coder(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
        elif ml_technique == "codellama":
            with torch.no_grad():
                preds, category_token_map, top_tokens_per_test = give_test_data_in_chunks_codellama(X_test, tokenizer, model, batch_size, device, project_group, test_y.numpy(), ml_technique)
        else:
            print('no model name found')
        predictions_per_project_group[f"Fold_{project_group}"] = preds
        tokens_per_project_group[f"Fold_{project_group}"] = top_tokens_per_test
        ground_truth_per_project_group[f"Fold_{project_group}"] = test_y
        Org_test_per_project_group[f"Fold_{project_group}"] = X_test

        # Merge tokens from the current project_group into the global category-token map
        for category, tokens in category_token_map.items():
            if category not in global_category_token_map:
                global_category_token_map[category] = []  # Initialize list if category not present
            global_category_token_map[category].extend(tokens)  # Append tokens from current project_group

        cr=classification_report(test_y, preds)
        print(type(cr))
        parse_cr(cr, technique, str(project_group))
    
        with open(where_data_comes+"-result/classification_report_"+str(project_group)+"project_groups_"+str(project_group), "a") as file:
            file.write("Fold="+str(project_group)+"\n")
            file.write(cr)
            file.write("\n")
    
        cm = confusion_matrix(test_y, preds)
        #print(cm)
    	
        with open(where_data_comes+"-result/confusion_matrix_"+str(project_group)+"project_groups_"+str(project_group), "a") as file:
            file.write("Fold="+str(project_group)+"\n")
            file.write(np.array2string(cm))
            file.write("\n")
    
        #tn, fp, fn, tp = confusion_matrix(test_y, preds, labels=[0, 1]).ravel()
        #TN = TN + tn
        #FP = FP + fp
        #FN = FN + fn
        #TP = TP + tp
        print("delete model")
        del model
        torch.cuda.empty_cache()
    
        #project_group = project_group+1

    #exit()
    #**Merging & Saving is done AFTER the loop**
    '''df_predictions = pd.DataFrame.from_dict(predictions_per_project_group, orient="index").transpose()
    df_tokens = pd.DataFrame.from_dict(tokens_per_project_group, orient="index").transpose()
    
    
    # Rename columns
    df_predictions.columns = [f"Predictions_{col}" for col in df_predictions.columns]
    df_tokens.columns = [f"Tokens_{col}" for col in df_tokens.columns]
    
    # Merge both DataFrames
    df_combined = pd.concat([df_predictions, df_tokens], axis=1)
    
    # Save to CSV
    df_combined.to_csv(where_data_comes+"-result/"+ml_technique+".csv", index=False)    
    print("\nPredictions and tokens saved to llama.csv")'''
    # Initialize empty list to store reshaped data
    reshaped_data = []
    
    # Iterate over each fold
    for fold in predictions_per_project_group.keys():  # Example: "Fold_1", "Fold_2", ...
        preds = predictions_per_project_group[fold]
        tokens = tokens_per_project_group[fold]
        ground_truths = ground_truth_per_project_group[fold]
        org_test = Org_test_per_project_group[fold]
    
        # Iterate over all samples in this fold
        for test_code, pred, token_list, gt in zip(org_test, preds, tokens, ground_truths):
            reshaped_data.append({
                "test_code": test_code,
                "Prediction": pred,
                "Ground_Truth": int(gt.item()) if isinstance(gt, torch.Tensor) else int(gt),
                "Token_List": token_list
            })
    
    # Convert reshaped data to DataFrame
    df_final = pd.DataFrame(reshaped_data)
    
    # Save to CSV
    csv_path = f"{where_data_comes}-result/{ml_technique}.csv"
    df_final.to_csv(csv_path, index=False)
    
    print("\nPredictions and tokens saved to", csv_path)
    exit()


    top_10_tokens_per_category = {}
    for category, tokens in global_category_token_map.items():
        token_counts = Counter(tokens).most_common(10)  # Get top-10 most frequent tokens
        top_10_tokens_per_category[category] = token_counts  # Store as (token, count) pairs

    # Convert to DataFrame for better visualization
    df_token_per_cat = pd.DataFrame.from_dict(
        {category: dict(tokens) for category, tokens in top_10_tokens_per_category.items()},
        orient="index"
    ).transpose()
    
    #df_token_per_cat = pd.DataFrame.from_dict(top_5_tokens_per_category, orient='index').transpose()
    # Display result
    # Print the result in a readable format
    print("\nTop-10 Tokens Per Category:")
    for category, tokens in top_10_tokens_per_category.items():
        #print(f"Category {category}: {tokens}")
        print(f"Category {category}:")
        for token, count in tokens:
            print(f"  - {token}: {count}")

def initialize_environment(seed_value):
    """Initializes the environment by setting the seed and configuring logging."""
    set_seed(seed_value)  # Set the seed for reproducibility
    setup_logging()  # Setup standardized logging

if __name__ == "__main__":
    dataset_path = sys.argv[1]
    model_weights_path = sys.argv[2]
    results_file = sys.argv[3]
    data_name_dir = sys.argv[4]
    technique = sys.argv[5]
    initialize_environment(42)
    run_experiment(dataset_path, model_weights_path, results_file, data_name_dir, technique)
