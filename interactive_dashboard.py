import asyncio
from pathlib import Path
import pandas as pd
from dashboard_agent import create_dashboard
import json

class DashboardSession:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.df = pd.read_excel(excel_file, sheet_name=1)
        self.temp_csv = "amazon_sales_data.csv"
        self.df.to_csv(self.temp_csv, index=False)
        self.columns = list(self.df.columns)
        self.current_dashboard = None
        
    def get_data_summary(self) -> str:
        """Get a summary of the available data."""
        summary = {
            "columns": self.columns,
            "rows": len(self.df),
            "numeric_columns": self.df.select_dtypes(include=['int64', 'float64']).columns.tolist(),
            "categorical_columns": self.df.select_dtypes(include=['object']).columns.tolist()
        }
        return json.dumps(summary, indent=2)
    
    async def generate_dashboard(self, instructions: str) -> str:
        """Generate a dashboard based on user instructions."""
        try:
            dashboard_path = await create_dashboard(
                dataset=Path(self.temp_csv),
                instructions=instructions,
                output_dir=Path("dashboards"),
                dataset_name="amazon_sales"
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

async def interactive_session():
    print("\nWelcome to the Interactive Dashboard Generator!")
    print("\nInitializing session with your Amazon sales data...")
    
    session = DashboardSession("Top Products - categories - sales-performance - amazon.com - 2024-02 - 2025-01.xlsx")
    
    print("\nData Summary:")
    print(session.get_data_summary())
    
    print("\nYou can now interact with the dashboard generator. Here are some example commands:")
    print("1. show columns - Display available data columns")
    print("2. create dashboard [your instructions] - Generate a new dashboard")
    print("3. help - Show this help message")
    print("4. exit - End the session")
    
    while True:
        try:
            # Get input and clean it
            user_input = input("\nWhat would you like to do? ").strip()
            # Remove any quotes and convert to lowercase for command matching
            cleaned_input = user_input.replace("'", "").replace('"', "").lower().strip()
            
            if cleaned_input in ['exit', '4', 'quit']:
                print("Ending session...")
                break
            
            elif cleaned_input in ['help', '3', '?']:
                print("\nAvailable commands:")
                print("1. show columns - Display available data columns")
                print("2. create dashboard [your instructions] - Generate a new dashboard")
                print("3. help - Show this help message")
                print("4. exit - End the session")
            
            elif cleaned_input in ['show columns', '1', 'columns']:
                print("\nAvailable columns:")
                for col in session.columns:
                    print(f"- {col}")
            
            elif cleaned_input.startswith('create dashboard') or cleaned_input.startswith('2 '):
                # Extract instructions, handling both "create dashboard" and "2" prefix
                instructions = (user_input[len('create dashboard'):] if cleaned_input.startswith('create dashboard') 
                              else user_input[2:]).strip()
                
                if not instructions:
                    print("Please provide instructions for the dashboard.")
                    print("Example: create dashboard Show me a bar chart of top 10 categories by Revenue")
                    print("   - or -")
                    print("2 Show me a bar chart of top 10 categories by Revenue")
                    continue
                
                print("\nGenerating dashboard...")
                result = await session.generate_dashboard(instructions)
                print(result)
            
            else:
                print("\nUnrecognized command. Type 'help' or '3' for available commands.")
        
        except KeyboardInterrupt:
            print("\nEnding session...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(interactive_session()) 