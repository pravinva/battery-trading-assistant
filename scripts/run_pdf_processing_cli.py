#!/usr/bin/env python3
"""
Run PDF Processing via Databricks Jobs API
Usage: python3 run_pdf_processing_cli.py
"""

from databricks.sdk import WorkspaceClient
import time

def run_pdf_processing():
    """Run PDF processing notebook via Jobs API"""
    w = WorkspaceClient()
    
    job_id = 775038827791218
    notebook_path = "/Users/pravin.varma@databricks.com/battery-trading/process_pdf_index"
    
    print("🚀 Starting PDF Processing Job...")
    print(f"   Job ID: {job_id}")
    print(f"   Notebook: {notebook_path}")
    
    # Run the job
    run = w.jobs.run_now(job_id=job_id)
    run_id = run.run_id
    
    print(f"\n✅ Job started! Run ID: {run_id}")
    print("\n⏳ Monitoring progress...")
    
    # Monitor progress
    for i in range(60):  # Check for up to 10 minutes
        time.sleep(10)
        run_status = w.jobs.get_run(run_id=run_id)
        state = run_status.state.life_cycle_state.value
        
        if i % 3 == 0:  # Print every 30 seconds
            print(f"   [{i*10}s] State: {state}")
        
        if state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            result = run_status.state.result_state.value if run_status.state.result_state else "N/A"
            print(f"\n📊 Final Status:")
            print(f"   State: {state}")
            print(f"   Result: {result}")
            
            # Check task results
            if hasattr(run_status, 'tasks') and run_status.tasks:
                for task in run_status.tasks:
                    task_state = task.state.life_cycle_state.value if hasattr(task.state, 'life_cycle_state') else "UNKNOWN"
                    task_result = task.state.result_state.value if hasattr(task.state, 'result_state') and task.state.result_state else "N/A"
                    print(f"   Task {task.task_key}: {task_state} - {task_result}")
            
            if state == "TERMINATED" and result == "SUCCESS":
                print("\n✅ PDF Processing Completed Successfully!")
                return True
            else:
                print("\n❌ Job failed or was skipped")
                return False
    
    print("\n⏱️  Job still running after 10 minutes. Check Databricks UI for final status.")
    return None

if __name__ == "__main__":
    success = run_pdf_processing()
    exit(0 if success else 1)

