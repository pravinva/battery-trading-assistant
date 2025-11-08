# Genie Test Questions

Here are suggested test questions to validate Genie's SQL generation capabilities across different scenarios:

## Basic Status Queries

1. **"What is the current SoC for RESS2?"**
   - Tests: Simple single-battery query with current data
   - Expected: Single row with latest SoC value

2. **"Show me the current SoC for all batteries"**
   - Tests: Multi-battery query
   - Expected: Multiple rows, one per battery

3. **"What are the charge and discharge capabilities for GANNBG1?"**
   - Tests: Multiple column selection
   - Expected: Charge/discharge MW values

## Time-Based Queries

4. **"What is the total energy throughput for each battery over the last 12 hours?"**
   - Tests: Time-based aggregation with GROUP BY
   - Expected: 4 rows with throughput per battery

5. **"Compare average SoC across all batteries in the last hour"**
   - Tests: AVG aggregation with time filter
   - Expected: Average SoC per battery

6. **"Show me batteries with SoC readings older than 10 minutes"**
   - Tests: Time comparison filter
   - Expected: Batteries with stale data

7. **"What's the total revenue across all batteries today?"**
   - Tests: SUM aggregation across multiple batteries
   - Expected: Single total revenue value

## Aggregation & Comparison Queries

8. **"Which battery has the highest discharge capability?"**
   - Tests: MAX aggregation with identification
   - Expected: Battery ID with highest discharge MW

9. **"Find batteries with SoC below 50%"**
   - Tests: Filter with threshold
   - Expected: Batteries meeting condition

10. **"What's the average spot price for battery dispatch in the last 24 hours?"**
    - Tests: AVG on different table
    - Expected: Average price value

## Complex Multi-Table Queries

11. **"Show me revenue and current SoC for each battery"**
    - Tests: JOIN or multiple table access
    - Expected: Combined data from dispatch and telemetry

12. **"Which battery has the oldest telemetry reading?"**
    - Tests: MIN on timestamp with identification
    - Expected: Battery with oldest data

## Throughput & Energy Queries

13. **"What's the total energy throughput for all batteries combined over the last 12 hours?"**
    - Tests: SUM across batteries
    - Expected: Single total throughput value

14. **"Calculate throughput for RESS2 using the cumulative energy fields"**
    - Tests: Complex calculation (MAX - MIN on cumulative fields)
    - Expected: Throughput calculation

15. **"Show me energy throughput from the dispatch table for the last 6 hours"**
    - Tests: Alternative throughput calculation method
    - Expected: Throughput per battery

## Revenue & Financial Queries

16. **"What's the total revenue for DPNTBESS in the last 24 hours?"**
    - Tests: SUM with time filter
    - Expected: Revenue amount

17. **"Compare revenue across all batteries for today"**
    - Tests: Comparison query
    - Expected: Revenue per battery

18. **"Which battery generated the most revenue in the last week?"**
    - Tests: MAX with time window
    - Expected: Battery ID with highest revenue

## Filtering & Conditions

19. **"Show me batteries at Darlington Point"**
    - Tests: Location-based filter
    - Expected: RESS2 and DPNTBESS

20. **"Find batteries with discharge capability greater than 50 MW"**
    - Tests: Numeric filter
    - Expected: Batteries meeting threshold

## Edge Cases & Error Handling

21. **"What's the throughput for batteries with NULL SoC?"**
    - Tests: NULL handling
    - Expected: Proper NULL filtering

22. **"Show me the most recent telemetry reading for each battery"**
    - Tests: Latest record per group
    - Expected: Most recent reading per battery

## Recommended Test Sequence

Start with simple queries and progress to complex ones:

**Phase 1: Basic (Questions 1-3)**
- Verify Genie can access tables and return basic data

**Phase 2: Aggregations (Questions 4-7)**
- Test SUM, AVG, COUNT functions
- Test time-based filtering

**Phase 3: Comparisons (Questions 8-10)**
- Test MAX, MIN with identification
- Test threshold filters

**Phase 4: Complex (Questions 11-15)**
- Test multi-table access
- Test complex calculations

**Phase 5: Financial (Questions 16-18)**
- Test revenue queries
- Test comparisons

**Phase 6: Edge Cases (Questions 19-22)**
- Test filters and conditions
- Test NULL handling

## Success Criteria

For each question, verify:
- ✅ Genie generates valid SQL
- ✅ SQL executes successfully
- ✅ Results match expected format
- ✅ Numerical values are correct
- ✅ Response time is reasonable (< 30 seconds)

## Notes

- Some questions may require Genie to use the `throughput_mwh` field directly (as documented in GENIE_SQL_FIXES.md)
- Questions about cumulative energy fields should be avoided or handled carefully
- Throughput queries should use SUM(throughput_mwh) rather than MAX - MIN calculations

