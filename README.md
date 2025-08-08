# Data Analyst Agent API

A comprehensive API that uses Large Language Models (LLMs) to source, prepare, analyze, and visualize data. This API can handle web scraping, data analysis, statistical computations, and generate visualizations - all through natural language questions.

## 🚀 Features

### Core Capabilities
- **Intelligent Data Sourcing**: Web scraping from various sources including Wikipedia
- **Data Preparation**: Automatic data cleaning, transformation, and preprocessing  
- **Advanced Analytics**: Statistical analysis, correlation, regression, and more
- **Smart Visualizations**: Automatically generate charts, plots, and graphs
- **LLM Integration**: Uses OpenAI GPT for intelligent analysis and code generation
- **Multi-format Support**: CSV, JSON, Excel, Parquet, and more

### Supported Analysis Types
- **Web Scraping**: Extract data from websites and APIs
- **Statistical Analysis**: Correlations, regressions, hypothesis testing
- **Data Visualization**: Scatterplots, bar charts, histograms, line plots
- **Database Queries**: DuckDB support for large-scale data analysis
- **Custom Analysis**: Any analysis that can be expressed in natural language

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Usage](#api-usage)
- [Examples](#examples)
- [Deployment](#deployment)
- [Development](#development)
- [Contributing](#contributing)

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/data-analyst-agent.git
cd data-analyst-agent
```

2. **Set up virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_openai_api_key_here
```

5. **Start the server:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 🔧 API Usage

### Endpoint

**POST** `/api/`

### Request Format

Send a `multipart/form-data` request with:
- **questions.txt** (required): File containing your analysis questions
- **Additional files** (optional): CSV, JSON, Excel files with your data

### Example Request

```bash
curl "http://localhost:8000/api/" \
  -F "questions.txt=@questions.txt" \
  -F "data.csv=@data.csv"
```

### Response Format

The API returns results in the format specified in your questions:
- **JSON Array**: `[1, "Titanic", 0.485782, "data:image/png;base64,iV..."]`
- **JSON Object**: `{"answer1": 42, "answer2": "result", ...}`

## 📊 Examples

### Example 1: Wikipedia Film Analysis

**questions.txt:**
```
Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings:

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak with a dotted red regression line.
   Return as a base-64 encoded data URI under 100,000 bytes.
```

**Request:**
```bash
curl "http://localhost:8000/api/" \
  -F "questions.txt=@questions.txt"
```

**Response:**
```json
[1, "Titanic", 0.485782, "data:image/png;base64,iVBORw0KG..."]
```

### Example 2: CSV Data Analysis

**questions.txt:**
```
Analyze the provided movie data and answer:

1. What is the average worldwide gross?
2. How many movies grossed over $2 billion?
3. What is the correlation between Rank and Worldwide_Gross?
4. Create a bar chart of top 5 movies. Return as base64 data URI.
```

**data.csv:**
```csv
Title,Worldwide_Gross,Year,Rank
Avatar,2923706026,2009,1
Titanic,2257844554,1997,2
...
```

**Request:**
```bash
curl "http://localhost:8000/api/" \
  -F "questions.txt=@questions.txt" \
  -F "data.csv=@data.csv"
```

### Example 3: Database Query Analysis

**questions.txt:**
```
Query the Indian high court dataset and respond with a JSON object:

{
  "Which high court disposed the most cases from 2019-2022?": "...",
  "What's the regression slope of registration to decision date by year?": "...",
  "Plot delay days by year as scatterplot with regression line": "data:image/webp;base64,..."
}

Use this DuckDB query to start:
SELECT COUNT(*) FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet?s3_region=ap-south-1');
```

## 🚀 Deployment

Multiple deployment options are available:

### Quick Deploy (Heroku)
```bash
heroku create your-app-name
heroku config:set OPENAI_API_KEY="your-key"
git push heroku main
```

### Docker
```bash
docker build -t data-analyst-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" data-analyst-agent
```

### Other Platforms
- **Railway**: Connect GitHub repo and deploy
- **Render**: Create web service from repository  
- **Google Cloud Run**: Deploy container
- **AWS Lambda**: Use with Mangum adapter

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔍 API Reference

### Endpoints

- `GET /` - API information and status
- `GET /health` - Health check endpoint
- `POST /api/` - Main analysis endpoint

### Supported File Formats

- **Data**: CSV, JSON, Excel (xlsx/xls), Parquet
- **Questions**: Text files (.txt)
- **Images**: PNG, JPG, JPEG (for context)

### Environment Variables

- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `PORT` (optional) - Server port (default: 8000)
- `DEBUG` (optional) - Enable debug logging (default: False)

## 🔐 LLM Configuration

Supports any OpenAI-compatible endpoint.

Environment variables (first found is used):
- OPENAI_API_KEY / AI_PIPE_TOKEN / AIPIPE_API_KEY / AI_PIPE_API_KEY
- OPENAI_BASE_URL / AI_PIPE_BASE_URL (e.g. https://api.aipipe.example/v1)
- LLM_MODEL (default: gpt-4)

Example (.env):
```
AI_PIPE_TOKEN=sk-your-ai-pipe-token
AI_PIPE_BASE_URL=https://api.aipipe.yourdomain/v1
LLM_MODEL=gpt-4o-mini
```

If no key is provided the system falls back to heuristic parsing (limited functionality).

## 🛠 Development

### Project Structure
```
data-analyst-agent/
├── main.py                 # FastAPI application
├── services/              # Core services
│   ├── data_processor.py  # Data loading and processing
│   ├── llm_analyzer.py    # LLM integration
│   └── visualization_engine.py # Chart generation
├── utils/                 # Utilities
│   ├── file_handler.py    # File operations
│   └── logging_config.py  # Logging setup
├── examples/              # Example files
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Adding New Features

1. **New Analysis Types**: Add handlers in `main.py`
2. **Data Sources**: Extend `data_processor.py` 
3. **Visualization Types**: Add to `visualization_engine.py`
4. **LLM Capabilities**: Enhance `llm_analyzer.py`

### Testing

Run the test suite:
```bash
python test_api.py
```

Test specific examples:
```bash
python test_api.py http://localhost:8000
```

## 📈 Performance Tips

1. **Large Datasets**: Use DuckDB queries for efficient processing
2. **Image Size**: Keep visualizations under 100KB as requested
3. **Timeouts**: Complex analyses may take 2-3 minutes
4. **API Limits**: Monitor OpenAI usage and implement rate limiting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## 🔒 Security

- Keep your OpenAI API key secure and never commit it
- Validate all input files before processing
- Monitor API usage to prevent abuse
- Consider implementing authentication for production use

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/data-analyst-agent/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/data-analyst-agent/wiki)
- **Deployment Help**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🎯 Roadmap

- [ ] Support for more data sources (APIs, databases)
- [ ] Advanced statistical analysis methods
- [ ] Interactive visualizations
- [ ] Caching and performance improvements
- [ ] Authentication and rate limiting
- [ ] Real-time data streaming support

---

**Made with ❤️ for the TDS Data Analyst Agent Challenge**
