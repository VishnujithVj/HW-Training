from items import ProductData
from settings import PROJECT_NAME
from datetime import datetime
import csv
import json

def export_data():
    """ Generate filenames with current date"""
    date_str = datetime.now().strftime('%Y%m%d')
    csv_file = f"{PROJECT_NAME}_product_data_{date_str}.csv"
    json_file = f"{PROJECT_NAME}_product_data_{date_str}.json"
    
    """ Get all fields except 'id' """
    fields = [f for f in ProductData._fields if f != "id"]
    products = ProductData.objects()
    
    csv_count = 0
    json_data = []

    """Export to Pipe-delimited CSV"""
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(fields)
        
        for product in products:
            row = [str(getattr(product, f, "") or "") for f in fields]
            writer.writerow(row)
            csv_count += 1
            
            """prepare data for JSON"""
            product_dict = {}
            for field in fields:
                value = getattr(product, field, "")

                """Convert datetime to string for JSON"""
                if isinstance(value, datetime):
                    value = value.isoformat()
                product_dict[field] = str(value) if value is not None else ""
            json_data.append(product_dict)

    """Export to JSON Array"""
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"Exported {csv_count} products to:")
    print(f"CSV: {csv_file}")
    print(f"JSON: {json_file}")

if __name__ == "__main__":
    export_data()