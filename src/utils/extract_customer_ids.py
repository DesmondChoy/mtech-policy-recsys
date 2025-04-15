import os
import json

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'results')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ux-webapp', 'public', 'customer_ids.json')

def main():
    customer_ids = [
        name for name in os.listdir(RESULTS_DIR)
        if os.path.isdir(os.path.join(RESULTS_DIR, name))
    ]
    customer_ids.sort()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(customer_ids, f, indent=2)
    print(f"Extracted {len(customer_ids)} customer IDs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
