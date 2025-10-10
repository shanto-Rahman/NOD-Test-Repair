#source /scratch/tbaral/oopsla26/NOD-Test-Repair/py10/bin/activate

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('raw_data_rq3.csv')

# Filter for tests that were reproduced by both approaches
cond_td = df['TDRepro_GPT_failed_within_100_runs'] > 0
cond_rerun = df['Rerun_failure_counts_within10k_reruns'] > 0
df = df[cond_td & cond_rerun].copy()

print(f"Number of tests reproduced by both approaches: {len(df)}")

machine_cost_per_hour = 0.97376 # m8a.4xlarge instance in AWS
machine_cost_per_second = machine_cost_per_hour / 3600
llm_cost_per_1M = 2.50

N_vals = np.arange(1, 51)
records = []

for idx, row in df.iterrows():
    # TDRepro
    td_failures = row['TDRepro_GPT_failed_within_100_runs']
    td_failure_rate = td_failures / 100
    td_find = row['TDRepro_GPT_find_config_time']
    td_rerun_time = row['TDRepro_GPT_100_runs_time']
    td_time_per_run = td_rerun_time / 100
    td_prompt_tokens = row['Token-length-of-the-prompt by TDRepro']
    td_prompt_cost = (td_prompt_tokens / 1000000) * llm_cost_per_1M

    # Rerun
    rerun_failures = row['Rerun_failure_counts_within10k_reruns']
    rerun_failure_rate = rerun_failures / 10000
    rerun_time_10k = row['time_10k_reruns']
    rerun_time_per_run = rerun_time_10k / 10000

    time_in_isolation = row['time_to_run_in_isolation']

    for N in N_vals:
        # TDRepro
        exp_runs_td = N / td_failure_rate
        exp_time_td = td_find + exp_runs_td * td_time_per_run
        exp_money_td = td_prompt_cost + exp_time_td * machine_cost_per_second

        # Rerun
        exp_runs_rerun = N / rerun_failure_rate
        exp_time_rerun = exp_runs_rerun * rerun_time_per_run
        exp_money_rerun = exp_time_rerun * machine_cost_per_second

        records.append({'test': row['test'], 'N': N, 'Approach': 'TDRepro_GPT', 'Money_Cost': exp_money_td})
        records.append({'test': row['test'], 'N': N, 'Approach': 'Reruns', 'Money_Cost': exp_money_rerun})

result_df = pd.DataFrame.from_records(records)

# Aggregate: mean across tests for each N and approach
agg = result_df.groupby(['Approach', 'N'])['Money_Cost'].mean().reset_index()

# --- Plot ---
plt.figure(figsize=(9, 7))
for approach in agg['Approach'].unique():
    subset = agg[agg['Approach'] == approach]
    plt.plot(subset['N'], subset['Money_Cost'],
             label=approach,
             marker='o' if approach=='TDRepro_GPT' else 's')
plt.yscale('log')
plt.xlabel('Desired Reproduction Count (N)')
plt.ylabel('Average Money Cost (USD)')
plt.title('Expected Average Money Cost to N Failures')
plt.legend()
plt.tight_layout()
plt.savefig('avg_money_cost_avg_last.pdf')
plt.show()