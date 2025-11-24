from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from database import Base


class Dataset(Base):
    """Model for storing uploaded dataset metadata"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    rows_count = Column(Integer)
    columns_count = Column(Integer)
    column_names = Column(JSON)


class Analysis(Base):
    """Model for storing analysis results"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    
    # Analysis results
    cleaned_data_info = Column(JSON)
    statistics = Column(JSON)
    anomalies = Column(JSON)
    insights = Column(Text)
    sql_queries = Column(Text)
    
    # Status
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)


class Visualization(Base):
    """Model for storing visualization metadata"""
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False)
    visualization_type = Column(String, nullable=False)  # histogram, scatter, correlation, etc.
    file_path = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
