import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import os
from utils.visualization import create_visualization
from utils.ai_insights import generate_report_with_ai

def generate_report_template(title, description, sections, author="", date=None):
    """
    Generate a report template structure
    
    Args:
        title (str): Report title
        description (str): Report description
        sections (list): List of section dictionaries
        author (str, optional): Report author name
        date (str, optional): Report date
        
    Returns:
        dict: Report template structure
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "title": title,
        "description": description,
        "author": author,
        "date": date,
        "sections": sections
    }

def add_section_to_report(report, title, content, visualizations=None):
    """
    Add a section to an existing report
    
    Args:
        report (dict): Report dictionary
        title (str): Section title
        content (str): Section content
        visualizations (list, optional): List of visualization dictionaries
        
    Returns:
        dict: Updated report
    """
    if visualizations is None:
        visualizations = []
    
    new_section = {
        "title": title,
        "content": content,
        "visualizations": visualizations
    }
    
    report["sections"].append(new_section)
    return report

def render_report_in_streamlit(report, df=None):
    """
    Render a report in Streamlit
    
    Args:
        report (dict): Report dictionary to render
        df (pandas.DataFrame, optional): Dataframe for generating visualizations
    """
    st.title(report["title"])
    st.write(f"*{report['date']}*")
    
    if report["author"]:
        st.write(f"**Author:** {report['author']}")
    
    st.write(report["description"])
    
    for section in report["sections"]:
        st.subheader(section["title"])
        st.write(section["content"])
        
        # Render visualizations if any
        if section["visualizations"] and df is not None:
            for viz in section["visualizations"]:
                try:
                    viz_type = viz.get("type")
                    config = viz.get("config", {})
                    
                    if viz_type and config:
                        fig = create_visualization(df, viz_type, config)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add caption if available
                        if "caption" in viz:
                            st.caption(viz["caption"])
                except Exception as e:
                    st.error(f"Error rendering visualization: {str(e)}")

def generate_report_html(report, df=None):
    """
    Generate an HTML version of the report
    
    Args:
        report (dict): Report dictionary
        df (pandas.DataFrame, optional): Dataframe for generating visualizations
        
    Returns:
        str: HTML string of the report
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report["title"]}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .header h1 {{
                margin-bottom: 10px;
                color: #2c3e50;
            }}
            .meta {{
                color: #7f8c8d;
                font-size: 0.9em;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section h2 {{
                color: #3498db;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .visualization {{
                margin: 20px 0;
                text-align: center;
            }}
            .caption {{
                font-style: italic;
                color: #7f8c8d;
                text-align: center;
                margin-top: 5px;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{report["title"]}</h1>
                <div class="meta">
                    <p>Date: {report["date"]}</p>
                    {"<p>Author: " + report["author"] + "</p>" if report["author"] else ""}
                </div>
                <p>{report["description"]}</p>
            </div>
    """
    
    # Add sections
    for section in report["sections"]:
        html += f"""
            <div class="section">
                <h2>{section["title"]}</h2>
                <div class="content">
                    {section["content"].replace('\n', '<br>')}
                </div>
            </div>
        """
        
        # Add visualizations if any
        if section["visualizations"] and df is not None:
            for i, viz in enumerate(section["visualizations"]):
                try:
                    viz_type = viz.get("type")
                    config = viz.get("config", {})
                    
                    if viz_type and config:
                        # Create visualization using plotly
                        fig = create_visualization(df, viz_type, config)
                        
                        # Convert to static image for HTML
                        img_bytes = fig.to_image(format="png")
                        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                        
                        html += f"""
                            <div class="visualization">
                                <img src="data:image/png;base64,{img_base64}" alt="{viz_type} visualization">
                                {"<div class='caption'>" + viz.get("caption", "") + "</div>" if "caption" in viz else ""}
                            </div>
                        """
                except Exception as e:
                    html += f"""<div class="error">Error rendering visualization: {str(e)}</div>"""
        
        html += "</div>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

def generate_pdf_report(report, df=None):
    """
    Generate a PDF version of the report
    
    Note: This function creates an HTML report and converts it to PDF
    
    Args:
        report (dict): Report dictionary
        df (pandas.DataFrame, optional): Dataframe for generating visualizations
        
    Returns:
        BytesIO: PDF file as BytesIO object
    """
    try:
        import weasyprint
        
        # Generate HTML report
        html_report = generate_report_html(report, df)
        
        # Convert HTML to PDF
        pdf_bytes = BytesIO()
        weasyprint.HTML(string=html_report).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)
        
        return pdf_bytes
    
    except ImportError:
        # Fallback if weasyprint is not available
        st.error("PDF generation requires WeasyPrint library, which is not available. Providing HTML report instead.")
        return None

def generate_excel_report(report, df):
    """
    Generate an Excel version of the report
    
    Args:
        report (dict): Report dictionary
        df (pandas.DataFrame): Dataframe for the report
        
    Returns:
        BytesIO: Excel file as BytesIO object
    """
    output = BytesIO()
    
    try:
        # Create a Pandas Excel writer using XlsxWriter as the engine
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Create a sheet for the data
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Create a sheet for the report
            report_data = {
                'Section': [],
                'Content': []
            }
            
            # Add report title and description
            report_data['Section'].append('Title')
            report_data['Content'].append(report['title'])
            
            report_data['Section'].append('Description')
            report_data['Content'].append(report['description'])
            
            report_data['Section'].append('Date')
            report_data['Content'].append(report['date'])
            
            report_data['Section'].append('Author')
            report_data['Content'].append(report['author'])
            
            # Add each section
            for section in report['sections']:
                report_data['Section'].append(section['title'])
                report_data['Content'].append(section['content'])
            
            # Write report data to Excel
            pd.DataFrame(report_data).to_excel(writer, sheet_name='Report', index=False)
            
            # Access the workbook and the worksheets
            workbook = writer.book
            report_sheet = writer.sheets['Report']
            
            # Set column widths in the report sheet
            report_sheet.set_column('A:A', 20)
            report_sheet.set_column('B:B', 80)
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write the column headers with the defined format
            for col_num, value in enumerate(['Section', 'Content']):
                report_sheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        return output
    
    except Exception as e:
        st.error(f"Error generating Excel report: {str(e)}")
        return None

def download_report(report, df, file_format="html"):
    """
    Create a download button for the report
    
    Args:
        report (dict): Report dictionary
        df (pandas.DataFrame): Dataframe used in the report
        file_format (str): Format to download ('html', 'pdf', 'excel')
    """
    if file_format == "html":
        html_report = generate_report_html(report, df)
        b64 = base64.b64encode(html_report.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="{report["title"]}.html">Download HTML Report</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    elif file_format == "pdf":
        pdf_bytes = generate_pdf_report(report, df)
        if pdf_bytes:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"{report['title']}.pdf",
                mime="application/pdf"
            )
    
    elif file_format == "excel":
        excel_bytes = generate_excel_report(report, df)
        if excel_bytes:
            st.download_button(
                label="Download Excel Report",
                data=excel_bytes,
                file_name=f"{report['title']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def generate_ai_report(df, report_type="overview", title="AI-Generated Data Report"):
    """
    Generate a complete report using AI
    
    Args:
        df (pandas.DataFrame): Dataframe to analyze
        report_type (str): Type of report ('overview', 'detailed', 'executive')
        title (str): Report title
        
    Returns:
        dict: Report dictionary
    """
    # Generate report content with AI
    report_content = generate_report_with_ai(df, report_type)
    
    # Create initial report structure
    report = generate_report_template(
        title=title,
        description="This report was automatically generated using AI analysis.",
        sections=[],
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Parse the content into sections
    import re
    
    # Extract sections using headers
    section_pattern = r'#+\s+(.+?)\n(.+?)(?=\n#+\s+|\Z)'
    sections = re.findall(section_pattern, report_content, re.DOTALL)
    
    # If no sections found, use the entire content as one section
    if not sections:
        sections = [("Key Findings", report_content)]
    
    # Add each section to the report
    for section_title, section_content in sections:
        add_section_to_report(
            report,
            title=section_title.strip(),
            content=section_content.strip(),
            visualizations=[]  # No visualizations yet
        )
    
    return report
