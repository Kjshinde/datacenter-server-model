import pandas as pd
import os

file_path = 'data/SDC_Financial_Model rev6.xlsx'

print(f"Current CWD: {os.getcwd()}")
print(f"File exists: {os.path.exists(file_path)}")

try:
    df = pd.read_excel(file_path, sheet_name='CPU', header=3, index_col=0)
    print("Successfully read Excel file.")
    print(df.head())
except Exception as e:
    print(f"Error reading Excel file: {e}")
    import traceback
    traceback.print_exc()
