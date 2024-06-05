import os
import requests
import json
import msal
from django.db.models import Q
from people.models import Sharepoint

def DownloadFiles(curso, file):
    sharepoint = Sharepoint.objects.get(pk=1)
    authority = sharepoint.authority_url+'{}'.format(sharepoint.tenant_id)
    SCOPES = ['Sites.ReadWrite.All','Files.ReadWrite.All'] 
    cognos_to_onedrive = msal.PublicClientApplication(sharepoint.client_id, authority=authority)
    token = cognos_to_onedrive.acquire_token_by_username_password(sharepoint.username,sharepoint.password,SCOPES)
    folder = '{}_{}'.format(curso.pk, curso.nombre)
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    onedrive_destination = '{}/{}/me/drive/root:/{}'.format(sharepoint.resource_url, sharepoint.api_version, folder)
    response = requests.get(onedrive_destination +':/children', headers=headers)
    content = json.loads(response.content)
    row = next((row for row in content['value'] if row['name'] == file), None)
    print(row)
    return row 


def UploadFile(file, matricula, curso):
    sharepoint = Sharepoint.objects.get(pk=1)
    authority = sharepoint.authority_url+'{}'.format(sharepoint.tenant_id)
    SCOPES = ['Sites.ReadWrite.All','Files.ReadWrite.All'] # Add other scopes/permissions as needed.
    folder = '{}_{}'.format(curso.pk, curso.nombre)
    #https://login.microsoftonline.com/6b874ffe-e856-4262-bc7f-9f7b945ef3b3/oauth2/v2.0/authorize?response_type=token&client_id=de4fad1d-eb00-48ff-aed5-bd79ff1d0878&scope=Sites.ReadWrite.All+Files.ReadWrite.All&state=NVQnGCAchrJIqsAeAxYO0Mc0N8l3Wq

    cognos_to_onedrive = msal.PublicClientApplication(sharepoint.client_id, authority=authority)
    token = cognos_to_onedrive.acquire_token_by_username_password(sharepoint.username,sharepoint.password,SCOPES)
    extension = os.path.splitext(file.name)[1]
    onedrive_destination = '{}/{}/me/drive/root:/{}'.format(sharepoint.resource_url, sharepoint.api_version, folder)
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    if file.size < 4100000: 
        r = requests.put(onedrive_destination+"/"+matricula+extension+":/content", data=file, headers=headers)
    else:
        upload_session = requests.post(onedrive_destination+"/"+matricula+extension+":/createUploadSession", headers=headers).json()
        total_file_size = file.size
        chunk_size = 327680
        chunk_number = total_file_size//chunk_size
        chunk_leftover = total_file_size - chunk_size * chunk_number
        i = 0
        while True:
            chunk_data = file.read(chunk_size)
            start_index = i*chunk_size
            end_index = start_index + chunk_size
            #If end of file, break
            if not chunk_data:
                break
            if i == chunk_number:
                end_index = start_index + chunk_leftover
            headers = {'Content-Length':'{}'.format(chunk_size),'Content-Range':'bytes {}-{}/{}'.format(start_index, end_index-1, total_file_size)}
            chunk_data_upload = requests.put(upload_session['uploadUrl'], data=chunk_data, headers=headers)
            i = i + 1
            
    file.close()
    return matricula+extension