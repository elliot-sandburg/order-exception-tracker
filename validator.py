"""
validator.py
Automated order validation and fulfillment exception pipeline.
Ingests multi-vendor order data, audits operational parameters against business rules,
and exports an itemized exception log and vendor scorecard to Excel.
"""
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def run_pipeline(input_csv="orders_raw.csv", output_xlsx="order_exceptions_report.xlsx"):
    print(f"[1/4] Ingesting multi-vendor order feed: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Normalize column headers and parse dates
    df.columns = df.columns.str.strip().str.lower()
    df['expected_delivery'] = pd.to_datetime(df['expected_delivery'], errors='coerce')
    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    today = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
    
    print(f"[2/4] Auditing {len(df)} records across operational business rules...")
    exceptions = []
    
    # -------------------------------------------------------------
    # RULE 1: Duplicate Order IDs (Severity: CRITICAL)
    # -------------------------------------------------------------
    duplicate_mask = df.duplicated(subset=['order_id'], keep=False)
    for _, row in df[duplicate_mask].iterrows():
        exceptions.append({
            'order_id': row['order_id'],
            'customer_name': row['customer_name'],
            'vendor_name': row['vendor_name'],
            'status': row['status'],
            'exception_type': 'DUPLICATE_ORDER_ID',
            'severity': 'CRITICAL',
            'action_required': 'Cancel duplicate PO in POS/ERP; verify billing ledger.',
            'details': f"Order ID {row['order_id']} appears multiple times."
        })
        
    # Filter active orders (Excludes Cancelled & Inactive records)
    normalized_status = df['status'].astype(str).str.strip().str.casefold()
    active_df = df[~normalized_status.isin(['cancelled', 'inactive'])].copy()
    
    # -------------------------------------------------------------
    # RULE 2: Missing Shipping Zip Code (Severity: HIGH)
    # -------------------------------------------------------------
    missing_zip_mask = active_df['shipping_zip'].isna() | (active_df['shipping_zip'].astype(str).str.strip() == '')
    for _, row in active_df[missing_zip_mask].iterrows():
        exceptions.append({
            'order_id': row['order_id'],
            'customer_name': row['customer_name'],
            'vendor_name': row['vendor_name'],
            'status': row['status'],
            'exception_type': 'MISSING_SHIPPING_ZIP',
            'severity': 'HIGH',
            'action_required': 'Contact customer to confirm jobsite zip code.',
            'details': 'Fulfillment address missing required postal code.'
        })
        
    # -------------------------------------------------------------
    # RULE 3: Non-Positive Line Quantities (Severity: MEDIUM)
    # -------------------------------------------------------------
    invalid_qty_mask = active_df['quantity'] <= 0
    for _, row in active_df[invalid_qty_mask].iterrows():
        exceptions.append({
            'order_id': row['order_id'],
            'customer_name': row['customer_name'],
            'vendor_name': row['vendor_name'],
            'status': row['status'],
            'exception_type': 'INVALID_QUANTITY',
            'severity': 'MEDIUM',
            'action_required': 'Review order line items; re-enter valid unit count.',
            'details': f"Quantity is {row['quantity']}. Active items must be > 0."
        })
        
    # -------------------------------------------------------------
    # RULE 4: Overdue Open Fulfillment (Severity: CRITICAL)
    # -------------------------------------------------------------
    overdue_mask = (active_df['expected_delivery'] < today) & (active_df['status'] == 'Open')
    for _, row in active_df[overdue_mask].iterrows():
        days_late = (today - row['expected_delivery']).days
        exceptions.append({
            'order_id': row['order_id'],
            'customer_name': row['customer_name'],
            'vendor_name': row['vendor_name'],
            'status': row['status'],
            'exception_type': 'OVERDUE_FULFILLMENT',
            'severity': 'CRITICAL',
            'action_required': 'Escalate to vendor dispatch for revised tracking ETA.',
            'details': f"Shipment is {days_late} days past promised delivery date."
        })
        
    exceptions_df = pd.DataFrame(exceptions)
    print(f"[3/4] Isolated {len(exceptions_df)} exception events.")
    
    # Build Vendor Performance Scorecard
    if not exceptions_df.empty:
        scorecard = exceptions_df.groupby(['vendor_name', 'severity']).size().unstack(fill_value=0)
        for col in ['CRITICAL', 'HIGH', 'MEDIUM']:
            if col not in scorecard.columns:
                scorecard[col] = 0
        scorecard = scorecard[['CRITICAL', 'HIGH', 'MEDIUM']]
        scorecard['TOTAL_EXCEPTIONS'] = scorecard.sum(axis=1)
        scorecard = scorecard.sort_values(by='TOTAL_EXCEPTIONS', ascending=False)
        scorecard_df = scorecard.reset_index()
    else:
        scorecard_df = pd.DataFrame()
        
    # Write formatted multi-tab Excel output
    print(f"[4/4] Writing formatted report to: {output_xlsx}")
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        exceptions_df.to_excel(writer, sheet_name='Itemized Exceptions', index=False)
        scorecard_df.to_excel(writer, sheet_name='Vendor Scorecard', index=False)
        
        wb = writer.book
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
        
        for sheet_name in ['Itemized Exceptions', 'Vendor Scorecard']:
            ws = wb[sheet_name]
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)
                
    print(f"[COMPLETE] Success! Generated: {output_xlsx}")

if __name__ == "__main__":
    run_pipeline()