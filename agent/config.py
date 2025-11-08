# Configuration for Battery Trading Agent

CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "one-env-shared-endpoint-10"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
LLM_ENDPOINT = "databricks-meta-llama-3-1-70b-instruct"
MODEL_NAME = "battery_trading_agent"
SERVING_ENDPOINT_NAME = "battery-trading-agent"

# Vector Search Configuration
EMBEDDING_MODEL = "databricks-gte-large-en"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Battery IDs
BATTERY_IDS = ["RESS2", "DPNTBESS", "GANNBG1", "GANNBL1"]

