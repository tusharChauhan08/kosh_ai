# Transaction Reconciliation System

A clean, efficient web application for reconciling bank/payment transactions between Statement and Settlement files. Built with FastAPI and modern web technologies.

## Features

- **File Upload**: Simple interface to upload Statement and Settlement Excel files
- **Automatic Processing**: Smart transaction classification and reconciliation logic
- **Real-time Results**: Instant processing with live status updates
- **Transaction Categories**:
  - **5**: Present in Both files (matched transactions)
  - **6**: Settlement Only (missing in Statement)
  - **7**: Statement Only (missing in Settlement)
- **Variance Calculation**: Automatic calculation of amount differences
- **Clean UI**: Minimal, responsive web interface
- **Export Ready**: CSV export functionality for processed data

## Quick Start

### 1. Setup Environment
```bash
cd /home/ritik/Downloads/kosh_ai
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Application
```bash
python main.py
```

Open your browser to `http://localhost:8000`

### 3. Alternative Startup
```bash
chmod +x start.sh
./start.sh
```

## How It Works

### File Processing Logic

**Statement File:**
- Removes header rows (1-9, 11)
- Extracts partner PINs from description column
- Identifies duplicate transactions
- Classifies transactions for reconciliation

**Settlement File:**
- Removes header rows (1-2)
- Calculates USD amounts (PayoutRoundAmt ÷ APIRate)
- Processes partner PINs and duplicates
- Prepares for matching

**Reconciliation:**
- Matches transactions by partner PIN
- Calculates variances for matched transactions
- Categorizes into 3 groups with status codes 5/6/7

### Data Flow
1. Upload both Excel files
2. Automatic processing and validation
3. Transaction matching and classification
4. Results display with filtering
5. Optional CSV export

## File Format Requirements

### Statement File
- Excel format (.xlsx/.xls)
- Required columns: Type, Description (with PIN), Settle Amount
- Partner PINs extracted from description field

### Settlement File
- Excel format (.xlsx/.xls)
- Required columns: Partner PIN, Type, PayoutRoundAmt, APIRate
- Direct partner PIN column

## API Reference

### Upload Files
```http
POST /upload
Content-Type: multipart/form-data

statement: [Excel File]
settlement: [Excel File]
```

**Response:**
```json
{
  "status": "success",
  "message": "Files processed successfully",
  "summary": {
    "statement_rows": 81,
    "settlement_rows": 67,
    "reconciliation_records": 68
  }
}
```

### Get Transactions
```http
GET /api/transactions
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "PartnerPin": "777123456789",
      "Status": "Present in Both",
      "StatementAmount": 0.0,
      "SettlementAmount": 150.75,
      "Variance": 150.75
    }
  ]
}
```

### Get Summary
```http
GET /api/summary
```

**Response:**
```json
{
  "status": "success",
  "summary": {
    "Present in Both": 65,
    "Present in Settlement File but not in the Partner Statement File": 1,
    "Present in Statement File but not in the Settlement File": 2
  }
}
```

## Project Structure

```
kosh_ai/
├── main.py              # FastAPI application & processing logic
├── static/index.html    # Web interface
├── requirements.txt     # Python dependencies
├── start.sh            # Startup script
└── README.md           # This file
```

## Technical Details

- **Backend**: FastAPI with automatic API documentation
- **Data Processing**: Pandas for Excel handling and calculations
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Server**: Uvicorn ASGI server
- **File Handling**: Secure temporary file processing

## Troubleshooting

**Port already in use:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
# Or change port in main.py
```

**Import errors:**
```bash
pip install --upgrade pandas openpyxl fastapi uvicorn
```

**File processing issues:**
- Ensure Excel files have correct column structure
- Check that partner PINs are in expected format
- Verify amounts are numeric (not text)

## Development

The application is designed to be lightweight and maintainable. Key principles:

- Clean separation of concerns
- Minimal dependencies
- Error handling with user-friendly messages
- Responsive design for all devices
- RESTful API design

## License

This project is built for transaction reconciliation workflows. Feel free to adapt and extend for your specific needs.
