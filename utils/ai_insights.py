import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
import streamlit as st
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

# Get API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_ai_data_insights(df, question=None):
    """
    Generate insights about the data using OpenAI
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        question (str, optional): Specific question to ask about the data
        
    Returns:
        str: Generated insights about the data
    """
    if OPENAI_API_KEY is None:
        return "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    
    try:
        # Prepare data summary
        data_description = get_data_description(df)
        
        # Build the prompt
        if question:
            prompt = f"Analyze this dataset and answer the following question: {question}\n\nDataset summary:\n{data_description}"
        else:
            prompt = f"Analyze this dataset and provide valuable insights about the data. Focus on patterns, anomalies, and actionable findings. Keep the analysis concise and insightful.\n\nDataset summary:\n{data_description}"
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst expert providing insights based on data summaries. Keep your answers concise, data-focused, and actionable."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating AI insights: {str(e)}"

def suggest_visualizations_with_ai(df):
    """
    Suggest visualizations for the dataset using OpenAI
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        
    Returns:
        list: List of suggested visualization types and configurations
    """
    if OPENAI_API_KEY is None:
        return [{"error": "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."}]
    
    try:
        # Prepare data summary
        data_description = get_data_description(df)
        
        # Build the prompt
        prompt = f"""Based on this dataset, suggest 3-5 effective visualizations that would reveal insights. For each visualization, specify:
1. The type of chart
2. What columns to use
3. Why this visualization would be helpful

Dataset summary:
{data_description}

Respond in JSON format with an array of suggestions like this:
[
  {{
    "type": "bar",
    "config": {{
      "x": "column_name",
      "y": "column_name",
      "title": "Suggested title"
    }},
    "description": "Why this visualization is helpful"
  }}
]
Only include visualization types from this list: bar, line, scatter, pie, histogram, heatmap, box, violin, treemap, table
"""
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data visualization expert who suggests effective charts based on dataset summaries."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        # Parse the response
        suggestions = response.choices[0].message.content
        import json
        return json.loads(suggestions)
    
    except Exception as e:
        return [{"error": f"Error generating AI visualization suggestions: {str(e)}"}]

def get_data_description(df):
    """
    Create a comprehensive description of the dataframe
    
    Args:
        df (pandas.DataFrame): The dataframe to describe
        
    Returns:
        str: Text description of the dataframe
    """
    # Basic info
    description = f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
    
    # Column info
    description += "Columns:\n"
    for col in df.columns:
        col_type = df[col].dtype
        description += f"- {col} ({col_type}): "
        
        # Add column statistics based on data type
        if pd.api.types.is_numeric_dtype(df[col]):
            description += f"min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}, null_count={df[col].isna().sum()}\n"
        elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            unique_count = df[col].nunique()
            description += f"unique_values={unique_count}, null_count={df[col].isna().sum()}\n"
            
            # Add sample values for categorical columns
            if unique_count < 10:
                top_values = df[col].value_counts().head(5).to_dict()
                description += f"   Most common values: {top_values}\n"
        else:
            description += f"unique_values={df[col].nunique()}, null_count={df[col].isna().sum()}\n"
    
    # Add correlation info for numeric columns
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if len(numeric_cols) >= 2:
        description += "\nCorrelations between numeric columns:\n"
        corr = df[numeric_cols].corr()
        
        # Get top 5 correlations
        corr_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                corr_pairs.append((numeric_cols[i], numeric_cols[j], corr.iloc[i, j]))
        
        # Sort by absolute correlation and take top 5
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        for col1, col2, corr_val in corr_pairs[:5]:
            description += f"- {col1} and {col2}: {corr_val:.2f}\n"
    
    return description

def detect_anomalies(df, numeric_cols=None, contamination=0.05):
    """
    Detect anomalies in the dataset using Isolation Forest
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        numeric_cols (list, optional): List of numeric columns to use
        contamination (float, optional): Expected proportion of anomalies
        
    Returns:
        pandas.DataFrame: Dataframe with anomaly scores
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    
    if not numeric_cols:
        return pd.DataFrame({"error": ["No numeric columns available for anomaly detection"]})
    
    # Create a copy of the data
    df_copy = df.copy()
    
    # Select only rows with no missing values in the numeric columns
    df_clean = df_copy.dropna(subset=numeric_cols)
    
    if df_clean.shape[0] < 10:
        return pd.DataFrame({"error": ["Not enough data points for anomaly detection after removing rows with missing values"]})
    
    try:
        # Scale the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_clean[numeric_cols])
        
        # Detect anomalies
        model = IsolationForest(contamination=contamination, random_state=42)
        df_clean['anomaly_score'] = model.fit_predict(scaled_data)
        
        # Convert to binary labels and scores
        df_clean['is_anomaly'] = df_clean['anomaly_score'].apply(lambda x: 'Yes' if x == -1 else 'No')
        
        # Calculate anomaly score (negative of decision function, higher = more anomalous)
        decision_scores = model.decision_function(scaled_data)
        df_clean['anomaly_score'] = -decision_scores
        
        # Sort by anomaly score (descending)
        df_anomalies = df_clean.sort_values('anomaly_score', ascending=False)
        
        return df_anomalies
    
    except Exception as e:
        return pd.DataFrame({"error": [f"Error in anomaly detection: {str(e)}"]})

def identify_clusters(df, numeric_cols=None, n_clusters=3):
    """
    Identify clusters in the dataset using KMeans
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        numeric_cols (list, optional): List of numeric columns to use
        n_clusters (int, optional): Number of clusters to form
        
    Returns:
        tuple: (Dataframe with cluster labels, cluster centers)
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    
    if not numeric_cols:
        return pd.DataFrame({"error": ["No numeric columns available for clustering"]}), None
    
    # Create a copy of the data
    df_copy = df.copy()
    
    # Select only rows with no missing values in the numeric columns
    df_clean = df_copy.dropna(subset=numeric_cols)
    
    if df_clean.shape[0] < n_clusters + 1:
        return pd.DataFrame({"error": [f"Not enough data points for {n_clusters} clusters after removing rows with missing values"]}), None
    
    try:
        # Scale the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_clean[numeric_cols])
        
        # Apply KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_clean['cluster'] = kmeans.fit_predict(scaled_data)
        
        # Calculate cluster centers in original space
        centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=numeric_cols)
        centers['cluster'] = range(n_clusters)
        
        return df_clean, centers
    
    except Exception as e:
        return pd.DataFrame({"error": [f"Error in clustering: {str(e)}"]}), None

def create_data_profile(df):
    """
    Create a comprehensive profile of the dataset
    
    Args:
        df (pandas.DataFrame): The dataframe to profile
        
    Returns:
        dict: Dictionary with profiling information
    """
    profile = {
        'basic_info': {
            'rows': df.shape[0],
            'columns': df.shape[1],
            'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024),  # In MB
            'duplicate_rows': df.duplicated().sum()
        },
        'column_info': [],
        'correlations': [],
        'missing_values': {}
    }
    
    # Column information
    for col in df.columns:
        col_info = {
            'name': col,
            'type': str(df[col].dtype),
            'missing': df[col].isna().sum(),
            'missing_percent': round((df[col].isna().sum() / len(df)) * 100, 2),
            'unique_values': df[col].nunique()
        }
        
        # Add statistics based on data type
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
                'median': df[col].median(),
                'std': df[col].std()
            })
        elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            # For categorical data, add most common values
            if df[col].nunique() < 20:  # Only for columns with reasonable number of categories
                value_counts = df[col].value_counts().head(5).to_dict()
                col_info['most_common'] = value_counts
        
        profile['column_info'].append(col_info)
    
    # Correlations for numeric columns
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        
        # Get top correlations
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                profile['correlations'].append({
                    'column1': numeric_cols[i],
                    'column2': numeric_cols[j],
                    'correlation': round(corr.iloc[i, j], 2)
                })
        
        # Sort by absolute correlation
        profile['correlations'].sort(key=lambda x: abs(x['correlation']), reverse=True)
    
    # Missing values summary
    missing_cols = df.columns[df.isna().any()].tolist()
    for col in missing_cols:
        missing_count = df[col].isna().sum()
        profile['missing_values'][col] = {
            'count': missing_count,
            'percent': round((missing_count / len(df)) * 100, 2)
        }
    
    return profile

def generate_report_with_ai(df, report_type='overview'):
    """
    Generate a comprehensive data report using AI
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        report_type (str): Type of report to generate ('overview', 'detailed', 'executive')
        
    Returns:
        str: Generated report text
    """
    if OPENAI_API_KEY is None:
        return "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    
    try:
        # Prepare data profile
        profile = create_data_profile(df)
        data_description = get_data_description(df)
        
        # Build the prompt based on report type
        if report_type == 'overview':
            prompt = f"""Create a concise overview report for this dataset, focusing on key findings and insights.
            
Dataset summary:
{data_description}

Include sections on:
1. Dataset Overview (size, structure, key variables)
2. Data Quality Issues (missing values, outliers)
3. Key Insights and Patterns
4. Recommendations for Further Analysis

Keep the report concise, informative, and action-oriented. Use a professional tone.
"""
        elif report_type == 'detailed':
            prompt = f"""Create a detailed analytical report for this dataset with comprehensive analysis.
            
Dataset summary:
{data_description}

Include sections on:
1. Dataset Overview and Structure
2. Data Quality Assessment (missing values, outliers, inconsistencies)
3. Univariate Analysis (distribution and statistics of key variables)
4. Bivariate Analysis (relationships between variables)
5. Key Patterns and Insights
6. Limitations of the Current Data
7. Recommendations for Further Analysis and Data Collection

Use a professional, analytical tone with data-driven insights.
"""
        else:  # executive
            prompt = f"""Create an executive summary report for this dataset, focusing on business insights and strategic implications.
            
Dataset summary:
{data_description}

Include sections on:
1. Executive Summary (1-2 paragraphs on key findings)
2. Data Highlights (key metrics and patterns)
3. Business Implications
4. Recommended Actions
5. Suggested Next Steps

Use a concise, business-oriented tone. Focus on actionable insights rather than technical details.
"""
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data science expert creating professional data reports. Your reports are clear, insightful, and actionable."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating AI report: {str(e)}"
