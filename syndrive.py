from __future__ import print_function

import os

from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer


class MyGoogleDrive:
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        self.service = build('drive', 'v3', credentials=creds)

    def list_files(self, files_no=10):
        results = self.service.files().list(
            pageSize=files_no, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return

        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

    def upload_file(self, path, filename):
        FOLDER_ID = "1PyIBynk6dk5200DnWXV3C_t9xjVciTkD"
        media = MediaFileUpload(path)

        response = self.service.files().list(
            q=f"name='{filename}' and parents='{FOLDER_ID}'",
            spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageToken=None).execute()

        if len(response["files"]) == 0:
            file_metadata = {'name': filename, 'parents': [FOLDER_ID]}

            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id').execute()
            print(f"File Uploaded: {file.get('id')}")
        else:
            for file in response.get('files', []):
                file = self.service.files().update(
                    fileId=file.get('id'), media_body=media).execute()
                print(f"File Updated: {file.get('name')}")


class EventHandler(LoggingEventHandler):
    def on_modified(self, event):
        print("Watchdog received modified event - % s." % event.src_path)

        filename = event.src_path.split('/')[-1]
        if event.src_path != "SRC_LOC":
            my_drive.upload_file(event.src_path, filename)

    def on_created(self, event):
        print("Watchdog received modified event - % s." % event.src_path)

        filename = event.src_path.split('/')[-1]
        if event.src_path != "SRC_LOC":
            my_drive.upload_file(event.src_path, filename)


if __name__ == '__main__':
    src_path = "SRC_LOC/"
    my_drive = MyGoogleDrive()
    handler = EventHandler()
    observer = Observer()
    observer.schedule(handler, path=src_path, recursive=True)
    observer.start()

    try:
        while observer.is_alive():
            observer.join()
    except KeyboardInterrupt:
        print("\nProcess Terminated\n")
    except Exception as e:
        print(e)
    finally:
        observer.stop()
        observer.join()
