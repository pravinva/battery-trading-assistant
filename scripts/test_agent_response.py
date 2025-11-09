#!/usr/bin/env python3
"""
Test what the agent actually returns - simulate agent.invoke()
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent components
import importlib.util
spec = importlib.util.spec_from_file_location(
    "agent_dev", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "02_agent_development_local.py")
)
agent_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_dev)

agent = agent_dev.agent
query_genie = agent_dev.query_genie

print("=" * 80)
print("Testing Agent Response")
print("=" * 80)

# Test question
question = "What is the highest hourly revenue for GANNBG1 by day? Show the date and maximum hourly revenue for each day."

print(f"\nQuestion: {question}")

# Simulate what Streamlit does - call the agent
from langchain_core.messages import SystemMessage, HumanMessage

print("\nCalling agent.invoke()...")
try:
    response = agent.invoke({
        "messages": [
            SystemMessage(content=agent_dev.SYSTEM_PROMPT),
            HumanMessage(content=question)
        ]
    })
    
    print(f"\n✓ Agent response received")
    print(f"  Response type: {type(response)}")
    print(f"  Response keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
    
    # Get the last message (assistant's response)
    if isinstance(response, dict) and 'messages' in response:
        messages = response['messages']
        print(f"  Number of messages: {len(messages)}")
        
        # Find the last assistant message
        assistant_response = None
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                assistant_response = msg.content
                break
        
        if assistant_response:
            print(f"\n  Assistant response length: {len(assistant_response)} characters")
            print(f"  Contains PLOTLY_CHART_START: {'PLOTLY_CHART_START' in assistant_response}")
            
            if 'PLOTLY_CHART_START' in assistant_response:
                # Find the marker
                start_pos = assistant_response.find('[PLOTLY_CHART_START]')
                end_pos = assistant_response.find('[PLOTLY_CHART_END]')
                if end_pos > start_pos:
                    marker_text = assistant_response[start_pos:end_pos+len('[PLOTLY_CHART_END]')]
                    print(f"\n  Chart marker found!")
                    print(f"  Marker length: {len(marker_text)}")
                    print(f"  First 300 chars: {marker_text[:300]}")
                else:
                    print(f"\n  ⚠️ Chart marker start found but no end marker")
            else:
                print(f"\n  ✗ No chart markers in response")
                # Show last 500 chars to see what agent returned
                print(f"\n  Last 500 chars of response:")
                print(f"  {assistant_response[-500:]}")
        else:
            print(f"\n  ✗ No assistant response found")
            # Show all messages
            for idx, msg in enumerate(messages):
                print(f"  Message {idx}: {type(msg).__name__}")
                if hasattr(msg, 'content'):
                    print(f"    Content: {str(msg.content)[:100]}")
    
except Exception as e:
    print(f"\n✗ Error calling agent: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)

