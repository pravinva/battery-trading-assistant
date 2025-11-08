# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 3: Battery Agent Evaluation
# MAGIC 
# MAGIC Evaluate agent performance using Mosaic AI Agent Evaluation

# COMMAND ----------
# MAGIC %pip install databricks-agents mlflow pandas

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import mlflow
import pandas as pd
from databricks import agents

# COMMAND ----------
# Set your logged agent run ID from previous notebook
AGENT_RUN_ID = "<paste_run_id_from_notebook_02>"  # Update this!
AGENT_MODEL_URI = f"runs:/{AGENT_RUN_ID}/agent"

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3.1 Create Evaluation Dataset

# COMMAND ----------
# Evaluation questions covering different query types
eval_data = [
    {
        "request": "What is the current SoC for RESS2?",
        "expected_response": "Should query battery_telemetry and provide current SoC in MWh and percentage",
        "query_type": "structured"
    },
    {
        "request": "How is throughput calculated for Darlington Point batteries?",
        "expected_response": "Should search documentation and explain the 7.5 hour window calculation formula",
        "query_type": "unstructured"
    },
    {
        "request": "What's the revenue for GANNBG1 in the last 24 hours?",
        "expected_response": "Should query battery_dispatch and calculate total revenue with breakdown",
        "query_type": "structured"
    },
    {
        "request": "Explain the PI system integration architecture",
        "expected_response": "Should retrieve documentation about PI integration and data flow",
        "query_type": "unstructured"
    },
    {
        "request": "What are the SoC limits for DPNTBESS and how do they affect availability?",
        "expected_response": "Should combine asset info query with documentation search about restrictions",
        "query_type": "hybrid"
    },
    {
        "request": "Show me the current status of all Wooreen batteries",
        "expected_response": "Should query GANNBG1 and GANNBL1 telemetry with current SoC and capabilities",
        "query_type": "structured"
    },
    {
        "request": "What happens when battery telemetry reading is older than 10 minutes?",
        "expected_response": "Should search docs about data age restrictions on availability",
        "query_type": "unstructured"
    },
    {
        "request": "Compare revenue performance of RESS2 vs DPNTBESS over last 24 hours",
        "expected_response": "Should query revenue for both batteries and provide comparison",
        "query_type": "structured"
    },
]

eval_df = pd.DataFrame(eval_data)
print(f"✅ Created evaluation dataset with {len(eval_df)} questions")
print(f"\nQuery type distribution:")
print(eval_df['query_type'].value_counts())

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3.2 Run Agent Evaluation

# COMMAND ----------
# Run evaluation
with mlflow.start_run(run_name="battery_agent_evaluation"):
    
    # Evaluate agent
    eval_results = mlflow.evaluate(
        model=AGENT_MODEL_URI,
        data=eval_df,
        model_type="databricks-agent",
    )
    
    print("✅ Evaluation complete!")
    print(f"\nEvaluation Results:")
    print(f"  - Retrieval precision: {eval_results.metrics.get('retrieval/llm_judged/chunk_relevance/precision', 'N/A')}")
    print(f"  - Response quality: {eval_results.metrics.get('response/llm_judged/relevance_to_input/rating', 'N/A')}")
    print(f"  - Groundedness: {eval_results.metrics.get('response/llm_judged/groundedness/rating', 'N/A')}")

# COMMAND ----------
# View detailed results
eval_results_df = eval_results.tables["eval_results"]
display(eval_results_df)

# COMMAND ----------
print("=" * 80)
print("AGENT EVALUATION COMPLETE")
print("=" * 80)
print(f"\n✅ View evaluation results in MLflow UI")
print(f"\n➡️  Next Step: Run notebook 04_deployment.py")

