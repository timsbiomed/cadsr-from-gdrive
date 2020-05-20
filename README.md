# CADSR Extractor for CCDH

This script traverse the CCDH google directory and parses each google sheet. It extracts any caDSR identifiers if a cell contains
the identifier as

    3587247 - caDSR

### Set up

First generate a Google devloper API credentials.json file and put it in this directory. 
Then run the following to install python libraries. 

```
pipenv install
```

### Run 

To run the script, simply do the following to traverse a directory and process all the Google sheets in the directory and subdirectories. 

```
pipenv run python gdrive/cadsr_from_dir.py <google_drive_folder_id> <output_file>
``` 

Or run the following to extract caDSR identifers from a Google sheet. 

```
pipenv run python gdrive/cadsr_from_sheet.py <google_sheet_id> <output_file>
```

caDSR identifers will be stored in `output_file`. 