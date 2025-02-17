import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard
import json
from typing import List, Optional, Dict
from difflib import get_close_matches

class CompetitiveAnalysis:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        print(f"\nLoading data from {excel_file}...")
        self.df = pd.read_excel(excel_file, sheet_name=1)
        print(f"Data loaded: {len(self.df)} rows")
        
        # Create a filtered DataFrame with only the columns we need
        self.df = self.df[[
            'Brand', 
            'Category',
            'Revenue',
            'Units Sold',
            'Rating',
            'Reviews',
            'Best Seller Rank'
        ]].copy()
        
        # Convert Revenue to numeric, removing any currency symbols and commas
        self.df['Revenue'] = pd.to_numeric(self.df['Revenue'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
        self.df['Units Sold'] = pd.to_numeric(self.df['Units Sold'].astype(str).str.replace(',', ''), errors='coerce')
        
        # Get list of all unique brands for validation
        self.available_brands = sorted(self.df['Brand'].unique())
        
        print(f"Columns prepared: {list(self.df.columns)}")
        print(f"Sample of processed data:\n{self.df.head()}\n")
        
        self.temp_csv = "amazon_sales_data.csv"
        self.df.to_csv(self.temp_csv, index=False)
        self.columns = list(self.df.columns)
        self.current_dashboard = None
        
    def validate_brand(self, brand: str) -> Optional[str]:
        """Validate and normalize brand name, handling typos and case sensitivity."""
        if not brand:
            return None
            
        # First try exact match (case insensitive)
        exact_matches = [b for b in self.available_brands if b.lower() == brand.lower()]
        if exact_matches:
            return exact_matches[0]
        
        # If no exact match, try to find close matches
        close_matches = get_close_matches(brand.upper(), [b.upper() for b in self.available_brands], n=3, cutoff=0.6)
        
        if close_matches:
            # Get the original case for the matches
            original_case_matches = [b for b in self.available_brands if b.upper() in close_matches]
            
            print(f"\nDid you mean one of these brands?")
            for i, match in enumerate(original_case_matches, 1):
                print(f"{i}. {match}")
            
            choice = input("Enter the number of the correct brand (or press Enter to use your original input): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(original_case_matches):
                return original_case_matches[int(choice)-1]
        
        print(f"\nWarning: Brand '{brand}' not found exactly. Available brands:")
        print("\n".join(f"- {b}" for b in self.available_brands))
        return None
    
    def validate_competitors(self, competitors: List[str]) -> List[str]:
        """Validate and normalize competitor brand names."""
        validated = []
        for comp in competitors:
            valid_name = self.validate_brand(comp)
            if valid_name and valid_name not in validated:
                validated.append(valid_name)
        return validated
    
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
        
        print("\nMarket Overview Stats:")
        print(f"Total Revenue: ${total_revenue:,.2f}")
        print(f"Total Units: {total_units:,.0f}")
        print(f"Top Brands Revenue:\n{top_brands['Revenue']}\n")
        
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
        
        analysis = {
            "market_share": market_share,
            "unit_share": unit_share,
            "avg_rating": brand_data['Rating'].mean(),
            "total_reviews": brand_data['Reviews'].sum(),
            "products_count": len(brand_data),
            "categories": brand_data['Category'].unique().tolist(),
            "best_sellers": len(brand_data[brand_data['Best Seller Rank'] > 0])
        }
        
        print(f"\nBrand Analysis for {brand}:")
        print(f"Market Share: {market_share:.1f}%")
        print(f"Unit Share: {unit_share:.1f}%")
        print(f"Products: {len(brand_data)}")
        
        return analysis
    
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
            # Validate brand name
            valid_brand = self.validate_brand(brand)
            if not valid_brand:
                return f"Error: Could not validate brand name '{brand}'"
            
            if competitors:
                # Validate competitor names
                valid_competitors = self.validate_competitors(competitors)
                if not valid_competitors:
                    return "Error: No valid competitor brands provided"
                
                title = f"Competitive Analysis: {valid_brand} vs. Competitors"
                comp_analysis = self.get_competitive_analysis(valid_brand, valid_competitors)
                brands = [valid_brand] + valid_competitors
            else:
                title = f"Market Analysis: {valid_brand}"
                comp_analysis = self.get_competitive_analysis(valid_brand)
                brands = [valid_brand] + [comp for comp in self.df['Brand'].unique() if comp != valid_brand][:5]
            
            # Filter data for the dashboard
            dashboard_data = self.df[self.df['Brand'].isin(brands)].copy()
            dashboard_data.to_csv(self.temp_csv, index=False)
            
            print(f"\nPreparing dashboard for brands: {brands}")
            print(f"Dashboard data shape: {dashboard_data.shape}")
            
            instructions = f"""
            Create a comprehensive competitive analysis dashboard for {valid_brand} with:
            
            1. Market Overview:
               - Bar chart showing Revenue comparison between {valid_brand} and competitors
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
            
            Note: The data has been pre-filtered to include only {len(brands)} brands: {', '.join(brands)}
            """
        else:
            title = "Market Overview Analysis"
            overview = self.get_market_overview()
            
            # Filter data for top 10 brands
            top_brands = list(overview['top_brands'].keys())
            dashboard_data = self.df[self.df['Brand'].isin(top_brands)].copy()
            dashboard_data.to_csv(self.temp_csv, index=False)
            
            print(f"\nPreparing market overview dashboard")
            print(f"Top brands included: {top_brands}")
            print(f"Dashboard data shape: {dashboard_data.shape}")
            
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
            print("\nGenerating dashboard with instructions:")
            print(instructions)
            
            dashboard_path = await create_dashboard(
                dataset=Path(self.temp_csv),
                instructions=instructions,
                output_dir=Path("dashboards"),
                dataset_name="competitive_analysis"
            )
            self.current_dashboard = dashboard_path
            return f"Dashboard created successfully at: {dashboard_path}"
        except Exception as e:
            print(f"\nError creating dashboard: {str(e)}")
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