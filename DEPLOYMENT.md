# Deployment Guide

This guide covers different ways to deploy the Data Analyst Agent API.

## Prerequisites

1. Python 3.9 or higher
2. OpenAI API key
3. Git

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd data-analyst-agent
```

2. Set up virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Deployment Options

### 1. Heroku (Recommended for quick deployment)

1. Install Heroku CLI and login:
```bash
heroku login
```

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Set environment variables:
```bash
heroku config:set OPENAI_API_KEY="your-openai-api-key"
```

4. Deploy:
```bash
git push heroku main
```

Your API will be available at `https://your-app-name.herokuapp.com/`

### 2. Railway

1. Go to [railway.app](https://railway.app) and connect your GitHub repo
2. Set the `OPENAI_API_KEY` environment variable in Railway dashboard
3. Deploy automatically on push

### 3. Render

1. Go to [render.com](https://render.com) and create a new Web Service
2. Connect your GitHub repository
3. Set environment variables:
   - `OPENAI_API_KEY`: your OpenAI API key
4. Deploy

### 4. Google Cloud Run

1. Install Google Cloud SDK
2. Build and push Docker image:
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/data-analyst-agent
```

3. Deploy:
```bash
gcloud run deploy --image gcr.io/PROJECT-ID/data-analyst-agent --platform managed
```

### 5. AWS Lambda (using Mangum)

1. Add `mangum` to requirements.txt
2. Create lambda handler:
```python
from mangum import Mangum
from main import app

handler = Mangum(app)
```

3. Deploy using AWS CLI or Serverless Framework

### 6. DigitalOcean App Platform

1. Go to DigitalOcean Apps
2. Create app from GitHub repository  
3. Set environment variables
4. Deploy

### 7. Docker Deployment

1. Build Docker image:
```bash
docker build -t data-analyst-agent .
```

2. Run container:
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" data-analyst-agent
```

Or use docker-compose:
```bash
docker-compose up
```

### 8. Ngrok (For testing/development)

If you want to quickly expose your local development server:

1. Install ngrok: https://ngrok.com/download
2. Start your local server:
```bash
uvicorn main:app --port 8000
```

3. In another terminal:
```bash
ngrok http 8000
```

4. Use the provided HTTPS URL for testing

## Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `PORT` (optional): Port to run the server on (default: 8000)
- `DEBUG` (optional): Enable debug mode (default: False)

## Testing Your Deployment

1. Health check:
```bash
curl https://your-deployed-url/health
```

2. Test with sample data:
```bash
curl "https://your-deployed-url/api/" \
  -F "questions.txt=@examples/simple_analysis_questions.txt" \
  -F "sample_movies.csv=@examples/sample_movies.csv"
```

## Performance Considerations

1. **Timeout**: Some analyses may take time. Consider increasing timeout limits.
2. **Memory**: Large datasets may require more memory. Monitor usage.
3. **Rate Limits**: OpenAI API has rate limits. Consider implementing request queuing.
4. **Caching**: Consider caching results for repeated queries.

## Security

1. Keep your OpenAI API key secure
2. Consider adding API authentication
3. Validate input files and sizes
4. Monitor API usage to prevent abuse

## Monitoring

1. Check logs regularly: `logs/app.log`
2. Monitor API response times
3. Track OpenAI API usage and costs
4. Set up alerts for errors

## Troubleshooting

### Common Issues:

1. **Import errors**: Ensure all dependencies are installed
2. **OpenAI API errors**: Check your API key and quota
3. **Memory errors**: Reduce data size or increase server memory
4. **Timeout errors**: Increase timeout settings

### Debug Mode:

Set `DEBUG=True` in `.env` for verbose logging.

### Logs:

Check `logs/app.log` for detailed error information.
