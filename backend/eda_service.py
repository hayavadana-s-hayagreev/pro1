import pandas as pd
from pathlib import Path
import json

DATA_PATH = Path("data/raw/yield_df.csv")

# We will cache this in memory to avoid reading CSV on every request
eda_cache = {}

def load_eda_data():
    if eda_cache:
        return
        
    try:
        df = pd.read_csv(DATA_PATH)
        
        # 1. Yield by crop (average)
        crop_yield = df.groupby('Item')['hg/ha_yield'].mean().reset_index()
        crop_yield.columns = ['crop', 'avg_yield']
        eda_cache['crop_yield'] = crop_yield.to_dict(orient='records')
        
        # 2. Yield trend over years
        yearly_yield = df.groupby('Year')['hg/ha_yield'].mean().reset_index()
        yearly_yield.columns = ['year', 'avg_yield']
        eda_cache['yearly_trend'] = yearly_yield.to_dict(orient='records')
        
        # 3. Top 20 countries by average yield
        country_yield = df.groupby('Area')['hg/ha_yield'].mean().sort_values(ascending=False).head(20).reset_index()
        country_yield.columns = ['country', 'avg_yield']
        eda_cache['top_countries'] = country_yield.to_dict(orient='records')
        
        # 4. Summary Stats
        eda_cache['summary'] = {
            'total_records': int(len(df)),
            'unique_crops': int(df['Item'].nunique()),
            'unique_countries': int(df['Area'].nunique()),
            'year_range': f"{df['Year'].min()} - {df['Year'].max()}"
        }
    except Exception as e:
        print(f"Error loading EDA data: {e}")
        
def get_eda_data(key: str):
    load_eda_data()
    return eda_cache.get(key, [])
