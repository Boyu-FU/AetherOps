# AetherOps MCP Pricing Server

A Python-based MCP (Model Context Protocol) server that provides unified cloud pricing data from AWS, Azure, and Scaleway using public APIs (no authentication required).

## 🌟 Features

- **Multi-Cloud Support**: Query pricing from AWS, Azure, and Scaleway
- **No Authentication Required**: Uses public APIs and curated data
- **Async & Concurrent**: Fast parallel API calls using asyncio
- **Smart Caching**: TTL-based caching to reduce API calls
- **Docker Ready**: Easy deployment with Docker Compose
- **Graceful Degradation**: Individual provider failures don't affect others

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed
- Git (optional, for cloning)

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/Boyu-FU/AetherOps.git
cd AetherOps/price-server

# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f
```

The server will be available at `http://localhost:8000/sse`

## 📡 API Usage

### MCP Tool: `get_cloud_pricing`

**Input Parameters:**
- `tiers`: List of instance tiers (e.g., `["small", "medium", "large"]`)
- `regions`: List of region codes (e.g., `["eu", "us"]`)

**Example Query:**
```python
from fastmcp import Client

async with Client("http://localhost:8000/sse") as client:
    result = await client.call_tool(
        "get_cloud_pricing",
        {"tiers": ["medium"], "regions": ["eu"]}
    )
    print(result)
```

**Response Format:**
```json
{
  "providers": [
    {
      "name": "AWS",
      "sku": "t3.medium",
      "price_hourly": 0.0416,
      "region": "eu-west-1",
      "is_eu": true,
      "cpu": 2,
      "ram_gb": 4.0
    },
    {
      "name": "Azure",
      "sku": "Standard_B2s",
      "price_hourly": 0.0448,
      "region": "westeurope",
      "is_eu": true,
      "cpu": 2,
      "ram_gb": 4.0
    }
  ]
}
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         MCP Pricing Server              │
│         (FastMCP + Uvicorn)             │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │  Price Cache   │
       │  (TTL: 12h)    │
       └───────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼──────┐
│ AWS   │ │Azure  │ │Scaleway  │
│Connector│ │Connector│ │Connector │
└───────┘ └───────┘ └──────────┘
    │          │          │
    ▼          ▼          ▼
 Public     Public     Curated
  API        API        Data
```

## 📊 Supported Cloud Providers

### AWS
- **API**: Bulk Price List API
- **Endpoint**: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json`
- **Data**: Curated list of common EC2 instance types
- **Regions**: US East, US West, EU (Ireland, Frankfurt, Paris)

### Azure
- **API**: Retail Prices API
- **Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Data**: Real-time VM pricing with pagination
- **Regions**: Multiple global regions

### Scaleway
- **Data Source**: Curated pricing data (public APIs unavailable)
- **Coverage**: Popular instance types (DEV, PRO, ENT series)
- **Regions**: Paris, Amsterdam, Warsaw (all EU)

## 🔧 Configuration

### Environment Variables

Create a `.env` file (optional):

```env
# Logging
LOG_LEVEL=INFO

# Cache TTL (seconds)
CACHE_TTL=43200

# API Endpoints (defaults provided)
AWS_BULK_PRICE_URL=https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json
AZURE_RETAIL_API_URL=https://prices.azure.com/api/retail/prices
EUR_TO_USD_RATE=1.08
```

## 🧪 Testing

### Run Integration Tests

```bash
# Inside Docker container
docker exec -it aetherops-mcp-pricing-server python test_in_docker.py
```

### Run Unit Tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
price-server/
├── src/
│   ├── connectors/
│   │   ├── aws_connector.py       # AWS pricing connector
│   │   ├── azure_connector.py     # Azure pricing connector
│   │   └── scaleway_connector.py  # Scaleway pricing connector
│   ├── normalizer.py              # Price normalization & filtering
│   ├── cache.py                   # TTL-based caching
│   └── __init__.py
├── tests/
│   ├── test_normalizer.py         # Unit tests
│   └── __init__.py
├── server.py                      # Main MCP server entry point
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── QUICKSTART.md                  # Quick start guide
```

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

### Docker Development

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📝 Technical Details

### Tier Mapping

| Tier   | Min CPU | Min RAM (GB) | Example Instances      |
|--------|---------|--------------|------------------------|
| small  | 1       | 1.0          | t3.micro, B1s         |
| medium | 2       | 4.0          | t3.medium, B2s        |
| large  | 4       | 8.0          | t3.large, D2s_v3      |
| xlarge | 8       | 16.0         | t3.xlarge, D4s_v3     |

### Region Filtering

- `eu`: Matches EU regions (eu-west-*, eu-central-*, france, germany, etc.)
- `us`: Matches US regions (us-east-*, us-west-*, virginia, oregon, etc.)

### Caching Strategy

- **Cache Key**: Sorted combination of tiers and regions
- **TTL**: 12 hours (configurable via `CACHE_TTL`)
- **Storage**: In-memory dictionary
- **Invalidation**: Time-based only

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of the AetherOps capstone project.

## 🔗 References

- [FastMCP Documentation](https://gofastmcp.com)
- [AWS Pricing API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-aws-pricing.html)
- [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
- [Scaleway Instance API](https://developers.scaleway.com/en/products/instance/api/)
- [MCP Protocol](https://modelcontextprotocol.io)

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ for the AetherOps Capstone Project**
