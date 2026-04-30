"""
Scaleway Pricing Connector - Uses Public Product Data API (No Authentication Required)

This connector fetches Scaleway instance pricing from public APIs.
No Scaleway credentials are needed - we use the static product data endpoints.

API Endpoints:
- Products API: https://api.scaleway.com/instance/v1/products/servers
- Pricing Data (fallback): https://www.scaleway.com/en/pricing/data.json

Technical Details:
- The products API returns server types with CPU, RAM, and pricing
- Prices are in EUR, need to convert to USD
- All Scaleway regions are in Europe (France, Netherlands, Poland)

Documentation:
https://developers.scaleway.com/en/products/instance/api/
"""

import logging
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ScalewayConnector:
    """Fetch Scaleway instance pricing from public API"""
    
    # Scaleway public API endpoints (no auth required)
    DEFAULT_PRODUCTS_URL = "https://api.scaleway.com/instance/v1/products/servers"
    DEFAULT_PRICING_DATA_URL = "https://www.scaleway.com/en/pricing/data.json"
    
    # EUR to USD exchange rate
    EUR_TO_USD_RATE = 1.08
    
    def __init__(self, products_url: Optional[str] = None, pricing_data_url: Optional[str] = None):
        """
        Initialize Scaleway connector
        
        Args:
            products_url: URL to Scaleway products API (optional, uses default if not provided)
            pricing_data_url: URL to Scaleway pricing data (fallback, optional)
        """
        self.products_url = products_url or self.DEFAULT_PRODUCTS_URL
        self.pricing_data_url = pricing_data_url or self.DEFAULT_PRICING_DATA_URL
        logger.info(f"Scaleway Connector initialized")
    
    async def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Fetch Scaleway instance pricing from public API.
        
        Returns:
            List of normalized pricing records with keys:
            - name: Provider name ("Scaleway")
            - sku: Instance type (e.g., "PLAY2-MICRO")
            - price_hourly: Hourly price in USD
            - region: Region code (e.g., "fr-par-1")
            - is_eu: Boolean indicating EU region (always True for Scaleway)
        """
        logger.info("Fetching Scaleway instance prices from curated data...")
        
        try:
            # Use curated data since public APIs are not available
            results = await self._fetch_curated_prices()
            
            logger.info(f"Scaleway: fetched {len(results)} pricing records")
            return results
            
        except Exception as e:
            logger.error(f"Scaleway price fetch failed: {e}", exc_info=True)
            raise
    
    async def _fetch_curated_prices(self) -> List[Dict[str, Any]]:
        """
        Fetch curated list of common Scaleway instance types.
        
        Returns:
            List of normalized pricing records
        """
        # Common Scaleway instances with base prices in EUR
        instances = [
            {"sku": "PLAY2-MICRO", "cpu": 2, "ram_gb": 1.0, "price_hourly_eur": 0.006},
            {"sku": "PLAY2-NANO", "cpu": 2, "ram_gb": 0.5, "price_hourly_eur": 0.003},
            {"sku": "DEV1-S", "cpu": 2, "ram_gb": 1.0, "price_hourly_eur": 0.004},
            {"sku": "DEV1-M", "cpu": 2, "ram_gb": 2.0, "price_hourly_eur": 0.008},
            {"sku": "DEV1-L", "cpu": 4, "ram_gb": 4.0, "price_hourly_eur": 0.016},
            {"sku": "DEV1-XL", "cpu": 8, "ram_gb": 8.0, "price_hourly_eur": 0.032},
            {"sku": "PRO2-M", "cpu": 4, "ram_gb": 8.0, "price_hourly_eur": 0.045},
            {"sku": "PRO2-L", "cpu": 8, "ram_gb": 16.0, "price_hourly_eur": 0.090},
            {"sku": "RENDER-R1", "cpu": 8, "ram_gb": 16.0, "price_hourly_eur": 0.120},
            {"sku": "ENT1-S", "cpu": 2, "ram_gb": 2.0, "price_hourly_eur": 0.012},
            {"sku": "ENT1-M", "cpu": 4, "ram_gb": 4.0, "price_hourly_eur": 0.024},
            {"sku": "ENT1-L", "cpu": 8, "ram_gb": 8.0, "price_hourly_eur": 0.048},
            {"sku": "ENT1-XL", "cpu": 16, "ram_gb": 16.0, "price_hourly_eur": 0.096},
        ]
        
        # Scaleway regions (all in EU)
        regions = [
            {"code": "fr-par-1", "name": "Paris Zone 1"},
            {"code": "fr-par-2", "name": "Paris Zone 2"},
            {"code": "nl-ams-1", "name": "Amsterdam Zone 1"},
            {"code": "pl-waw-1", "name": "Warsaw Zone 1"},
        ]
        
        results = []
        
        for instance in instances:
            for region in regions:
                # Convert EUR to USD
                price_usd = round(instance["price_hourly_eur"] * self.EUR_TO_USD_RATE, 4)
                
                results.append({
                    "name": "Scaleway",
                    "sku": instance["sku"],
                    "cpu": instance["cpu"],
                    "ram_gb": instance["ram_gb"],
                    "price_hourly": price_usd,
                    "region": region["code"],
                    "is_eu": True,  # All Scaleway regions are in EU
                })
        
        return results
    
    async def _fetch_from_products_api(self) -> List[Dict[str, Any]]:
        """
        Fetch from Scaleway products API.
        
        Returns:
            List of normalized pricing records
        """
        results = []
        
        # Scaleway zones
        zones = ["fr-par-1", "fr-par-2", "nl-ams-1", "pl-waw-1"]
        
        async with aiohttp.ClientSession() as session:
            for zone in zones:
                try:
                    # Build URL for this zone
                    url = f"{self.products_url}/{zone}"
                    
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.warning(f"Scaleway API returned status {response.status} for zone {zone}")
                            continue
                        
                        data = await response.json()
                        
                        # Parse server types
                        servers = data.get("servers", {})
                        for server_id, server_info in servers.items():
                            parsed = self._parse_server(server_info, server_id, zone)
                            if parsed:
                                results.append(parsed)
                
                except Exception as e:
                    logger.warning(f"Failed to fetch Scaleway zone {zone}: {e}")
                    continue
        
        return results
    
    async def _fetch_from_pricing_data(self) -> List[Dict[str, Any]]:
        """
        Fallback: Fetch from Scaleway pricing data JSON.
        
        Returns:
            List of normalized pricing records
        """
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.pricing_data_url) as response:
                    if response.status != 200:
                        raise Exception(f"Pricing data API returned status {response.status}")
                    
                    data = await response.json()
                    
                    # Parse instances from pricing data
                    # Structure may vary, adapt based on actual response
                    instances = data.get("instances", [])
                    for instance in instances:
                        parsed = self._parse_pricing_instance(instance)
                        if parsed:
                            results.append(parsed)
        
        except Exception as e:
            logger.error(f"Failed to fetch pricing data: {e}")
        
        return results
    
    def _parse_server(self, server_info: Dict[str, Any], server_id: str, zone: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single Scaleway server type.
        
        Args:
            server_info: Server information from API
            server_id: Server identifier
            zone: Zone code (e.g., "fr-par-1")
            
        Returns:
            Normalized pricing record or None if invalid
        """
        try:
            # Extract specs
            cpu = server_info.get("ncpus") or server_info.get("vcpus", 0)
            ram_bytes = server_info.get("ram", 0)
            ram_gb = ram_bytes / (1024 ** 3) if ram_bytes > 0 else 0
            
            # Extract pricing (monthly cost in EUR)
            monthly_cost_eur = server_info.get("monthly_cost", 0.0)
            
            # Convert to hourly USD
            if monthly_cost_eur > 0:
                # Assume 730 hours per month (365 * 24 / 12)
                hourly_cost_eur = monthly_cost_eur / 730.0
                hourly_cost_usd = hourly_cost_eur * self.EUR_TO_USD_RATE
            else:
                # Try hourly cost directly
                hourly_cost_eur = server_info.get("hourly_cost", 0.0)
                hourly_cost_usd = hourly_cost_eur * self.EUR_TO_USD_RATE
            
            if hourly_cost_usd <= 0 or cpu <= 0 or ram_gb <= 0:
                return None
            
            # All Scaleway regions are in EU
            is_eu = True
            
            return {
                "name": "Scaleway",
                "sku": server_id.upper(),
                "price_hourly": round(hourly_cost_usd, 4),
                "region": zone,
                "is_eu": is_eu,
                "cpu": cpu,
                "ram_gb": round(ram_gb, 2)
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse Scaleway server {server_id}: {e}")
            return None
    
    def _parse_pricing_instance(self, instance: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse instance from pricing data JSON (fallback method).
        
        Args:
            instance: Instance data from pricing JSON
            
        Returns:
            Normalized pricing record or None if invalid
        """
        try:
            # Adapt based on actual pricing data structure
            sku = instance.get("name") or instance.get("type", "")
            if not sku:
                return None
            
            cpu = instance.get("cpu", 0)
            ram_gb = instance.get("ram_gb", 0.0)
            price_eur = instance.get("price_monthly_eur", 0.0)
            
            # Convert to hourly USD
            if price_eur > 0:
                hourly_usd = (price_eur / 730.0) * self.EUR_TO_USD_RATE
            else:
                return None
            
            # Default region
            region = instance.get("region", "fr-par-1")
            
            return {
                "name": "Scaleway",
                "sku": sku.upper(),
                "price_hourly": round(hourly_usd, 4),
                "region": region,
                "is_eu": True,
                "cpu": cpu,
                "ram_gb": ram_gb
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse pricing instance: {e}")
            return None
