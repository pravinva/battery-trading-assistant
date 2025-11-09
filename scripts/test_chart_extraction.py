#!/usr/bin/env python3
"""Test chart extraction pattern used in Streamlit"""

import sys
import os
sys.path.insert(0, '.')
os.environ['USE_GENIE_MCP'] = 'false'
os.environ['GENIE_ROOM_ID'] = '01f0bca10415147a91fe3c98f80e596e'

# Import supervisor
import importlib.util
spec = importlib.util.spec_from_file_location('supervisor_module', 'scripts/02_agent_supervisor.py')
supervisor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor_module)
supervisor = supervisor_module.supervisor

# Test chart extraction
question = 'Plot the current SoC for all batteries'
response = supervisor.process(question)

# Test the extraction pattern used in Streamlit
import re
import json

pattern = r'(?:```[^\n]*\n)?\[PLOTLY_CHART_START\]\s*(.*?)\s*\[PLOTLY_CHART_END\](?:[^\n]*\n```)?'
matches = re.findall(pattern, response, re.DOTALL | re.MULTILINE)

print('=' * 80)
print('Testing Chart Extraction Pattern')
print('=' * 80)
print(f'Response length: {len(response)}')
print(f'Chart markers present: {"[PLOTLY_CHART_START]" in response}')
print(f'Matches found: {len(matches)}')
print()

if matches:
    print('Match found!')
    match_clean = matches[0].strip()
    print(f'Match length: {len(match_clean)}')
    print(f'Match preview: {match_clean[:200]}...')
    print()
    
    try:
        chart_data = json.loads(match_clean)
        print('✅ JSON parsing successful')
        print(f'Chart data keys: {list(chart_data.keys())}')
        if 'json' in chart_data:
            chart_json = chart_data['json']
            print(f'Chart JSON type: {type(chart_json)}')
            if isinstance(chart_json, dict):
                print(f'Chart JSON keys: {list(chart_json.keys())}')
                if 'data' in chart_json:
                    print(f'Chart data traces: {len(chart_json["data"])}')
                if 'layout' in chart_json:
                    print(f'Chart layout keys: {list(chart_json["layout"].keys())}')
            elif isinstance(chart_json, str):
                print(f'Chart JSON string length: {len(chart_json)}')
                # Try parsing the string
                try:
                    parsed = json.loads(chart_json)
                    print(f'✅ Nested JSON parsed successfully')
                except:
                    print(f'❌ Nested JSON parsing failed')
    except json.JSONDecodeError as e:
        print(f'❌ JSON parsing failed: {e}')
        print(f'First 500 chars: {match_clean[:500]}')
else:
    print('❌ No matches found')
    # Check if markers exist
    if '[PLOTLY_CHART_START]' in response:
        start_pos = response.find('[PLOTLY_CHART_START]')
        end_pos = response.find('[PLOTLY_CHART_END]')
        print(f'Markers found at positions: {start_pos} to {end_pos}')
        print(f'Content between markers (first 500 chars):')
        print(response[start_pos:start_pos+500])
        print()
        print('Trying simpler pattern...')
        # Try simpler pattern
        simple_pattern = r'\[PLOTLY_CHART_START\](.*?)\[PLOTLY_CHART_END\]'
        simple_matches = re.findall(simple_pattern, response, re.DOTALL)
        print(f'Simple pattern matches: {len(simple_matches)}')
        if simple_matches:
            print(f'Simple match length: {len(simple_matches[0])}')
