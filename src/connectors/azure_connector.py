"""
Azure Pricing Connector - Uses Retail Prices API (No Authentication Required)

This connector fetches Azure VM pricing data from the public Retail Prices API.
No Azure credentials are needed for basic pricing queries.

API Endpoint:
- Retail Prices: https://prices.azure.com/api/retail/prices

Technical Details:
- API supports pagination via NextPageLink
- Filter by serviceName='Virtual Machines' to get VM prices
- Returns price in USD with vCPU and memory information

Documentation:
https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
"""

import logging
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AzureConnector:
    """Fetch Azure VM pricing from public Retail Prices API"""
    
    # Azure Retail Prices API endpoint (no auth required)
    DEFAULT_API_URL = "https://prices.azure.com/api/retail/prices"
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize Azure connector
        
        Args:
            api_url: Base URL for Azure Retail Prices API (optional, uses default if not provided)
        """
        self.api_url = api_url or self.DEFAULT_API_URL
        logger.info(f"Azure Connector initialized with URL: {self.api_url}")
    
    async def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Fetch Azure VM pricing data from public API.
        
        Returns:
            List of normalized pricing records with keys:
            - name: Provider name ("Azure")
            - sku: VM size (e.g., "Standard_B2s")
            - price_hourly: Hourly price in USD
            - region: Region code (e.g., "westeurope")
            - is_eu: Boolean indicating EU region
        """
        logger.info("Fetching Azure VM prices from Retail Prices API...")
        
        try:
            results = []
            
            # Build initial query URL
            # Filter for Virtual Machines service
            filter_query = "$filter=serviceName eq 'Virtual Machines' and priceType eq 'Consumption'"
            url = f"{self.api_url}?{filter_query}"
            
            page_count = 0
            max_pages = 5  # Limit to avoid too many requests
            
            async with aiohttp.ClientSession() as session:
                while url and page_count < max_pages:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise Exception(f"Azure API returned status {response.status}")
                        
                        data = await response.json()
                        
                        # Process items
                        items = data.get("Items", [])
                        for item in items:
                            parsed = self._parse_item(item)
                            if parsed:
                                results.append(parsed)
                        
                        # Get next page link
                        url = data.get("NextPageLink")
                        page_count += 1
                        
                        if url:
                            logger.debug(f"Azure: fetched page {page_count}, continuing...")
            
            logger.info(f"Azure: fetched {len(results)} pricing records")
            return results
            
        except Exception as e:
            logger.error(f"Azure price fetch failed: {e}", exc_info=True)
            raise
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single Azure price item into normalized format.
        
        Args:
            item: Raw Azure Retail API item
            
        Returns:
            Normalized pricing record or None if invalid
        """
        try:
            # Extract service name - only process Virtual Machines
            service_name = item.get("serviceName", "")
            if service_name != "Virtual Machines":
                return None
            
            # Extract SKU name
            sku = item.get("armSkuName") or item.get("skuName", "")
            if not sku:
                return None
            
            # Extract region
            region = item.get("armRegionName") or item.get("location", "unknown")
            
            # Determine if EU region
            eu_regions = ["westeurope", "northeurope", "francecentral", "francesouth", 
                         "germanywestcentral", "italynorth", "polandcentral", 
                         "swedencentral", "switzerlandnorth", "switzerlandwest"]
            is_eu = region.lower() in eu_regions
            
            # Extract price
            price = item.get("retailPrice", 0.0)
            if price <= 0:
                return None
            
            # Extract specs (if available)
            cpu = item.get("vCPUs", 0)
            ram_gb = item.get("memoryInGiB", 0.0)
            
            return {
                "name": "Azure",
                "sku": sku,
                "price_hourly": round(price, 4),
                "region": region,
                "is_eu": is_eu,
                "cpu": cpu,
                "ram_gb": ram_gb
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse Azure item: {e}")
            return None
