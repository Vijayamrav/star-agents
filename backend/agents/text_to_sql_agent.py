"""
Text-to-SQL Agent
Converts natural language questions to valid PostgreSQL queries using dataset schema.
"""

import os
import re
import pandas as pd
from typing import Dict, Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Initialize LLM with DeepSeek
llm = ChatOpenAI(
    model="deepseek/deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0.1  # Low temperature for more deterministic SQL generation
)


def extract_schema_from_dataset(file_path: str) -> Dict[str, str]:
    """
    Extract schema information from a dataset file.
    
    Args:
        file_path: Path to the CSV/Excel file
        
    Returns:
        Dictionary mapping column names to their data types
    """
    try:
        # Read the dataset
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
        
        # Extract schema
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Map pandas dtypes to PostgreSQL types
            if dtype.startswith('int'):
                pg_type = 'INTEGER'
            elif dtype.startswith('float'):
                pg_type = 'NUMERIC'
            elif dtype == 'bool':
                pg_type = 'BOOLEAN'
            elif dtype == 'datetime64':
                pg_type = 'TIMESTAMP'
            else:
                pg_type = 'TEXT'
            
            schema[col] = pg_type
        
        return schema
    
    except Exception as e:
        print(f"Error extracting schema: {str(e)}")
        return {}


def validate_sql_columns(sql: str, valid_columns: list) -> tuple[bool, list]:
    """
    Validate that SQL query only references columns that exist in the schema.
    
    Args:
        sql: The SQL query to validate
        valid_columns: List of valid column names
        
    Returns:
        Tuple of (is_valid, invalid_columns)
    """
    # Convert to lowercase for case-insensitive comparison
    sql_lower = sql.lower()
    valid_columns_lower = [col.lower() for col in valid_columns]
    
    # Extract potential column references (simple regex, not perfect but good enough)
    # Matches words that could be column names
    potential_columns = re.findall(r'\b([a-z_][a-z0-9_]*)\b', sql_lower)
    
    # Filter out SQL keywords
    sql_keywords = {
        'select', 'from', 'where', 'group', 'by', 'order', 'having', 'limit',
        'offset', 'join', 'inner', 'left', 'right', 'outer', 'on', 'as',
        'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null', 'distinct',
        'count', 'sum', 'avg', 'min', 'max', 'case', 'when', 'then', 'else',
        'end', 'asc', 'desc', 'true', 'false', 'cast', 'integer', 'text',
        'numeric', 'boolean', 'timestamp', 'date', 'varchar', 'char'
    }
    
    # Check for invalid columns
    invalid_columns = []
    for col in potential_columns:
        if col not in sql_keywords and col not in valid_columns_lower:
            # Check if it might be a table name (e.g., dataset_1)
            if not col.startswith('dataset_'):
                invalid_columns.append(col)
    
    return len(invalid_columns) == 0, invalid_columns


def generate_sql_query(
    question: str,
    dataset_id: int,
    file_path: str,
    table_name: Optional[str] = None
) -> Dict:
    """
    Generate a PostgreSQL query from a natural language question.
    
    Args:
        question: Natural language question
        dataset_id: ID of the dataset
        file_path: Path to the dataset file
        table_name: Optional table name (defaults to dataset_{dataset_id})
        
    Returns:
        Dictionary with sql_query, needs_clarification, and clarification_message
    """
    try:
        # Extract schema
        schema = extract_schema_from_dataset(file_path)
        
        if not schema:
            return {
                "sql_query": None,
                "needs_clarification": True,
                "clarification_message": "Unable to extract schema from dataset. Please ensure the file is valid."
            }
        
        # Build schema description
        table_name = table_name or f"dataset_{dataset_id}"
        schema_lines = [f"  {col} {dtype}" for col, dtype in schema.items()]
        schema_text = ",\n".join(schema_lines)
        
        # Create prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a PostgreSQL SQL query generator. Your task is to convert natural language questions into valid PostgreSQL SQL queries.

CRITICAL RULES:
1. Output ONLY the SQL query - no explanations, no markdown, no code blocks
2. Use ONLY the columns provided in the schema below
3. Do NOT invent or hallucinate column names
4. If the question is ambiguous or unclear, respond with EXACTLY: "CLARIFICATION NEEDED: [your specific question]"
5. Use proper PostgreSQL syntax
6. Always use the exact table name provided
7. For aggregations, use appropriate GROUP BY clauses
8. End the query with a semicolon

Table Schema:
Table name: {table_name}
Columns:
{schema_text}

Available columns (use ONLY these): {column_list}"""),
            ("human", "{question}")
        ])
        
        # Generate SQL
        chain = prompt_template | llm
        response = chain.invoke({
            "table_name": table_name,
            "schema_text": schema_text,
            "column_list": ", ".join(schema.keys()),
            "question": question
        })
        
        sql_output = response.content.strip()
        
        # Check if clarification is needed
        if sql_output.startswith("CLARIFICATION NEEDED:"):
            clarification_msg = sql_output.replace("CLARIFICATION NEEDED:", "").strip()
            return {
                "sql_query": None,
                "needs_clarification": True,
                "clarification_message": clarification_msg
            }
        
        # Clean up the SQL (remove markdown if present)
        sql_output = sql_output.replace("```sql", "").replace("```", "").strip()
        
        # Validate columns
        is_valid, invalid_cols = validate_sql_columns(sql_output, list(schema.keys()))
        
        if not is_valid:
            return {
                "sql_query": None,
                "needs_clarification": True,
                "clarification_message": f"The generated query references columns that don't exist: {', '.join(invalid_cols)}. Available columns are: {', '.join(schema.keys())}"
            }
        
        return {
            "sql_query": sql_output,
            "needs_clarification": False,
            "clarification_message": None,
            "table_name": table_name,
            "schema": schema
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating SQL: {error_msg}")
        
        # Check for API errors
        if "402" in error_msg or "Insufficient Balance" in error_msg or "404" in error_msg:
            return {
                "sql_query": None,
                "needs_clarification": True,
                "clarification_message": "AI service is currently unavailable (Mock Mode). Please try again later."
            }
        
        return {
            "sql_query": None,
            "needs_clarification": True,
            "clarification_message": f"Error generating SQL query: {error_msg}"
        }
