#!/usr/bin/env python3
"""
Test script to directly test Genie API and see response structure
"""
import os
import time
from databricks.sdk import WorkspaceClient

# Get Genie room ID from environment
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID")
if not GENIE_ROOM_ID:
    print("ERROR: GENIE_ROOM_ID environment variable not set")
    print("Set it with: export GENIE_ROOM_ID='your-space-id'")
    exit(1)

# Initialize workspace client
w = WorkspaceClient()
genie = w.genie

# Test question
question = "What is the total energy throughput for each battery over the last 12 hours?"

print("=" * 80)
print("Testing Genie API Directly")
print("=" * 80)
print(f"Genie Room ID: {GENIE_ROOM_ID}")
print(f"Question: {question}")
print()

# Step 1: Start conversation
print("Step 1: Starting conversation...")
try:
    conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
    print(f"  ✓ Conversation started")
    
    # Extract message from Wait object
    message = None
    if callable(getattr(conversation_wait, 'result', None)):
        message = conversation_wait.result()
    elif hasattr(conversation_wait, '__iter__'):
        for msg in conversation_wait:
            message = msg
    else:
        message = conversation_wait
    
    print(f"  Message type: {type(message)}")
    print(f"  Message attributes: {dir(message) if hasattr(message, '__dict__') else 'N/A'}")
    
    # Extract IDs
    message_id = None
    if hasattr(message, 'message_id'):
        message_id = message.message_id
    elif hasattr(message, 'id'):
        message_id = message.id
    elif isinstance(message, dict):
        message_id = message.get('message_id') or message.get('id')
    
    conversation_id = None
    if hasattr(message, 'conversation_id'):
        conversation_id = message.conversation_id
    elif isinstance(message, dict):
        conversation_id = message.get('conversation_id')
    
    print(f"  Message ID: {message_id}")
    print(f"  Conversation ID: {conversation_id}")
    print()
    
except Exception as e:
    print(f"  ✗ Error starting conversation: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 2: Poll for status
print("Step 2: Polling for message status...")
max_poll_time = 60  # 1 minute max for testing
poll_interval = 2  # Start with 2 seconds
max_poll_interval = 10  # Max 10 seconds between polls
start_time = time.time()
message_status = None
message_details = None
poll_count = 0

while time.time() - start_time < max_poll_time:
    try:
        poll_count += 1
        message_details = genie.get_message(space_id=GENIE_ROOM_ID, conversation_id=conversation_id, message_id=message_id)
        
        # Extract status
        if hasattr(message_details, 'status'):
            message_status = message_details.status
        elif isinstance(message_details, dict):
            message_status = message_details.get('status')
        
        elapsed = int(time.time() - start_time)
        print(f"  Poll #{poll_count} [{elapsed}s] Status: {message_status}")
        
        if message_status in ['COMPLETED', 'FAILED', 'CANCELLED'] or str(message_status) in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED']:
            print(f"  ✓ Message reached conclusive state: {message_status}")
            break
        
        wait_time = min(poll_interval, max_poll_interval)
        print(f"  Waiting {wait_time}s before next poll...")
        time.sleep(wait_time)
        poll_interval = min(poll_interval * 1.5, max_poll_interval)
        
    except KeyboardInterrupt:
        print("\n  ✗ Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"  ✗ Error polling: {e}")
        wait_time = min(poll_interval, max_poll_interval)
        time.sleep(wait_time)
        poll_interval = min(poll_interval * 1.5, max_poll_interval)

if message_status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
    elapsed = int(time.time() - start_time)
    print(f"  ✗ Polling timeout after {elapsed} seconds, status: {message_status}")
    print(f"  Continuing with last known status...")

print()

# Step 3: Inspect message details
print("Step 3: Inspecting message details...")
print(f"  Message details type: {type(message_details)}")
print(f"  Message details attributes: {dir(message_details) if hasattr(message_details, '__dict__') else 'N/A'}")
print()

# Print all attributes
if hasattr(message_details, '__dict__'):
    print("  Message details __dict__:")
    for key, value in message_details.__dict__.items():
        if isinstance(value, str) and len(value) > 200:
            print(f"    {key}: {value[:200]}...")
        else:
            print(f"    {key}: {value}")
elif isinstance(message_details, dict):
    print("  Message details dict:")
    for key, value in message_details.items():
        if isinstance(value, str) and len(value) > 200:
            print(f"    {key}: {value[:200]}...")
        else:
            print(f"    {key}: {value}")
print()

# Step 4: Extract attachments
print("Step 4: Extracting attachments...")
attachments = None
if hasattr(message_details, 'attachments'):
    attachments = message_details.attachments
elif isinstance(message_details, dict):
    attachments = message_details.get('attachments')

if attachments:
    print(f"  Found {len(attachments)} attachment(s)")
    for idx, attachment in enumerate(attachments):
        print(f"  Attachment {idx + 1}:")
        print(f"    Type: {type(attachment)}")
        if hasattr(attachment, '__dict__'):
            print(f"    Attributes: {dir(attachment)}")
            for key, value in attachment.__dict__.items():
                if isinstance(value, str) and len(value) > 200:
                    print(f"      {key}: {value[:200]}...")
                else:
                    print(f"      {key}: {value}")
        elif isinstance(attachment, dict):
            for key, value in attachment.items():
                if isinstance(value, str) and len(value) > 200:
                    print(f"      {key}: {value[:200]}...")
                else:
                    print(f"      {key}: {value}")
        
        # Extract text and query
        text = None
        query = None
        attachment_id = None
        
        if hasattr(attachment, 'text'):
            text = attachment.text
        elif isinstance(attachment, dict):
            text = attachment.get('text')
        
        # Query is a GenieQueryAttachment object, extract the actual query string
        if hasattr(attachment, 'query'):
            query_obj = attachment.query
            # GenieQueryAttachment has a .query attribute containing the SQL string
            if hasattr(query_obj, 'query'):
                query = query_obj.query  # Extract the SQL string
            elif isinstance(query_obj, str):
                query = query_obj
            else:
                query = None
        elif isinstance(attachment, dict):
            query_obj = attachment.get('query')
            if isinstance(query_obj, dict) and 'query' in query_obj:
                query = query_obj.get('query')
            elif isinstance(query_obj, str):
                query = query_obj
            else:
                query = None
        else:
            query = None
        
        if hasattr(attachment, 'attachment_id'):
            attachment_id = attachment.attachment_id
        elif isinstance(attachment, dict):
            attachment_id = attachment.get('attachment_id') or attachment.get('id')
        
        print(f"    Extracted text: {text[:500] if text else 'None'}...")
        print(f"    Extracted query: {query[:500] if query else 'None'}...")
        print(f"    Attachment ID: {attachment_id}")
        print()
        
        # Step 5: Get query results
        # Use statement_id from query attachment to get results via statement execution API
        if attachment_id and conversation_id:
            print(f"  Step 5: Getting query results...")
            try:
                # Get statement_id from query attachment
                statement_id = None
                if hasattr(attachment, 'query') and hasattr(attachment.query, 'statement_id'):
                    statement_id = attachment.query.statement_id
                elif isinstance(attachment, dict) and attachment.get('query'):
                    query_obj = attachment.get('query')
                    if isinstance(query_obj, dict):
                        statement_id = query_obj.get('statement_id')
                    elif hasattr(query_obj, 'statement_id'):
                        statement_id = query_obj.statement_id
                
                if statement_id:
                    print(f"    Using statement_id: {statement_id}")
                    # Use statement execution API to get results
                    from databricks.sdk.service.sql import StatementState
                    result = w.statement_execution.get_statement(statement_id)
                    
                    if result:
                        print(f"    Statement status: {result.status.state}")
                        if result.status.state == StatementState.SUCCEEDED and result.result:
                            print(f"    Result type: {type(result.result)}")
                            if hasattr(result.result, 'data_array'):
                                print(f"    Rows returned: {len(result.result.data_array) if result.result.data_array else 0}")
                                if result.result.data_array:
                                    print(f"    First few rows:")
                                    for idx, row in enumerate(result.result.data_array[:5]):
                                        print(f"      Row {idx + 1}: {row}")
                            elif hasattr(result.result, 'rows'):
                                print(f"    Rows returned: {len(result.result.rows) if result.result.rows else 0}")
                                if result.result.rows:
                                    print(f"    First few rows:")
                                    for idx, row in enumerate(result.result.rows[:5]):
                                        print(f"      Row {idx + 1}: {row}")
                else:
                    print(f"    No statement_id found in attachment")
            except Exception as e:
                print(f"    ✗ Error getting query result: {e}")
                import traceback
                traceback.print_exc()
else:
    print("  No attachments found")

print()

# Step 6: Try list_conversation_messages
print("Step 6: Listing conversation messages...")
try:
    messages = genie.list_conversation_messages(GENIE_ROOM_ID, conversation_id=conversation_id)
    print(f"  Messages type: {type(messages)}")
    if hasattr(messages, 'messages'):
        msg_list = messages.messages
    elif hasattr(messages, 'items'):
        msg_list = messages.items
    elif isinstance(messages, list):
        msg_list = messages
    else:
        msg_list = None
    
    if msg_list:
        print(f"  Found {len(msg_list)} message(s)")
        for idx, msg in enumerate(msg_list):
            print(f"  Message {idx + 1}:")
            print(f"    Type: {type(msg)}")
            if hasattr(msg, '__dict__'):
                for key, value in msg.__dict__.items():
                    if isinstance(value, str) and len(value) > 200:
                        print(f"      {key}: {value[:200]}...")
                    else:
                        print(f"      {key}: {value}")
            elif isinstance(msg, dict):
                for key, value in msg.items():
                    if isinstance(value, str) and len(value) > 200:
                        print(f"      {key}: {value[:200]}...")
                    else:
                        print(f"      {key}: {value}")
            print()
    else:
        print("  No messages found")
except Exception as e:
    print(f"  ✗ Error listing messages: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Test Complete")
print("=" * 80)

