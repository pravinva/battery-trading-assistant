#!/usr/bin/env python3
"""
Local Agent Evaluation Script
Evaluates the Battery Trading Assistant agent performance
Logs results to MLflow in Databricks workspace
"""
import os
import sys
import warnings
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import mlflow
from langchain_core.messages import HumanMessage, SystemMessage

# Configure MLflow to use Databricks workspace (not local)
mlflow.set_registry_uri("databricks-uc")
# Set experiment to your workspace path
EXPERIMENT_NAME = "/Users/pravin.varma@databricks.com/battery_agent_evaluation"
mlflow.set_experiment(EXPERIMENT_NAME)
print(f"✅ MLflow experiment set to: {EXPERIMENT_NAME}")
print("   (Results will appear in Databricks MLflow UI, not local mlruns)\n")

# Import agent from local script
print("=" * 80)
print("Battery Trading Agent Evaluation")
print("=" * 80)

# Import agent module
import importlib.util
agent_script_path = Path(__file__).parent / "02_agent_development_local.py"
spec = importlib.util.spec_from_file_location("agent_module", agent_script_path)
agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_module)

agent = agent_module.agent
SYSTEM_PROMPT = agent_module.SYSTEM_PROMPT

print("✅ Agent loaded successfully\n")

# Create evaluation dataset
print("=" * 80)
print("Creating Evaluation Dataset")
print("=" * 80)

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
print()

# Run evaluation with MLflow logging
print("=" * 80)
print("Running Evaluation")
print("=" * 80)

# Start MLflow run
with mlflow.start_run(run_name="battery_agent_evaluation_local"):
    print(f"📊 MLflow Run ID: {mlflow.active_run().info.run_id}")
    print(f"📊 Experiment: {EXPERIMENT_NAME}\n")
    
    results = []
    
    for idx, row in eval_df.iterrows():
        question = row['request']
        query_type = row['query_type']
        expected = row['expected_response']
        
        print(f"\n[{idx + 1}/{len(eval_df)}] Testing: {question}")
        print(f"  Type: {query_type}")
        print("  Running...", end=" ", flush=True)
        
        try:
            # Invoke agent
            response = agent.invoke({
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=question)
                ]
            })
            
            # Extract response
            assistant_response = response["messages"][-1].content
            
            # Check if response contains expected elements
            success_indicators = []
            
            if query_type == "structured":
                # Check for data indicators
                if any(keyword in assistant_response.lower() for keyword in ['mwh', 'mw', '%', 'soc', 'revenue', '$']):
                    success_indicators.append("Contains data")
                if any(keyword in assistant_response.lower() for keyword in ['ress2', 'dppntbess', 'gannbg1', 'gannbl1']):
                    success_indicators.append("Contains battery ID")
            elif query_type == "unstructured":
                # Check for explanation/documentation
                if len(assistant_response) > 100:
                    success_indicators.append("Detailed explanation")
                if any(keyword in assistant_response.lower() for keyword in ['throughput', 'pi', 'integration', 'calculation', 'process']):
                    success_indicators.append("Relevant content")
            elif query_type == "hybrid":
                # Check for both data and explanation
                if any(keyword in assistant_response.lower() for keyword in ['mwh', 'mw', '%', 'soc']):
                    success_indicators.append("Contains data")
                if len(assistant_response) > 150:
                    success_indicators.append("Combined response")
            
            # Store result
            result = {
                "question": question,
                "query_type": query_type,
                "expected": expected,
                "response": assistant_response,
                "response_length": len(assistant_response),
                "success_indicators": ", ".join(success_indicators) if success_indicators else "None",
                "status": "SUCCESS" if success_indicators else "NEEDS_REVIEW",
                "error": None
            }
            
            print(f"✅ ({len(success_indicators)} indicators)")
            
        except Exception as e:
            result = {
                "question": question,
                "query_type": query_type,
                "expected": expected,
                "response": None,
                "response_length": 0,
                "success_indicators": "None",
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Error: {str(e)[:100]}")
        
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Calculate metrics for MLflow
    total_questions = len(results_df)
    successful = len(results_df[results_df['status'] == 'SUCCESS'])
    needs_review = len(results_df[results_df['status'] == 'NEEDS_REVIEW'])
    errors = len(results_df[results_df['status'] == 'ERROR'])
    success_rate = (successful / total_questions) * 100 if total_questions > 0 else 0
    avg_response_length = results_df['response_length'].mean()
    
    # Calculate metrics by query type
    structured_success = len(results_df[(results_df['query_type'] == 'structured') & (results_df['status'] == 'SUCCESS')])
    unstructured_success = len(results_df[(results_df['query_type'] == 'unstructured') & (results_df['status'] == 'SUCCESS')])
    hybrid_success = len(results_df[(results_df['query_type'] == 'hybrid') & (results_df['status'] == 'SUCCESS')])
    
    # Log metrics to MLflow
    mlflow.log_metric("total_questions", total_questions)
    mlflow.log_metric("successful", successful)
    mlflow.log_metric("needs_review", needs_review)
    mlflow.log_metric("errors", errors)
    mlflow.log_metric("success_rate", success_rate)
    mlflow.log_metric("avg_response_length", avg_response_length)
    mlflow.log_metric("structured_success", structured_success)
    mlflow.log_metric("unstructured_success", unstructured_success)
    mlflow.log_metric("hybrid_success", hybrid_success)
    
    # Log evaluation dataset as artifact
    eval_df_path = "/tmp/evaluation_dataset.csv"
    eval_df.to_csv(eval_df_path, index=False)
    mlflow.log_artifact(eval_df_path, "evaluation_dataset")
    
    # Log results as artifact
    results_path = "/tmp/evaluation_results.csv"
    results_df.to_csv(results_path, index=False)
    mlflow.log_artifact(results_path, "evaluation_results")
    
    # Log parameters
    mlflow.log_param("evaluation_type", "local_agent_evaluation")
    mlflow.log_param("agent_type", "langgraph_react_agent")
    mlflow.log_param("query_types", ",".join(results_df['query_type'].unique()))
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("Evaluation Summary")
    print("=" * 80)
    
    print(f"\nTotal Questions: {total_questions}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Needs Review: {needs_review}")
    print(f"Errors: {errors}")
    
    print(f"\nBy Query Type:")
    for qtype in results_df['query_type'].unique():
        type_df = results_df[results_df['query_type'] == qtype]
        print(f"  {qtype}:")
        print(f"    Total: {len(type_df)}")
        print(f"    Success: {len(type_df[type_df['status'] == 'SUCCESS'])}")
        print(f"    Errors: {len(type_df[type_df['status'] == 'ERROR'])}")
    
    print(f"\nAverage Response Length: {avg_response_length:.0f} characters")
    print(f"Min: {results_df['response_length'].min()}, Max: {results_df['response_length'].max()}")
    
    print(f"\n✅ Metrics logged to MLflow:")
    print(f"   - Success Rate: {success_rate:.1f}%")
    print(f"   - Total Questions: {total_questions}")
    print(f"   - Successful: {successful}")
    print(f"   - Errors: {errors}")
    
    # Save results locally as well
    output_file = Path(__file__).parent.parent / "evaluation_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n✅ Results also saved locally to: {output_file}")
    
    # Show detailed results
    print("\n" + "=" * 80)
    print("Detailed Results")
    print("=" * 80)
    
    for idx, row in results_df.iterrows():
        print(f"\n[{idx + 1}] {row['question']}")
        print(f"    Type: {row['query_type']}")
        print(f"    Status: {row['status']}")
        print(f"    Indicators: {row['success_indicators']}")
        if row['response']:
            print(f"    Response Preview: {row['response'][:200]}...")
        if row['error']:
            print(f"    Error: {row['error']}")
    
    # Show errors if any
    errors_df = results_df[results_df['status'] == 'ERROR']
    if len(errors_df) > 0:
        print("\n" + "=" * 80)
        print("Errors Summary")
        print("=" * 80)
        for idx, row in errors_df.iterrows():
            print(f"\n[{idx + 1}] {row['question']}")
            print(f"    Error: {row['error']}")
    
    run_id = mlflow.active_run().info.run_id
    
    print("\n" + "=" * 80)
    print("Evaluation Complete")
    print("=" * 80)
    print(f"\n✅ View results in Databricks MLflow UI:")
    print(f"   Experiment: {EXPERIMENT_NAME}")
    print(f"   Run Name: battery_agent_evaluation_local")
    print(f"   Run ID: {run_id}")
    print(f"\n   Navigate to: Databricks UI → Experiments → {EXPERIMENT_NAME}")
    print(f"   → Click on run 'battery_agent_evaluation_local'")
    print(f"   → View Metrics tab for summary")
    print(f"   → View Artifacts tab for detailed results CSV")
