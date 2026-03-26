# Needed raw_data_rq3.csv and module_ids.csv
# Expected columns in raw_data_rq3.csv:
# 'slug', 'module', 'TDRepro_GPT_failed_within_100_runs', 'TDRepro_GPT_find_config_time', 'TDRepro_GPT_100_runs_time', 'Token-length-of-the-prompt by TDRepro', 'Rerun_failure_counts_within10k_reruns', 'time_10k_reruns', 'time_to_run_in_isolation'
# 
# Expected columns in module_ids.csv:
# 'slug', 'module', 'Module ID'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os


os.makedirs('plot_time', exist_ok=True)


# --- 1. Load and Merge Data ---
df = pd.read_csv('raw.csv')

# in df fill 0 the empty cell for TDRepro_GPT_failed_within_100_runs and Rerun_failure_counts_within10k_reruns columns (since they represent failure counts, and empty likely means 0 failures)
df['TDRepro_GPT_failed_within_100_runs'] = df['TDRepro_GPT_failed_within_100_runs'].fillna(0)
df['Rerun_failure_counts_within10k_reruns'] = df['Rerun_failure_counts_within10k_reruns'].fillna(0)

mod_mapping = pd.read_csv('module_ids.csv')

# Merge to get "Module ID" into your main dataframe
df = df.merge(mod_mapping[['slug', 'module', 'Module ID']], on=['slug', 'module'], how='left')

# Filter for reproducible tests
cond_td = df['TDRepro_GPT_failed_within_100_runs'] > 0
cond_rerun = df['Rerun_failure_counts_within10k_reruns'] > 0
df = df[cond_td & cond_rerun].copy()

# --- 2. Constants ---
machine_cost_per_hour = 0.97376 #m8a.4xlarge instance in AWS
machine_cost_per_second = machine_cost_per_hour / 3600
llm_cost_per_1M = 2.50

N_vals = np.arange(1, 51)

grouped = list(df.groupby('Module ID'))

# --- 4. Plotting Loop ---
for i, (module_id, group_df) in enumerate(grouped):
    # if not module_id == 'M2':
    #     continue

    # if i >= rows * cols: break
    # ax = axes_flat[i]
    records = []
    
    for _, row in group_df.iterrows():
        # TDRepro
        td_failures = row['TDRepro_GPT_failed_within_100_runs']
        td_p = td_failures / 100
        td_find = row['TDRepro_GPT_find_config_time']
        td_rerun_time = row['TDRepro_GPT_100_runs_time']
        td_time_per_run = td_rerun_time / 100
        td_prompt_tokens = row['Token-length-of-the-prompt by TDRepro']

        # Flakerake
        # flake_failures = row['Flakerake_failed_within_100_runs']
        # flake_p = flake_failures / 100
        # flake_find = row['Flakerake_find_config_time']
        # flake_rerun_time = row['Flakerake_100_runs_time']
        # flake_time_per_run = flake_rerun_time / 100

        # Reruns
        rerun_failures = row['Rerun_failure_counts_within10k_reruns']
        rerun_p = rerun_failures / 10000
        rerun_time_10k = row['time_10k_reruns']
        rerun_time_per_run = rerun_time_10k / 10000

        time_in_isolation = row['time_to_run_in_isolation'] # time to run the test once in isolation

        for N in N_vals:
            # TDRepro expected runs, time, money
            exp_runs_td = N / td_p
            exp_time_td_non_normal = td_find + exp_runs_td * td_time_per_run
            exp_time_td = exp_time_td_non_normal / time_in_isolation
            # prompt_cost = (td_prompt_tokens / 1000000) * llm_cost_per_1M
            # machine_cost_td = exp_time_td * machine_cost_per_second
            # money_cost_td = prompt_cost + machine_cost_td

            # Flakerake
            # exp_runs_flake = N / flake_p
            # exp_time_flake_non_normal = flake_find + exp_runs_flake * flake_time_per_run
            # exp_time_flake = exp_time_flake_non_normal / time_in_isolation
            # money_cost_flake = exp_time_flake * machine_cost_per_second

            # Reruns
            exp_runs_rerun = N / rerun_p
            exp_time_rerun_non_normal = exp_runs_rerun * rerun_time_per_run
            exp_time_rerun = exp_time_rerun_non_normal / time_in_isolation
            # money_cost_rerun = exp_time_rerun * machine_cost_per_second

            records.append({'N': N, 'Approach': 'TDRepro', 'Time_Cost': exp_time_td})
            # records.append({'N': N, 'Approach': 'Flakerake', 'Money_Cost': money_cost_flake})
            records.append({'N': N, 'Approach': 'Isolated Reruns', 'Time_Cost': exp_time_rerun})

    
    result_df = pd.DataFrame.from_records(records)
    result_df.to_csv('time_costs_all_tests.csv', index=False)

    # Aggregate (mean time cost)
    agg = result_df.groupby(['Approach', 'N'])['Time_Cost'].mean().reset_index()

    marker_dict = {'TDRepro': 'o', 'Isolated Reruns': 's'}
    color_dict = {'TDRepro': '#1f78b4', 'Isolated Reruns': '#ff7f0e'}

    # plt.figure(figsize=(9, 7))
    sns.set(style="whitegrid", font_scale=1.0)
    for approach in agg['Approach'].unique():
        subset = agg[agg['Approach'] == approach]
        plt.plot(subset['N'], subset['Time_Cost'],
                label=approach,
                marker=marker_dict.get(approach, 'o'),
                color=color_dict.get(approach, None),
                markersize=3,
                linewidth=2)
    #  # Bottom-right Module Label (like "Module: M10")
    plt.text(0.95, 0.01, f"Module: {module_id}", 
                transform=plt.gca().transAxes, fontsize=12, 
                verticalalignment='bottom', horizontalalignment='right')
    plt.yscale('log')
    plt.xlabel('Desired Reproduction Count (N)')
    plt.ylabel('Normalized Average Time Cost (Seconds, Log Scale)')
    plt.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(f'plot_time/time_{module_id}.pdf')
    # plt.show()
    plt.close()
