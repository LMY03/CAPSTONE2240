from django.http import HttpResponse
from django.conf import settings

import csv, os, zipfile

def download_files(zip_filename, file_paths):
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'
    
    with zipfile.ZipFile(response, 'w') as zip_file:
        for file_path in file_paths:
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))

    return response

def download_csv(filename, headers, data):
    response = HttpResponse(
        content_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}.csv"',
        },
    )

    writer = csv.writer(response)
    writer.writerow(headers)

    for row in data : writer.writerow(row)

    return response
