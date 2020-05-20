from __future__ import print_function
import pickle
import os.path
import sys
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import time

def authorize(scopes):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def iterfiles(service, name=None, is_folder=None, parent=None, order_by='folder,name,createdTime'):
    q = []
    if name is not None:
        q.append("name = '%s'" % name.replace("'", "\\'"))
    if is_folder is not None:
        q.append("mimeType %s '%s'" % ('=' if is_folder else '!=', FOLDER))
    if parent is not None:
        q.append("'%s' in parents" % parent.replace("'", "\\'"))
    params = {'pageToken': None, 'orderBy': order_by}
    if q:
        params['q'] = ' and '.join(q)
    while True:
        response = service.files().list(**params).execute()
        for f in response['files']:
            yield f
        try:
            params['pageToken'] = response['nextPageToken']
        except KeyError:
            return


def iter_directory(dir_id, credentials):
    service = build('drive', 'v3', credentials=credentials)
    root = service.files().get(fileId=dir_id).execute()
    stack = [((root['name'],), root)]
    while stack: 
        path, top = stack.pop()
        dirs, files = is_file = [], []
        for f in iterfiles(service, parent=top['id']):
            is_file[f['mimeType'] != 'application/vnd.google-apps.folder'].append(f)
        yield path, top, dirs, files 
        if dirs:
            stack.extend((path + (d['name'],), d) for d in reversed(dirs))


def extract_cadsr(sheet_id, credentials):
    """
    Traverse all the sheets in a Google sheet and extract all caDSR identifiers
    """
    service = build('sheets', 'v4', credentials=credentials)

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
        print('Usage: cadsr_from_drive.py google_drive_folder_id output_file')
        sys.exit(1)
        
    folder_id = sys.argv[1]
    output = sys.argv[2]

    # If modifying these scopes, delete the file token.pickle.
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
    creds = authorize(scopes)
    ids = set()
    for path, root, dirs, files in iter_directory(folder_id, creds):
        for f in files:
            if f['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                print(f)
                for id in extract_cadsr(f['id'], creds):
                    ids.add(id)
                time.sleep(10)  # sleep such that the script won't exceed quota
        # print('%s\t%d %d' % (path, len(dirs), len(files)))
    with open(output, 'w') as fh:     
        for id in ids:
            fh.write(id + '\n')