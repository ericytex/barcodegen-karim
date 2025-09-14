#!/usr/bin/env python3
"""
Create a sample Excel template for barcode generation
"""

import pandas as pd
import os

def create_sample_excel_template():
    """Create a sample Excel template with proper column names"""
    
    # Sample data
    sample_data = [
        {
            'IMEI/SN': '359827134443046',
            'Model': 'X6525D',
            'Product': 'SMART 8 64+3 SHINY GOLD',
            'Color': 'SHINY GOLD',
            'D/N': 'M8N7',
            'Box ID': 'BOX001'
        },
        {
            'IMEI/SN': '359827134443047',
            'Model': 'X6525D',
            'Product': 'SMART 8 64+3 MIDNIGHT BLACK',
            'Color': 'MIDNIGHT BLACK',
            'D/N': 'M8N7',
            'Box ID': 'BOX002'
        },
        {
            'IMEI/SN': '359827134443048',
            'Model': 'X6525D',
            'Product': 'SMART 8 64+3 OCEAN BLUE',
            'Color': 'OCEAN BLUE',
            'D/N': 'M8N7',
            'Box ID': 'BOX003'
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Save to Excel file
    template_path = 'uploads/sample_barcode_template.xlsx'
    df.to_excel(template_path, index=False)
    
    print(f"✅ Sample Excel template created: {template_path}")
    print(f"📊 Template contains {len(sample_data)} sample rows")
    print(f"📋 Column names: {list(df.columns)}")
    
    return template_path

if __name__ == "__main__":
    create_sample_excel_template()
