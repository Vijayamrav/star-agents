# AI Data Analyst Agent Platform

A full-stack platform that uses AI agents to automatically analyze uploaded datasets, generate insights, create visualizations, and answer follow-up questions.

![Platform](https://img.shields.io/badge/Platform-Full--Stack-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-blue)
![AI](https://img.shields.io/badge/AI-LangGraph%20%2B%20DeepSeek-purple)

## ✨ Features

- **🧹 Automatic Data Cleaning**: Handles missing values, duplicates, and data type conversions
- **📊 Statistical Analysis**: Generates comprehensive summary statistics and correlations
- **🔍 Anomaly Detection**: Uses Isolation Forest and statistical methods to detect outliers
- **📈 Automated Visualizations**: Creates histograms, scatter plots, correlation heatmaps, and bar charts
- **💡 AI-Powered Insights**: Leverages DeepSeek LLM to generate natural language insights and recommendations
- **🗄️ SQL Generation**: Automatically creates SQL schemas and INSERT statements for PostgreSQL
- **💬 Interactive Q&A**: Ask follow-up questions about your dataset using natural language

## 🏗️ Architecture

### Backend
- **FastAPI**: High-performance Python web framework
- **LangGraph**: Orchestrates 7 specialized AI agent nodes in a workflow
- **PostgreSQL**: Stores dataset metadata and analysis results
- **DeepSeek AI**: Powers insights generation and Q&A capabilities

### Frontend
- **React 18 + TypeScript**: Type-safe component architecture
- **Vite**: Lightning-fast development and build tool
- **Modern CSS**: Dark theme with glassmorphism and smooth animations

### AI Agent Workflow
```
Upload → Clean Data → Generate Statistics → Detect Anomalies → 
Create Visualizations → Generate Insights → Generate SQL → Complete
```

## 📋 Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (running instance)
- **DeepSeek API Key** ([Get one here](https://platform.deepseek.com/))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd "Data Analyst Agent"
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env
# Edit .env with your PostgreSQL connection and DeepSeek API key
```

**Edit `.env` file:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/data_analyst_db
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
UPLOAD_DIR=./uploads
VISUALIZATIONS_DIR=./visualizations
```

### 3. Set Up Database

Create a PostgreSQL database:
```sql
CREATE DATABASE data_analyst_db;
```

The tables will be created automatically when you start the backend.

### 4. Start Backend Server

# Install dependencies
## 🎯 API Endpoints

### Upload File
```http
POST /api/upload
Content-Type: multipart/form-data

Response: { dataset_id, filename, rows, columns }
```

### Analyze Dataset
```http
POST /api/analyze/{dataset_id}

Response: { analysis_id, status, message }
```

### Get Analysis Results
```http
GET /api/analysis/{analysis_id}

Response: { statistics, anomalies, insights, visualizations, sql_queries }
```

### Ask Question
```http
POST /api/question
Content-Type: application/json

Body: { dataset_id, question }
Response: { question, answer }
```

### List Datasets
```http
GET /api/datasets

Response: [{ id, filename, upload_date, rows, columns }]
```

## 🧪 Testing

### Test with Sample Data

Create a sample CSV file (`sample_data.csv`):
```csv
name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
Alice,28,55000,Sales
Charlie,32,65000,Marketing
```

Upload this file through the UI and observe the analysis results.

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | FastAPI |
| AI Orchestration | LangGraph |
| LLM Provider | DeepSeek |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Data Processing | pandas, numpy |
| ML/Anomaly Detection | scikit-learn |
| Visualization | matplotlib, seaborn |
| Frontend Framework | React 18 |
| Type Safety | TypeScript |
| Build Tool | Vite |
| HTTP Client | Axios |
| Routing | React Router |

## 📁 Project Structure

```
Data Analyst Agent/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py          # Agent state definition
│   │   ├── nodes.py          # 7 agent nodes
│   │   ├── graph.py          # LangGraph workflow
│   │   └── qa_agent.py       # Q&A functionality
│   ├── main.py               # FastAPI application
│   ├── database.py           # Database configuration
│   ├── models.py             # SQLAlchemy models
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── AnalysisDashboard.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | `sk-...` |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL | `https://api.deepseek.com/v1` |
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `VISUALIZATIONS_DIR` | Directory for generated charts | `./visualizations` |

## 🎨 Features in Detail

### Data Cleaning Agent
- Removes duplicate rows
- Handles missing values (median for numeric, mode for categorical)
- Reports cleaning statistics

### Statistics Agent
- Descriptive statistics for numeric columns
- Value counts for categorical columns
- Correlation matrix

### Anomaly Detection Agent
- IQR-based outlier detection
- Isolation Forest for multivariate anomalies
- Detailed anomaly reports

### Visualization Agent
- Histograms for numeric distributions
- Correlation heatmaps
- Bar charts for categorical data
- Scatter plots for relationships

### Insights Agent
- Natural language insights using DeepSeek LLM
- Pattern identification
- Business recommendations

### SQL Generation Agent
- CREATE TABLE statements
- Sample INSERT statements
- PostgreSQL-compatible syntax

### Q&A Agent
- Context-aware question answering
- Uses dataset schema and statistics
- Powered by DeepSeek LLM

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error:**
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists

**API Key Error:**
- Verify `DEEPSEEK_API_KEY` is set correctly
- Check API key is valid at DeepSeek platform

### Frontend Issues

**Cannot Connect to Backend:**
- Ensure backend is running on port 8000
- Check Vite proxy configuration in `vite.config.ts`

**Build Errors:**
- Delete `node_modules` and run `npm install` again
- Ensure Node.js version is 18+

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ using LangGraph, FastAPI, React, and DeepSeek AI**
