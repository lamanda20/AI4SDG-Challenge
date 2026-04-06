# Deployment Guide - SportRX AI ML Module

## 🚀 Quick Start (Development)

### 1. Installation locale
```bash
# Clone repo
cd C:\Users\dell\PycharmProjects\AI4SDG-Challenge

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies (minimal)
pip install pydantic fastapi uvicorn

# Or for full stack (with ML):
pip install -r requirements.txt

# Run demo
python backend/ml/sentiment_analysis.py
python backend/ml/pipeline.py
```

### 2. Test the ML module
```bash
# Test sentiment analysis
python -c "from backend.ml.sentiment_analysis import SentimentAnalyzer; \
analyzer = SentimentAnalyzer(); \
result = analyzer.analyze_sentiment('I feel great!'); \
print(f'Sentiment: {result.label}, Score: {result.score}')"

# Test complete pipeline
python backend/ml/pipeline.py

# Run tests
pytest backend/ml/test_ml.py -v
```

### 3. Start API server
```bash
# Development server
python -m uvicorn backend.main:app --reload --port 8000

# Production server
python -m uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY .env .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from backend.ml.pipeline import get_ml_pipeline; get_ml_pipeline().health_check()"

# Start API
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/sportrx_ai
      - ML_MODEL_TYPE=heuristic
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: sportrx_ai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Build & Run
```bash
# Build image
docker build -t sportrx-ai-ml .

# Run container
docker run -p 8000:8000 sportrx-ai-ml

# Or use docker-compose
docker-compose up -d
```

## ☁️ Cloud Deployment Options

### AWS Lambda (Serverless)
```python
# handler.py - AWS Lambda entry point
from backend.ml.pipeline import get_ml_pipeline
import json

def lambda_handler(event, context):
    """AWS Lambda handler for ML predictions"""
    try:
        body = json.loads(event['body'])
        pipeline = get_ml_pipeline()
        result = pipeline.process_user_profile(body)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
```

### Google Cloud Run
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/sportrx-ml

# Deploy
gcloud run deploy sportrx-ml \
  --image gcr.io/PROJECT_ID/sportrx-ml \
  --platform managed \
  --region europe-west1 \
  --memory 512Mi \
  --cpu 1
```

### Azure Container Instances
```bash
# Build image
docker build -t sportrx-ml:latest .

# Push to Azure Registry
az acr build --registry <registry-name> --image sportrx-ml:latest .

# Deploy
az container create \
  --resource-group <group-name> \
  --name sportrx-ml \
  --image <registry-name>.azurecr.io/sportrx-ml:latest \
  --cpu 1 --memory 1
```

## 📊 Performance Tuning

### Model Optimization
```python
# For production, consider:
# 1. Model quantization (reduce size)
# 2. Caching predictions for same profiles
# 3. Batch processing for multiple users

# Example: Simple caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_predict(user_profile_hash):
    # This would cache results
    pass
```

### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_user_id ON user_profiles(user_id);
CREATE INDEX idx_created_at ON predictions(created_at);
CREATE INDEX idx_risk_level ON risk_assessments(risk_level);

-- Partitioning for large tables
CREATE TABLE predictions_2026_q1 PARTITION OF predictions
FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```

### API Optimization
```bash
# Use async/await for I/O operations
# Enable compression
# Implement rate limiting
# Use CDN for static assets
# Enable CORS caching
```

## 🔒 Security Checklist

- [ ] Validate all inputs (Pydantic)
- [ ] Use HTTPS in production
- [ ] Implement authentication (JWT)
- [ ] Add rate limiting
- [ ] Sanitize error messages
- [ ] Log security events
- [ ] Use environment variables for secrets
- [ ] Enable CORS restrictions
- [ ] Implement API versioning
- [ ] Regular dependency updates

## 📈 Monitoring & Observability

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Prediction for user {user_id}: risk_score={risk_score}")
logger.warning(f"High risk detected: {warnings}")
logger.error(f"Prediction failed: {error}")
```

### Metrics
```python
from prometheus_client import Counter, Histogram

prediction_counter = Counter('ml_predictions_total', 'Total predictions')
prediction_latency = Histogram('ml_prediction_latency_seconds', 'Prediction latency')
```

### Health Checks
```bash
# Health endpoint
GET /health
→ 200 OK: {"status": "healthy", "version": "1.0"}
GET /health/ready
→ 200 OK: {"ready": true}
```

## 🧪 Load Testing

### Using locust
```python
from locust import HttpUser, task, between

class MLUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def predict(self):
        self.client.post("/api/ml/analyze", json={
            "user_id": "test_user",
            "age": 55,
            "bmi": 28.5,
            # ... other fields
        })
```

```bash
# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

## 📋 Deployment Checklist

Before deploying to production:

### Code
- [ ] All tests passing
- [ ] Code review completed
- [ ] No secrets in code
- [ ] No hardcoded URLs/credentials
- [ ] Logging is appropriate
- [ ] Error handling comprehensive

### Configuration
- [ ] Environment variables configured
- [ ] Database credentials secure
- [ ] API keys rotated
- [ ] Timeouts appropriate
- [ ] Resource limits set

### Data
- [ ] Database migrations run
- [ ] Backup strategy in place
- [ ] Data retention policy defined
- [ ] Privacy compliance verified (GDPR)

### Monitoring
- [ ] Logging system active
- [ ] Metrics collection enabled
- [ ] Alerting configured
- [ ] Health checks working

### Documentation
- [ ] README updated
- [ ] API documentation current
- [ ] Runbooks prepared
- [ ] Incident response plan ready

## 🚨 Troubleshooting

### Common Issues

**Issue**: ImportError: No module named 'xgboost'
**Solution**: Fallback to heuristic model (automatic) or install: `pip install xgboost`

**Issue**: Database connection timeout
**Solution**: Check DATABASE_URL, increase connection pool, check firewall

**Issue**: Slow predictions
**Solution**: Enable caching, optimize features, reduce batch size

**Issue**: Memory spike
**Solution**: Reduce cache size, enable garbage collection, profile code

## 📞 Support

**Issues**: Check logs in `logs/ml_pipeline.log`
**Metrics**: Dashboard at `/metrics`
**Health**: API health at `/api/ml/health`
**Contact**: ML module maintainer (Taha)

---

**Version**: 1.0  
**Last Updated**: April 4, 2026  
**Status**: Production Ready

