import sys
from googleapiclient.discovery import build
import time
from cadsr_from_sheet import extract_cadsr
from authorize import authorize

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


def iter_directory(dir_id):
    service = build('drive', 'v3', credentials=authorize())
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


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: cadsr_from_drive.py google_drive_folder_id output_file')
        sys.exit(1)
        
    folder_id = sys.argv[1]
    output = sys.argv[2]

    # If modifying these scopes, delete the file token.pickle.
    ids = set()
    for path, root, dirs, files in iter_directory(folder_id):
        for f in files:
            if f['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                print(f)
                for id in extract_cadsr(f['id']):
                    ids.add(id)
                time.sleep(10)  # sleep such that the script won't exceed quota
        # print('%s\t%d %d' % (path, len(dirs), len(files)))
    with open(output, 'w') as fh:     
        for id in ids:
            fh.write(id + '\n')