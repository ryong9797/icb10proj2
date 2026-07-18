import pandas as pd
import sys

def inspect_parquet(file_path):
    try:
        df = pd.read_parquet(file_path)
        with open('inspect_out.txt', 'w', encoding='utf-8') as f:
            f.write("--- DataFrame Info ---\n")
            import io
            buf = io.StringIO()
            df.info(buf=buf)
            f.write(buf.getvalue())
            f.write("\n--- DataFrame Head ---\n")
            f.write(df.head().to_string())
            f.write("\n--- Descriptive Statistics ---\n")
            f.write(df.describe().to_string())
            f.write("\n--- Missing Values ---\n")
            f.write(df.isnull().sum().to_string())
    except Exception as e:
        with open('inspect_out.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_parquet(sys.argv[1])
