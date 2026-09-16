import sqlite3
import csv
import os

DB_PATH = "opsintel.db"
OUTPUT_DIR = "demo_dataset"

def export_table_to_csv(table_name, output_filename, limit=None):
    print(f"Exporting {table_name}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write headers
        headers = [description[0] for description in cursor.description]
        writer.writerow(headers)
        # Write rows
        rows = cursor.fetchall()
        writer.writerows(rows)
        
    print(f"Exported {len(rows)} rows to {output_path}")
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database opsintel.db not found!")
        exit(1)
        
    export_table_to_csv("services", "services_demo.csv")
    
    # We will export a subset (e.g., 2000 rows) so the files aren't overwhelmingly massive for a demo,
    # but still a "good amount of data" as requested.
    export_table_to_csv("incidents", "incidents_demo.csv", limit=5000)
    export_table_to_csv("problems", "problems_demo.csv", limit=1500)
    export_table_to_csv("changes", "changes_demo.csv", limit=2000)
    export_table_to_csv("sla_records", "slas_demo.csv", limit=3000)
    
    print("Demo dataset generated successfully!")
