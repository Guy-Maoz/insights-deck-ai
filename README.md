# AI Dashboard Generator

An AI-powered dashboard generator that creates interactive HTML dashboards from datasets based on natural language instructions. Built with Plotly, Pydantic, and OpenAI's GPT models.

## Features

- **Natural Language Instructions**: Create dashboards by describing what you want to visualize
- **Automatic Data Analysis**: Intelligent selection of appropriate visualizations based on data types
- **Interactive Visualizations**: Built with Plotly for rich, interactive charts
- **Responsive Layout**: Grid and vertical layouts with automatic responsiveness
- **Theme Support**: Light and dark theme options
- **Multiple Chart Types**:
  - Line charts
  - Bar charts
  - Scatter plots
  - Pie charts
  - Histograms
  - Box plots

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-dashboard-generator.git
cd ai-dashboard-generator
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

```python
import asyncio
from pathlib import Path
from dashboard_agent import create_dashboard

async def main():
    # Create a dashboard from a CSV file
    dashboard_path = await create_dashboard(
        dataset=Path("your_data.csv"),
        instructions="""
        Create a dashboard showing:
        1. A line chart of daily trends
        2. A histogram of values
        3. A scatter plot comparing two metrics
        Use a dark theme and grid layout
        """,
        output_dir=Path("output")
    )
    print(f"Dashboard created at: {dashboard_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Sample Data Generation

The repository includes a sample data generator for testing:

```python
python sample_data.py
```

This will create sample e-commerce data files that you can use to test the dashboard generator.

### Running the Example

```python
python run_dashboard.py
```

This will create two sample dashboards:
1. E-commerce daily metrics dashboard
2. Product category performance dashboard

## Configuration

The dashboard generator supports various configuration options:

- **Layout**: Grid or vertical layout
- **Theme**: Light or dark theme
- **Chart Types**: Multiple chart types with customizable parameters
- **Output Directory**: Configurable output location for generated dashboards

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Plotly](https://plotly.com/python/)
- Powered by [OpenAI GPT](https://openai.com/gpt-4)
- Uses [Pydantic](https://pydantic.dev/) for data validation 