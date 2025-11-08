# Agent tools for Battery Trading Assistant
# These tools are used by the LangGraph agent to interact with data sources

from langchain_core.tools import tool
from typing import Annotated
from databricks.vector_search.client import VectorSearchClient
from agent.config import CATALOG, SCHEMA, ENDPOINT_NAME, INDEX_NAME

# Note: These tools require Spark context and Vector Search access
# They are typically used within Databricks notebooks

def create_tools(spark, vsc=None):
    """
    Create agent tools with Spark and Vector Search client.
    
    Args:
        spark: SparkSession instance
        vsc: VectorSearchClient instance (optional, will create if None)
    
    Returns:
        List of tool instances
    """
    if vsc is None:
        vsc = VectorSearchClient(disable_notice=True)
    
    @tool
    def search_battery_docs(
        query: Annotated[str, "The search query about battery technical specifications, processes, or architecture"]
    ) -> str:
        """Search battery integration documentation for technical information about 
        Wartsila BESS systems, PI integration, throughput calculations, SoC limits, 
        and AEMO bidding processes."""
        
        index = vsc.get_index(endpoint_name=ENDPOINT_NAME, index_name=INDEX_NAME)
        
        results = index.similarity_search(
            query_text=query,
            columns=["content", "doc_title", "page_number"],
            num_results=3
        )
        
        context_parts = []
        for hit in results.get('result', {}).get('data_array', []):
            content, title, page = hit[0], hit[1], hit[2]
            context_parts.append(f"[Page {page}] {content}")
        
        return "\n\n".join(context_parts) if context_parts else "No relevant documentation found."
    
    @tool
    def get_battery_status(
        battery_id: Annotated[str, "Battery ID (RESS2, DPNTBESS, GANNBG1, GANNBL1) or 'all' for all batteries"] = "all"
    ) -> str:
        """Get current state of charge (SoC), capabilities, and telemetry for batteries.
        Returns latest reading with SoC in MWh and %, charge/discharge capabilities."""
        
        if battery_id.lower() == "all":
            query = f"""
                SELECT battery_id, 
                       ROUND(soc_mwh, 2) as soc_mwh,
                       ROUND(soc_percent, 1) as soc_percent,
                       ROUND(capability_charge_mw, 1) as charge_cap_mw,
                       ROUND(capability_discharge_mw, 1) as discharge_cap_mw,
                       reading_age_minutes,
                       timestamp
                FROM {CATALOG}.{SCHEMA}.battery_telemetry
                WHERE timestamp = (SELECT MAX(timestamp) FROM {CATALOG}.{SCHEMA}.battery_telemetry)
                ORDER BY battery_id
            """
        else:
            query = f"""
                SELECT battery_id, 
                       ROUND(soc_mwh, 2) as soc_mwh,
                       ROUND(soc_percent, 1) as soc_percent,
                       ROUND(capability_charge_mw, 1) as charge_cap_mw,
                       ROUND(capability_discharge_mw, 1) as discharge_cap_mw,
                       reading_age_minutes,
                       timestamp
                FROM {CATALOG}.{SCHEMA}.battery_telemetry
                WHERE battery_id = '{battery_id.upper()}'
                  AND timestamp = (SELECT MAX(timestamp) FROM {CATALOG}.{SCHEMA}.battery_telemetry)
            """
        
        result = spark.sql(query).collect()
        
        if not result:
            return f"No telemetry data found for battery: {battery_id}"
        
        output = []
        for row in result:
            output.append(
                f"{row.battery_id}: {row.soc_mwh} MWh ({row.soc_percent}% SoC), "
                f"Charge: {row.charge_cap_mw} MW, Discharge: {row.discharge_cap_mw} MW, "
                f"Reading age: {row.reading_age_minutes} min (as of {row.timestamp})"
            )
        
        return "\n".join(output)
    
    @tool
    def get_battery_revenue(
        battery_id: Annotated[str, "Battery ID (RESS2, DPNTBESS, GANNBG1, GANNBL1)"],
        hours: Annotated[int, "Number of hours to look back (default 24)"] = 24
    ) -> str:
        """Calculate total revenue/cost for a battery over specified time period.
        Positive revenue = earning from discharge, negative = cost of charging."""
        
        query = f"""
            SELECT battery_id,
                   COUNT(*) as num_intervals,
                   ROUND(SUM(revenue_dollar), 2) as total_revenue_dollar,
                   ROUND(AVG(spot_price_dollar_per_mwh), 2) as avg_spot_price,
                   ROUND(SUM(CASE WHEN dispatch_mw > 0 THEN dispatch_mw ELSE 0 END) * 5/60, 2) as total_discharge_mwh,
                   ROUND(SUM(CASE WHEN dispatch_mw < 0 THEN ABS(dispatch_mw) ELSE 0 END) * 5/60, 2) as total_charge_mwh
            FROM {CATALOG}.{SCHEMA}.battery_dispatch
            WHERE battery_id = '{battery_id.upper()}'
              AND dispatch_interval >= current_timestamp() - INTERVAL {hours} HOURS
            GROUP BY battery_id
        """
        
        result = spark.sql(query).collect()
        
        if not result:
            return f"No dispatch data found for {battery_id} in last {hours} hours"
        
        row = result[0]
        return (f"{row.battery_id} performance (last {hours}h):\n"
                f"  Revenue: ${row.total_revenue_dollar:,.2f}\n"
                f"  Avg spot price: ${row.avg_spot_price}/MWh\n"
                f"  Energy discharged: {row.total_discharge_mwh} MWh\n"
                f"  Energy charged: {row.total_charge_mwh} MWh\n"
                f"  Trading intervals: {row.num_intervals}")
    
    @tool
    def get_battery_info(
        battery_id: Annotated[str, "Battery ID or 'all' for all batteries"] = "all"
    ) -> str:
        """Get battery asset information including capacity, location, partner, and commissioning details."""
        
        if battery_id.lower() == "all":
            query = f"SELECT * FROM {CATALOG}.{SCHEMA}.battery_assets ORDER BY battery_id"
        else:
            query = f"SELECT * FROM {CATALOG}.{SCHEMA}.battery_assets WHERE battery_id = '{battery_id.upper()}'"
        
        result = spark.sql(query).collect()
        
        if not result:
            return f"No asset information found for: {battery_id}"
        
        output = []
        for row in result:
            output.append(
                f"{row.battery_id} ({row.site_name}):\n"
                f"  Location: {row.location}\n"
                f"  Capacity: {row.nameplate_capacity_mw} MW\n"
                f"  Storage: {row.max_soc_mwh} MWh max, {row.min_soc_mwh} MWh min\n"
                f"  Partner: {row.partner}\n"
                f"  Commissioned: {row.commissioning_date}"
            )
        
        return "\n\n".join(output)
    
    return [search_battery_docs, get_battery_status, get_battery_revenue, get_battery_info]

