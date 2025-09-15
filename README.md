# Stonkulator

**Purpose:** Stonkulator is a personal stock market dashboard built in python using the Panel and yFinance libraries. Its goal is to display stock market data for selected financial instruments as charts and calculate returns, key statistics and run simulations of relevant market information.

**Solution:** A containerized dashboard using Panel and yFinance deployed via GCP Cloud Run. Data is cached using DuckDB with Cloud Storage persistence.

## Deploy
```bash
gcloud run deploy stonkulator --source . --platform managed --region us-central1 --allow-unauthenticated
```
