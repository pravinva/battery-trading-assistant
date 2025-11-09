#!/usr/bin/env python3
"""
Test Genie Direct API locally to debug why it's returning question unchanged
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ["USE_GENIE_MCP"] = "false"  # Force direct API
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"
os.environ["DEBUG"] = "true"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Testing Genie Direct API Locally")
print("=" * 80)
print(f"USE_GENIE_MCP: {os.environ.get('USE_GENIE_MCP')}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")
print()

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.dashboards import MessageStatus
    
    w = WorkspaceClient()
    genie = w.genie
    
    print("✅ WorkspaceClient initialized")
    print()
    
    # Test question
    question = "What is the current SoC for RESS2?"
    print(f"Question: {question}")
    print()
    
    # Step 1: Start conversation
    print("=" * 80)
    print("Step 1: Starting conversation...")
    print("=" * 80)
    
    conversation_wait = genie.start_conversation(os.environ["GENIE_ROOM_ID"], question)
    print(f"✅ Conversation started")
    print(f"   Type: {type(conversation_wait)}")
    print()
    
    # Step 2: Wait for result
    print("=" * 80)
    print("Step 2: Waiting for message...")
    print("=" * 80)
    
    message = None
    try:
        # Try Wait.result() without timeout
        if hasattr(conversation_wait, 'result'):
            print("   Trying conversation_wait.result()...")
            message = conversation_wait.result()
            print(f"   ✅ Got message via result(): {type(message)}")
        else:
            print("   ⚠️  No result() method")
    except Exception as e:
        print(f"   ⚠️  result() failed: {e}")
        # Try with timeout
        try:
            from datetime import timedelta
            message = conversation_wait.result(timeout=timedelta(seconds=60))
            print(f"   ✅ Got message via result(timeout): {type(message)}")
        except Exception as e2:
            print(f"   ⚠️  result(timeout) failed: {e2}")
    
    # If still no message, try iteration
    if not message:
        if hasattr(conversation_wait, '__iter__'):
            print("   Trying iteration...")
            try:
                for msg in conversation_wait:
                    message = msg
                print(f"   ✅ Got message via iteration: {type(message)}")
            except Exception as e:
                print(f"   ⚠️  Iteration failed: {e}")
    
    # If still no message, use directly
    if not message:
        message = conversation_wait
        print(f"   Using conversation_wait directly: {type(message)}")
    
    print()
    
    # Step 3: Extract message details
    print("=" * 80)
    print("Step 3: Extracting message details...")
    print("=" * 80)
    
    message_id = None
    conversation_id = None
    
    if hasattr(message, 'message_id'):
        message_id = message.message_id
    elif hasattr(message, 'id'):
        message_id = message.id
    
    if hasattr(message, 'conversation_id'):
        conversation_id = message.conversation_id
    
    print(f"Message ID: {message_id}")
    print(f"Conversation ID: {conversation_id}")
    print()
    
    # Check status
    status = None
    if hasattr(message, 'status'):
        status = message.status
        print(f"Status: {status}")
        print(f"Status type: {type(status)}")
        print(f"Status string: {str(status)}")
    
    # Check if completed
    is_completed = False
    if status:
        status_str = str(status)
        is_completed = (
            status in ['COMPLETED', 'FAILED', 'CANCELLED'] or
            status_str in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED'] or
            'COMPLETED' in status_str or 'FAILED' in status_str or 'CANCELLED' in status_str
        )
        print(f"Is completed: {is_completed}")
    
    print()
    
    # Step 4: Check content field
    print("=" * 80)
    print("Step 4: Checking message.content...")
    print("=" * 80)
    
    if hasattr(message, 'content'):
        content = message.content
        print(f"message.content: {content}")
        print(f"Content type: {type(content)}")
        print(f"Content == question: {content == question}")
        print(f"Content length: {len(content) if content else 0}")
        print(f"Question length: {len(question)}")
    else:
        print("⚠️  No content attribute")
    
    print()
    
    # Step 5: Check attachments
    print("=" * 80)
    print("Step 5: Checking attachments...")
    print("=" * 80)
    
    attachments = None
    if hasattr(message, 'attachments'):
        attachments = message.attachments
        print(f"Attachments: {attachments}")
        print(f"Attachments type: {type(attachments)}")
        print(f"Number of attachments: {len(attachments) if attachments else 0}")
        
        if attachments:
            for i, attachment in enumerate(attachments):
                print(f"\nAttachment {i+1}:")
                print(f"  Type: {type(attachment)}")
                print(f"  Attributes: {dir(attachment)}")
                
                # Check for text
                if hasattr(attachment, 'text'):
                    text_obj = attachment.text
                    print(f"  Has text: {text_obj}")
                    if hasattr(text_obj, 'content'):
                        print(f"    text.content: {text_obj.content}")
                
                # Check for query
                if hasattr(attachment, 'query'):
                    query_obj = attachment.query
                    print(f"  Has query: {type(query_obj)}")
                    if hasattr(query_obj, 'query'):
                        print(f"    query.query: {query_obj.query}")
                    if hasattr(query_obj, 'statement_id'):
                        print(f"    query.statement_id: {query_obj.statement_id}")
                    if hasattr(query_obj, 'description'):
                        print(f"    query.description: {query_obj.description}")
    else:
        print("⚠️  No attachments attribute")
    
    print()
    
    # Step 6: If not completed, poll
    if not is_completed and message_id and conversation_id:
        print("=" * 80)
        print("Step 6: Polling for completion...")
        print("=" * 80)
        
        import time
        max_poll_time = 60
        poll_interval = 1
        start_time = time.time()
        poll_count = 0
        
        while time.time() - start_time < max_poll_time:
            poll_count += 1
            try:
                message_details = genie.get_message(
                    space_id=os.environ["GENIE_ROOM_ID"],
                    conversation_id=conversation_id,
                    message_id=message_id
                )
                
                status = None
                if hasattr(message_details, 'status'):
                    status = message_details.status
                
                status_str = str(status) if status else ''
                is_completed = (
                    status in ['COMPLETED', 'FAILED', 'CANCELLED'] or
                    status_str in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED'] or
                    'COMPLETED' in status_str or 'FAILED' in status_str or 'CANCELLED' in status_str
                )
                
                print(f"Poll #{poll_count}: Status = {status}, Completed = {is_completed}")
                
                if is_completed:
                    message = message_details
                    print(f"✅ Message completed after {poll_count} polls")
                    
                    # Re-check attachments
                    if hasattr(message, 'attachments'):
                        attachments = message.attachments
                        print(f"Attachments after completion: {len(attachments) if attachments else 0}")
                    break
                
                time.sleep(poll_interval)
            except Exception as e:
                print(f"Poll #{poll_count} error: {e}")
                time.sleep(1)
        
        if not is_completed:
            print(f"⚠️  Polling timeout after {max_poll_time}s")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Question: {question}")
    print(f"Message ID: {message_id}")
    print(f"Status: {status}")
    print(f"Completed: {is_completed}")
    print(f"Attachments: {len(attachments) if attachments else 0}")
    
    if hasattr(message, 'content'):
        print(f"message.content: {message.content}")
        if message.content == question:
            print("⚠️  WARNING: message.content is the same as question!")
    
    if attachments:
        print("\nAttachments found - extracting response...")
        for i, attachment in enumerate(attachments):
            print(f"\nAttachment {i+1}:")
            if hasattr(attachment, 'text'):
                text_obj = attachment.text
                if hasattr(text_obj, 'content'):
                    print(f"  Text content: {text_obj.content[:200]}")
            if hasattr(attachment, 'query'):
                query_obj = attachment.query
                if hasattr(query_obj, 'query'):
                    print(f"  SQL query: {query_obj.query[:200]}")
                if hasattr(query_obj, 'statement_id'):
                    print(f"  Statement ID: {query_obj.statement_id}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

