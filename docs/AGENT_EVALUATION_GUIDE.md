# Agent Evaluation Guide

## Overview

Agent evaluation measures the quality and accuracy of the Battery Trading Assistant using MLflow's Agent Evaluation framework. This guide explains how to run evaluation and where to view the results.

## Evaluation Metrics

The evaluation measures three key aspects:

1. **Retrieval Precision** (`retrieval/llm_judged/chunk_relevance/precision`)
   - Measures how relevant the retrieved documentation chunks are to the question
   - Range: 0.0 to 1.0 (higher is better)
   - Evaluates Vector Search quality

2. **Response Relevance** (`response/llm_judged/relevance_to_input/rating`)
   - Measures how well the agent's answer addresses the user's question
   - Range: 1-5 scale (higher is better)
   - Evaluates overall answer quality

3. **Groundedness** (`response/llm_judged/groundedness/rating`)
   - Measures how well the answer is supported by retrieved data
   - Range: 1-5 scale (higher is better)
   - Evaluates whether answers are factually grounded

## Running Evaluation

### Option 1: Using Databricks Notebook

1. **Upload the evaluation notebook:**
   ```bash
   databricks workspace import notebooks/03_agent_evaluation.py /Users/<your_email>/battery-trading/03_agent_evaluation
   ```

2. **Get your agent run ID:**
   - First, log your agent to MLflow (see `notebooks/02_agent_development.py`)
   - Copy the run ID from the output

3. **Update the notebook:**
   - Open `03_agent_evaluation.py` in Databricks
   - Set `AGENT_RUN_ID = "<your_run_id>"`

4. **Run the notebook:**
   - Executes evaluation on 8 test questions
   - Creates evaluation dataset
   - Runs MLflow evaluation
   - Displays results

### Option 2: Local Evaluation Script

Create a local evaluation script (similar to the notebook):

```python
import mlflow
import pandas as pd

# Set your logged agent run ID
AGENT_RUN_ID = "<your_run_id>"
AGENT_MODEL_URI = f"runs:/{AGENT_RUN_ID}/agent"

# Create evaluation dataset
eval_data = [
    {
        "request": "What is the current SoC for RESS2?",
        "expected_response": "Should query battery_telemetry and provide current SoC",
        "query_type": "structured"
    },
    # ... more questions
]

eval_df = pd.DataFrame(eval_data)

# Run evaluation
with mlflow.start_run(run_name="battery_agent_evaluation"):
    eval_results = mlflow.evaluate(
        model=AGENT_MODEL_URI,
        data=eval_df,
        model_type="databricks-agent",
    )
    
    print("Evaluation Results:")
    print(f"  - Retrieval precision: {eval_results.metrics.get('retrieval/llm_judged/chunk_relevance/precision', 'N/A')}")
    print(f"  - Response quality: {eval_results.metrics.get('response/llm_judged/relevance_to_input/rating', 'N/A')}")
    print(f"  - Groundedness: {eval_results.metrics.get('response/llm_judged/groundedness/rating', 'N/A')}")
```

## Viewing Evaluation Results

### 1. MLflow UI (Primary Method)

**Access MLflow UI:**
1. Go to your Databricks workspace
2. Click **"Experiments"** in the sidebar (or **"MLflow"**)
3. Navigate to your experiment: `/Users/<your_email>/battery_agent_dev`
4. Find the evaluation run: `battery_agent_evaluation`

**View Metrics:**
- Click on the evaluation run
- Go to **"Metrics"** tab
- See:
  - `retrieval/llm_judged/chunk_relevance/precision`
  - `response/llm_judged/relevance_to_input/rating`
  - `response/llm_judged/groundedness/rating`

**View Detailed Results:**
- Go to **"Artifacts"** tab
- Open `eval_results_table.json` or `eval_results_table.parquet`
- See per-question evaluation results

### 2. Evaluation Results Table

The evaluation creates a detailed table (`eval_results`) with:
- **request**: The question asked
- **response**: Agent's actual response
- **retrieval/chunk_relevance**: Relevance score for each retrieved chunk
- **response/relevance_to_input**: How relevant the answer is
- **response/groundedness**: How well-grounded the answer is
- **query_type**: Type of query (structured/unstructured/hybrid)

### 3. Programmatic Access

```python
# After running evaluation
eval_results_df = eval_results.tables["eval_results"]

# View summary statistics
print(eval_results_df.describe())

# Filter by query type
structured_results = eval_results_df[eval_results_df['query_type'] == 'structured']

# View per-question scores
for idx, row in eval_results_df.iterrows():
    print(f"Question: {row['request']}")
    print(f"  Relevance: {row['response/llm_judged/relevance_to_input/rating']}")
    print(f"  Groundedness: {row['response/llm_judged/groundedness/rating']}")
```

## Evaluation Dataset

The default evaluation dataset includes 8 questions covering:

- **Structured queries** (4): SQL/data queries
  - Current SoC lookup
  - Revenue analysis
  - Battery status
  - Performance comparison

- **Unstructured queries** (3): Documentation/RAG queries
  - Throughput calculation explanation
  - PI integration architecture
  - Data age restrictions

- **Hybrid queries** (1): Combines both
  - SoC limits + availability impact

## Current Status

**Note**: Evaluation requires the agent to be logged to MLflow first. 

**To check if evaluation has been run:**
1. Go to MLflow UI in Databricks
2. Look for experiment: `/Users/<your_email>/battery_agent_dev`
3. Check for run named: `battery_agent_evaluation`

**If evaluation hasn't been run:**
1. First log your agent to MLflow (see `notebooks/02_agent_development.py`)
2. Then run the evaluation notebook (`notebooks/03_agent_evaluation.py`)

## Customizing Evaluation

### Add More Questions

Edit the `eval_data` list in `03_agent_evaluation.py`:

```python
eval_data.append({
    "request": "Your test question here",
    "expected_response": "What you expect the agent to do",
    "query_type": "structured"  # or "unstructured" or "hybrid"
})
```

### Focus on Specific Metrics

You can filter results by query type to see:
- How well structured queries perform
- How well unstructured/RAG queries perform
- How well hybrid queries combine both

## Troubleshooting

**Issue**: "Model not found" error
- **Fix**: Ensure agent is logged to MLflow first
- **Check**: Verify `AGENT_RUN_ID` is correct

**Issue**: "databricks-agent model type not supported"
- **Fix**: Ensure you're using latest `databricks-agents` package
- **Check**: `pip install --upgrade databricks-agents mlflow`

**Issue**: Evaluation takes too long
- **Cause**: Each question invokes the agent (calls Genie, Vector Search, etc.)
- **Fix**: Reduce number of questions or run in background

## Next Steps

After evaluation:
1. Review metrics in MLflow UI
2. Identify low-scoring questions
3. Improve agent prompts or tools based on results
4. Re-run evaluation to measure improvements
5. Set up evaluation as part of CI/CD pipeline

## References

- [MLflow Agent Evaluation](https://docs.databricks.com/en/machine-learning/mlflow/agent-evaluation.html)
- [Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/tutorials/agent-framework-notebook)

