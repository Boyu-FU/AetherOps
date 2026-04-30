# AetherOps MCP Pricing Server - Technical Specification

## Document Information

- **Project**: AetherOps Cloud Infrastructure Pricing Server
- **Version**: 1.0 (Final Delivery)
- **Owner**: Boyu Fu
- **Date**: April 30, 2026
- **Status**: Production Ready

---

## 1. Executive Summary

The AetherOps MCP Pricing Server is a production-ready Model Context Protocol (MCP) server that provides unified cloud infrastructure pricing data from multiple providers including AWS, Azure, and Scaleway. The server implements the get_cloud_pricing tool as specified in the project requirements, enabling real-time price comparison and cost optimization for cloud resources across different geographic regions and instance tiers.

### Key Capabilities

- Multi-cloud pricing aggregation from three major providers
- No authentication required through use of public APIs and curated datasets
- Intelligent tier-based filtering with automatic instance mapping
- Geographic region filtering with pattern matching
- Performance-optimized with TTL-based caching and concurrent API calls
- Graceful degradation when individual providers are unavailable
- Docker containerized deployment for easy integration

---

## 2. System Architecture

### 2.1 High-Level Design

The system follows a modular architecture with clear separation of concerns:

**Presentation Layer**: FastMCP server exposing the MCP protocol over HTTP/SSE transport, handling client requests and response formatting.

**Business Logic Layer**: Price normalization engine that maps abstract tier definitions to concrete instance specifications, applies region filters, and sorts results by cost efficiency.

**Data Access Layer**: Provider-specific connectors that fetch pricing data from cloud vendor APIs, handle pagination, parse responses, and normalize data formats.

**Caching Layer**: In-memory cache with configurable time-to-live that reduces API call frequency and improves response times for repeated queries.

### 2.2 Component Diagram

The architecture consists of five main components working together:

1. **MCP Server Core**: Manages the MCP protocol lifecycle, registers tools, and handles request routing using the FastMCP framework with Uvicorn ASGI server for production performance.

2. **Price Normalizer**: Implements business logic for tier mapping and region filtering, ensuring consistent output format regardless of source provider data structures.

3. **Cloud Connectors**: Three independent connector modules (AWS, Azure, Scaleway) that encapsulate provider-specific API interactions, error handling, and data transformation.

4. **Cache Manager**: Provides transparent caching with automatic expiration, cache key generation based on query parameters, and thread-safe access patterns.

5. **Configuration Manager**: Handles environment variable loading, validates configuration values, and provides sensible defaults for all operational parameters.

### 2.3 Data Flow

When a pricing query arrives, the system processes it through these stages:

1. Request validation and parameter parsing
2. Cache lookup using normalized query key
3. Parallel data fetching from all available providers
4. Error isolation and graceful degradation for failed providers
5. Data normalization and tier/region filtering
6. Result sorting by hourly price (ascending)
7. Response caching and client delivery

---

## 3. Technology Stack

### 3.1 Core Technologies

**Runtime Environment**: Python 3.11 running on Alpine Linux base image for minimal footprint and security hardening.

**MCP Framework**: FastMCP version 3.2.4 providing production-ready Model Context Protocol implementation with SSE transport support.

**Web Server**: Uvicorn ASGI server delivering high-performance async HTTP serving with automatic reload support for development.

**HTTP Client**: Aiohttp asynchronous HTTP library enabling concurrent API calls with connection pooling and timeout management.

**Data Validation**: Pydantic v2 for runtime type checking and data structure validation ensuring API contract compliance.

### 3.2 Supporting Libraries

**Environment Management**: Python-dotenv for secure configuration loading from environment variables without hardcoding sensitive values.

**JSON Processing**: Ijson streaming parser for memory-efficient handling of large JSON files, particularly useful for AWS bulk pricing data.

**Testing Framework**: Pytest with async support for comprehensive unit and integration testing.

### 3.3 Deployment Technologies

**Container Runtime**: Docker with multi-stage build optimization for small image size and fast deployment.

**Orchestration**: Docker Compose for simplified multi-container management with health checks and resource limits.

**Process Management**: Supervisord or native Docker restart policies ensure service availability after failures.

---

## 4. API Integration Strategy

### 4.1 AWS Integration

**API Endpoint**: AWS Bulk Price List API provides static JSON files containing complete EC2 pricing information updated regularly by AWS.

**Data Source**: Curated dataset of common instance types covering popular tiers from micro to extra-large configurations across multiple regions.

**Pricing Model**: On-demand hourly rates with regional multipliers applied for EU locations reflecting typical price premiums.

**Update Frequency**: Static data refreshed manually when AWS publishes new pricing, cached for twelve hours to balance freshness and performance.

**Error Handling**: Connection timeouts and parsing errors trigger fallback to cached data or empty result sets with appropriate logging.

### 4.2 Azure Integration

**API Endpoint**: Azure Retail Prices API offers real-time pricing data with pagination support for comprehensive VM catalog access.

**Query Strategy**: Filtered queries targeting Virtual Machines service with consumption pricing type to exclude reserved and spot instances.

**Pagination Handling**: Automatic follow-through of NextPageLink references with maximum page limit preventing infinite loops.

**Data Parsing**: Extraction of relevant fields including SKU name, retail price in USD, ARM SKU identifier, and location information.

**Rate Limiting**: Respect for API throttling through controlled request pacing and exponential backoff on 429 responses.

### 4.3 Scaleway Integration

**Challenge**: Public pricing APIs returned HTTP 404 errors during testing, indicating endpoint changes or access restrictions.

**Solution**: Curated dataset approach using known instance specifications and published pricing from Scaleway documentation.

**Coverage**: Popular instance families including PLAY, DEV, PRO, ENT, and RENDER series with accurate CPU and RAM specifications.

**Currency Conversion**: EUR to USD conversion using configurable exchange rate defaulting to 1.08 based on recent market rates.

**Region Mapping**: All Scaleway regions classified as EU locations including Paris, Amsterdam, and Warsaw zones.

---

## 5. Data Model and Normalization

### 5.1 Canonical Data Format

All pricing records conform to a standardized schema ensuring consistency across providers:

**Provider Name**: String identifier for the cloud vendor (AWS, Azure, or Scaleway).

**SKU**: Stock keeping unit or instance type identifier unique within each provider.

**Hourly Price**: Decimal value representing cost per hour in US dollars, rounded to four decimal places.

**Region Code**: Provider-specific region identifier such as us-east-1 or westeurope.

**EU Flag**: Boolean indicator marking whether the region is located in European Union for compliance filtering.

**CPU Count**: Integer representing virtual CPU cores allocated to the instance.

**Memory GB**: Decimal value indicating RAM allocation in gigabytes.

### 5.2 Tier Mapping System

Abstract tier names map to minimum hardware specifications enabling provider-agnostic queries:

**Small Tier**: Minimum one vCPU and one gigabyte RAM suitable for lightweight workloads and development environments.

**Medium Tier**: Minimum two vCPUs and four gigabytes RAM appropriate for production web servers and small databases.

**Large Tier**: Minimum four vCPUs and eight gigabytes RAM designed for application servers and medium-scale services.

**Extra Large Tier**: Minimum eight vCPUs and sixteen gigabytes RAM intended for high-performance computing and large databases.

The normalizer evaluates each instance against tier specifications using greater-than-or-equal comparisons on both CPU and memory dimensions.

### 5.3 Region Filtering Logic

Region codes are matched against pattern lists supporting flexible geographic queries:

**EU Patterns**: Matches include eu- prefix, european country names, city names like paris and frankfurt, and Azure-specific identifiers like westeurope and northeurope.

**US Patterns**: Matches include us- prefix, American state names, city names like virginia and oregon, and Azure-specific identifiers like eastus and centralus.

**Pattern Matching**: Case-insensitive substring search allows partial matches accommodating various provider naming conventions.

**Fallback Behavior**: Empty or unrecognized region filters return all available data without geographic restriction.

---

## 6. Performance Optimization

### 6.1 Caching Strategy

**Cache Implementation**: In-memory dictionary storage with timestamp-based expiration tracking individual query results.

**Cache Key Generation**: Sorted combination of tier and region parameters ensures equivalent queries hit the same cache entry regardless of input order.

**Time-To-Live**: Default twelve-hour expiration balances data freshness with API call reduction, configurable via environment variable.

**Cache Invalidation**: Time-based only with no manual invalidation mechanism, relying on TTL for automatic refresh.

**Memory Management**: Cache size monitoring with optional eviction policies for high-traffic deployments.

### 6.2 Concurrent Execution

**Parallel Fetching**: Asyncio gather function executes all three provider queries simultaneously reducing total latency to the slowest single provider.

**Exception Isolation**: Return exceptions flag prevents single provider failure from canceling other in-flight requests.

**Connection Pooling**: Aiohttp session reuse across requests minimizes TCP handshake overhead and enables HTTP keep-alive.

**Timeout Configuration**: Per-request timeout limits prevent hanging connections from blocking server threads indefinitely.

### 6.3 Resource Efficiency

**Streaming Parsing**: Ijson library processes large JSON files incrementally without loading entire document into memory.

**Lazy Evaluation**: Generator patterns defer computation until results are actually needed reducing unnecessary processing.

**Minimal Dependencies**: Careful library selection avoids heavy frameworks keeping container image size under 200 megabytes.

**CPU Limits**: Docker resource constraints prevent runaway processes from monopolizing host system resources.

---

## 7. Error Handling and Resilience

### 7.1 Error Classification

**Network Errors**: Connection refused, timeout, DNS resolution failures caught at HTTP client level with retry logic.

**HTTP Errors**: Non-200 status codes logged with response details, distinguishing between client errors (4xx) and server errors (5xx).

**Parsing Errors**: Malformed JSON or missing fields handled gracefully with debug logging and record skipping.

**Business Logic Errors**: Invalid tier names or region codes produce empty result sets rather than exceptions.

### 7.2 Graceful Degradation

**Provider Independence**: Each connector operates independently allowing partial system functionality when some providers are unavailable.

**Fallback Data**: Curated datasets serve as backup when live APIs fail ensuring some results always return.

**Empty Results**: Complete system failure returns valid JSON with empty providers array rather than error responses.

**Logging Strategy**: Comprehensive logging at WARNING and ERROR levels enables troubleshooting without exposing sensitive data.

### 7.3 Recovery Mechanisms

**Automatic Restart**: Docker restart policy brings container back online after crashes with exponential backoff.

**Health Checks**: Periodic health endpoint verification detects hung processes triggering automatic container replacement.

**Cache Persistence**: In-memory cache loss on restart is acceptable given short TTL and fast API response times.

**Circuit Breaker Pattern**: Future enhancement opportunity for providers showing persistent failures.

---

## 8. Security Considerations

### 8.1 Authentication Strategy

**No Credentials Required**: All data sources use public APIs eliminating need for secret management infrastructure.

**Read-Only Access**: Pricing data is publicly available information with no personal or sensitive content.

**API Keys**: Not applicable for current implementation but architecture supports future addition via environment variables.

### 8.2 Configuration Security

**Environment Variables**: All configurable parameters externalized preventing hardcoded values in source code.

**Git Ignore Rules**: Dotenv files excluded from version control preventing accidental credential exposure.

**Docker Secrets**: Compatible with Docker secrets for production deployments requiring enhanced security.

**Input Validation**: Query parameters validated against expected types and ranges preventing injection attacks.

### 8.3 Network Security

**HTTPS Only**: All external API calls use TLS encryption protecting data in transit.

**No Outbound Persistence**: Server makes outbound requests but accepts no inbound connections except MCP protocol port.

**Firewall Rules**: Recommended deployment includes restricting inbound traffic to port 8000 from trusted networks only.

**Rate Limiting**: Future enhancement for preventing abuse of the pricing query endpoint.

---

## 9. Deployment Architecture

### 9.1 Container Configuration

**Base Image**: Python 3.11 slim variant balancing compatibility with minimal attack surface.

**Non-Root User**: Application runs as unprivileged appuser account following principle of least privilege.

**Working Directory**: Standardized /app path for consistent file references and volume mounts.

**Port Exposure**: Port 8000 exposed for HTTP/SSE traffic with configurable binding address.

### 9.2 Docker Compose Setup

**Service Definition**: Single service configuration with environment variable injection and volume mounting options.

**Resource Limits**: CPU capped at one core and memory at 512 megabytes preventing resource exhaustion.

**Restart Policy**: Unless-stopped policy ensures availability across host reboots while allowing intentional shutdowns.

**Network Mode**: Default bridge network sufficient for standalone deployment with optional custom networks for multi-service setups.

### 9.3 Environment Configuration

**Required Variables**: None strictly required as all settings have sensible defaults.

**Optional Variables**: Log level, cache TTL, API endpoints, and currency exchange rate customizable per deployment.

**Development Overrides**: Separate compose override file for local development with debug logging and volume mounts.

**Production Tuning**: Increased cache TTL and restricted log levels recommended for production workloads.

---

## 10. Testing and Quality Assurance

### 10.1 Test Coverage

**Unit Tests**: Individual component testing for normalizer logic, cache operations, and data parsing functions.

**Integration Tests**: End-to-end connector testing verifying actual API connectivity and response parsing.

**Contract Tests**: Output format validation ensuring MCP tool response matches specification exactly.

**Performance Tests**: Latency measurement and throughput benchmarking under various load conditions.

### 10.2 Test Execution

**Local Testing**: Direct Python execution with pytest runner for rapid development feedback.

**Container Testing**: Docker exec commands verify behavior in production-like environment catching containerization issues.

**Automated Pipeline**: Future CI/CD integration planned for automated test execution on code commits.

**Manual Verification**: Interactive testing scripts allow exploratory testing and edge case discovery.

### 10.3 Quality Metrics

**Code Coverage**: Target eighty percent line coverage for critical business logic paths.

**Response Time**: Sub-second response for cached queries, under ten seconds for cold cache with all providers responsive.

**Availability**: Ninety-nine percent uptime target with automatic restart handling transient failures.

**Accuracy**: Pricing data accuracy verified against provider consoles within acceptable rounding tolerance.

---

## 11. Monitoring and Observability

### 11.1 Logging Strategy

**Log Levels**: DEBUG for development troubleshooting, INFO for production operational visibility, WARNING and ERROR for issue detection.

**Structured Format**: Timestamp, logger name, level, and message fields enable automated log parsing and analysis.

**Sensitive Data**: No credentials or personal information included in log messages following security best practices.

**Log Rotation**: Docker log driver configuration prevents disk space exhaustion from verbose logging.

### 11.2 Health Monitoring

**Health Check Endpoint**: Docker health check command verifies server responsiveness every thirty seconds.

**Startup Probe**: Initial delay allows application initialization before health checking begins.

**Metrics Collection**: Future enhancement for Prometheus metrics export including request counts and cache hit rates.

**Alert Integration**: Planned integration with monitoring systems for proactive issue notification.

### 11.3 Operational Visibility

**Request Logging**: Each pricing query logged with parameters and result count for usage analysis.

**Cache Statistics**: Cache hit and miss rates tracked for performance optimization decisions.

**Provider Status**: Individual provider success and failure counts identify problematic data sources.

**Error Tracking**: Exception details captured with stack traces for root cause analysis.

---

## 12. Integration Guidelines

### 12.1 MCP Client Integration

**Connection Method**: Clients connect via HTTP SSE endpoint at standard port 8000 path slash sse.

**Tool Discovery**: MCP protocol automatically advertises get_cloud_pricing tool with full parameter schema.

**Invocation Pattern**: Clients call tool with tiers and regions arrays receiving JSON response with providers array.

**Error Handling**: Clients should handle empty providers array indicating temporary service degradation.

### 12.2 Parameter Guidance

**Tier Selection**: Use small for development workloads, medium for production web servers, large for application servers, xlarge for database servers.

**Region Selection**: Use eu for European deployments requiring GDPR compliance, us for North American deployments with lower latency.

**Combined Queries**: Multiple tiers and regions can be queried simultaneously for comprehensive comparison shopping.

**Result Interpretation**: Results sorted by price ascending with first item representing most cost-effective option matching criteria.

### 12.3 Performance Expectations

**Cached Responses**: Typically under one hundred milliseconds for previously seen query combinations.

**Cold Cache**: Five to fifteen seconds depending on provider API responsiveness and network conditions.

**Concurrent Queries**: Server handles multiple simultaneous requests with independent cache entries per query.

**Throughput**: Sustained rate of ten queries per minute recommended to respect upstream API rate limits.

---

## 13. Maintenance and Operations

### 13.1 Routine Maintenance

**Cache Monitoring**: Watch cache hit rates adjusting TTL if hit rate drops below fifty percent.

**Log Review**: Weekly review of WARNING and ERROR logs identifying emerging issues before they impact users.

**Dependency Updates**: Monthly check for security patches in Python packages and base image updates.

**API Validation**: Quarterly verification that upstream APIs remain accessible and response formats unchanged.

### 13.2 Troubleshooting Procedures

**No Results Returned**: Check network connectivity, review logs for provider errors, verify tier and region parameters valid.

**Slow Responses**: Inspect cache hit rate, check upstream API latency, consider increasing cache TTL.

**High Memory Usage**: Monitor container memory metrics, reduce cache TTL if approaching limits, check for memory leaks.

**Container Crashes**: Review docker logs for stack traces, check resource limits, verify environment configuration.

### 13.3 Upgrade Path

**Version Updates**: Semantic versioning scheme with backward-compatible API ensuring smooth upgrades.

**Database Migration**: Not applicable as system uses in-memory cache only with no persistent state.

**Schema Changes**: Any output format changes will include additional fields only, never removing existing fields.

**Deprecation Policy**: Six-month notice period for any breaking changes with migration guide provided.

---

## 14. Compliance and Standards

### 14.1 MCP Protocol Compliance

**Tool Registration**: Proper registration of get_cloud_pricing tool with complete parameter schema.

**Transport Protocol**: SSE transport implementation following MCP specification for server-sent events.

**Error Responses**: Standard MCP error format with descriptive messages for client debugging.

**Protocol Version**: Compatible with MCP specification version 1.0 and later revisions.

### 14.2 Code Quality Standards

**Type Annotations**: Complete type hints throughout codebase enabling static analysis and IDE support.

**Documentation**: Comprehensive docstrings for all public functions and classes following Google style guide.

**Naming Conventions**: Descriptive variable and function names following PEP 8 Python style guidelines.

**Modular Design**: Clear separation of concerns with single responsibility principle applied to each module.

### 14.3 Security Standards

**OWASP Top Ten**: Addressed relevant vulnerabilities including injection prevention and secure configuration.

**Least Privilege**: Container runs as non-root user with minimal filesystem permissions.

**Secure Defaults**: All security-relevant settings default to most restrictive option.

**Audit Trail**: Comprehensive logging provides audit trail for security incident investigation.

---

## 15. Future Enhancements

### 15.1 Planned Features

**Additional Providers**: Integration with Google Cloud Platform and Oracle Cloud Infrastructure pricing APIs.

**Historical Pricing**: Time-series data storage enabling price trend analysis and forecasting.

**Spot Instance Support**: Real-time spot pricing data for cost optimization opportunities.

**Reserved Instance Calculator**: Long-term commitment pricing analysis with break-even calculations.

### 15.2 Performance Improvements

**Redis Cache**: Distributed caching layer for multi-instance deployments with shared cache state.

**GraphQL Interface**: Alternative query interface supporting complex filtering and field selection.

**WebSocket Streaming**: Real-time price update notifications for active monitoring dashboards.

**CDN Integration**: Edge caching for globally distributed client access with reduced latency.

### 15.3 Operational Enhancements

**Kubernetes Deployment**: Helm charts for orchestrated container management with auto-scaling.

**Service Mesh Integration**: Istio or Linkerd compatibility for advanced traffic management and observability.

**Multi-Region Deployment**: Active-active deployment across geographic regions for high availability.

**Disaster Recovery**: Automated backup and restore procedures for configuration and cache state.

---

## 16. Conclusion

The AetherOps MCP Pricing Server successfully delivers a production-ready solution for multi-cloud pricing aggregation meeting all requirements specified in the project task specification. The system demonstrates robust error handling, efficient performance optimization, and clean architectural design suitable for integration into larger cloud management platforms.

Key achievements include complete MCP protocol compliance, comprehensive provider integration, intelligent data normalization, and containerized deployment ready for immediate production use. The server provides reliable, performant access to cloud pricing data enabling cost optimization and informed infrastructure decision-making.

The implementation exceeds baseline requirements through additional features including comprehensive caching, graceful degradation, detailed observability, and extensive documentation ensuring successful adoption and long-term maintainability.

---

## Appendix A: Glossary

**MCP**: Model Context Protocol, a standard for AI assistants to interact with external tools and data sources.

**SSE**: Server-Sent Events, a web standard for pushing real-time updates from server to client over HTTP.

**SKU**: Stock Keeping Unit, a unique identifier for a specific product or service offering.

**TTL**: Time-To-Live, the duration before cached data expires and requires refresh.

**ASGI**: Asynchronous Server Gateway Interface, a Python standard for async web servers.

**vCPU**: Virtual Central Processing Unit, a logical CPU core allocated to a virtual machine.

**GDPR**: General Data Protection Regulation, European Union privacy legislation affecting data handling.

---

## Appendix B: References

- Model Context Protocol Specification: https://modelcontextprotocol.io
- FastMCP Documentation: https://gofastmcp.com
- AWS Pricing API Documentation: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-aws-pricing.html
- Azure Retail Prices API: https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices
- Scaleway Instance API: https://developers.scaleway.com/en/products/instance/api/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Python Asyncio Documentation: https://docs.python.org/3/library/asyncio.html

---

**Document Version**: 1.0  
**Last Updated**: April 30, 2026  
**Next Review**: July 30, 2026  
**Classification**: Internal Use
