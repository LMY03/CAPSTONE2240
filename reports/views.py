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

# Parse date to InfluxDB compatible
def parse_form_date(date_string):
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT00:00:00Z")
    except ValueError:
        raise ValueError(f"Invalid date format: {data_string}. Expected YYYY-MM-DD")
        

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

    client.close()

    return JsonResponse({
        'vmList': VMList,
        'vmids': vmids,
    })


def get_proxmox_client():
    return ProxmoxAPI('10.1.200.11', user='root@pam', password='cap2240', verify_ssl=False)

# Get influxdb client
def get_influxdb_client():
    return InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)

def construct_vm_flux_query(hosts, metrics, start_date, end_date, window):

    host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
    field_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in metrics) if metrics else 'true'

    query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => {host_filter})
            |> filter(fn: (r) => {field_filter})
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> yield(name: "mean")
            '''
    return query

# Construct Flux Query
def construct_flux_query(measurement, fields, hosts, start_date, end_date, window):
    host_filter = ' or '.join(f'r.host == "{host}"' for host in hosts) if hosts else 'true'
    field_filter = ' or '.join(f'r._field == "{field}"' for field in fields) if fields else 'true'

    query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => {host_filter})
            |> filter(fn: (r) => {field_filter})
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> yield(name: "mean")
            '''
    # TODO: REMOVE!
    print(f"query statement: {query}")
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
        # Prepare and execute queries
        query_api = influxdb_client.query_api()

        # Process request data
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')

        if not start_date_str or not end_date_str:
            return HttpResponse("Start date and end date are required", status=400)

        start_date = parse_form_date(start_date_str)
        end_date = parse_form_date(end_date_str)

        # # TODO: REMOVE!
        # print(f"Parsed start date: {start_date}")
        # print(f"Parsed end date: {end_date}")

        metrics = [key for key in ['cpuUsage', 'memoryUsage', 'netin', 'netout'] if key in request.POST]
        selected_metrics = []
        for metric in metrics:
            if metric == 'cpuUsage':
                selected_metrics.append('cpu')
            elif metric == 'memoryUsage':
                selected_metrics.append('maxmem')
                selected_metrics.append('mem')
            elif metric == 'netin':
                selected_metrics.append('netin')
            elif metric == 'netout':
                selected_metrics.append('netout')

        selected_vms = request.POST.getlist('selectedVMs')
        node_hosts = [node['node'] for node in proxmox_client.nodes.get()]
        
        # # TODO: REMOVE!
        # print("Selected metrics:", selected_metrics)
        # print("Selected VMs:", selected_vms)
        # print(f"all hosts: {node_hosts}")

        # Prepare csv response
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{start_date_str}_to_{end_date_str}.csv"'},
        )
        writer = csv.writer(response)

        # TODO: add window in response
        vm_query = construct_vm_flux_query(selected_vms, selected_metrics, start_date, end_date, '1h')
        # TODO: REMOVE!
        print(f"vm_query: {vm_query}")
        vm_result = query_api.query(vm_query)
        # TODO: REMOVE!
        print(f"vm_result: {vm_result}")


        # Write the grouped data to CSV - header
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['time', 'host', 'nodename'] + selected_metrics)

        # Dictionary to store grouped data
        grouped_data = {}

        for table in vm_result:
            for record in table.records:
                timestamp = record.get_time().strftime('%Y-%m-%d %H:%M:%S')
                host = record.values.get('host', '')
                nodename = record.values.get('nodename', '')
                field = record.values.get('_field', '')
                value = record.values.get('_value', '')

                # Unique key for each timestamp-host combination
                key = (timestamp, host, nodename)

                if key not in grouped_data:
                    grouped_data[key] = {metric: '' for metric in selected_metrics}

                # Add value to the corresponding metric
                if field in selected_metrics:
                    if field == 'cpu':
                        value = str(round(value * 100, 2)) + "%"
                    elif field == 'mem' or field == 'maxmem':
                        value = str(round(value / (1024*1024*1024), 2)) + "GiB"
                    grouped_data[key][field] = str(value).strip().replace('\n', '').replace('\r', '')


        # Write the grouped data to CSV - data
        for (timestamp, host, nodename), metrics in grouped_data.items():
            row = [timestamp, host, nodename]
            row.extend([metrics.get(metric, '') for metric in selected_metrics])
            writer.writerow(row)

        influxdb_client.close()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        # TODO: logger info - CSV completed in ? seconds

        return response

    except Exception as e:
        # logger error - error generating CSV report.
        return HttpResponse(f"Error generating report: {str(e)}", status=500)


def open_report_page(request):
    # Get clients
    influxdb_client = get_influxdb_client()
    proxmox_client = get_proxmox_client()
    # Prepare and execute queries
    query_api = influxdb_client.query_api()
    vm_infos = proxmox_client.cluster.resources.get(type='vm')

    node_names = [node['node'] for node in proxmox_client.nodes.get()]

    # Metrics
    cpuUsageList = []
    memUsageList = []
    netInUsageList = []
    netOutUsageList = []
    vmNameList = []
    vmIdList = []
    neededStatList = []
    selectedNodeNameList = []

    formData = {}

    data = request.POST
    # TODO: REMOVE!
    print(f"data: {data}")

    for name in data.keys():
        if str(name) not in ['categoryFilter', 'select_all', 'csrfmiddlewaretoken', 'vmInfoTable_length',
            'cpuUsage', 'memoryUsage', 'netin', 'netout',
            'enddate', 'startdate']:
            vmNameList.append(data.get(str(name)))
            vmIdList.append(str(name))
        elif str(name) == 'startdate':
            startdate = data.get(str(name))
        elif str(name) == 'enddate':
            enddate = data.get(str(name))
        elif str(name) in ['cpuUsage', 'memoryUsage', 'netin', 'netout']:
            neededStatList.append(data.get(str(name)))

    # insert data into formData
    formData['vmNameList'] = vmNameList
    formData['nodeNameList'] = selectedNodeNameList
    formData['vmIdList'] = vmIdList
    formData['startdate'] = startdate
    formData['enddate'] = enddate
    formData['statList'] = neededStatList

    request.session['formData'] = formData

    # TODO: REMOVE!
    print(f"vmNameList: {formData['vmNameList']}")
    print(f"nodeNameList: {formData['nodeNameList']}")
    print(f"vmIdList: {formData['vmIdList']}")
    print(f"startdate: {formData['startdate']}")
    print(f"enddate: {formData['enddate']}")
    print(f"statList: {formData['statList']}")

    influxdb_client.close()

    return render(request, 'reports/gen-reports.html')


def report_gen(request):
    try:
        # Get clients
        influxdb_client = get_influxdb_client()
        proxmox_client = get_proxmox_client()
        # Prepare and execute queries
        query_api = influxdb_client.query_api()

        # form_data = request.session.get('formData', {})
        # start_date = form_data.get('startdate')
        # end_date = form_data.get('enddate')

        # sd = datetime.strptime(start_date, "%Y-%m-%d")
        # ed = datetime.strptime(end_date, "%Y-%m-%d")
        # date_diff = (ed - sd).days

        # window = "1d" if date_diff >= 30 else "1h"

        # node_metrics = ['cpu', 'memused', 'netin', 'netout', 'memtotal', 'swaptotal']
        # vm_metrics = ['cpu', 'mem', 'netin', 'netout']

        node_data = {}
        # for node in form_data.get('nodeNameList', []):
        #     node_query = construct_flux_query('system', node_metrics, [node], start_date, end_date, window)
        #     node_result = query_api.query(node_query)
        #     node_data[node] = process_query_result(node_result, node_metrics)

        vm_data = {}
        # for vm in form_data.get('vmNameList', []):
        #     vm_query = construct_flux_query('system', vm_metrics, [vm], start_date, end_date, window)
        #     vm_result = query_api.query(vm_query)
        #     vm_data[vm] = process_query_result(vm_result, vm_metrics)

        influxdb_client.close()

        return JsonResponse({
            'nodeData': node_data,
            'vmData': vm_data,
            # 'dateDiff': date_diff,
            # 'formData': form_data
        })

    except Exception as e:
        # TODO: logger error - error generating report page
        return JsonResponse({'error': 'An error occurred while preparing the report generation page.'}, status=500)