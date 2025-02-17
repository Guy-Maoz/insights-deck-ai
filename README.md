# Dashboard Generator AI Agent

An AI-powered dashboard generator that creates interactive HTML dashboards from datasets based on natural language instructions.

## Features

- Automatic data analysis and visualization selection
- Interactive Plotly charts
- Responsive layout with grid/vertical options
- Light/dark theme support
- Multiple chart types supported (line, bar, scatter, pie, histogram, box)

## Installation

```bash
# Clone the repository
git clone https://github.com/Guy-Maoz/insights-deck-ai.git
cd insights-deck-ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Environment Variables

Copy `.env.example` to `.env` and set the following variables:

- `OPENAI_API_KEY`: Your OpenAI API key (get it from https://platform.openai.com/api-keys)

## Usage

```python
import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard

# Example with a CSV file
async def main():
    # From CSV file
    dashboard_path = await create_dashboard(
        dataset=Path("your_data.csv"),
        instructions="Create a dashboard showing sales trends over time and top products",
        output_dir=Path("output")
    )
    print(f"Dashboard created at: {dashboard_path}")

    # Or with a pandas DataFrame
    df = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=100),
        "sales": np.random.randn(100).cumsum()
    })
    
    dashboard_path = await create_dashboard(
        dataset=df,
        instructions="Create a line chart showing sales trends with a 7-day moving average",
        output_dir=Path("output")
    )
    print(f"Dashboard created at: {dashboard_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Supported Chart Types

- Line charts
- Bar charts
- Scatter plots
- Pie charts
- Histograms
- Box plots

## Configuration

The dashboard layout and theme can be customized through the natural language instructions. For example:

- "Create a dark theme dashboard with a grid layout..."
- "Generate a vertical dashboard with light theme..."

## Output

The agent generates a standalone HTML file containing the dashboard, which can be opened in any modern web browser. The dashboard is responsive and includes interactive features like zooming and hovering.

## Security Note

Never commit your `.env` file to version control. The `.gitignore` file is configured to exclude it. 