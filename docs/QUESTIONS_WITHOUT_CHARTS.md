# Questions that DON'T need chart rendering

## Single Value Queries
- "What is the current SoC for RESS2?"
- "What's the total revenue for GANNBG1 today?"
- "How much energy did DPNTBESS discharge in the last hour?"
- "What is the maximum capacity of RESS2?"
- "Show me the oldest telemetry reading age"

## Metadata/Descriptive Queries
- "What tables are available in the database?"
- "Describe the structure of the battery_telemetry table"
- "What columns does battery_dispatch have?"
- "Show me the battery asset information for RESS2"

## Documentation/Explanation Queries
- "How is throughput calculated?"
- "What are the SoC limits?"
- "Explain how AEMO bidding works"
- "What happens when SoC readings are older than 10 minutes?"
- "How do throughput limits affect bidding?"

## Count/Summary Queries (Single Result)
- "How many batteries are in the system?"
- "How many dispatch records exist?"
- "What's the count of batteries at Darlington Point?"

## Simple Status Queries
- "Is RESS2 currently charging or discharging?"
- "What's the status of GANNBG1?"
- "Which batteries have SoC below 50%?" (if result is just a list of names)

## Comparison Queries (Few Values)
- "Compare the SoC of RESS2 and DPNTBESS" (if only 2 values)
- "What's the difference in capacity between GANNBG1 and GANNBL1?"

## Questions that DO need charts:
- "Show me revenue trends over the last week"
- "Plot SoC over time for all batteries"
- "Compare average SoC across all batteries in the last hour"
- "What is the highest hourly revenue for GANNBG1 by day?"
- "Show throughput for each battery over the last 12 hours"
- "Display revenue comparison across all batteries"

