import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard

async def main():
    # Read the Excel file, skipping the description sheet
    excel_file = "Top Products - categories - sales-performance - amazon.com - 2024-02 - 2025-01.xlsx"
    df = pd.read_excel(excel_file, sheet_name=1)
    
    # Save as temporary CSV for the dashboard generator
    temp_csv = "amazon_sales_data.csv"
    df.to_csv(temp_csv, index=False)
    
    try:
        # Create a dashboard for Amazon sales performance
        dashboard_path = await create_dashboard(
            dataset=Path(temp_csv),
            instructions="""
            Create a comprehensive dashboard analyzing Amazon product performance with:
            1. A bar chart showing top 10 categories by Revenue
            2. A scatter plot comparing Units Sold vs Revenue, colored by Category
            3. A bar chart showing average Rating by Category
            4. A pie chart showing distribution of Units Sold by Category
            
            Additional requirements:
            - Sort bars by value in descending order
            - Use clear, readable labels
            - Include hover information with detailed metrics
            - Use a professional light theme with a grid layout
            - Add appropriate titles and axis labels
            """,
            output_dir=Path("dashboards"),
            dataset_name="amazon_sales"
        )
        print(f"Amazon sales dashboard created at: {dashboard_path}")
    
    finally:
        # Clean up temporary CSV file
        import os
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

if __name__ == "__main__":
    asyncio.run(main()) 