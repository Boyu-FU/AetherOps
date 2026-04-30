"""
AetherOps MCP Pricing Server - Main Entry Point

This server provides a unified interface for querying cloud pricing data
from AWS, Azure, and Scaleway using public APIs (no authentication required).

Tool Contract:
- Tool Name: get_cloud_pricing
- Input: tiers (List[str]), regions (List[str])
- Output: JSON with providers array containing normalized pricing data

Usage:
    python server.py
    
Or with Docker:
    docker-compose up
"""

import asyncio
import logging
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP

from src.connectors.aws_connector import AWSConnector
from src.connectors.azure_connector import AzureConnector
from src.connectors.scaleway_connector import ScalewayConnector
from src.normalizer import PriceNormalizer
from src.cache import PriceCache

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("AetherOps Pricing Server")

# Initialize connectors (using public APIs - no auth required)
aws_connector = AWSConnector(
    price_url=os.getenv("AWS_BULK_PRICE_URL")
)
azure_connector = AzureConnector(
    api_url=os.getenv("AZURE_RETAIL_API_URL")
)
scaleway_connector = ScalewayConnector(
    products_url=os.getenv("SCALEWAY_PRODUCTS_URL"),
    pricing_data_url=os.getenv("SCALEWAY_PRICING_DATA_URL")
)

# Initialize normalizer and cache
normalizer = PriceNormalizer()
cache_ttl = int(os.getenv("CACHE_TTL", "43200"))
cache = PriceCache(ttl_seconds=cache_ttl)


@mcp.tool()
async def get_cloud_pricing(
    tiers: List[str],
    regions: List[str]
) -> Dict[str, Any]:
    """
    Query cloud pricing data from multiple providers.
    
    Fetches real-time pricing from AWS, Azure, and Scaleway using public APIs.
    No authentication required. Results are cached for performance.
    
    Args:
        tiers: List of instance tiers (e.g., ["small", "medium", "large"])
               Supported tiers: small, medium, large, xlarge
        regions: List of region codes (e.g., ["eu", "us"])
                 Supported regions: eu, us, or specific region codes
    
    Returns:
        Dictionary with 'providers' key containing list of pricing data.
        Each provider entry includes:
        - name: Provider name (AWS, Azure, Scaleway)
        - sku: Instance type identifier
        - price_hourly: Hourly price in USD
        - region: Region code
        - is_eu: Boolean indicating EU region
        - cpu: Number of vCPUs
        - ram_gb: Memory in GB
        
    Example:
        {
            "providers": [
                {
                    "name": "AWS",
                    "sku": "t3.medium",
                    "price_hourly": 0.0416,
                    "region": "us-east-1",
                    "is_eu": false,
                    "cpu": 2,
                    "ram_gb": 4.0
                },
                {
                    "name": "Scaleway",
                    "sku": "PLAY2-MICRO",
                    "price_hourly": 0.028,
                    "region": "fr-par-1",
                    "is_eu": true,
                    "cpu": 2,
                    "ram_gb": 2.0
                }
            ]
        }
    """
    logger.info(f"Received pricing request: tiers={tiers}, regions={regions}")
    
    try:
        # Check cache first
        cache_key = f"{','.join(sorted(tiers))}:{','.join(sorted(regions))}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return cached_result
        
        # Fetch data from all providers concurrently
        logger.info("Fetching pricing data from all providers...")
        aws_data, azure_data, scaleway_data = await asyncio.gather(
            aws_connector.fetch_prices(),
            azure_connector.fetch_prices(),
            scaleway_connector.fetch_prices(),
            return_exceptions=True
        )
        
        # Handle exceptions gracefully (error handling / hardening)
        all_raw_data = []
        
        if not isinstance(aws_data, Exception):
            all_raw_data.extend(aws_data)
            logger.info(f"AWS: fetched {len(aws_data)} records")
        else:
            logger.warning(f"AWS fetch failed: {aws_data}")
        
        if not isinstance(azure_data, Exception):
            all_raw_data.extend(azure_data)
            logger.info(f"Azure: fetched {len(azure_data)} records")
        else:
            logger.warning(f"Azure fetch failed: {azure_data}")
        
        if not isinstance(scaleway_data, Exception):
            all_raw_data.extend(scaleway_data)
            logger.info(f"Scaleway: fetched {len(scaleway_data)} records")
        else:
            logger.warning(f"Scaleway fetch failed: {scaleway_data}")
        
        # Normalize and filter data
        normalized_data = normalizer.normalize_and_filter(
            all_raw_data, tiers, regions
        )
        
        # Build response
        result = {
            "providers": normalized_data
        }
        
        # Cache the result
        cache.set(cache_key, result)
        
        logger.info(f"Returning {len(normalized_data)} pricing records")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_cloud_pricing: {e}", exc_info=True)
        return {
            "providers": [],
            "error": str(e)
        }


def main():
    """Start the MCP server"""
    logger.info("Starting AetherOps MCP Pricing Server...")
    logger.info(f"Cache TTL: {cache_ttl} seconds")
    logger.info("Using public APIs - no authentication required")
    
    # Use SSE transport for Docker deployment
    import uvicorn
    from fastmcp.server.http import create_sse_app
    
    app = create_sse_app(mcp, message_path="/messages", sse_path="/sse")
    
    logger.info("Starting HTTP server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
