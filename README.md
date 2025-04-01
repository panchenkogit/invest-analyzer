# Stock Fundamental Data API

## Overview
This API provides fundamental financial data for US companies. It follows a **microservice architecture** with two core services:

### 1. Data Collector Service
- **Purpose**: Collects company data from Alpha Vantage and stores it in the database.
- **Database**: MongoDB (chosen for its flexibility with dynamic schemas, as Alpha Vantage responses contain approximately 50 fields, some of which are optional).
- **Caching**: Redis (TTL: 24 hours) to reduce external API calls.

#### Endpoint: `/fetch`
- **Method**: GET
- **Parameters**: `symbol` (comma-separated list of tickers, e.g., `AAPL,MSFT`).
- **Workflow**:
  1. Check Redis → return cached data if available.
  2. If not in Redis, check MongoDB → return DB data.
  3. If not in MongoDB, fetch from Alpha Vantage → save to MongoDB and Redis → return data.

**Example Response**:
```json
[
  {
    "ticker": "AAPL",
    "data": {
      "MarketCapitalization": 2000000000,
      "RevenueTTM": 300000000
      // ... other fields
    }
  },
  {
    "ticker": "MSFT",
    "data": {
      "MarketCapitalization": 1500000000,
      "RevenueTTM": 200000000
      // ... other fields
    }
  }
]
```

### 2. Cluster Service
- **Purpose**: Assigns clusters to companies based on their fundamental data using machine learning.
- **Database**: MongoDB (shared with Data Collector Service for accessing company data).
- **Clustering**: Uses scikit-learn with features like MarketCapitalization, RevenueTTM, and others.

#### Endpoint: `/update-company`
- **Method**: POST
- **Parameters**: Request body with ticker and data (e.g., financial metrics for a company).
- **Workflow**:
  1. Save or update company data in MongoDB → ensure data is stored.
  2. Assign a cluster using predefined features → return the cluster assignment.

**Example Response**:
```json
{
  "ticker": "AAPL",
  "cluster": 2
}
```

## Technology Stack
- **Programming Language**: Python 3.8+
- **Framework**: FastAPI (for building both microservices)
- **Databases**:
  - MongoDB (for persistent storage)
  - Redis (for caching)
- **Libraries**:
  - scikit-learn (for clustering in Cluster Service)
  - Pydantic (for data validation)
  - pymongo (for MongoDB interaction)
- **External API**: Alpha Vantage (for fetching financial data)
- **Containerization**: Docker (for deployment)
