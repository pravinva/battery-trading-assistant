# How to View Evaluation Results in Databricks MLflow UI

## Quick Access

1. **Open Databricks Workspace** → Go to your workspace URL

2. **Navigate to MLflow**:
   - Click **"Experiments"** in the left sidebar (or **"ML"** → **"Experiments"**)
   - OR go directly to: `https://<your-workspace>.cloud.databricks.com/#mlflow/experiments`

3. **Find Your Experiment**:
   - Look for: **`/Users/pravin.varma@databricks.com/battery_agent_evaluation`**
   - It should appear in the experiments list
   - If you don't see it, try:
     - Clicking "All Experiments" or "My Experiments"
     - Using the search box to search for "battery_agent_evaluation"

4. **Open the Experiment**:
   - Click on the experiment name
   - You'll see all runs listed

5. **View Run Details**:
   - Click on the run named **`battery_agent_evaluation_local`**
   - You'll see tabs:
     - **Metrics**: Success rate, total questions, etc.
     - **Parameters**: Evaluation type, agent type, etc.
     - **Artifacts**: CSV files with detailed results

## Alternative: Direct URL

If you know your workspace URL, you can go directly to:
```
https://<your-workspace>.cloud.databricks.com/#mlflow/experiments/967855982061769630
```

(Replace `<your-workspace>` with your actual workspace name)

## Experiment Details

- **Experiment Name**: `/Users/pravin.varma@databricks.com/battery_agent_evaluation`
- **Experiment ID**: `967855982061769630`
- **Run Name**: `battery_agent_evaluation_local`

## If You Still Can't See It

1. **Check Permissions**: Ensure you're logged in as `pravin.varma@databricks.com`
2. **Check Workspace**: Make sure you're in the correct Databricks workspace
3. **Refresh**: Try refreshing the Experiments page
4. **Search**: Use the search box in the Experiments page to search for "battery_agent_evaluation"

## Verify Experiment Exists

Run this command locally to verify:
```bash
python3 -c "
import mlflow
mlflow.set_registry_uri('databricks-uc')
exp = mlflow.get_experiment_by_name('/Users/pravin.varma@databricks.com/battery_agent_evaluation')
print(f'Experiment: {exp.name}')
print(f'Experiment ID: {exp.experiment_id}')
"
```

If this works, the experiment exists and should be visible in the UI.

