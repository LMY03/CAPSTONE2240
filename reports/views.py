from django.shortcuts import render
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from proxmoxer import ProxmoxAPI
from influxdb_client import InfluxDBClient
import json
import csv
from decouple import config

from proxmox.models import VirtualMachines

INFLUX_ADDRESS = config('INFLUX_ADDRESS')
token = config('INFLUX_TOKEN')
org = config('INFLUXDB_ORG')
bucket = config('INFLUXDB_BUCKET')
proxmox_password = config('PROXMOX_PASSWORD')

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


def get_proxmox_client():
    return ProxmoxAPI('10.1.200.11', user='root@pam', password='cap2240', verify_ssl=False)

# Get influxdb client
def get_influxdb_client():
    return InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)

# Construct Flux Query
def construct_flux_query(measurement, fields, hosts, start_date, end_date):
    host_filter = ' or '.join(f'r.host == "{host}"' for host in hosts)
    field_filter = ' or '.join(f'r._field == "{field}"' for field in fields)

    query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => {host_filter})
            |> filter(fn: (r) => {field_filter})
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> yield(name: "mean")
            '''
    
    return query

# Process Query Result
def process_query_result(result, fields):
    processed_data = []
    for table in result:
        for record in table.records:
            row = {
                'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                'host': record.values.get('host', ''),
                'nodename': record.values.get('nodename', ''),
            }
            field = record.get_field()
            if field in fields:
                row[field] = round(record.get_value(), 2) if record.get_value() is not None else None
            processed_data.append(row)
    
    return processed_data

def write_csv(writer, data, selected_metrics):
    for row in data:
        csv_row = [row['time'], row['host'], row['nodename']]
        for metric in selected_metrics:
            csv_row.append(row.get(metric, ''))
        writer.writerow(csv_row)

# extract data to csv
def index_csv(request):
    try:
        start_time = datetime.now()
        # TODO: logger info - start csv report

        # Get clients
        influxdb_client = get_influxdb_client()
        proxmox_client = get_proxmox_client()

        # Process request data
        start_date = request.POST.get('startdate')
        end_date = request.POST.get('enddate')
        selected_metrics = [key for key in ['cpuUsage', 'memoryUsage', 'netin', 'netout'] if key in request.POST]
        vm_hosts = request.POST.getlist('vmHosts')
        node_hosts = [node['node'] for node in proxmox_client.nodes.get()]

        # Prepare response
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{start_date}_to_{end_date}.csv"'},
        )
        writer = csv.writer(response)

        # Write CSV header
        header = ['time', 'name', 'nodename'] + selected_metrics
        writer.writerow(header)

        # Prepare and execute queries
        query_api = influxdb_client.query_api()

        vm_query = construct_flux_query('system', selected_metrics, vm_hosts, start_date, end_date)
        vm_result = query_api.query(vm_query)
        vm_date = process_query_result(vm_result, selected_metrics)

        node_cpu_query = construct_flux_query('cpustat', ['cpu'], node_hosts, start_date, end_date)
        node_mem_query = construct_flux_query('memory', ['memused', 'memtotal'], node_hosts, start_date, end_date)
        node_net_query = construct_flux_query('system', ['netin', 'netout'], node_hosts, start_date, end_date)

        node_cpu_result = query_api.query(node_cpu_query)
        node_mem_result = query_api.query(node_mem_query)
        node_net_result = query_api.query(node_net_query)

        # Process node data
        node_data = {}
        for result, fields in [(node_cpu_result, ['cpu']), (node_mem_result, ['memused', 'memtotal']), (node_net_result, ['netin', 'netout'])]:
            for row in process_query_result(result, fields):
                key = (row['time'], row['host'])
                if key not in node_data:
                    node_data[key] = row
                else:
                    node_data[key].update(row)

        # Calculate memory percentage for nodes
        for row in node_data.values():
            if 'memused' in row and 'memtotal' in row and row['memtotal'] != 0:
                row['memoryUsage'] = round((row['memused'] / row['memtotal']) * 100, 2)

        # Wrtie data to CSV
        write_csv(writer, node_data.values(), selected_metrics)
        write_csv(writer, vm_date, selected_metrics)

        influxdb_client.close()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        # TODO: logger info - CSV completed in ? seconds

        return response

    except Exception as e:
        # logger error - error generating CSV report.
        return HttpResponse(f"Error generating report: {str(e)}", status=500)



    