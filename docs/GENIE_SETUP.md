# Setting Up Databricks Genie Integration

This guide explains how to configure the agent to use Databricks Genie API instead of custom SQL tools.

## Why Use Genie?

Instead of implementing custom SQL execution, the agent can use Databricks Genie which:
- Automatically generates SQL from natural language
- Handles query execution and optimization
- Provides better error handling
- Leverages Databricks' built-in capabilities

## Setup Steps

### 1. Create a Genie Room

1. Go to Databricks SQL Editor
2. Click on "Genie" or "AI Assistant"
3. Create a new room/conversation
4. Note the room ID (you'll need this)

### 2. Configure Environment Variable

Set the Genie room ID:

```bash
export GENIE_ROOM_ID="your-room-id-here"
```

Or add it to your `.env` file or `~/.databrickscfg`:

```
[default]
genie_room_id = your-room-id-here
```

### 3. Enable Genie Conversation API

Ensure Genie Conversation API is enabled in your Databricks workspace:
- Check workspace admin settings
- Verify API access permissions
- Ensure Unity Catalog is configured

### 4. Update Code (if needed)

The code will automatically use Genie if `GENIE_ROOM_ID` is set. The agent will:
- Use predefined tools for common queries (faster)
- Fall back to Genie for complex questions
- Genie handles SQL generation and execution

## Using Genie

Once configured, the agent will automatically use Genie when:
- Predefined tools can't answer the question
- Complex queries are needed
- Custom aggregations or analysis required

Example questions that will use Genie:
- "Compare average SoC across all batteries"
- "Show me batteries with SoC below 50%"
- "What's the total revenue across all batteries today?"

## Troubleshooting

If Genie is not working:
1. Verify `GENIE_ROOM_ID` is set correctly
2. Check Genie API is enabled in workspace
3. Ensure you have permissions to use Genie
4. Check Databricks SDK version supports Genie API

## Fallback

If Genie is not configured, the agent will provide a helpful error message and suggest using custom SQL tools instead.

