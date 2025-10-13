import pandas as pd
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

# calculate average test_run_time_in_isolation:     time_in_isolation = row['time_to_run_in_isolation']
average_time_in_isolation = df['time_to_run_in_isolation'].mean()

# --- TDRepro averages ---
average_time_td_find = df['TDRepro_GPT_find_config_time'].mean()
td_failures_average = df['TDRepro_GPT_failed_within_100_runs'].mean()
td_failure_rate = td_failures_average / 100
td_time_100_runs_average = df['TDRepro_GPT_100_runs_time'].mean()
td_time_per_run = td_time_100_runs_average / 100
td_prompt_tokens_average = df['Token-length-of-the-prompt by TDRepro'].mean()
td_prompt_cost = (td_prompt_tokens_average / 1000000) * llm_cost_per_1M

# --- Rerun averages ---
rerun_failures_average = df['Rerun_failure_counts_within10k_reruns'].mean()
rerun_failure_rate = rerun_failures_average / 10000
rerun_time_10k_average = df['time_10k_reruns'].mean()
rerun_time_per_run = rerun_time_10k_average / 10000


# print all the averages
# print(f"Average time to run in isolation: {average_time_in_isolation:.2ff} seconds")
print(f"--- TDRepro Averages ---")
print(f"Average time to find config: {average_time_td_find:.2f} seconds")
print(f"Average failures in 100 runs: {td_failures_average:.2f}")
print(f"TDRepro failure rate: {td_failure_rate:.4f}")
print(f"Average time for 100 runs: {td_time_100_runs_average:.2f} seconds")
print(f"Average time per run: {td_time_per_run:.2f} seconds")
print(f"Average prompt tokens: {td_prompt_tokens_average:.2f}")
print(f"prompt cost per: ${td_prompt_cost:.4f}")

print(f"--- Rerun Averages ---")
print(f"Average failures in 10k runs: {rerun_failures_average:.2f}")
print(f"Rerun failure rate: {rerun_failure_rate:.4f}")
print(f"Average time for 10k runs: {rerun_time_10k_average:.2f} seconds")
print(f"Average time per run: {rerun_time_per_run:.2f} seconds")

# --- For N failures, expected cost ---
N_vals = range(1, 51)
td_costs = []
rerun_costs = []

for N in N_vals:
    # TDRepro
    exp_runs_td = N / td_failure_rate
    exp_time_td = average_time_td_find + exp_runs_td * td_time_per_run
    exp_money_td = td_prompt_cost + exp_time_td * machine_cost_per_second
    td_costs.append(exp_money_td)

    # Rerun
    exp_runs_rerun = N / rerun_failure_rate
    exp_time_rerun = exp_runs_rerun * rerun_time_per_run
    exp_money_rerun = exp_time_rerun * machine_cost_per_second
    rerun_costs.append(exp_money_rerun)

# --- Plot ---
plt.figure(figsize=(9, 7))
plt.plot(N_vals, td_costs, label="TDRepro_GPT", marker='o')
plt.plot(N_vals, rerun_costs, label="Reruns", marker='s')
plt.yscale('log')
plt.xlabel('Desired Reproduction Count (N)')
plt.ylabel('Average Money Cost (USD)')
plt.title('Expected Average Money Cost to N Failures')
plt.legend()
plt.tight_layout()
plt.savefig('avg_money_cost_avg_first.pdf')
plt.show()