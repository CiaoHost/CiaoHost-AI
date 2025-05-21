import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def create_visualization(df: pd.DataFrame, x: str, y: str, chart_type: str = "bar"):
    """Crea un grafico matplotlib a seconda del tipo scelto."""
    fig, ax = plt.subplots()

    if chart_type == "bar":
        df.groupby(x)[y].mean().plot(kind="bar", ax=ax)
    elif chart_type == "line":
        df.groupby(x)[y].mean().plot(kind="line", ax=ax)
    elif chart_type == "scatter":
        sns.scatterplot(data=df, x=x, y=y, ax=ax)
    else:
        ax.text(0.5, 0.5, "Tipo grafico non supportato", ha='center')

    return fig

def render_chart_in_streamlit(fig):
    """Mostra un grafico in Streamlit."""
    st.pyplot(fig)

def suggest_visualizations(df: pd.DataFrame) -> list:
    """Suggerisce grafici in base al contenuto del dataframe."""
    suggestions = []
    numeric_columns = df.select_dtypes(include='number').columns
    categorical_columns = df.select_dtypes(include='object').columns

    if len(categorical_columns) > 0 and len(numeric_columns) > 0:
        suggestions.append({
            "x": categorical_columns[0],
            "y": numeric_columns[0],
            "type": "bar"
        })

    return suggestions
