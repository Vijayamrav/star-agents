from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import shutil
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from database import get_db, init_db
from models import Dataset, Analysis, Visualization
from agents.graph import analysis_graph
from agents.qa_agent import answer_question
from agents.text_to_sql_agent import generate_sql_query

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Data Analyst Agent Platform",
    description="Upload datasets and get AI-powered analysis, insights, and visualizations",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
VIZ_DIR = os.getenv("VISUALIZATIONS_DIR", "./visualizations")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VIZ_DIR, exist_ok=True)

# Mount static files for visualizations
app.mount("/visualizations", StaticFiles(directory=VIZ_DIR), name="visualizations")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Pydantic models for requests/responses
class QuestionRequest(BaseModel):
    dataset_id: int
    question: str


class TextToSQLRequest(BaseModel):
    dataset_id: int
    question: str


class AnalysisResponse(BaseModel):
    analysis_id: int
    status: str
    message: str


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Data Analyst Agent Platform API"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV or Excel file for analysis
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload CSV or Excel files only."
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Load file to get basic info
        import pandas as pd
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Create dataset record
        dataset = Dataset(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            rows_count=len(df),
            columns_count=len(df.columns),
            column_names=df.columns.tolist()
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return {
            "dataset_id": dataset.id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "message": "File uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/analyze/{dataset_id}", response_model=AnalysisResponse)
async def analyze_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Run AI analysis on uploaded dataset
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create analysis record
        analysis = Analysis(
            dataset_id=dataset_id,
            status="processing"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Run LangGraph workflow
        initial_state = {
            "dataset_id": dataset_id,
            "file_path": dataset.file_path,
            "filename": dataset.original_filename,
            "visualizations": [],
            "errors": [],
            "status": "processing"
        }
        
        # Execute the graph
        result = analysis_graph.invoke(initial_state)
        
        # Check for errors
        if result.get("errors"):
            analysis.status = "failed"
            analysis.error_message = "; ".join(result["errors"])
            db.commit()
            raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis.error_message}")
        
        # Save results to database
        analysis.cleaned_data_info = result.get("cleaning_report")
        analysis.statistics = result.get("statistics")
        analysis.anomalies = result.get("anomalies")
        analysis.insights = result.get("insights")
        analysis.sql_queries = result.get("sql_queries")
        analysis.status = "completed"
        db.commit()
        
        # Save visualizations
        for viz in result.get("visualizations", []):
            visualization = Visualization(
                analysis_id=analysis.id,
                visualization_type=viz.get("type"),
                file_path=viz.get("filename")
            )
            db.add(visualization)
        db.commit()
        
        return AnalysisResponse(
            analysis_id=analysis.id,
            status="completed",
            message="Analysis completed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Update analysis status
        if 'analysis' in locals():
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get analysis results
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Get visualizations
    visualizations = db.query(Visualization).filter(
        Visualization.analysis_id == analysis_id
    ).all()
    
    return {
        "id": analysis.id,
        "dataset_id": analysis.dataset_id,
        "status": analysis.status,
        "analysis_date": analysis.analysis_date,
        "cleaning_report": analysis.cleaned_data_info,
        "statistics": analysis.statistics,
        "anomalies": analysis.anomalies,
        "insights": analysis.insights,
        "sql_queries": analysis.sql_queries,
        "visualizations": [
            {
                "id": viz.id,
                "type": viz.visualization_type,
                "url": f"/visualizations/{viz.file_path}"
            }
            for viz in visualizations
        ],
        "error_message": analysis.error_message
    }


@app.post("/api/question")
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Ask a follow-up question about the dataset
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get latest analysis for statistics
        analysis = db.query(Analysis).filter(
            Analysis.dataset_id == request.dataset_id,
            Analysis.status == "completed"
        ).order_by(Analysis.analysis_date.desc()).first()
        
        statistics = analysis.statistics if analysis else None
        
        # Get answer from Q&A agent
        answer = answer_question(
            file_path=dataset.file_path,
            question=request.question,
            statistics=statistics
        )
        
        return {
            "question": request.question,
            "answer": answer
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")


@app.post("/api/text-to-sql")
async def text_to_sql(request: TextToSQLRequest, db: Session = Depends(get_db)):
    """
    Convert natural language question to SQL query
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Generate SQL query
        result = generate_sql_query(
            question=request.question,
            dataset_id=dataset.id,
            file_path=dataset.file_path
        )
        
        return {
            "question": request.question,
            "sql_query": result.get("sql_query"),
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_message": result.get("clarification_message"),
            "table_name": result.get("table_name"),
            "schema": result.get("schema")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")


@app.get("/api/datasets")
async def list_datasets(db: Session = Depends(get_db)):
    """
    List all uploaded datasets
    """
    datasets = db.query(Dataset).order_by(Dataset.upload_date.desc()).all()
    return [
        {
            "id": ds.id,
            "filename": ds.original_filename,
            "upload_date": ds.upload_date,
            "rows": ds.rows_count,
            "columns": ds.columns_count
        }
        for ds in datasets
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
