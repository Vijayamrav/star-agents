from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator


class AgentState(TypedDict):
    """State that flows through the LangGraph workflow"""
    
    # Input
    dataset_id: int
    file_path: str
    filename: str
    
    # Data processing
    raw_data: Optional[Any]  # pandas DataFrame
    cleaned_data: Optional[Any]  # pandas DataFrame
    cleaning_report: Optional[Dict[str, Any]]
    
    # Analysis results
    statistics: Optional[Dict[str, Any]]
    anomalies: Optional[Dict[str, Any]]
    visualizations: Annotated[List[Dict[str, str]], operator.add]  # List of viz metadata
    insights: Optional[str]
    sql_queries: Optional[str]
    
    # Q&A specific
    question: Optional[str]
    answer: Optional[str]
    
    # Error handling
    errors: Annotated[List[str], operator.add]
    status: str  # "processing", "completed", "failed"
