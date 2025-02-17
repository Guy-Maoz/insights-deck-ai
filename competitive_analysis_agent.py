import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard
import json
from typing import List, Optional, Dict

class CompetitiveAnalysis:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.df = pd.read_excel(excel_file, sheet_name=1)
        self.temp_csv = "amazon_sales_data.csv"
        self.df.to_csv(self.temp_csv, index=False)
        self.columns = list(self.df.columns)
        self.current_dashboard = None
        
    def get_market_overview(self) -> Dict:
        """Get a high-level overview of the market."""
        total_revenue = self.df['Revenue'].sum()
        total_units = self.df['Units Sold'].sum()
        total_brands = self.df['Brand'].nunique()
        
        top_brands = (self.df.groupby('Brand')
                     .agg({
                         'Revenue': 'sum',
                         'Units Sold': 'sum',
                         'Rating': 'mean'
                     })
                     .sort_values('Revenue', ascending=False)
                     .head(10))
        
        return {
            "total_revenue": total_revenue,
            "total_units": total_units,
            "total_brands": total_brands,
            "top_brands": top_brands.to_dict(orient='index')
        }
    
    def get_brand_analysis(self, brand: str) -> Dict:
        """Get detailed analysis for a specific brand."""
        brand_data = self.df[self.df['Brand'] == brand]
        if len(brand_data) == 0:
            return {"error": f"Brand '{brand}' not found in the dataset"}
        
        market_share = (brand_data['Revenue'].sum() / self.df['Revenue'].sum()) * 100
        unit_share = (brand_data['Units Sold'].sum() / self.df['Units Sold'].sum()) * 100
        
        return {
            "market_share": market_share,
            "unit_share": unit_share,
            "avg_rating": brand_data['Rating'].mean(),
            "total_reviews": brand_data['Reviews'].sum(),
            "products_count": len(brand_data),
            "categories": brand_data['Category'].unique().tolist(),
            "best_sellers": len(brand_data[brand_data['Best Seller Rank'] > 0])
        }
    
    def get_competitive_analysis(self, brand: str, competitors: Optional[List[str]] = None) -> Dict:
        """Get comparative analysis between brands."""
        if competitors is None:
            # Get top 5 competitors by revenue excluding the main brand
            competitors = (self.df[self.df['Brand'] != brand]
                         .groupby('Brand')['Revenue']
                         .sum()
                         .sort_values(ascending=False)
                         .head(5)
                         .index.tolist())
        
        brands = [brand] + competitors
        comp_data = self.df[self.df['Brand'].isin(brands)]
        
        analysis = {}
        for b in brands:
            analysis[b] = self.get_brand_analysis(b)
        
        return {
            "brands_analyzed": brands,
            "analysis": analysis
        }
    
    async def generate_competitive_dashboard(self, 
                                          brand: Optional[str] = None, 
                                          competitors: Optional[List[str]] = None) -> str:
        """Generate a competitive analysis dashboard."""
        if brand:
            if competitors:
                title = f"Competitive Analysis: {brand} vs. Competitors"
                comp_analysis = self.get_competitive_analysis(brand, competitors)
            else:
                title = f"Market Analysis: {brand}"
                comp_analysis = self.get_competitive_analysis(brand)
            
            instructions = f"""
            Create a comprehensive competitive analysis dashboard for {brand} with:
            
            1. Market Overview:
               - Bar chart showing Revenue comparison between {brand} and competitors
               - Pie chart showing market share distribution
               - Bar chart comparing average ratings
            
            2. Performance Metrics:
               - Scatter plot of Units Sold vs Revenue for all competitors
               - Bar chart showing review counts by brand
               - Bar chart showing number of products by category for each brand
            
            Additional requirements:
            - Use a professional dark theme for better visualization
            - Sort all bar charts by value in descending order
            - Include hover information with detailed metrics
            - Add clear titles and labels
            - Use a grid layout for better comparison
            """
        else:
            title = "Market Overview Analysis"
            overview = self.get_market_overview()
            
            instructions = """
            Create a comprehensive market overview dashboard with:
            
            1. Market Leaders:
               - Bar chart showing top 10 brands by Revenue
               - Scatter plot comparing Units Sold vs Revenue for top brands
               - Bar chart showing average ratings for top brands
            
            2. Market Distribution:
               - Pie chart showing market share of top 10 brands
               - Bar chart showing number of products by top brands
               - Bar chart showing total reviews by brand
            
            Additional requirements:
            - Use a professional dark theme for better visualization
            - Sort all bar charts by value in descending order
            - Include hover information with detailed metrics
            - Add clear titles and labels
            - Use a grid layout for better comparison
            """
        
        try:
            dashboard_path = await create_dashboard(
                dataset=Path(self.temp_csv),
                instructions=instructions,
                output_dir=Path("dashboards"),
                dataset_name="competitive_analysis"
            )
            self.current_dashboard = dashboard_path
            return f"Dashboard created successfully at: {dashboard_path}"
        except Exception as e:
            return f"Error creating dashboard: {str(e)}"
    
    def __del__(self):
        """Cleanup temporary files."""
        import os
        if os.path.exists(self.temp_csv):
            os.remove(self.temp_csv)

async def interactive_analysis():
    print("\nWelcome to the Amazon Competitive Analysis Dashboard!")
    print("\nInitializing analysis with your Amazon sales data...")
    
    analyzer = CompetitiveAnalysis("Top Products - categories - sales-performance - amazon.com - 2024-02 - 2025-01.xlsx")
    
    print("\nMarket Overview:")
    overview = analyzer.get_market_overview()
    print(f"Total Brands: {overview['total_brands']}")
    print(f"Top 10 Brands by Revenue:")
    for brand, data in overview['top_brands'].items():
        print(f"- {brand}")
    
    while True:
        try:
            print("\nAnalysis Options:")
            print("1. Market Overview (no specific brand)")
            print("2. Brand Analysis (your brand)")
            print("3. Competitive Analysis (your brand + competitors)")
            print("4. Exit")
            
            choice = input("\nWhat would you like to analyze? ").strip()
            
            if choice in ['4', 'exit', 'quit']:
                print("Ending session...")
                break
            
            elif choice in ['1', 'market', 'overview']:
                print("\nGenerating market overview dashboard...")
                result = await analyzer.generate_competitive_dashboard()
                print(result)
            
            elif choice in ['2', 'brand']:
                brand = input("\nEnter your brand name: ").strip()
                if not brand:
                    print("Please provide a brand name.")
                    continue
                    
                print(f"\nGenerating analysis for {brand}...")
                result = await analyzer.generate_competitive_dashboard(brand=brand)
                print(result)
            
            elif choice in ['3', 'competitive']:
                brand = input("\nEnter your brand name: ").strip()
                if not brand:
                    print("Please provide a brand name.")
                    continue
                
                competitors = input("\nEnter competitor brands (comma-separated) or press Enter for top competitors: ").strip()
                competitors = [c.strip() for c in competitors.split(',')] if competitors else None
                
                print(f"\nGenerating competitive analysis for {brand}...")
                result = await analyzer.generate_competitive_dashboard(brand=brand, competitors=competitors)
                print(result)
            
            else:
                print("\nUnrecognized option. Please choose 1-4.")
        
        except KeyboardInterrupt:
            print("\nEnding session...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(interactive_analysis()) 