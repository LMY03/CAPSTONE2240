import zipfile
import os
from django.http import HttpResponse
from django.conf import settings

def download_files(zip_filename, issue_files):
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'
    
    with zipfile.ZipFile(response, 'w') as zip_file:
        for issue_file in issue_files:
            file_path = os.path.join(settings.MEDIA_ROOT, issue_file.file.name)
            
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))

    return response
