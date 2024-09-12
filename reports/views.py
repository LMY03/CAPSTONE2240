from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from proxmoxer import ProxmoxAPI
from influxdb_client import InfluxDBClient
import json

from proxmox.models import VirtualMachines

# INFLUX_ADDRESS = config('INFLUX_ADDRESS')
# token = config('INFLUX_TOKEN')
# org = config('INFLUXDB_ORG')
# bucket = config('INFLUXDB_BUCKET')
# proxmox_password = config('PROXMOX_PASSWORD')

# Get Report Page
def index(request):
    return render(request, 'reports/reports.html')

# Get VM Info
def getVmList(request):
    #Connection between Proxmox API and application
    proxmox = ProxmoxAPI('10.1.200.11', user='root@pam', password='cap2240', verify_ssl=False)
    client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    
    #Get VM Info from Proxmox API
    vmids = proxmox.cluster.resources.get(type='vm')    
    VMList= []
    query_api = client.query_api()
    #Query to get all nodes being used
    
    flux_query = f'''
                    from(bucket:"{bucket}")
                    |> range(start: -5m)
                    |> filter(fn: (r) => r._measurement == "system")
                    |> filter(fn: (r) => r.object == "nodes")
                    |> group(columns: ["host"])
                    |> distinct(column: "host")
                    '''
    
    result = query_api.query(query=flux_query)
    nodes = []
    for table in result:
        for record in table.records:
            nodes.append(record.values.get("host", ""))

    #Loop through each VM to get info
    for vmid in vmids:
        VMDict = {}
        VMDict["id"] = vmid['vmid']
        VMDict["type"] = vmid['type']        
        VMDict["cpu"] = vmid['cpu']
        VMDict["disk"] = vmid['disk']
        VMDict["maxcpu"] = vmid['maxcpu']
        VMDict["maxdisk"] = vmid['maxdisk']        
        VMDict["maxmem"] = vmid['maxmem']
        VMDict["mem"] = vmid['mem']
        VMDict["name"] = vmid['name']
        VMDict["node"] = vmid['node']
        VMDict["status"] = vmid['status']
        VMDict["uptime"] = vmid['uptime']
        VMDict['network_in'] = vmid['netin']
        VMDict['network_out'] = vmid['netout']
        VMList.append(VMDict)

    return JsonResponse({
        'vmList': VMList,
        'vmids': vmids,
    })
    # # Get All VMs - not able to get it
    # try:
    #     vminfos = VirtualMachines.objects.all()
    #     serialized_data = serializers.serialize('json', vminfos)
    #     data = json.loads(serialized_data)
    #     return JsonResponse({'vmList' : data}, safe=False)
    # except Exception as e:
    #     return JsonResponse({'error': str(e)}, status=500)