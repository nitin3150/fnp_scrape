import re
import csv

def clean_title(title):
    title = re.sub(r"^(Buy/Send|Buy|Send)\s+", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*FNP.*$", "", title, flags=re.I)
    title = re.sub(r"\s*Online\s*", "", title, flags=re.I)
    return title.strip()

def save_data_to_csv(data, filename="products_partial.csv"):
    if not data:
        print("No data to save.")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"\n✅ Saved {len(data)} records to {filename}")