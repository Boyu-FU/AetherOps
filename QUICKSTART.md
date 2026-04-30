# Quick Start Guide

## 🚀 Start MCP Pricing Server in 5 Minutes

### Prerequisites

- ✅ Docker Desktop installed
- ✅ PowerShell (Windows) or Bash (Linux/Mac)

---

## Option 1: Docker Deployment (Recommended)

### Windows Users

```powershell
# 1. Navigate to project directory
cd c:\Users\Sichu\Desktop\course\capstone\price-server

# 2. Run startup script
.\start.ps1
```

### Linux/Mac Users

```bash
# 1. Navigate to project directory
cd price-server

# 2. Grant execute permission
chmod +x start.sh

# 3. Run startup script
./start.sh
```

### Verify Service

```bash
# View logs
docker-compose logs -f

# Check container status
docker-compose ps
```

---

## Option 2: Local Development

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows**:
```powershell
venv\Scripts\activate
```

**Linux/Mac**:
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

```bash
cp .env.example .env
```

### 5. Run Server

```bash
python server.py
```

---

## 🧪 Test the Server

### Run Integration Tests

```bash
python test_server.py
```

**Expected Output**:
```
============================================================
Testing AetherOps MCP Pricing Server
============================================================

[Test 1] Query: tiers=['medium'], regions=['eu']
------------------------------------------------------------
✓ Found 15 pricing records

Top 3 cheapest options:
  1. Scaleway  | PLAY2-MICRO          | $0.0280/hr | fr-par-1
  2. Azure     | Standard_B2s         | $0.0416/hr | westeurope
  3. AWS       | t3.medium            | $0.0478/hr | eu-west-3

[Test 2] Query: tiers=['small'], regions=['us']
------------------------------------------------------------
✓ Found 12 pricing records

Cheapest option:
  AWS        | t3.small             | $0.0208/hr | us-east-1

[Test 3] Query: tiers=['small', 'medium', 'large'], regions=['eu', 'us']
------------------------------------------------------------
✓ Found 45 pricing records

Results by provider:
  AWS: 15 instances
  Azure: 15 instances
  Scaleway: 15 instances

============================================================
All tests passed! ✓
============================================================
```

### Run Unit Tests

```bash
pytest tests/ -v
```

---

## 📡 Using MCP Tools

### Example Query

```python
from server import get_cloud_pricing
import asyncio

# Query medium instances in EU region
result = asyncio.run(get_cloud_pricing(
    tiers=["medium"],
    regions=["eu"]
))

print(result)
```

### Response Format

```json
{
  "providers": [
    {
      "name": "Scaleway",
      "sku": "PLAY2-MICRO",
      "price_hourly": 0.028,
      "region": "fr-par-1",
      "is_eu": true,
      "cpu": 2,
      "ram_gb": 2.0
    },
    {
      "name": "Azure",
      "sku": "Standard_B2s",
      "price_hourly": 0.0416,
      "region": "westeurope",
      "is_eu": true,
      "cpu": 2,
      "ram_gb": 4.0
    }
  ]
}
```

---

## 🔧 Troubleshooting

### Q1: Docker Build Fails

**Solution**:
```bash
# Clean cache and rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Q2: No Data Returned

**Check Network Connectivity**:
```bash
# Test AWS API
curl https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json | head -c 100

# Test Azure API
curl "https://prices.azure.com/api/retail/prices?\$filter=serviceName eq 'Virtual Machines'&\$top=1"

# Test Scaleway API
curl https://api.scaleway.com/instance/v1/products/servers
```

### Q3: High Memory Usage

**Reduce Cache TTL**:
```bash
# Edit .env file
echo "CACHE_TTL=21600" >> .env  # 6 hours

# Restart service
docker-compose restart
```

### Q4: View Real-time Logs

```bash
docker-compose logs -f mcp-pricing-server
```

---

## 🛑 Stop Service

### Docker

```bash
docker-compose down
```

### Local Execution

Press `Ctrl+C` to stop the server

---

## 📚 Additional Documentation

- 📖 [README.md](README.md) - Complete project documentation
- 📊 [COMPARISON.md](COMPARISON.md) - Java vs Python comparison
- 📝 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project summary

---

## ✅ Verification Checklist

After startup, confirm the following:

- [ ] Docker container is running (`docker-compose ps`)
- [ ] No errors in logs (`docker-compose logs`)
- [ ] Tests pass (`python test_server.py`)
- [ ] Can query pricing data

---

**Happy using!** 🎉
