"""
generate_data.py
Generates 520 synthetic orders across 4 vendors with exactly 26 deliberate
operational exceptions for pipeline validation.
"""
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

vendors = ['Armstrong Flooring', 'Mohawk Industries', 'Shaw Floors', 'Daltile']
customers = ['Apex Contractors', 'Cascade Builders', 'Eugene Remodeling', 
             'Willamette Homes', 'Pacific Construction', 'Emerald Valley Co']
statuses = ['Delivered', 'Open', 'In Transit', 'Cancelled', 'Inactive']
zips = ['97401', '97402', '97403', '97405', '97408']

rows = []
base_date = datetime.now() - timedelta(days=25)

# 1. Build 520 baseline records
for i in range(1001, 1521):
    order_date = base_date + timedelta(days=random.randint(0, 10))
    delivery_date = order_date + timedelta(days=random.randint(3, 7))
    
    rows.append({
        'order_id': i,
        'customer_name': random.choice(customers),
        'vendor_name': random.choice(vendors),
        'order_date': order_date.strftime('%Y-%m-%d'),
        'expected_delivery': delivery_date.strftime('%Y-%m-%d'),
        'status': random.choices(statuses, weights=[0.45, 0.38, 0.10, 0.05, 0.02])[0],
        'quantity': random.randint(15, 300),
        'unit_price': round(random.uniform(18.50, 72.00), 2),
        'shipping_zip': random.choice(zips)
    })

df = pd.DataFrame(rows)

# 2. Baseline open orders get future delivery dates (+10 days) to prevent accidental overdue flags
future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
active_mask = df['status'].isin(['Open', 'In Transit'])
df.loc[active_mask, 'expected_delivery'] = future_date

# -------------------------------------------------------------
# 3. Inject Exactly 26 Deliberate Exceptions
# -------------------------------------------------------------

# A. 6 Duplicate Order IDs (3 duplicate pairs) -> CRITICAL
for target_idx, source_idx in [(50, 49), (180, 179), (340, 339)]:
    df.loc[target_idx, 'order_id'] = df.loc[source_idx, 'order_id']

# B. 7 Missing Postal Codes on Active Shipments -> HIGH
for idx in [22, 95, 160, 245, 312, 410, 490]:
    df.loc[idx, 'shipping_zip'] = ''
    df.loc[idx, 'status'] = 'Open'

# C. 5 Non-Positive Quantities on Active Shipments -> MEDIUM
for idx in [35, 140, 275, 385, 460]:
    df.loc[idx, 'quantity'] = random.choice([-15, 0, -50])
    df.loc[idx, 'status'] = 'Open'

# D. 8 Overdue Open Shipments -> CRITICAL
past_due_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
for idx in [65, 115, 205, 290, 335, 415, 475, 510]:
    df.loc[idx, 'expected_delivery'] = past_due_date
    df.loc[idx, 'status'] = 'Open'

# 4. Inactive/Cancelled Control Tests (Must NOT trigger false positives)
df.loc[12, 'status'] = 'Cancelled'
df.loc[12, 'quantity'] = 0
df.loc[88, 'status'] = 'Inactive'
df.loc[88, 'expected_delivery'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# 5. Export clean raw CSV
df.to_csv('orders_raw.csv', index=False)
print(f"[SUCCESS] Generated orders_raw.csv with {len(df)} records.")