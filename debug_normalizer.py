import sys
sys.path.insert(0, '/app')
from src.normalizer import PriceNormalizer

n = PriceNormalizer()
print("EU patterns:", n.REGION_MAPPINGS.get('eu'))

test_data = [
    {"name": "Azure", "sku": "B2s", "price_hourly": 0.05, "region": "westeurope", "is_eu": True, "cpu": 2, "ram_gb": 4.0},
]

result = n.normalize_and_filter(test_data, ["small"], ["eu"])
print(f"Input: {test_data[0]['region']}")
print(f"Output: {len(result)} results")
if result:
    print(f"Result: {result[0]}")
