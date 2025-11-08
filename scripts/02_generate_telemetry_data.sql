-- SQL Script to Generate Synthetic Telemetry Data
-- Run this AFTER creating the battery_telemetry table structure
-- This generates 24 hours of 5-minute interval data

USE CATALOG ea_trading;

-- Generate telemetry data for RESS2 (75 MWh capacity)
INSERT INTO ea_trading.battery_trading.battery_telemetry
SELECT
    timestamp,
    'RESS2' as battery_id,
    'RESS2' as duid,
    soc_mwh,
    soc_percent,
    capability_charge_mw,
    capability_discharge_mw,
    cum_energy_exported_mwh,
    cum_energy_imported_mwh,
    throughput_mwh,
    75.0 as fullpackenergy_mwh,
    reading_age_minutes
FROM (
    SELECT
        date_add(current_timestamp(), -24 * 3600) + (row_number() OVER (ORDER BY 1) - 1) * 300 as timestamp,
        50.0 + (row_number() OVER (ORDER BY 1) % 20) * 1.5 as soc_mwh,
        ((50.0 + (row_number() OVER (ORDER BY 1) % 20) * 1.5) / 75.0) * 100 as soc_percent,
        CASE WHEN ((50.0 + (row_number() OVER (ORDER BY 1) % 20) * 1.5) / 75.0) * 100 < 85 THEN 50.0 ELSE 22.5 END as capability_charge_mw,
        CASE WHEN ((50.0 + (row_number() OVER (ORDER BY 1) % 20) * 1.5) / 75.0) * 100 > 15 THEN 50.0 ELSE 22.5 END as capability_discharge_mw,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_exported_mwh,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_imported_mwh,
        75.0 + (row_number() OVER (ORDER BY 1) % 75) as throughput_mwh,
        (row_number() OVER (ORDER BY 1) % 15) as reading_age_minutes
    FROM RANGE(288)
);

-- Generate telemetry data for DPNTBESS (50 MWh capacity)
INSERT INTO ea_trading.battery_trading.battery_telemetry
SELECT
    timestamp,
    'DPNTBESS' as battery_id,
    'DPNTBESS' as duid,
    soc_mwh,
    soc_percent,
    capability_charge_mw,
    capability_discharge_mw,
    cum_energy_exported_mwh,
    cum_energy_imported_mwh,
    throughput_mwh,
    50.0 as fullpackenergy_mwh,
    reading_age_minutes
FROM (
    SELECT
        date_add(current_timestamp(), -24 * 3600) + (row_number() OVER (ORDER BY 1) - 1) * 300 as timestamp,
        30.0 + (row_number() OVER (ORDER BY 1) % 15) * 1.2 as soc_mwh,
        ((30.0 + (row_number() OVER (ORDER BY 1) % 15) * 1.2) / 50.0) * 100 as soc_percent,
        CASE WHEN ((30.0 + (row_number() OVER (ORDER BY 1) % 15) * 1.2) / 50.0) * 100 < 85 THEN 33.5 ELSE 15.0 END as capability_charge_mw,
        CASE WHEN ((30.0 + (row_number() OVER (ORDER BY 1) % 15) * 1.2) / 50.0) * 100 > 15 THEN 33.5 ELSE 15.0 END as capability_discharge_mw,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_exported_mwh,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_imported_mwh,
        60.0 + (row_number() OVER (ORDER BY 1) % 60) as throughput_mwh,
        (row_number() OVER (ORDER BY 1) % 15) as reading_age_minutes
    FROM RANGE(288)
);

-- Generate telemetry data for GANNBG1 (300 MWh capacity)
INSERT INTO ea_trading.battery_trading.battery_telemetry
SELECT
    timestamp,
    'GANNBG1' as battery_id,
    'GANNBG1' as duid,
    soc_mwh,
    soc_percent,
    capability_charge_mw,
    capability_discharge_mw,
    cum_energy_exported_mwh,
    cum_energy_imported_mwh,
    throughput_mwh,
    300.0 as fullpackenergy_mwh,
    reading_age_minutes
FROM (
    SELECT
        date_add(current_timestamp(), -24 * 3600) + (row_number() OVER (ORDER BY 1) - 1) * 300 as timestamp,
        150.0 + (row_number() OVER (ORDER BY 1) % 60) * 2.5 as soc_mwh,
        ((150.0 + (row_number() OVER (ORDER BY 1) % 60) * 2.5) / 300.0) * 100 as soc_percent,
        CASE WHEN ((150.0 + (row_number() OVER (ORDER BY 1) % 60) * 2.5) / 300.0) * 100 < 85 THEN 200.0 ELSE 90.0 END as capability_charge_mw,
        CASE WHEN ((150.0 + (row_number() OVER (ORDER BY 1) % 60) * 2.5) / 300.0) * 100 > 15 THEN 200.0 ELSE 90.0 END as capability_discharge_mw,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_exported_mwh,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_imported_mwh,
        100.0 + (row_number() OVER (ORDER BY 1) % 50) as throughput_mwh,
        (row_number() OVER (ORDER BY 1) % 15) as reading_age_minutes
    FROM RANGE(288)
);

-- Generate telemetry data for GANNBL1 (300 MWh capacity)
INSERT INTO ea_trading.battery_trading.battery_telemetry
SELECT
    timestamp,
    'GANNBL1' as battery_id,
    'GANNBL1' as duid,
    soc_mwh,
    soc_percent,
    capability_charge_mw,
    capability_discharge_mw,
    cum_energy_exported_mwh,
    cum_energy_imported_mwh,
    throughput_mwh,
    300.0 as fullpackenergy_mwh,
    reading_age_minutes
FROM (
    SELECT
        date_add(current_timestamp(), -24 * 3600) + (row_number() OVER (ORDER BY 1) - 1) * 300 as timestamp,
        120.0 + (row_number() OVER (ORDER BY 1) % 80) * 2.0 as soc_mwh,
        ((120.0 + (row_number() OVER (ORDER BY 1) % 80) * 2.0) / 300.0) * 100 as soc_percent,
        CASE WHEN ((120.0 + (row_number() OVER (ORDER BY 1) % 80) * 2.0) / 300.0) * 100 < 85 THEN 200.0 ELSE 90.0 END as capability_charge_mw,
        CASE WHEN ((120.0 + (row_number() OVER (ORDER BY 1) % 80) * 2.0) / 300.0) * 100 > 15 THEN 200.0 ELSE 90.0 END as capability_discharge_mw,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_exported_mwh,
        200.0 + (row_number() OVER (ORDER BY 1) % 300) as cum_energy_imported_mwh,
        90.0 + (row_number() OVER (ORDER BY 1) % 60) as throughput_mwh,
        (row_number() OVER (ORDER BY 1) % 15) as reading_age_minutes
    FROM RANGE(288)
);

-- Verify
SELECT battery_id, COUNT(*) as count, MIN(timestamp) as first_reading, MAX(timestamp) as last_reading
FROM ea_trading.battery_trading.battery_telemetry
GROUP BY battery_id;

