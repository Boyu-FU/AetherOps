"""
Price Normalizer - Maps tiers to instance types and filters by region

This module handles:
1. Tier mapping: "small", "medium", "large" → specific instance types
2. Region filtering: "eu", "us" → specific region codes
3. Cost-effectiveness: Select cheapest instances matching criteria
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PriceNormalizer:
    """Normalize and filter cloud pricing data based on tiers and regions"""
    
    # Tier to instance specifications mapping
    # Defines minimum CPU and RAM requirements for each tier
    TIER_SPECS = {
        "small": {"min_cpu": 1, "min_ram_gb": 1.0},
        "medium": {"min_cpu": 2, "min_ram_gb": 4.0},
        "large": {"min_cpu": 4, "min_ram_gb": 8.0},
        "xlarge": {"min_cpu": 8, "min_ram_gb": 16.0},
    }
    
    # Region code mappings
    REGION_MAPPINGS = {
        "eu": ["eu-", "france", "germany", "ireland", "paris", "par-", "frankfurt", 
               "amsterdam", "ams-", "warsaw", "waw-", "sweden", "switzerland", "italy", "europe", "westeurope", "northeurope", "uksouth", "ukwest"],
        "us": ["us-", "north-virginia", "oregon", "california", "ohio", "eastus", "westus", "centralus", "southcentralus", "westcentralus", "useast", "uswest", "virginia"],
    }
    
    def normalize_and_filter(
        self,
        raw_data: List[Dict[str, Any]],
        tiers: List[str],
        regions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Normalize and filter pricing data based on tiers and regions.
        
        Args:
            raw_data: Raw pricing records from all providers
            tiers: List of tier names (e.g., ["small", "medium"])
            regions: List of region codes (e.g., ["eu", "us"])
            
        Returns:
            Filtered and normalized list of pricing records
        """
        logger.info(f"Normalizing data: {len(raw_data)} records, tiers={tiers}, regions={regions}")
        
        # Get tier specifications
        tier_specs = self._get_tier_specs(tiers)
        
        # Get region filters
        region_filters = self._get_region_filters(regions)
        
        # Filter and normalize
        filtered = []
        for record in raw_data:
            # Check if matches any tier
            if not self._matches_tier(record, tier_specs):
                continue
            
            # Check if matches any region
            if not self._matches_region(record, region_filters):
                continue
            
            # Add to results (already in correct format from connectors)
            filtered.append(record)
        
        # Sort by price (cheapest first)
        filtered.sort(key=lambda x: x.get("price_hourly", float('inf')))
        
        logger.info(f"Filtered to {len(filtered)} records")
        return filtered
    
    def _get_tier_specs(self, tiers: List[str]) -> List[Dict[str, Any]]:
        """
        Get specifications for requested tiers.
        
        Args:
            tiers: List of tier names
            
        Returns:
            List of tier specification dictionaries
        """
        specs = []
        for tier in tiers:
            tier_lower = tier.lower()
            if tier_lower in self.TIER_SPECS:
                specs.append(self.TIER_SPECS[tier_lower])
            else:
                logger.warning(f"Unknown tier: {tier}, skipping")
        
        # If no valid tiers, use all
        if not specs:
            specs = list(self.TIER_SPECS.values())
        
        return specs
    
    def _get_region_filters(self, regions: List[str]) -> List[str]:
        """
        Get region filter patterns.
        
        Args:
            regions: List of region codes (e.g., ["eu", "us"])
            
        Returns:
            List of region pattern strings
        """
        filters = []
        for region in regions:
            region_lower = region.lower()
            if region_lower in self.REGION_MAPPINGS:
                filters.extend(self.REGION_MAPPINGS[region_lower])
            else:
                # Treat as exact region code
                filters.append(region_lower)
        
        # If no valid regions, match all
        if not filters:
            filters = [""]
        
        return filters
    
    def _matches_tier(self, record: Dict[str, Any], tier_specs: List[Dict[str, Any]]) -> bool:
        """
        Check if a record matches any tier specification.
        
        Args:
            record: Pricing record
            tier_specs: List of tier specifications
            
        Returns:
            True if record matches at least one tier
        """
        cpu = record.get("cpu", 0)
        ram_gb = record.get("ram_gb", 0.0)
        
        # Check if matches any tier (use the smallest matching tier)
        for spec in tier_specs:
            if cpu >= spec["min_cpu"] and ram_gb >= spec["min_ram_gb"]:
                return True
        
        return False
    
    def _matches_region(self, record: Dict[str, Any], region_filters: List[str]) -> bool:
        """
        Check if a record matches any region filter.
        
        Args:
            record: Pricing record
            region_filters: List of region filter patterns
            
        Returns:
            True if record matches at least one filter
        """
        region = record.get("region", "").lower()
        
        # If no filters, match all
        if not region_filters or region_filters == [""]:
            return True
        
        # Check if region matches any filter
        for filter_pattern in region_filters:
            if filter_pattern in region:
                return True
        
        return False
