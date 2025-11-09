#!/usr/bin/env python3
"""
Test script to debug Plotly chart creation locally
This helps verify chart JSON doesn't contain binary data before using in Streamlit
"""

import sys
import os
import json

# Add parent directory to path to import the chart function
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the chart creation function
# Need to import the module dynamically since it starts with a number
import importlib.util
spec = importlib.util.spec_from_file_location(
    "agent_dev", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "02_agent_development_local.py")
)
agent_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_dev)
create_plotly_chart = agent_dev.create_plotly_chart

# Sample data similar to what Genie returns
# Format: [['date', 'revenue'], ...]
sample_query_data = [
    ['2011-01-26', '-709.5656379102695'],
    ['2011-11-22', '-129.73351960452032'],
    ['2012-09-17', '216.0369243251566'],
    ['2013-07-14', '340.80696277561196'],
    ['2014-05-10', '26.46256108629221'],
    ['2015-03-06', '50.14346535915815'],
    ['2015-12-31', '-532.9336927404264'],
    ['2016-10-26', '592.301981946919'],
    ['2017-08-22', '-561.3354429242221'],
    ['2018-06-18', '-189.69995270757553'],
]

# Column names from SQL result
columns = ['revenue_date', 'max_hourly_revenue']

# Test question
question = "What is the highest hourly revenue for GANNBG1 by day? Show the date and maximum hourly revenue for each day."

print("=" * 80)
print("Testing Chart Creation")
print("=" * 80)
print(f"\nQuestion: {question}")
print(f"\nSample data ({len(sample_query_data)} rows):")
for i, row in enumerate(sample_query_data[:5]):
    print(f"  {i+1}. {row}")
print(f"  ... ({len(sample_query_data) - 5} more rows)")
print(f"\nColumns: {columns}")

print("\n" + "=" * 80)
print("Creating Chart...")
print("=" * 80)

try:
    chart_data = create_plotly_chart(sample_query_data, columns, question)
    
    if chart_data:
        print(f"\n✓ Chart created successfully!")
        print(f"  Type: {chart_data['type']}")
        print(f"  Title: {chart_data.get('title', 'N/A')}")
        
        # Parse JSON to check structure
        chart_json_str = chart_data['json']
        chart_dict = json.loads(chart_json_str)
        
        print(f"\n✓ JSON parsed successfully!")
        print(f"  JSON length: {len(chart_json_str)} characters")
        
        # Check for binary data
        json_str = json.dumps(chart_dict, indent=2)
        has_binary = 'bdata' in json_str.lower()
        
        if has_binary:
            print("\n⚠️  WARNING: Binary data (bdata) found in JSON!")
            print("   This will not render properly in Streamlit.")
        else:
            print("\n✓ No binary data found - JSON is clean!")
        
        # Check structure
        print(f"\nChart structure:")
        print(f"  - Has 'data': {'data' in chart_dict}")
        print(f"  - Has 'layout': {'layout' in chart_dict}")
        
        if 'data' in chart_dict and len(chart_dict['data']) > 0:
            first_trace = chart_dict['data'][0]
            print(f"\n  First trace keys: {list(first_trace.keys())[:10]}...")
            
            # Check for x and y data
            if 'x' in first_trace:
                x_data = first_trace['x']
                print(f"  - Has 'x' data: {type(x_data)}")
                if isinstance(x_data, list):
                    print(f"    First 3 x values: {x_data[:3]}")
                else:
                    print(f"    x is not a list: {type(x_data)}")
            
            if 'y' in first_trace:
                y_data = first_trace['y']
                print(f"  - Has 'y' data: {type(y_data)}")
                if isinstance(y_data, list):
                    print(f"    First 3 y values: {y_data[:3]}")
                else:
                    print(f"    y is not a list: {type(y_data)}")
        
        # Save JSON to file for inspection
        output_file = "/tmp/chart_test_output.json"
        with open(output_file, 'w') as f:
            json.dump(chart_dict, f, indent=2)
        print(f"\n✓ Full JSON saved to: {output_file}")
        
        # Try to create a figure from the JSON to verify it works
        print("\n" + "=" * 80)
        print("Testing JSON Deserialization...")
        print("=" * 80)
        
        try:
            import plotly.graph_objects as go
            # Use from_json with the JSON string, or create figure directly from dict
            fig = go.Figure(chart_dict)
            print("✓ Successfully created Plotly figure from JSON!")
            print("  Chart can be rendered!")
            
            # Optionally show the chart (if in interactive environment)
            try:
                import plotly.io as pio
                # Save as HTML for viewing
                html_file = "/tmp/chart_test_output.html"
                fig.write_html(html_file)
                print(f"✓ Chart saved as HTML: {html_file}")
                print(f"  Open in browser: file://{html_file}")
            except Exception as e:
                print(f"  Could not save HTML: {e}")
                
        except Exception as e:
            print(f"✗ Failed to create figure from JSON: {e}")
            import traceback
            traceback.print_exc()
        
        # Show first 500 chars of JSON
        print("\n" + "=" * 80)
        print("JSON Preview (first 500 chars):")
        print("=" * 80)
        print(chart_json_str[:500] + "..." if len(chart_json_str) > 500 else chart_json_str)
        
    else:
        print("\n✗ Chart creation returned None")
        print("  Check the create_plotly_chart function for errors")
        
except Exception as e:
    print(f"\n✗ Error creating chart: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)

