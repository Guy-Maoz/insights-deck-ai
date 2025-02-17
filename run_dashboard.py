import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard

async def main():
    # First generate the sample data
    import sample_data
    
    # Create a dashboard for daily metrics
    daily_dashboard_path = await create_dashboard(
        dataset=Path("ecommerce_daily.csv"),
        instructions="""
        Create a dashboard showing e-commerce performance metrics with:
        1. A line chart showing daily sales trends
        2. A scatter plot of orders vs average order value
        3. A histogram of customer satisfaction scores
        Use a dark theme and grid layout for better visualization
        """,
        output_dir=Path("dashboards")
    )
    print(f"Daily metrics dashboard created at: {daily_dashboard_path}")
    
    # Create a dashboard for product categories
    product_dashboard_path = await create_dashboard(
        dataset=Path("product_categories.csv"),
        instructions="""
        Create a dashboard analyzing product category performance with:
        1. A bar chart of total sales by category
        2. A pie chart showing sales distribution
        3. A bar chart of profit margins by category
        Use a light theme with vertical layout
        """,
        output_dir=Path("dashboards")
    )
    print(f"Product categories dashboard created at: {product_dashboard_path}")

if __name__ == "__main__":
    asyncio.run(main()) 