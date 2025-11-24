import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM with DeepSeek
llm = ChatOpenAI(
    model="deepseek/deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0.7
)


def answer_question(file_path: str, question: str, statistics: dict = None) -> str:
    """
    Answer questions about the dataset using LLM
    
    Args:
        file_path: Path to the dataset file
        question: User's question
        statistics: Pre-computed statistics (optional)
    
    Returns:
        Answer to the question
    """
    try:
        # Load dataset
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Prepare context
        context_parts = [
            f"Dataset Information:",
            f"- Shape: {df.shape[0]} rows, {df.shape[1]} columns",
            f"- Columns: {', '.join(df.columns.tolist())}",
            f"\nFirst few rows:\n{df.head(3).to_string()}",
        ]
        
        # Add statistics if available
        if statistics:
            context_parts.append(f"\nStatistics Summary:")
            if 'numeric_summary' in statistics:
                context_parts.append(f"Numeric columns summary: {statistics['numeric_summary']}")
            if 'categorical_summary' in statistics:
                context_parts.append(f"Categorical columns summary: {statistics['categorical_summary']}")
        else:
            # Generate basic statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                context_parts.append(f"\nNumeric Summary:\n{df[numeric_cols].describe().to_string()}")
        
        context = '\n'.join(context_parts)
        
        # Create prompt
        prompt = f"""You are a data analyst assistant. Based on the following dataset information, answer the user's question accurately and concisely.

{context}

User Question: {question}

Provide a clear, data-driven answer. If you need to perform calculations, show your work. If the question cannot be answered with the available data, explain why.

Answer:"""
        
        # Get response from LLM
        response = llm.invoke(prompt)
        return response.content
    
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Caught exception in answer_question: {error_msg}")
        
        if "402" in error_msg or "Insufficient Balance" in error_msg or "insufficient_quota" in error_msg or "404" in error_msg or "Not Found" in error_msg:
            print("API Error: Insufficient Balance or Not Found. Falling back to mock answer.")
            return "I apologize, but I'm currently running in Mock Mode due to API limits. I cannot provide specific answers to your questions at this time, but you can still view the generated statistics and visualizations."
            
        return f"Error answering question: {error_msg}"
