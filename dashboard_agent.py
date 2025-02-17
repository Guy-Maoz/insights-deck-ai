from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

class Dataset(BaseModel):
    data: pd.DataFrame
    name: str
    description: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class DashboardConfig(BaseModel):
    title: str = Field(..., description="Dashboard title")
    charts: List[Dict[str, str]] = Field(..., description="List of chart configurations")
    layout: str = Field(default="grid", description="Layout style (grid/vertical)")
    theme: str = Field(default="light", description="Dashboard theme")

class DashboardDependencies(BaseModel):
    dataset: Dataset
    output_dir: Path = Field(default=Path("dashboards"))

# System prompt that instructs the agent how to handle dashboard creation
SYSTEM_PROMPT = """You are a data visualization expert that creates beautiful and insightful dashboards.
Given a dataset and instructions, you will:
1. Analyze the data to determine appropriate visualizations
2. Create a dashboard configuration with suitable charts
3. Generate an HTML dashboard using Plotly
4. Ensure the dashboard is responsive and user-friendly

When creating charts, consider:
- The data types of each column
- The relationships between variables
- The story the data is trying to tell
- Best practices in data visualization

You must use the generate_dashboard tool with a configuration that includes:
1. title: The dashboard title
2. charts: A list of chart configurations, where each chart has:
   - chart_type: One of [line, bar, scatter, pie, histogram, box]
   - x_column: The column name for the x-axis
   - y_column: The column name for the y-axis (optional for histogram and pie charts)
   - title: The chart title
3. layout: Either "grid" or "vertical"
4. theme: Either "light" or "dark"

Example configuration:
{
    "title": "Sales Dashboard",
    "charts": [
        {
            "chart_type": "line",
            "x_column": "date",
            "y_column": "sales",
            "title": "Daily Sales Trend"
        },
        {
            "chart_type": "histogram",
            "x_column": "order_value",
            "title": "Order Value Distribution"
        }
    ],
    "layout": "grid",
    "theme": "light"
}
"""

agent = Agent(
    model="openai:gpt-3.5-turbo-16k",
    deps_type=DashboardDependencies,
    system_prompt=SYSTEM_PROMPT
)

@agent.tool
async def analyze_dataset(ctx: RunContext[DashboardDependencies]) -> str:
    """Analyze the dataset and return a summary of its structure and content."""
    df = ctx.deps.dataset.data
    summary = {
        "columns": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "row_count": len(df),
        "sample": df.head(5).to_dict()
    }
    return json.dumps(summary, indent=2)

@agent.tool
async def create_chart(
    ctx: RunContext[DashboardDependencies],
    chart_type: str,
    x_column: str,
    y_column: Optional[str] = None,
    title: str = "",
    **kwargs
) -> str:
    """Create a Plotly chart and return its HTML representation."""
    df = ctx.deps.dataset.data
    available_columns = list(df.columns)
    
    # Validate column names
    if x_column not in available_columns:
        raise ValueError(f"Column '{x_column}' not found. Available columns: {available_columns}")
    if y_column and y_column not in available_columns:
        raise ValueError(f"Column '{y_column}' not found. Available columns: {available_columns}")
    
    chart_types = {
        "line": px.line,
        "bar": px.bar,
        "scatter": px.scatter,
        "pie": px.pie,
        "histogram": px.histogram,
        "box": px.box
    }
    
    if chart_type not in chart_types:
        raise ValueError(f"Unsupported chart type: {chart_type}. Available types: {list(chart_types.keys())}")
    
    # Special handling for different chart types
    if chart_type == "histogram":
        fig = px.histogram(df, x=x_column, title=title, **kwargs)
    elif chart_type == "pie":
        if not y_column:
            # For pie charts, if no y_column is provided, count occurrences of x_column
            values = df[x_column].value_counts()
            fig = px.pie(values=values.values, names=values.index, title=title, **kwargs)
        else:
            fig = px.pie(df, values=y_column, names=x_column, title=title, **kwargs)
    elif chart_type == "box":
        fig = px.box(df, x=x_column, y=y_column, title=title, **kwargs)
    else:
        # For other chart types that require both x and y
        if not y_column:
            raise ValueError(f"Chart type '{chart_type}' requires both x_column and y_column")
        fig = chart_types[chart_type](df, x=x_column, y=y_column, title=title, **kwargs)
    
    # Update layout for better visualization
    fig.update_layout(
        template="plotly_dark" if ctx.deps.dataset.name == "daily_metrics" else "plotly_white",
        margin=dict(t=50, l=50, r=50, b=50),
        title_x=0.5,  # Center the title
        showlegend=True
    )
    
    # Improve axis labels
    if y_column:
        fig.update_yaxes(title_text=y_column.replace('_', ' ').title())
    fig.update_xaxes(title_text=x_column.replace('_', ' ').title())
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

@agent.tool
async def generate_dashboard(
    ctx: RunContext[DashboardDependencies],
    config: DashboardConfig
) -> str:
    """Generate a complete HTML dashboard based on the configuration."""
    charts_html = []
    
    for chart_config in config.charts:
        chart_html = await create_chart(ctx, **chart_config)
        charts_html.append(chart_html)
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{config.title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: {config.theme == 'dark' and '#1a1a1a' or '#ffffff'};
                color: {config.theme == 'dark' and '#ffffff' or '#000000'};
            }}
            .dashboard-title {{
                text-align: center;
                padding: 20px;
            }}
            .charts-container {{
                display: {config.layout == 'grid' and 'grid' or 'flex'};
                {config.layout == 'grid' and 'grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));' or 'flex-direction: column;'}
                gap: 20px;
                padding: 20px;
            }}
            .chart-wrapper {{
                background: {config.theme == 'dark' and '#2d2d2d' or '#f5f5f5'};
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <h1 class="dashboard-title">{config.title}</h1>
        <div class="charts-container">
            {''.join([f'<div class="chart-wrapper">{chart}</div>' for chart in charts_html])}
        </div>
    </body>
    </html>
    """
    
    # Ensure output directory exists
    ctx.deps.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save dashboard
    output_file = ctx.deps.output_dir / f"{config.title.lower().replace(' ', '_')}.html"
    output_file.write_text(dashboard_html)
    
    return str(output_file.absolute())

async def create_dashboard(
    dataset: Union[pd.DataFrame, Path],
    instructions: str,
    output_dir: Path = Path("dashboards"),
    dataset_name: str = "dataset"
) -> str:
    """
    Create a dashboard from a dataset and instructions.
    
    Args:
        dataset: DataFrame or path to CSV file
        instructions: Natural language instructions for dashboard creation
        output_dir: Directory to save the dashboard
        dataset_name: Name of the dataset for reference
    
    Returns:
        Path to the generated dashboard HTML file
    """
    if isinstance(dataset, Path):
        df = pd.read_csv(dataset)
        dataset_name = dataset.stem
    else:
        df = dataset
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    deps = DashboardDependencies(
        dataset=Dataset(
            data=df,
            name=dataset_name,
            description=f"Dataset loaded from {dataset if isinstance(dataset, Path) else 'DataFrame'}"
        ),
        output_dir=output_dir
    )
    
    # Create a concise dataset summary
    df_summary = {
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "row_count": len(df)
    }
    
    # Add dataset information to the instructions
    enhanced_instructions = f"""
    Dataset Summary:
    - Columns: {', '.join(df_summary['columns'])}
    - Number of rows: {df_summary['row_count']}
    - Data types: {', '.join(f'{col} ({dtype})' for col, dtype in df_summary['data_types'].items())}
    
    Original Instructions:
    {instructions}
    
    Please create a dashboard using the available columns shown above.
    Ensure all column names match exactly with the dataset.
    """
    
    result = await agent.run(enhanced_instructions, deps=deps)
    return result.data 