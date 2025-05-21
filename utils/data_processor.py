import pandas as pd
import os
import json
import io

def get_file_extension(filename):
    """
    Extract the file extension from a filename
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: File extension (without the dot)
    """
    return os.path.splitext(filename)[1].lower().replace('.', '')

def load_data(file_obj, file_extension):
    """
    Load data from different file formats
    
    Args:
        file_obj: File object from st.file_uploader
        file_extension (str): File extension to determine the loading method
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    try:
        if file_extension in ['csv']:
            return pd.read_csv(file_obj)
        elif file_extension in ['xlsx', 'xls']:
            return pd.read_excel(file_obj)
        elif file_extension in ['json']:
            return pd.read_json(file_obj)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")

def list_available_datasets():
    """
    List all available datasets in the session state
    
    Returns:
        list: List of dataset names
    """
    if 'datasets' in st.session_state:
        return list(st.session_state.datasets.keys())
    return []

def get_column_types(df):
    """
    Categorize columns by data type for visualization selection
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        
    Returns:
        dict: Dictionary with column types categorized
    """
    column_types = {
        'numeric': [],
        'categorical': [],
        'datetime': [],
        'text': []
    }
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            column_types['numeric'].append(col)
        elif pd.api.types.is_datetime64_dtype(df[col]) or pd.api.types.is_period_dtype(df[col]):
            column_types['datetime'].append(col)
        elif df[col].nunique() < max(10, int(len(df) * 0.05)):  # Heuristic for categorical
            column_types['categorical'].append(col)
        else:
            column_types['text'].append(col)
    
    return column_types

def filter_dataframe(df, filters):
    """
    Apply a set of filters to a dataframe
    
    Args:
        df (pandas.DataFrame): The dataframe to filter
        filters (dict): Dictionary of filters to apply
        
    Returns:
        pandas.DataFrame: Filtered dataframe
    """
    filtered_df = df.copy()
    
    for col, filter_value in filters.items():
        if col in filtered_df.columns:
            if isinstance(filter_value, tuple) and len(filter_value) == 2:
                # Range filter for numeric columns
                min_val, max_val = filter_value
                filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]
            elif isinstance(filter_value, list):
                # Multi-select filter for categorical columns
                filtered_df = filtered_df[filtered_df[col].isin(filter_value)]
            else:
                # Simple equality filter
                filtered_df = filtered_df[filtered_df[col] == filter_value]
    
    return filtered_df

def transform_dataframe(df, transformations):
    """
    Apply a series of transformations to a dataframe
    
    Args:
        df (pandas.DataFrame): The dataframe to transform
        transformations (list): List of transformation operations
        
    Returns:
        pandas.DataFrame: Transformed dataframe
    """
    transformed_df = df.copy()
    
    for transform in transformations:
        transform_type = transform.get('type')
        
        if transform_type == 'filter':
            transformed_df = filter_dataframe(transformed_df, transform.get('filters', {}))
        
        elif transform_type == 'group_by':
            groupby_cols = transform.get('columns', [])
            agg_functions = transform.get('aggregations', {})
            if groupby_cols and agg_functions:
                transformed_df = transformed_df.groupby(groupby_cols).agg(agg_functions).reset_index()
        
        elif transform_type == 'sort':
            sort_col = transform.get('column')
            ascending = transform.get('ascending', True)
            if sort_col:
                transformed_df = transformed_df.sort_values(by=sort_col, ascending=ascending)
        
        elif transform_type == 'select_columns':
            columns = transform.get('columns', [])
            if columns:
                transformed_df = transformed_df[columns]
        
        elif transform_type == 'rename_columns':
            rename_dict = transform.get('rename_map', {})
            if rename_dict:
                transformed_df = transformed_df.rename(columns=rename_dict)
        
        elif transform_type == 'fillna':
            col = transform.get('column')
            value = transform.get('value')
            if col and value is not None:
                transformed_df[col] = transformed_df[col].fillna(value)
    
    return transformed_df

def convert_df_to_csv(df):
    """
    Convert dataframe to CSV for download
    
    Args:
        df (pandas.DataFrame): Dataframe to convert
        
    Returns:
        str: CSV data as string
    """
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df):
    """
    Convert dataframe to Excel for download
    
    Args:
        df (pandas.DataFrame): Dataframe to convert
        
    Returns:
        bytes: Excel file as bytes
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def get_data_summary(df):
    """
    Generate a summary of the dataframe
    
    Args:
        df (pandas.DataFrame): Dataframe to summarize
        
    Returns:
        dict: Summary statistics and information
    """
    missing_values = df.isna().sum().sum()
    missing_percentage = (missing_values / (df.shape[0] * df.shape[1])) * 100
    
    column_types = get_column_types(df)
    
    return {
        'rows': df.shape[0],
        'columns': df.shape[1],
        'missing_values': int(missing_values),
        'missing_percentage': round(missing_percentage, 2),
        'numeric_columns': len(column_types['numeric']),
        'categorical_columns': len(column_types['categorical']),
        'datetime_columns': len(column_types['datetime']),
        'text_columns': len(column_types['text']),
        'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024)  # In MB
    }
