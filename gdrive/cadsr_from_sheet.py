from googleapiclient.discovery import build
import re
from .authorize import authorize
import sys 

def extract_cadsr(sheet_id):
    """
    Traverse all the sheets in a Google sheet and extract all caDSR identifiers
    """
    service = build('sheets', 'v4', credentials=authorize())

    # List all sheets
    sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    ranges = [sheet['properties']['title'] for sheet in sheets]

    # Call the Sheets API
    result = service.spreadsheets().values().batchGet(spreadsheetId=sheet_id, ranges=ranges).execute()
    valueRanges = result.get('valueRanges', [])

    for values in valueRanges:
        if 'values' not in values:
            continue
        for row in values['values']:
            for cell in row:
                z = re.findall(r'^(\d+)\s+-\s+cadsr$', cell.lower().strip())
                if z:
                    yield z[0]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: cadsr_from_drive.py google_sheet_id output_file')
        sys.exit(1)
        
    sheet_id = sys.argv[1]
    output = sys.argv[2]

    ids = set(id for id in extract_cadsr(sheet_id))
    with open(output, 'w') as fh:     
        for id in ids:
            fh.write(id + '\n')