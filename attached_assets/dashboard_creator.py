import streamlit as st
import pandas as pd
import json
from utils.data_processor import get_column_types, filter_dataframe
from utils.visualization import create_visualization, render_chart_in_streamlit, suggest_visualizations
from utils.ai_insights import suggest_visualizations_with_ai

# st.set_page_config( # This should be called only once in the main app file
#     page_title="Dashboard Creator - DataInsight AI",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

def show_dashboard_creator_content(): # Renamed from main()
    st.title("📊 Dashboard Creator")
    st.write("Build custom, interactive dashboards with drag-and-drop simplicity")
    
    # Check if data is loaded
    if 'data' not in st.session_state or st.session_state.data is None:
        st.info("Please upload a dataset from the Home page first.")
        # if st.button("Go to Home Page"): # Navigation should be handled by the main app
            # st.switch_page("app.py") # Commented out, main.py handles navigation
        return
    
    # Initialize dashboard state if needed
    if 'dashboard_panels' not in st.session_state:
        st.session_state.dashboard_panels = []
    
    # Dashboard Configuration Section
    with st.expander("Dashboard Configuration", expanded=True if not st.session_state.dashboard_panels else False):
        dashboard_tabs = st.tabs(["Build Dashboard", "AI Suggestions", "Dashboard Templates"])
        
        with dashboard_tabs[0]:
            st.subheader("Create Visualization Panel")
            
            # Get data and column types
            df = st.session_state.data
            column_types = get_column_types(df)
            
            # Panel settings
            col1, col2 = st.columns(2)
            with col1:
                panel_title = st.text_input("Panel Title", "New Visualization")
                viz_type = st.selectbox(
                    "Visualization Type",
                    ["bar", "line", "scatter", "pie", "histogram", 
                     "heatmap", "box", "violin", "treemap", "table"],
                    index=0
                )
            
            with col2:
                panel_width = st.radio("Panel Width", ["Small", "Medium", "Large"], index=1, horizontal=True)
                panel_height = st.slider("Panel Height", 200, 800, 400, 50)
            
            # Configuration based on visualization type
            st.subheader("Visualization Configuration")
            
            # Filter section
            with st.expander("Data Filters (Optional)"):
                filters = {}
                
                # Add filters for categorical columns
                if column_types['categorical']:
                    for col in column_types['categorical']:
                        if st.checkbox(f"Filter by {col}"):
                            unique_values = df[col].dropna().unique().tolist()
                            selected = st.multiselect(
                                f"Select values for {col}",
                                unique_values,
                                default=unique_values[:min(5, len(unique_values))]
                            )
                            if selected:
                                filters[col] = selected
                
                # Add range filters for numeric columns
                if column_types['numeric']:
                    for col in column_types['numeric']:
                        if st.checkbox(f"Filter by range of {col}"):
                            min_val, max_val = float(df[col].min()), float(df[col].max())
                            filter_range = st.slider(
                                f"Range for {col}",
                                min_val, max_val, (min_val, max_val)
                            )
                            filters[col] = filter_range
            
            # Apply filters if any
            if filters:
                filtered_df = filter_dataframe(df, filters)
                st.write(f"Filtered data has {filtered_df.shape[0]} rows (from original {df.shape[0]} rows)")
            else:
                filtered_df = df
            
            # Configuration specific to visualization type
            config = {}
            
            if viz_type == "bar":
                config["x"] = st.selectbox("X-axis", df.columns.tolist())
                config["y"] = st.selectbox("Y-axis", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["color"] = st.selectbox("Color (optional)", ["None"] + column_types['categorical'], index=0)
                config["barmode"] = st.selectbox("Bar Mode", ["group", "stack", "relative"], index=0)
                config["orientation"] = st.radio("Orientation", ["v", "h"], index=0, horizontal=True)
                
            elif viz_type == "line":
                config["x"] = st.selectbox("X-axis", df.columns.tolist())
                config["y"] = st.selectbox("Y-axis", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["color"] = st.selectbox("Color/Group (optional)", ["None"] + column_types['categorical'], index=0)
                config["markers"] = st.checkbox("Show Markers", True)
                config["line_shape"] = st.selectbox("Line Shape", ["linear", "spline", "hv", "vh", "hvh", "vhv"], index=0)
                
            elif viz_type == "scatter":
                config["x"] = st.selectbox("X-axis", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["y"] = st.selectbox("Y-axis", column_types['numeric'] if column_types['numeric'] else df.columns.tolist(), index=min(1, len(df.columns)-1))
                config["color"] = st.selectbox("Color (optional)", ["None"] + df.columns.tolist(), index=0)
                config["size"] = st.selectbox("Size (optional)", ["None"] + column_types['numeric'], index=0)
                config["opacity"] = st.slider("Point Opacity", 0.1, 1.0, 0.7, 0.1)
                
            elif viz_type == "pie":
                config["names"] = st.selectbox("Categories", column_types['categorical'] if column_types['categorical'] else df.columns.tolist())
                config["values"] = st.selectbox("Values", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["hole"] = st.slider("Donut Hole Size", 0.0, 0.8, 0.0, 0.1)
                
            elif viz_type == "histogram":
                config["x"] = st.selectbox("Value", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["color"] = st.selectbox("Color/Group (optional)", ["None"] + column_types['categorical'], index=0)
                config["nbins"] = st.slider("Number of Bins", 5, 100, 30)
                config["opacity"] = st.slider("Bar Opacity", 0.1, 1.0, 0.7, 0.1)
                config["marginal"] = st.selectbox("Marginal Plot", ["None", "box", "violin", "rug"], index=0)
                if config["marginal"] == "None":
                    config["marginal"] = None
                
            elif viz_type == "heatmap":
                if len(column_types['numeric']) >= 2:
                    config["columns"] = st.multiselect(
                        "Numeric Columns for Correlation",
                        column_types['numeric'],
                        default=column_types['numeric'][:min(8, len(column_types['numeric']))]
                    )
                    config["colorscale"] = st.selectbox(
                        "Color Scale",
                        ["RdBu_r", "Viridis", "Plasma", "Blues", "Reds"],
                        index=0
                    )
                else:
                    st.warning("Heatmap requires at least 2 numeric columns.")
                
            elif viz_type == "box":
                config["y"] = st.selectbox("Values", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["x"] = st.selectbox("Categories (optional)", ["None"] + column_types['categorical'], index=0)
                config["color"] = st.selectbox("Color/Group (optional)", ["None"] + column_types['categorical'], index=0)
                config["notched"] = st.checkbox("Notched Boxes", False)
                config["points"] = st.selectbox("Show Points", ["outliers", "all", "suspected", "False"], index=0)
                if config["points"] == "False":
                    config["points"] = False
                
            elif viz_type == "violin":
                config["y"] = st.selectbox("Values", column_types['numeric'] if column_types['numeric'] else df.columns.tolist())
                config["x"] = st.selectbox("Categories (optional)", ["None"] + column_types['categorical'], index=0)
                config["color"] = st.selectbox("Color/Group (optional)", ["None"] + column_types['categorical'], index=0)
                config["box"] = st.checkbox("Show Box Plot", True)
                config["points"] = st.selectbox("Show Points", ["outliers", "all", "False"], index=0)
                if config["points"] == "False":
                    config["points"] = False
                
            elif viz_type == "treemap":
                avail_cols = column_types['categorical'] + column_types['text']
                if avail_cols:
                    config["path"] = st.multiselect(
                        "Hierarchy Levels (in order)",
                        avail_cols,
                        default=[avail_cols[0]] if avail_cols else []
                    )
                    config["values"] = st.selectbox("Values", ["None"] + column_types['numeric'], index=1 if column_types['numeric'] else 0)
                    config["color"] = st.selectbox("Color (optional)", ["None"] + df.columns.tolist(), index=0)
                else:
                    st.warning("Treemap requires categorical or text columns.")
                
            elif viz_type == "table":
                config["columns"] = st.multiselect(
                    "Columns to Include",
                    df.columns.tolist(),
                    default=df.columns.tolist()[:min(5, len(df.columns))]
                )
                config["rows"] = st.slider("Number of Rows", 5, 50, 10)
                config["header_color"] = st.color_picker("Header Color", "#D4E6F1")
                config["cell_color"] = st.color_picker("Cell Color", "#F8F9F9")
            
            # Clean up None values in config
            for key in list(config.keys()):
                if config[key] == "None":
                    config[key] = None
            
            # Add title to config
            config["title"] = panel_title
            
            # Preview visualization
            if st.checkbox("Preview Visualization", True):
                try:
                    fig = create_visualization(filtered_df, viz_type, config)
                    render_chart_in_streamlit(fig)
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
            
            # Add panel button
            if st.button("Add Panel to Dashboard"):
                panel = {
                    "id": len(st.session_state.dashboard_panels),
                    "title": panel_title,
                    "type": viz_type,
                    "config": config,
                    "filters": filters,
                    "width": panel_width,
                    "height": panel_height
                }
                st.session_state.dashboard_panels.append(panel)
                st.success(f"Added '{panel_title}' panel to the dashboard!")
                st.rerun()
        
        with dashboard_tabs[1]:
            st.subheader("AI-Generated Visualization Suggestions")
            
            if st.button("Generate Visualization Suggestions with AI"):
                with st.spinner("Generating suggestions..."):
                    suggestions = suggest_visualizations_with_ai(df)
                
                if "error" in suggestions[0]:
                    st.error(suggestions[0]["error"])
                else:
                    for i, suggestion in enumerate(suggestions):
                        st.write(f"### Suggestion {i+1}: {suggestion.get('description', '')}")
                        
                        try:
                            fig = create_visualization(df, suggestion["type"], suggestion["config"])
                            render_chart_in_streamlit(fig)
                            
                            if st.button(f"Add to Dashboard", key=f"add_suggestion_{i}"):
                                panel = {
                                    "id": len(st.session_state.dashboard_panels),
                                    "title": suggestion["config"].get("title", f"AI Suggestion {i+1}"),
                                    "type": suggestion["type"],
                                    "config": suggestion["config"],
                                    "filters": {},
                                    "width": "Medium",
                                    "height": 400
                                }
                                st.session_state.dashboard_panels.append(panel)
                                st.success(f"Added panel to the dashboard!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error creating visualization: {str(e)}")
            
            # Alternative: Basic suggestions without AI
            st.write("Or use automatic suggestions based on data structure:")
            if st.button("Generate Basic Suggestions"):
                with st.spinner("Analyzing data..."):
                    suggestions = suggest_visualizations(df)
                
                for i, suggestion in enumerate(suggestions[:5]):  # Show top 5 suggestions
                    st.write(f"### Suggestion {i+1}: {suggestion.get('description', '')}")
                    
                    try:
                        # For count-based charts, add computed values
                        if suggestion["type"] == "bar" and suggestion["config"]["y"] is None:
                            value_counts = df[suggestion["config"]["x"]].value_counts()
                            temp_df = pd.DataFrame({
                                suggestion["config"]["x"]: value_counts.index,
                                "count": value_counts.values
                            })
                            suggestion["config"]["y"] = "count"
                            fig = create_visualization(temp_df, suggestion["type"], suggestion["config"])
                        elif suggestion["type"] == "pie" and suggestion["config"]["values"] is None:
                            value_counts = df[suggestion["config"]["names"]].value_counts()
                            temp_df = pd.DataFrame({
                                suggestion["config"]["names"]: value_counts.index,
                                "count": value_counts.values
                            })
                            suggestion["config"]["values"] = "count"
                            fig = create_visualization(temp_df, suggestion["type"], suggestion["config"])
                        else:
                            fig = create_visualization(df, suggestion["type"], suggestion["config"])
                        
                        render_chart_in_streamlit(fig)
                        
                        if st.button(f"Add to Dashboard", key=f"add_basic_suggestion_{i}"):
                            panel = {
                                "id": len(st.session_state.dashboard_panels),
                                "title": suggestion["config"].get("title", f"Suggestion {i+1}"),
                                "type": suggestion["type"],
                                "config": suggestion["config"],
                                "filters": {},
                                "width": "Medium",
                                "height": 400
                            }
                            st.session_state.dashboard_panels.append(panel)
                            st.success(f"Added panel to the dashboard!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating visualization: {str(e)}")
        
        with dashboard_tabs[2]:
            st.subheader("Dashboard Templates")
            
            template_type = st.radio(
                "Select a Template",
                ["Data Overview", "Correlation Analysis", "Categorical Analysis", "Time Series Analysis"],
                horizontal=True
            )
            
            if st.button("Apply Template"):
                # Clear existing panels
                st.session_state.dashboard_panels = []
                
                if template_type == "Data Overview":
                    # Data overview template
                    st.session_state.dashboard_panels = [
                        {
                            "id": 0,
                            "title": "Data Summary Table",
                            "type": "table",
                            "config": {
                                "title": "Data Summary Table",
                                "columns": df.columns.tolist()[:min(6, len(df.columns))],
                                "rows": 10
                            },
                            "filters": {},
                            "width": "Large",
                            "height": 300
                        }
                    ]
                    
                    # Add numeric column distributions
                    numeric_cols = get_column_types(df)['numeric']
                    for i, col in enumerate(numeric_cols[:3]):  # First 3 numeric columns
                        st.session_state.dashboard_panels.append({
                            "id": i + 1,
                            "title": f"Distribution of {col}",
                            "type": "histogram",
                            "config": {
                                "title": f"Distribution of {col}",
                                "x": col,
                                "nbins": 30,
                                "opacity": 0.7,
                                "marginal": "box"
                            },
                            "filters": {},
                            "width": "Medium",
                            "height": 350
                        })
                    
                    # Add categorical column distributions
                    cat_cols = get_column_types(df)['categorical']
                    for i, col in enumerate(cat_cols[:2]):  # First 2 categorical columns
                        st.session_state.dashboard_panels.append({
                            "id": i + 4,
                            "title": f"Count of {col}",
                            "type": "bar",
                            "config": {
                                "title": f"Count of {col}",
                                "x": col,
                                "y": None  # Will be computed during rendering
                            },
                            "filters": {},
                            "width": "Medium",
                            "height": 350
                        })
                
                elif template_type == "Correlation Analysis":
                    # Add correlation heatmap
                    numeric_cols = get_column_types(df)['numeric']
                    if len(numeric_cols) >= 2:
                        st.session_state.dashboard_panels = [
                            {
                                "id": 0,
                                "title": "Correlation Matrix",
                                "type": "heatmap",
                                "config": {
                                    "title": "Correlation Matrix",
                                    "columns": numeric_cols[:min(8, len(numeric_cols))],
                                    "colorscale": "RdBu_r"
                                },
                                "filters": {},
                                "width": "Large",
                                "height": 500
                            }
                        ]
                        
                        # Add scatter plots for top correlations
                        for i in range(min(3, len(numeric_cols) - 1)):
                            for j in range(i + 1, min(i + 2, len(numeric_cols))):
                                st.session_state.dashboard_panels.append({
                                    "id": len(st.session_state.dashboard_panels),
                                    "title": f"{numeric_cols[i]} vs {numeric_cols[j]}",
                                    "type": "scatter",
                                    "config": {
                                        "title": f"{numeric_cols[i]} vs {numeric_cols[j]}",
                                        "x": numeric_cols[i],
                                        "y": numeric_cols[j],
                                        "opacity": 0.7
                                    },
                                    "filters": {},
                                    "width": "Medium",
                                    "height": 350
                                })
                    else:
                        st.warning("Not enough numeric columns for correlation analysis.")
                
                elif template_type == "Categorical Analysis":
                    cat_cols = get_column_types(df)['categorical']
                    numeric_cols = get_column_types(df)['numeric']
                    
                    if len(cat_cols) > 0 and len(numeric_cols) > 0:
                        # Distribution by category
                        st.session_state.dashboard_panels = []
                        
                        for i, cat_col in enumerate(cat_cols[:2]):
                            for j, num_col in enumerate(numeric_cols[:2]):
                                st.session_state.dashboard_panels.append({
                                    "id": i * 2 + j,
                                    "title": f"{num_col} by {cat_col}",
                                    "type": "box",
                                    "config": {
                                        "title": f"{num_col} by {cat_col}",
                                        "x": cat_col,
                                        "y": num_col,
                                        "notched": False
                                    },
                                    "filters": {},
                                    "width": "Medium",
                                    "height": 350
                                })
                        
                        # Pie charts
                        for i, col in enumerate(cat_cols[:2]):
                            if df[col].nunique() <= 10:  # Only if not too many categories
                                st.session_state.dashboard_panels.append({
                                    "id": len(st.session_state.dashboard_panels),
                                    "title": f"Distribution of {col}",
                                    "type": "pie",
                                    "config": {
                                        "title": f"Distribution of {col}",
                                        "names": col,
                                        "values": None  # Will be computed
                                    },
                                    "filters": {},
                                    "width": "Medium",
                                    "height": 350
                                })
                    else:
                        st.warning("Not enough categorical or numeric columns for this analysis.")
                
                elif template_type == "Time Series Analysis":
                    datetime_cols = get_column_types(df)['datetime']
                    numeric_cols = get_column_types(df)['numeric']
                    
                    if len(datetime_cols) > 0 and len(numeric_cols) > 0:
                        st.session_state.dashboard_panels = []
                        
                        # Time series line charts
                        for i, num_col in enumerate(numeric_cols[:3]):
                            st.session_state.dashboard_panels.append({
                                "id": i,
                                "title": f"{num_col} over Time",
                                "type": "line",
                                "config": {
                                    "title": f"{num_col} over Time",
                                    "x": datetime_cols[0],
                                    "y": num_col,
                                    "markers": True
                                },
                                "filters": {},
                                "width": "Large" if i == 0 else "Medium",
                                "height": 400 if i == 0 else 350
                            })
                    else:
                        st.warning("No datetime columns found in the dataset. This template requires at least one datetime column.")
                
                st.success(f"Applied {template_type} template! Scroll down to view the dashboard.")
                st.rerun()
    
    # Dashboard Display Section
    if st.session_state.dashboard_panels:
        st.subheader("Your Custom Dashboard")
        
        # Dashboard controls
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if st.button("Clear Dashboard"):
                st.session_state.dashboard_panels = []
                st.success("Dashboard cleared!")
                st.rerun()
                
        with col2:
            dashboard_name = st.text_input("Dashboard Name", "My Custom Dashboard")
        
        with col3:
            if st.button("Save Dashboard"):
                # For now, just save to session state
                if 'saved_dashboards' not in st.session_state:
                    st.session_state.saved_dashboards = {}
                
                st.session_state.saved_dashboards[dashboard_name] = st.session_state.dashboard_panels.copy()
                st.success(f"Dashboard '{dashboard_name}' saved!")
        
        # Dashboard panels
        current_row = []
        row_width = 0
        
        for panel in st.session_state.dashboard_panels:
            panel_width_value = {"Small": 1, "Medium": 2, "Large": 3}[panel["width"]]
            
            # Start a new row if this panel won't fit
            if row_width + panel_width_value > 3:
                # Render the current row
                cols = st.columns(current_row)
                for i, (col, panel_in_row) in enumerate(zip(cols, current_row)):
                    with col:
                        render_panel(panel_in_row, st.session_state.data)
                
                # Reset for new row
                current_row = []
                row_width = 0
            
            # Add panel to current row
            current_row.append(panel)
            row_width += panel_width_value
            
            # If row is full, render it
            if row_width == 3:
                cols = st.columns(current_row)
                for i, (col, panel_in_row) in enumerate(zip(cols, current_row)):
                    with col:
                        render_panel(panel_in_row, st.session_state.data)
                
                # Reset for new row
                current_row = []
                row_width = 0
        
        # Render any remaining panels
        if current_row:
            cols = st.columns(current_row)
            for i, (col, panel_in_row) in enumerate(zip(cols, current_row)):
                with col:
                    render_panel(panel_in_row, st.session_state.data)

def render_panel(panel, df):
    """Render a dashboard panel"""
    st.markdown(f"#### {panel['title']}")
    
    # Apply filters if any
    if panel["filters"]:
        filtered_df = filter_dataframe(df, panel["filters"])
    else:
        filtered_df = df
    
    # Special handling for count-based visualizations
    viz_type = panel["type"]
    config = panel["config"].copy()
    
    try:
        if viz_type == "bar" and config.get("y") is None:
            # Bar chart with counts
            value_counts = filtered_df[config["x"]].value_counts()
            temp_df = pd.DataFrame({
                config["x"]: value_counts.index,
                "count": value_counts.values
            })
            config["y"] = "count"
            fig = create_visualization(temp_df, viz_type, config)
        elif viz_type == "pie" and config.get("values") is None:
            # Pie chart with counts
            value_counts = filtered_df[config["names"]].value_counts()
            temp_df = pd.DataFrame({
                config["names"]: value_counts.index,
                "count": value_counts.values
            })
            config["values"] = "count"
            fig = create_visualization(temp_df, viz_type, config)
        else:
            # Standard visualization
            fig = create_visualization(filtered_df, viz_type, config)
        
        # Set chart height
        fig.update_layout(height=panel["height"])
        
        # Render in Streamlit
        render_chart_in_streamlit(fig)
        
        # Add edit/remove buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit", key=f"edit_{panel['id']}"):
                st.session_state.editing_panel = panel
                # This would require more complex state management
        
        with col2:
            if st.button("Remove", key=f"remove_{panel['id']}"):
                st.session_state.dashboard_panels = [p for p in st.session_state.dashboard_panels if p["id"] != panel["id"]]
                st.rerun()
    
    except Exception as e:
        st.error(f"Error rendering panel: {str(e)}")

# if __name__ == "__main__":  # This script is now imported as a module
#     show_dashboard_creator_content()
