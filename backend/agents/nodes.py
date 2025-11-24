import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from agents.state import AgentState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM with DeepSeek
llm = ChatOpenAI(
    model="deepseek/deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0.7
)

VIZ_DIR = os.getenv("VISUALIZATIONS_DIR", "./visualizations")
os.makedirs(VIZ_DIR, exist_ok=True)


def convert_numpy(obj):
    """Recursively convert NumPy types to native Python types"""
    if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                        np.int16, np.int32, np.int64, np.uint8,
                        np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy(i) for i in obj)
    return obj


def clean_data_node(state: AgentState) -> AgentState:
    """Clean the uploaded dataset"""
    try:
        # Load data
        file_path = state["file_path"]
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:  # Excel
            df = pd.read_excel(file_path)
        
        state["raw_data"] = df
        
        # 1. Remove completely empty rows or rows with all NaNs
        df = df.dropna(how='all')
        
        # 2. Fix malformed strings (trim whitespace)
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        # 3. Convert invalid numbers to NaN (coerce errors)
        # Iterate over columns that should be numeric but might have mixed types
        for col in df.columns:
            # Check if column has mixed types (object) but looks numeric
            if df[col].dtype == 'object':
                # Try to convert to numeric, coercing errors to NaN
                # This handles "invalid numbers" by turning them into NaN
                # We only do this if it doesn't result in losing too much data (heuristic)
                # For now, let's apply it to columns that are predominantly numeric
                try:
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    # If we successfully converted some values and didn't lose everything
                    if numeric_series.notna().sum() > 0:
                        df[col] = numeric_series
                except:
                    pass

        cleaning_report = {
            "original_shape": df.shape,
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "data_types": df.dtypes.astype(str).to_dict()
        }
        
        # 4. Remove duplicates
        df_cleaned = df.drop_duplicates()
        
        # 5. Handle missing values - BUT keep "realistic edge cases" and "statistical outliers"
        # The user said "convert invalid numbers to NaN" and "keep all valid rows"
        # We will fill NaNs for analysis purposes, but maybe we should be careful not to over-clean
        # if the user wants to "keep all valid rows".
        # However, for the "cleaned file" download, standard practice is to handle missing values.
        # Let's stick to the previous logic of filling NaNs, as that makes the data "clean".
        # Outliers are naturally kept unless we explicitly drop them (which we are NOT doing).
        
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype in ['float64', 'int64']:
                # Fill numeric columns with median
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
            else:
                # Fill categorical columns with mode
                mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Unknown'
                df_cleaned[col] = df_cleaned[col].fillna(mode_val)
        
        cleaning_report["cleaned_shape"] = df_cleaned.shape
        cleaning_report["rows_removed"] = df.shape[0] - df_cleaned.shape[0]
        
        # Save cleaned data to file
        cleaned_filename = f"cleaned_{os.path.basename(file_path)}"
        cleaned_file_path = os.path.join(os.path.dirname(file_path), cleaned_filename)
        df_cleaned.to_csv(cleaned_file_path, index=False)
        cleaning_report["cleaned_file_path"] = cleaned_filename

        state["cleaned_data"] = df_cleaned
        state["cleaning_report"] = convert_numpy(cleaning_report)
        state["status"] = "cleaning_completed"
        
        return state
    
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Data cleaning error: {str(e)}"]
        state["status"] = "failed"
        return state


def generate_statistics_node(state: AgentState) -> AgentState:
    """Generate summary statistics"""
    try:
        df = state["cleaned_data"]
        
        statistics = {
            "shape": df.shape,
            "columns": list(df.columns),
            "numeric_summary": {},
            "categorical_summary": {},
            "correlations": {}
        }
        
        # Numeric columns statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            statistics["numeric_summary"] = df[numeric_cols].describe().to_dict()
            
            # Correlation matrix
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                statistics["correlations"] = corr_matrix.to_dict()
        
        # Categorical columns statistics
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            statistics["categorical_summary"][col] = {
                "unique_values": int(df[col].nunique()),
                "top_values": df[col].value_counts().head(5).to_dict()
            }
        
        state["statistics"] = convert_numpy(statistics)
        state["status"] = "statistics_completed"
        
        return state
    
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Statistics generation error: {str(e)}"]
        return state


def detect_anomalies_node(state: AgentState) -> AgentState:
    """Advanced anomaly + data quality detection"""
    try:
        df = state["cleaned_data"].copy()
        anomalies = {
            "outliers": {},
            "invalid_values": {},
            "missing_values": {},
            "domain_anomalies": {},
            "duplicates": 0,
            "rows_with_duplicates": [],
            "anomaly_indices": [],
            "summary": ""
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        
        #Missing Values
        missing = df.isnull().sum()
        anomalies["missing_values"] = missing[missing > 0].to_dict()

        
        # 2 Duplicate Rows 
        dup_mask = df.duplicated(keep=False)
        anomalies["duplicates"] = dup_mask.sum()
        anomalies["rows_with_duplicates"] = df[dup_mask].index.tolist()

       
       
         #Invalid Data Types (e.g. salary="abc")
        for col in df.columns:
            invalid_mask = df[col].apply(
                lambda x: isinstance(x, str) and x.strip().lower() in ["nan", "null", "", "none"]
            )
            if invalid_mask.sum() > 0:
                anomalies["invalid_values"][col] = df[col][invalid_mask].tolist()



#Statistical Outliers (IQR)
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                anomalies["outliers"][col] = {
                    "count": len(outliers),
                    "percentage": round(len(outliers) / len(df) * 100, 2),
                    "values": outliers[col].tolist()[:10]
                }

       
        #Domain Rules
        domain_issues = {}

        # Age limits
        domain_issues["invalid_age"] = df[(df["age"] < 18) | (df["age"] > 70)].index.tolist() if "age" in df else []

        # Experience > Age (impossible)
        if "age" in df.columns and "years_experience" in df.columns:
            domain_issues["exp_gt_age"] = df[df["years_experience"] > df["age"]].index.tolist()

        # Future promotion year
        if "last_promotion_year" in df.columns:
            domain_issues["future_year"] = df[df["last_promotion_year"] > pd.Timestamp.now().year].index.tolist()

        # Negative values
        for col in numeric_cols:
            neg = df[df[col] < 0]
            if len(neg) > 0:
                domain_issues[f"negative_{col}"] = neg.index.tolist()

        anomalies["domain_anomalies"] = domain_issues

        
        #Multivariate Outliers (Isolation Forest)
        if len(numeric_cols) >= 2:
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            preds = iso_forest.fit_predict(df[numeric_cols].fillna(0))
            anomaly_mask = preds == -1
            anomalies["anomaly_indices"] = df[anomaly_mask].index.tolist()

        # Summary
        anomalies["summary"] = "Advanced anomaly detection completed."

        state["anomalies"] = convert_numpy(anomalies)
        state["status"] = "anomaly_detection_completed"
        return state

    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Anomaly detection error: {str(e)}"]
        return state



def create_visualizations_node(state: AgentState) -> AgentState:
    """Create visualizations"""
    try:
        df = state["cleaned_data"]
        dataset_id = state["dataset_id"]
        visualizations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.facecolor'] = 'white'
        
        # 1. Numeric distributions (histograms)
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                plt.figure(figsize=(10, 6))
                plt.hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Frequency')
                
                filename = f"hist_{dataset_id}_{col}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                filepath = os.path.join(VIZ_DIR, filename)
                plt.savefig(filepath, dpi=100, bbox_inches='tight')
                plt.close()
                
                visualizations.append({
                    "type": "histogram",
                    "column": col,
                    "filename": filename
                })
        
        # 2. Correlation heatmap
        if len(numeric_cols) > 1:
            plt.figure(figsize=(12, 10))
            corr_matrix = df[numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0)
            plt.title('Correlation Heatmap')
            
            filename = f"corr_{dataset_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(VIZ_DIR, filename)
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close()
            
            visualizations.append({
                "type": "correlation",
                "filename": filename
            })
        
        # 3. Categorical value counts
        if len(categorical_cols) > 0:
            col = categorical_cols[0]
            plt.figure(figsize=(12, 6))
            df[col].value_counts().head(10).plot(kind='bar')
            plt.title(f'Top 10 Values in {col}')
            plt.xlabel(col)
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            
            filename = f"bar_{dataset_id}_{col}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(VIZ_DIR, filename)
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close()
            
            visualizations.append({
                "type": "bar_chart",
                "column": col,
                "filename": filename
            })
        
        # 4. Scatter plot (if we have at least 2 numeric columns)
        if len(numeric_cols) >= 2:
            plt.figure(figsize=(10, 6))
            plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.5)
            plt.xlabel(numeric_cols[0])
            plt.ylabel(numeric_cols[1])
            plt.title(f'{numeric_cols[0]} vs {numeric_cols[1]}')
            
            filename = f"scatter_{dataset_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(VIZ_DIR, filename)
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close()
            
            visualizations.append({
                "type": "scatter",
                "columns": [numeric_cols[0], numeric_cols[1]],
                "filename": filename
            })
        
        state["visualizations"] = state.get("visualizations", []) + visualizations
        state["status"] = "visualizations_completed"
        
        return state
    
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Visualization error: {str(e)}"]
        return state


def generate_insights_node(state: AgentState) -> AgentState:
    """Generate insights using LLM"""
    try:
        stats = state["statistics"]
        anomalies = state["anomalies"]
        cleaning_report = state["cleaning_report"]
        
        # Prepare context for LLM
        context = f"""
Dataset Analysis Summary:

1. Data Cleaning:
- Original shape: {cleaning_report['original_shape']}
- Cleaned shape: {cleaning_report['cleaned_shape']}
- Rows removed: {cleaning_report['rows_removed']}
- Duplicates found: {cleaning_report['duplicates']}

2. Dataset Overview:
- Total rows: {stats['shape'][0]}
- Total columns: {stats['shape'][1]}
- Columns: {', '.join(stats['columns'])}

3. Numeric Summary:
{stats.get('numeric_summary', 'No numeric columns')}

4. Categorical Summary:
{stats.get('categorical_summary', 'No categorical columns')}

5. Anomalies Detected:
{anomalies.get('summary', 'No anomalies detected')}
Outliers by column: {list(anomalies.get('outliers', {}).keys())}

Based on this analysis, provide:
1. Key insights about the data
2. Notable patterns or trends
3. Data quality observations
4. Recommendations for further analysis
5. Potential business implications

Keep the response concise but informative.
"""
        
        response = llm.invoke(context)
        insights = response.content
        
        state["insights"] = insights
        state["status"] = "insights_completed"
        
        return state
    
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Caught exception in generate_insights_node: {error_msg}")
        
        # Check for various forms of 402/Insufficient Balance or 404/Not Found
        if "402" in error_msg or "Insufficient Balance" in error_msg or "insufficient_quota" in error_msg or "404" in error_msg or "Not Found" in error_msg:
            # Fallback to mock insights
            print("API Error: Insufficient Balance or Not Found. Falling back to mock insights.")
            state["insights"] = generate_mock_insights(state["statistics"], state["anomalies"])
            state["status"] = "insights_completed"
            return state
            
        state["errors"] = state.get("errors", []) + [f"Insights generation error: {error_msg}"]
        return state


def generate_mock_insights(stats: dict, anomalies: dict) -> str:
    """Generate mock insights when API is unavailable"""
    insights = [
        "### Data Analysis Insights (Mock Mode)",
        "",
        "**1. Key Insights**",
        f"- The dataset contains {stats['shape'][0]} rows and {stats['shape'][1]} columns.",
        f"- There are {len(stats.get('numeric_summary', {}))} numeric variables and {len(stats.get('categorical_summary', {}))} categorical variables.",
        "",
        "**2. Patterns & Trends**",
        "- Distribution analysis shows varying ranges across numeric features.",
        "- Correlation analysis suggests potential relationships between variables (refer to heatmap).",
        "",
        "**3. Data Quality**",
        "- Data cleaning process handled missing values and duplicates.",
        f"- {anomalies.get('summary', 'No anomalies detected')}.",
        "",
        "**4. Recommendations**",
        "- Consider collecting more data points for robust analysis.",
        "- Further investigate the identified outliers.",
        "",
        "**5. Business Implications**",
        "- These findings can support data-driven decision making.",
        "- Monitor key metrics for changes over time."
    ]
    return "\n".join(insights)


def generate_sql_node(state: AgentState) -> AgentState:
    """Generate SQL queries to load data into PostgreSQL"""
    try:
        df = state["cleaned_data"]
        filename = state["filename"]
        
        # Generate table name from filename
        table_name = filename.replace('.csv', '').replace('.xlsx', '').replace(' ', '_').lower()
        
        # Create table schema
        sql_parts = [f"-- SQL Schema and Data for {filename}\n"]
        sql_parts.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
        sql_parts.append("    id SERIAL PRIMARY KEY,")
        
        # Add columns
        for col in df.columns:
            col_name = col.replace(' ', '_').lower()
            dtype = df[col].dtype
            
            if dtype in ['int64', 'int32']:
                sql_type = 'INTEGER'
            elif dtype in ['float64', 'float32']:
                sql_type = 'DECIMAL'
            elif dtype == 'bool':
                sql_type = 'BOOLEAN'
            elif dtype == 'datetime64[ns]':
                sql_type = 'TIMESTAMP'
            else:
                sql_type = 'TEXT'
            
            sql_parts.append(f"    {col_name} {sql_type},")
        
        # Remove last comma and close
        sql_parts[-1] = sql_parts[-1].rstrip(',')
        sql_parts.append(");\n")
        
        # Add sample INSERT statements (first 5 rows)
        sql_parts.append(f"\n-- Sample INSERT statements (first 5 rows)")
        for idx, row in df.head(5).iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append('NULL')
                elif isinstance(val, str):
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))
            
            cols = ', '.join([col.replace(' ', '_').lower() for col in df.columns])
            vals = ', '.join(values)
            sql_parts.append(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")
        
        sql_queries = '\n'.join(sql_parts)
        state["sql_queries"] = sql_queries
        state["status"] = "completed"
        
        return state
    
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"SQL generation error: {str(e)}"]
        return state
