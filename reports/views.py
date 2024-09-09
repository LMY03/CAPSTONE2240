from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
import json

from proxmox.models import VirtualMachines


# Get Report Page
def index(request):
    return render(request, 'reports/reports.html')

# Get VM Info
def getVmList(request):
    
    # Get All VMs
    try:
        vminfos = VirtualMachines.objects.all()
        serialized_data = serializers.serialize('json', vminfos)
        data = json.loads(serialized_data)
        return JsonResponse({'vmList' : data}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)