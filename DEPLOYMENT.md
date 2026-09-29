# Cloud Deployment Guide (AWS & Azure)

This platform is containerized and cloud-ready for orchestration on **AWS ECS / EKS** or **Azure App Service / AKS**.

---

## 1. Architecture on AWS

- **Frontend**: Amazon S3 + CloudFront CDN, or AWS App Runner / ECS Fargate.
- **Backend API**: AWS ECS Fargate or EKS running the FastAPI container.
- **Relational Database**: Amazon Aurora PostgreSQL with PostGIS extension (`CREATE EXTENSION postgis;`).
- **Document Database**: Amazon DocumentDB (MongoDB-compatible) or AWS DynamoDB.
- **Storage / Reports**: Amazon S3 for generated PDF/Excel reports.
- **Secrets**: AWS Secrets Manager or Parameter Store.

```bash
# Push Backend Image to Amazon ECR:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com
docker tag solar_wind_backend:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/solar-wind-backend:v1.0.0
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/solar-wind-backend:v1.0.0
```

---

## 2. Architecture on Azure

- **Frontend**: Azure Static Web Apps or Azure Container Apps.
- **Backend API**: Azure App Service (Linux Container) or Azure Container Apps.
- **Relational Database**: Azure Database for PostgreSQL Flexible Server with PostGIS enabled.
- **Document Database**: Azure Cosmos DB with MongoDB API.
- **Blob Storage**: Azure Blob Storage for reports and spatial raster tiles.

```bash
# Push Backend Image to Azure Container Registry (ACR):
az acr login --name <acr_name>
docker tag solar_wind_backend:latest <acr_name>.azurecr.io/solar-wind-backend:v1.0.0
docker push <acr_name>.azurecr.io/solar-wind-backend:v1.0.0
```

---

## 3. Environment Variables in Production

Ensure the following variables are configured in your Cloud container settings:
- `DATABASE_URL`: Production PostgreSQL + PostGIS connection string.
- `MONGODB_URL`: Production DocumentDB / Cosmos DB connection string.
- `JWT_SECRET`: High-entropy 256-bit cryptographically secure secret.
- `CORS_ORIGINS`: Comma-separated list of allowed frontend domain origins.
- `ELECTRICITY_PRICE_PER_KWH`: Default regional wholesale PPA rate.
