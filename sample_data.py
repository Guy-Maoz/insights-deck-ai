import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate sample e-commerce data
np.random.seed(42)

# Date range for the last 90 days
dates = pd.date_range(end=datetime.now(), periods=90, freq='D')

# Generate sample data
data = {
    'date': dates,
    'daily_sales': np.random.normal(1000, 200, 90).cumsum(),  # Cumulative sales
    'orders': np.random.randint(50, 200, 90),
    'average_order_value': np.random.normal(85, 15, 90),
    'customer_satisfaction': np.random.normal(4.2, 0.3, 90).clip(1, 5),
}

# Create product categories data
products = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports']
product_sales = {
    'product_category': products,
    'total_sales': np.random.randint(5000, 50000, len(products)),
    'profit_margin': np.random.uniform(0.15, 0.35, len(products))
}

# Create the main DataFrame
df = pd.DataFrame(data)

# Create the products DataFrame
products_df = pd.DataFrame(product_sales)

# Save both datasets
df.to_csv('ecommerce_daily.csv', index=False)
products_df.to_csv('product_categories.csv', index=False)

print("Sample data generated and saved to 'ecommerce_daily.csv' and 'product_categories.csv'") 