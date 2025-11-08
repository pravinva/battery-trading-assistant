-- SQL Script to Generate Synthetic Dispatch Data
-- Run this AFTER creating the battery_dispatch table structure

USE CATALOG ea_trading;

-- Generate dispatch data for all batteries (24 hours, 5-minute intervals)
INSERT INTO ea_trading.battery_trading.battery_dispatch
SELECT
    dispatch_interval,
    battery_id,
    duid,
    dispatch_mw,
    spot_price_dollar_per_mwh,
    revenue_dollar,
    fcas_service,
    fcas_mw,
    fcas_price_dollar_per_mwh
FROM (
    SELECT
        date_add(current_timestamp(), -24 * 3600) + (row_number() OVER (ORDER BY 1) - 1) * 300 as dispatch_interval,
        battery_id,
        battery_id as duid,
        (RANDOM() * 60 - 30) as dispatch_mw,  -- Random between -30 and 30 MW
        50.0 + (RANDOM() * 250) as spot_price_dollar_per_mwh,  -- Random between 50 and 300 $/MWh
        ((RANDOM() * 60 - 30) * (50.0 + (RANDOM() * 250)) * (5.0/60.0)) as revenue_dollar,
        CASE WHEN RANDOM() > 0.7 THEN 
            CASE WHEN RANDOM() > 0.5 THEN 'RAISE_REG' ELSE 'LOWER_REG' END 
        ELSE NULL END as fcas_service,
        CASE WHEN RANDOM() > 0.7 THEN RANDOM() * 5 ELSE 0 END as fcas_mw,
        CASE WHEN RANDOM() > 0.7 THEN RANDOM() * 20 ELSE 0 END as fcas_price_dollar_per_mwh
    FROM (
        SELECT 'RESS2' as battery_id FROM RANGE(288)
        UNION ALL
        SELECT 'DPNTBESS' FROM RANGE(288)
        UNION ALL
        SELECT 'GANNBG1' FROM RANGE(288)
        UNION ALL
        SELECT 'GANNBL1' FROM RANGE(288)
    )
);

-- Verify
SELECT 
    battery_id,
    COUNT(*) as intervals,
    SUM(revenue_dollar) as total_revenue,
    AVG(spot_price_dollar_per_mwh) as avg_price,
    SUM(CASE WHEN dispatch_mw > 0 THEN dispatch_mw * 5/60 ELSE 0 END) as total_discharge_mwh,
    SUM(CASE WHEN dispatch_mw < 0 THEN ABS(dispatch_mw) * 5/60 ELSE 0 END) as total_charge_mwh
FROM ea_trading.battery_trading.battery_dispatch
GROUP BY battery_id;

