from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
import re
from typing import List, Dict, Tuple
import shutil
from datetime import datetime


app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


processed_data = {
    "statement": None,
    "settlement": None,
    "reconciliation": None,
    "timestamp": None
}


def extract_partner_pin(description):
    if pd.isna(description):
        return None
    
    desc_str = str(description).strip()
    match = re.search(r'(\d{9})$', desc_str)

    if match:
        return match.group(1)
    
    return None


def extract_partner_pin_from_statement(col_d_value):
    if pd.isna(col_d_value):
        return None
    col_d_str = str(col_d_value).strip()
    match = re.search(r'XXP(\d{8})', col_d_str)

    if match:
        return '777' + match.group(1)  
    
    return None


def extract_partner_pin_from_settlement(pin_value):
    if pd.isna(pin_value):
        return None
    pin_str = str(pin_value).strip()

    if len(pin_str) >= 8:
        return pin_str
    
    return None


def find_duplicates_by_pin(df, pin_column):
    duplicates = df[df.duplicated(subset=[pin_column], keep=False)]
    return duplicates


def process_statement_file(file_path):
    df = pd.read_excel(file_path, header=None)
    rows_to_drop = list(range(0, 10))
    df = df.drop(rows_to_drop).reset_index(drop=True)

    df.columns = ['Date', 'Type', 'Description', 'Col_D', 'Col_E', 'Col_F', 
                  'Col_G', 'Col_H', 'Col_I', 'Col_J', 'Settle_Amt', 'Balance', 'Col_M']
    
    df['Settle_Amt'] = pd.to_numeric(df['Settle_Amt'], errors='coerce')
    df['PartnerPin'] = df['Col_D'].apply(extract_partner_pin_from_statement)
    df['IsDuplicate'] = df.duplicated(subset=['PartnerPin'], keep=False)
    df['Classification'] = None
    df.loc[(df['IsDuplicate']) & (df['Type'] == 'Cancel'), 'Classification'] = 'Should Reconcile'
    df.loc[df['Type'] == 'Dollar Received', 'Classification'] = 'Should Not Reconcile'
    df.loc[~df['IsDuplicate'] & df['Classification'].isna(), 'Classification'] = 'Should Reconcile'
    df['Classification'].fillna('Should Reconcile', inplace=True)

    return df


def process_settlement_file(file_path):
    df = pd.read_excel(file_path, header=None)
    df = df.drop([0, 1, 2]).reset_index(drop=True)

    df.columns = ['tranno', 'Pin_Number', 'Partner_Tran_Id', 'PartnerPin', 'Col_E', 'Type', 'Col_G', 
                  'Col_H', 'Col_I', 'Col_J', 'PayoutRoundAmt', 'Col_L', 'APIRate', 'Col_N', 
                  'CostRate', 'Commission', 'CommissionCCy', 'FxGain', 'Col_R']
    
    df['PayoutRoundAmt'] = pd.to_numeric(df['PayoutRoundAmt'].astype(str).str.replace(',', ''), errors='coerce')
    df['APIRate'] = pd.to_numeric(df['APIRate'], errors='coerce')
    df['EstimatedAmountUSD'] = df['PayoutRoundAmt'] / df['APIRate']
    df['IsDuplicate'] = df.duplicated(subset=['PartnerPin'], keep=False)
    df['Classification'] = None
    df.loc[(df['IsDuplicate']) & (df['Type'] == 'Cancel'), 'Classification'] = 'Should Reconcile'
    df.loc[~df['IsDuplicate'] & df['Classification'].isna(), 'Classification'] = 'Should Reconcile'
    df['Classification'].fillna('Should Reconcile', inplace=True)

    return df

    
def match_and_reconcile(statement_df, settlement_df):
    stmt_reconcile = statement_df[statement_df['Classification'] == 'Should Reconcile'].copy()
    settle_reconcile = settlement_df[settlement_df['Classification'] == 'Should Reconcile'].copy()
    reconciliation_records = []
    stmt_pins = set(stmt_reconcile['PartnerPin'].dropna())
    settle_pins = set(settle_reconcile['PartnerPin'].dropna())
    all_pins = stmt_pins | settle_pins

    for pin in all_pins:
        stmt_rows = stmt_reconcile[stmt_reconcile['PartnerPin'] == pin]
        settle_rows = settle_reconcile[settle_reconcile['PartnerPin'] == pin]
        is_in_statement = len(stmt_rows) > 0
        is_in_settlement = len(settle_rows) > 0

        if is_in_statement and is_in_settlement:
            status = "Present in Both"
            stmt_amount = stmt_rows['Settle_Amt'].values[0] if len(stmt_rows) > 0 else 0
            settle_amount = settle_rows['EstimatedAmountUSD'].values[0] if len(settle_rows) > 0 else 0
            variance = settle_amount - stmt_amount  

        elif is_in_settlement and not is_in_statement:
            status = "Present in the Settlement File but not in the Partner Statement File"
            variance = None

        else:
            status = "Not Present in the Settlement File but Present in the Partner Statement File"
            variance = None

        record = {
            'PartnerPin': pin,
            'Status': status,
            'InStatement': is_in_statement,
            'InSettlement': is_in_settlement,
            'Variance': variance,
            'StatementAmount': stmt_rows['Settle_Amt'].values[0] if len(stmt_rows) > 0 else None,
            'SettlementAmount': settle_rows['EstimatedAmountUSD'].values[0] if len(settle_rows) > 0 else None
        }
        reconciliation_records.append(record)
    return pd.DataFrame(reconciliation_records)


@app.get("/")
async def root():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())
    

@app.post("/upload")
async def upload_files(statement: UploadFile = File(...), settlement: UploadFile = File(...)):
    try:
        stmt_path = os.path.join(UPLOAD_DIR, f"statement_{datetime.now().timestamp()}.xlsx")
        settle_path = os.path.join(UPLOAD_DIR, f"settlement_{datetime.now().timestamp()}.xlsx")

        with open(stmt_path, "wb") as buffer:
            shutil.copyfileobj(statement.file, buffer)

        with open(settle_path, "wb") as buffer:
            shutil.copyfileobj(settlement.file, buffer)

        statement_df = process_statement_file(stmt_path)
        settlement_df = process_settlement_file(settle_path)
        reconciliation_df = match_and_reconcile(statement_df, settlement_df)
        processed_data["statement"] = statement_df
        processed_data["settlement"] = settlement_df
        processed_data["reconciliation"] = reconciliation_df
        processed_data["timestamp"] = datetime.now().isoformat()
        os.remove(stmt_path)
        os.remove(settle_path)

        return JSONResponse({
            "status": "success",
            "message": "Files processed successfully",
            "summary": {
                "statement_rows": len(statement_df),
                "settlement_rows": len(settlement_df),
                "reconciliation_records": len(reconciliation_df)
            }
        })
    
    except Exception as e:
        print("error in upload file: ", e)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)
    

@app.get("/api/transactions")
async def get_transactions(classification: str = None):

    if processed_data["reconciliation"] is None:
        return JSONResponse({
            "status": "error",
            "message": "No data processed yet"
        }, status_code=400)
    
    df = processed_data["reconciliation"]

    if classification:
        df = df[df['Status'] == classification]
    records = []

    for _, row in df.iterrows():
        records.append({
            'PartnerPin': str(row['PartnerPin']) if row['PartnerPin'] else 'N/A',
            'Status': row['Status'],
            'StatementAmount': float(row['StatementAmount']) if pd.notna(row['StatementAmount']) else None,
            'SettlementAmount': float(row['SettlementAmount']) if pd.notna(row['SettlementAmount']) else None,
            'Variance': float(row['Variance']) if pd.notna(row['Variance']) else None
        })

    return JSONResponse({
        "status": "success",
        "data": records
    })


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
