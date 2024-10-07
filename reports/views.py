from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from proxmoxer import ProxmoxAPI
from influxdb_client import InfluxDBClient
from io import StringIO
import json
import csv
from decouple import config
from ticketing.models import RequestUseCase

from proxmox.models import VirtualMachines

INFLUX_ADDRESS = config('INFLUX_ADDRESS')
token = config('INFLUX_TOKEN')
org = config('INFLUXDB_ORG')
bucket = config('INFLUXDB_BUCKET')
proxmox_password = config('PROXMOX_PASSWORD')

# Parse date to InfluxDB compatible
def parse_form_date(date_string, is_start):
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%d")
        if is_start:
            return dt.strftime("%Y-%m-%dT00:00:00Z")
        else:
            next_day = dt + timedelta(days=1)
            return next_day.strftime("%Y-%m-%dT00:00:00Z")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")
        

# Get Report Page
def index(request):
    return render(request, 'reports/reports.html')

# Get VM Info
def getVmList(request):
    #Connection between Proxmox API and application
    proxmox = ProxmoxAPI('10.1.200.11', user='root@pam', password='cap2240', verify_ssl=False)
    client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = client.query_api()
    
    #Get VM Info from Proxmox API
    vmids = proxmox.cluster.resources.get(type='vm')    
    VMList= []
    
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

# def construct_vm_details_flux_query(hosts, metrics, start_date, end_date, window):

#     host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
#     field_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in metrics) if metrics else 'true'

#     query = f'''
#             from(bucket:"{bucket}")
#             |> range(start: {start_date}, stop: {end_date})
#             |> filter(fn: (r) => r["_measurement"] == "system")
#             |> filter(fn: (r) => {host_filter})
#             |> filter(fn: (r) => {field_filter})
#             |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
#             |> yield(name: "mean")
#             '''
#     return query

# def construct_vm_details_flux_query(hosts, metrics, start_date, end_date, window):

#     host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
    
#     # field_filter includes [network_metrics] and [other metrics]
#     network_metrics = [m for m in metrics if m in ['netin', 'netout']]
#     other_metrics = [m for m in metrics if m not in ['netin', 'netout']]
    
#     query_parts = []
    
#     if network_metrics:
#         network_metrics_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in network_metrics) if network_metrics else 'true'
#         network_query = f'''
#                 from(bucket:"{bucket}")
#                 |> range(start: {start_date}, stop: {end_date})
#                 |> filter(fn: (r) => r["_measurement"] == "system")
#                 |> filter(fn: (r) => {host_filter})
#                 |> filter(fn: (r) => {network_metrics_filter})
#                 |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
#                 |> derivative(unit: 10s, nonNegative: true, columns: ["_value"], timeColumn: "_time")
#                 |> yield(name: "mean")
#                 '''
#         query_parts.append(network_query)

#     if other_metrics:
#         other_metrics_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in other_metrics) if other_metrics else 'true'
#         other_query = f'''
#                 from(bucket:"{bucket}")
#                 |> range(start: {start_date}, stop: {end_date})
#                 |> filter(fn: (r) => r["_measurement"] == "system")
#                 |> filter(fn: (r) => {host_filter})
#                 |> filter(fn: (r) => {other_metrics_filter})
#                 |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
#                 '''
#         query_parts.append(other_query)

#     if len(query_parts) > 1:
#         combined_query = f'''
#                 networkData = {query_parts[0]}

#                 otherData = {query_parts[1]}

#                 union(tables: [networkData, otherData])
#                 |> yield(name: "combined")
#                 '''
#     elif len(query_parts) == 1:
#         combined_query = f'''
#                 {query_parts[0]}
#                 |> yield(name: "combined")
#                 '''
#     else:
#         combined_query = "// No metrics specified"

#     return combined_query


# # Fix this
# def construct_vm_summary_flux_query(hosts, metric, start_date, end_date):
#     host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
    
#     is_network_metric = metric in ['netin', 'netout']

#     base_query = f'''
#                 from(bucket:"{bucket}")
#                 |> range(start: {start_date}, stop: {end_date})
#                 |> filter(fn: (r) => r["_measurement"] == "system")
#                 |> filter(fn: (r) => {host_filter})
#                 |> filter(fn: (r) => r["_field"] == "{metric}")
#                 '''
    
#     if is_network_metric:
#         query = f'''
#                 data = {base_query}
#                 |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
#                 |> derivative(unit: 1h, nonNegative: true, columns: ["_value"], timeColumn: "_time")
#                 |> filter(fn: (r) => r._value != 0)
#                 |> group(columns: ["host"])

#                 mean = data
#                 |> mean()
#                 |> map(fn: (r) => ({ r with _value: r._value, _field: "mean_{metric}" }))

#                 max = data
#                 |> max()
#                 |> map(fn: (r) => ({ r with _value: r._value, _field: "max_{metric}" }))

#                 union(tables: [mean, max])
#                 |> yield(name: "usage_summary")
#                 '''
#     else:
#         query = f'''
#                 data = {base_query}
#                 |> filter(fn: (r) => r._value != 0)
#                 |> group(columns: ["host"])

#                 mean = data
#                 |> mean()
#                 |> map(fn: (r) => ({ r with _value: r._value * 100.0, _field: "mean_{metric}" }))

#                 max = data
#                 |> max()
#                 |> map(fn: (r) => ({ r with _value: r._value * 100.0, _field: "max_{metric}" }))

#                 union(tables: [mean, max])
#                 |> yield(name: "usage_summary")
#                 '''
    
#     return query


# # Process Query Result
# def process_query_result(result, fields):
#     processed_data = []
#     for table in result:
#         for record in table.records:
#             row = {
#                 'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
#                 'host': record.values.get('host', ''),
#                 'nodename': record.values.get('nodename', ''),
#             }
#             field = record.get_field()
#             if field in fields:
#                 row[field] = round(record.get_value(), 2) if record.get_value() is not None else None
#             processed_data.append(row)

#     return processed_data

# def write_csv(writer, data, selected_metrics):
#     for row in data:
#         csv_row = [row['time'], row['host'], row['nodename']]
#         for metric in selected_metrics:
#             csv_row.append(row.get(metric, ''))
#         writer.writerow(csv_row)

# # extract data to csv
# def index_csv(request):
#     try:
#         start_time = datetime.now()
#         # TODO: logger info - start csv report

#         # Get clients
#         influxdb_client = get_influxdb_client()
#         proxmox_client = get_proxmox_client()
#         # Prepare and execute queries
#         query_api = influxdb_client.query_api()

#         # Process request data
#         start_date_str = request.POST.get('startdate')
#         end_date_str = request.POST.get('enddate')

#         if not start_date_str or not end_date_str:
#             return HttpResponse("Start date and end date are required", status=400)

#         start_date = parse_form_date(start_date_str, 1)
#         end_date = parse_form_date(end_date_str, 0)

#         # # TODO: REMOVE!
#         # print(f"Parsed start date: {start_date}")
#         # print(f"Parsed end date: {end_date}")

#         metrics = [key for key in ['cpuUsage', 'memoryUsage', 'netin', 'netout'] if key in request.POST]
#         selected_metrics = []
#         for metric in metrics:
#             if metric == 'cpuUsage':
#                 selected_metrics.append('cpu')
#             elif metric == 'memoryUsage':
#                 selected_metrics.append('maxmem')
#                 selected_metrics.append('mem')
#             elif metric == 'netin':
#                 selected_metrics.append('netin')
#             elif metric == 'netout':
#                 selected_metrics.append('netout')

#         selected_vms = request.POST.getlist('selectedVMs')
#         node_hosts = [node['node'] for node in proxmox_client.nodes.get()]
        
#         # # TODO: REMOVE!
#         # print("Selected metrics:", selected_metrics)
#         # print("Selected VMs:", selected_vms)
#         # print(f"all hosts: {node_hosts}")

#         # Prepare csv response
#         response = HttpResponse(
#             content_type='text/csv',
#             headers={'Content-Disposition': f'attachment; filename="{start_date_str}_to_{end_date_str}.csv"'},
#         )
#         writer = csv.writer(response)

#         # TODO: add window in response
#         vm_query = construct_vm_details_flux_query(selected_vms, selected_metrics, start_date, end_date, '1h')
#         # TODO: REMOVE!
#         print(f"vm_query: {vm_query}")
#         vm_result = query_api.query(vm_query)
#         # TODO: REMOVE!
#         print(f"vm_result: {vm_result}")


#         # Write the grouped data to CSV - header
#         writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#         writer.writerow(['time', 'host', 'nodename'] + selected_metrics)

#         # Dictionary to store grouped data
#         grouped_data = {}

#         for table in vm_result:
#             for record in table.records:
#                 timestamp = record.get_time().strftime('%Y-%m-%d %H:%M:%S')
#                 host = record.values.get('host', '')
#                 nodename = record.values.get('nodename', '')
#                 field = record.values.get('_field', '')
#                 value = record.values.get('_value', '')

#                 # Unique key for each timestamp-host combination
#                 key = (timestamp, host, nodename)

#                 if key not in grouped_data:
#                     grouped_data[key] = {metric: '' for metric in selected_metrics}

#                 # Add value to the corresponding metric
#                 if field in selected_metrics:
#                     if field == 'cpu':
#                         value = str(round(value * 100, 2)) + "%"
#                     elif field == 'mem' or field == 'maxmem':
#                         value = str(round(value / (1024*1024*1024), 2)) + "GiB"
#                     grouped_data[key][field] = str(value).strip().replace('\n', '').replace('\r', '')


#         # Write the grouped data to CSV - data
#         for (timestamp, host, nodename), metrics in grouped_data.items():
#             row = [timestamp, host, nodename]
#             row.extend([metrics.get(metric, '') for metric in selected_metrics])
#             writer.writerow(row)

#         influxdb_client.close()

#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
#         # TODO: logger info - CSV completed in ? seconds

#         return response

#     except Exception as e:
#         # logger error - error generating CSV report.
#         return HttpResponse(f"Error generating report: {str(e)}", status=500)


# def open_report_page(request):
#     # Get clients
#     influxdb_client = get_influxdb_client()
#     proxmox_client = get_proxmox_client()
#     # Prepare and execute queries
#     query_api = influxdb_client.query_api()
#     vm_infos = proxmox_client.cluster.resources.get(type='vm')

#     node_names = [node['node'] for node in proxmox_client.nodes.get()]

#     # Metrics
#     cpuUsageList = []
#     memUsageList = []
#     netInUsageList = []
#     netOutUsageList = []
#     vmNameList = []
#     vmIdList = []
#     neededStatList = []
#     selectedNodeNameList = []

#     formData = {}

#     data = request.POST
#     # TODO: REMOVE!
#     print(f"data: {data}")

#     for name in data.keys():
#         if str(name) not in ['categoryFilter', 'select_all', 'csrfmiddlewaretoken', 'vmInfoTable_length',
#             'cpuUsage', 'memoryUsage', 'netin', 'netout',
#             'enddate', 'startdate']:
#             vmNameList.append(data.get(str(name)))
#             vmIdList.append(str(name))
#         elif str(name) == 'startdate':
#             startdate = data.get(str(name))
#         elif str(name) == 'enddate':
#             enddate = data.get(str(name))
#         elif str(name) in ['cpuUsage', 'memoryUsage', 'netin', 'netout']:
#             neededStatList.append(data.get(str(name)))

#     # insert data into formData
#     formData['vmNameList'] = vmNameList
#     formData['nodeNameList'] = selectedNodeNameList
#     # formData['vmIdList'] = vmIdList
#     formData['startdate'] = startdate
#     formData['enddate'] = enddate
#     formData['statList'] = neededStatList

#     request.session['formData'] = formData

#     # TODO: REMOVE!
#     # print(f"vmNameList: {formData['vmNameList']}")
#     # print(f"nodeNameList: {formData['nodeNameList']}")
#     # print(f"startdate: {formData['startdate']}")
#     # print(f"enddate: {formData['enddate']}")
#     # print(f"statList: {formData['statList']}")

#     influxdb_client.close()

#     return render(request, 'reports/gen-reports.html')

# def report_gen(request):
#     try:
#         # Get clients
#         influxdb_client = get_influxdb_client()
#         proxmox_client = get_proxmox_client()
#         # Prepare and execute queries
#         query_api = influxdb_client.query_api()

#         form_data = request.session.get('formData', {})
#         start_date = form_data.get('startdate')
#         print(f"start_date: {start_date}")
#         end_date = form_data.get('enddate')
#         date_diff = abs((datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days)
#         window = "1d" if date_diff >= 30 else "1h"

#         sd = parse_form_date(start_date, 1)
#         ed = parse_form_date(end_date, 0)
        
#         # node_metrics = ['cpu', 'memused', 'netin', 'netout', 'memtotal', 'swaptotal']
        
#         stat_list = form_data['statList']
#         metrics = [key for key in ['cpuUsage', 'memoryUsage', 'netin', 'netout'] if key in stat_list]
#         selected_metrics = []
#         for metric in metrics:
#             if metric == 'cpuUsage':
#                 selected_metrics.append('cpu')
#             elif metric == 'memoryUsage':
#                 selected_metrics.append('maxmem')
#                 selected_metrics.append('mem')
#             elif metric == 'netin':
#                 selected_metrics.append('netin')
#             elif metric == 'netout':
#                 selected_metrics.append('netout')
        
#         print(f"selected_metrics: {selected_metrics}")

#         # node_data = {}
#         # for node in form_data.get('nodeNameList', []):
#         #     node_query = construct_flux_query('system', node_metrics, [node], start_date, end_date, window)
#         #     node_result = query_api.query(node_query)
#         #     node_data[node] = process_query_result(node_result, node_metrics)

#         vm_list = form_data.get('vmNameList', [])
#         print(f"vm_list: {vm_list}")

#         cpuUsageList = []
#         memUsageList = []
#         netInUsageList = []
#         netOutUsageList = []

#         for vm in vm_list:
#             # Query for CPU Usage per VM
#             cpuUsageResult = {}
#             cpuUsageResult["vmname"] = vm
#             cpu_data = query_api.query(construct_vm_details_flux_query([vm], ['cpu'], sd, ed, window))
#             cpuUsageResult["data"] = process_query_result(cpu_data, ['cpu'])
#             cpu_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'cpu', sd, ed))
#             # cpuUsageResult["tableData"] = process_query_result(cpu_data, ['mean_cpu', 'max_cpu'])
#             cpuUsageList.append(cpuUsageResult)

#             # Query for Memory Used per VM
#             memUsageResult = {}
#             memUsageResult["vmname"] = vm
#             mem_data = query_api.query(construct_vm_details_flux_query([vm], ['mem'], sd, ed, window))
#             memUsageResult["data"] = process_query_result(mem_data, ['mem'])
#             mem_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'mem', sd, ed))
#             # memUsageResult["tableData"] = process_query_result(mem_table_data, ['mean_mem', 'max_mem'])
#             memUsageList.append(memUsageResult)

#             # Query for Network In per VM
#             netInUsageResult = {}
#             netInUsageResult["vmname"] = vm
#             netin_data = query_api.query(construct_vm_details_flux_query([vm], ['netin'], sd, ed, window))
#             netInUsageResult["data"] = process_query_result(netin_data, ['netin'])
#             netin_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'netin', sd, ed))
#             # netInUsageResult["tableData"] = process_query_result(netin_table_data, ['mean_netin', 'max_netin'])
#             netInUsageList.append(netInUsageResult)

#             # Query for Network Out per VM
#             netOutUsageResult = {}
#             netOutUsageResult["vmname"] = vm
#             netout_data = query_api.query(construct_vm_details_flux_query([vm], ['netout'], sd, ed, window))
#             netOutUsageResult["data"] = process_query_result(netout_data, ['netout'])
#             netout_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'netout', sd, ed))
#             # netOutUsageResult["tableData"] = process_query_result(netout_table_data, ['mean_netout', 'max_netout'])
#             netOutUsageList.append(netOutUsageResult)

#         influxdb_client.close()

#         return JsonResponse({
#             'cpuUsageList':cpuUsageList,
#             'memUsageList':memUsageList,
#             'netInUsageList':netInUsageList,
#             'netOutUsageList':netOutUsageList,
#             'dateDiff': date_diff,
#             'formData': form_data
#         })

#     except Exception as e:
#         # TODO: logger error - error generating report page
#         print(f"Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return JsonResponse({'error': 'An error occurred while preparing the report generation page.'}, status=500)


# def performance_gen(request):
#     return render(request, 'reports/performance_gen.html')


# Get Templates VM ids
def get_template_hosts_ids(start_date, end_date):

    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    query = f'''
        from(bucket:"proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "template")
        |> distinct(column: "host")
        |> yield(name: "template_hosts")

    '''

    result = query_api.query(query=query)

    template_hosts_ids = []
    for table in result:
        for record in table.records:
            template_hosts_ids.append(record.values["vmid"])

    influxdb_client.close()
    return template_hosts_ids

                
# Detail Stats
def extract_detail_stat(request):

    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    start_date_str = request.POST.get('startdate')
    end_date_str = request.POST.get('enddate')
    
    start_date = parse_form_date(start_date_str, 1)
    end_date = parse_form_date(end_date_str, 0)

    # TODO: add uptime
    queries = generate_vm_resource_query(start_date, end_date)

    # process result, 
    results = {}
    if queries:
        for resource, query in queries.items():
            result = query_api.query(query=query)
            print(f"result: {result}")
            results[resource] = result

    # process result
    processed_data = []
    if results:
        processed_data = process_vm_resource_data(results, start_date, end_date)
        print(f"processed_data: {processed_data}")

    influxdb_client.close()
    
    print(f"processed_data: {processed_data}")

    return generate_detail_csv_response(processed_data, start_date_str, end_date_str)

# Gerenate Detail Query Statement
def generate_vm_resource_query(start_date, end_date):
    
    # get template
    template_hosts_ids = get_template_hosts_ids(start_date, end_date)
    excluded_vmids_str = '|'.join(map(str, template_hosts_ids))

    queries = {}
    cpus_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> keep(columns: ["_value", "host", "nodename", "vmid"])
        |> last()
        |> yield(name: "cpus")
    '''
    queries["cpus"] = cpus_query

    cpu_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpu")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> keep(columns: ["_value", "host", "nodename"])
        |> last()
        |> yield(name: "cpu")
    '''
    queries["cpu"] = cpu_query

    # mem data
    mem_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> mean()
        |> pivot(rowKey: [], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
        |> yield(name: "mem")
    '''
    queries["mem"] = mem_query
    
    # maxmem data
    maxmem_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_field"] == "maxmem")
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1000.0) }}))
        |> yield(name: "maxmem")
    '''
    queries["maxmem"] = maxmem_query

    return queries

# Process Detail Query Result
def process_vm_resource_data(results, start_date, end_date):
    processed_data = []
    print(f"Debug: Results keys: {results.keys()}")

    def safe_get_value(result, resource, host):
        try:
            if result:
                for table in result:
                    for record in table.records:
                        if record.values.get('host') == host:
                            return record.values.get('_value', 0)
            return None
        except (IndexError, AttributeError):
            print(f"No data for {resource} on host {host}")
            return None

    all_vms = set()
    for resource in results:
        if results[resource]:
            for table in results[resource]:
                all_vms.update((record.values.get('nodename'), record.values.get('host')) for record in table.records)

    print(f"all_vms: {all_vms}")
    for nodename, host in all_vms:
        row = {
            'nodename': nodename,
            'host': host,
            'startdate': start_date,
            'enddate': end_date,
        }
        for resource in ['cpus', 'cpu', 'mem', 'maxmem']:
            value = safe_get_value(results.get(resource), resource, host)
            if value is not None:
                row[resource] = value
        if len(row) > 4:  # Ensure we have at least one resource value
            processed_data.append(row)

    return processed_data


def generate_detail_csv_response(data, start_date, end_date):
    # TODO: add uptime
    fieldnames = ['nodename', 'vmname', 'startdate', 'enddate', 'cpus', 'cpu', 'mem', 'maxmem']
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        writer.writerow(row)
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="detail_resource_usage_{start_date}_to_{end_date}.csv"'},
    )
    response.write(csv_buffer.getvalue())
    return response

# General Stats
def extract_general_stat(request):
    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    # Process request data
    start_date_str = request.POST.get('startdate')
    end_date_str = request.POST.get('enddate')
    query_type = request.POST.get('scope') # All, per-node, per-class

    start_date = parse_form_date(start_date_str, 1)
    end_date = parse_form_date(end_date_str, 0)


    # Get needed metrics 
    # (number of VMs, total CPU, CPU%, total mem, mem%, total storage, storage%, netin and netout)
    
    raw_class_list = RequestUseCase.objects.all().exclude(
        request_use_case__icontains="Research"
    ).exclude(
        request_use_case__icontains="Test"
    ).exclude(
        request_use_case__icontains="Thesis"
    ).values_list('request_use_case', flat=True)

    class_list = []
    for entry in raw_class_list:
        processed_entry = entry.split('_')[0]
        if processed_entry not in class_list:
            class_list.append(processed_entry)

    queries =  generate_resource_query(start_date, end_date, query_type, class_list)

    results = {}
    if queries:
        for resource, query in queries.items():
            print(f"query: {query}")
            result = query_api.query(query=query)
            results[resource] = result

    print(f"result: {results}")   

    # process result
    processed_data = []
    if results:
        processed_data = process_resource_data(results, query_type, start_date, end_date)
        print(f"processed_data: {processed_data}")

    influxdb_client.close()
    return generate_csv_response(processed_data, query_type, start_date_str, end_date_str)

# Generate General Query Statement
def generate_resource_query(start_date, end_date, query_type, class_list=None):

    # get template
    template_hosts_ids = get_template_hosts_ids(start_date, end_date)
    excluded_vmids_str = '|'.join(map(str, template_hosts_ids))

    print(f"template_hosts: {template_hosts_ids}")

    queries = {}

    
    if query_type == "all":
        # cpu cores data
        cpus_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> last()
            |> group()
            |> sum()
            |> yield(name: "cpus_total")
        '''
        queries["cpus"] = cpus_query

        # cpu data
        cpu_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> group()
            |> mean()
            |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
            |> yield(name: "cpu_total")
        '''
        queries["cpu"] = cpu_query

        # mem data
        mem_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> group(columns: ["_field"])
            |> mean()
            |> pivot(rowKey: [], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
            |> yield(name: "mem_total")
        '''
        queries["mem"] = mem_query

        # maxmem data
        maxmem_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memtotal")
            |> last()
            |> group()
            |> sum()
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1000.0) }}))
            |> yield(name: "maxmem_total")
        '''
        queries["maxmem"] = maxmem_query

    elif query_type == "per-node":
        # cpus data
        cpus_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> last()
            |> keep(columns: ["_value", "host"]) 
            |> yield(name: "cpus_per_node")
        '''
        queries["cpus"] = cpus_query
        
        # cpu data
        cpu_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> group(columns: ["host"])
            |> mean()
            |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
            |> keep(columns: ["_value", "host"])  
            |> yield(name: "cpu_per_node")
        '''
        queries["cpu"] = cpu_query

        # mem data
        mem_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "memused" or r["_field"] == "memtotal")
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> group(columns: ["_field", "host"])
            |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.memused / r.memtotal) * 100.0 }}))
            |> keep(columns: ["host", "_value"])
            |> yield(name: "mem_per_node")
        '''
        queries["mem"] = mem_query

        # maxmem data
        maxmem_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memtotal")
            |> last()
            |> keep(columns: ["_value", "host"])  
            |> yield(name: "maxmem_per_node")
        '''
        queries["maxmem"] = maxmem_query
       
    elif query_type == "per-class":
        if not class_list:
            return None
        class_filters = ' or '.join([f'r["host"] =~ /{class_name}/' for class_name in class_list])
        class_map = ' '.join([f'if r["host"] =~ /{class_name}/ then "{class_name}" else' for class_name in class_list]) + ' "Unknown"'
        
        # cpus data
        cpus_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => {class_filters})
            |> last()
            |> map(fn: (r) => ({{ r with class: {class_map} }}))
            |> group(columns: ["class"])
            |> sum()
            |> yield(name: "cpus_per_class")
        '''
        queries["cpus"] = cpus_query

        # cpu data
        cpu_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => {class_filters})
            |> map(fn: (r) => ({{ r with class: {class_map} }}))
            |> group(columns: ["class"])
            |> mean()
            |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
            |> yield(name: "cpu_per_class")
        '''
        queries["cpu"] = cpu_query
        
        # mem data
        mem_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => {class_filters})
            |> map(fn: (r) => ({{ r with class: {class_map} }}))
            |> group(columns: ["class", "_field"])
            |> mean()
            |> pivot(rowKey: ["class"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
            |> yield(name: "mem_per_class")
        '''
        queries["mem"] = mem_query
        
        # maxmem data
        query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_field"] == "maxmem")
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => {class_filters})
            |> last()
            |> map(fn: (r) => ({{ r with class: {class_map} }}))
            |> group(columns: ["class"])
            |> sum()
            |> yield(name: "maxmem_per_class")
        '''
        queries["maxmem"] = maxmem_query
    
    return queries

# Process General Query Result
def process_resource_data(results, query_type, start_date, end_date):
    processed_data = []

    print(f"Debug: Results keys: {results.keys()}")

    def safe_get_value(result, resource, key=None):
        try:
            if result:
                for table in result:
                    for record in table.records:
                        if key is None or record.values.get('host') == key:
                            return record.values.get('_value', 0)
            return None
        except (IndexError, AttributeError):
            print(f"No data for {resource}")
            return None

    if query_type == "all":
        row = {
            'startdate': start_date,
            'enddate': end_date,
        }

        for resource in ['cpus', 'cpu', 'mem', 'maxmem']:
            value = safe_get_value(results.get(resource), resource)
            if value is not None:
                row[resource] = value
        
        if len(row) > 2:  
            processed_data.append(row)
    
    elif query_type in ["per-node", "per-class"]:
        key = 'nodename' if query_type == "per-node" else 'classname'
        all_entities = set()
        
        for resource in results:
            if results[resource]:
                for table in results[resource]:
                    all_entities.update(record.values.get('host' if query_type == "per-node" else 'class') for record in table.records)
        
        print(f"all_entities: {all_entities}")

        for entity in all_entities:
            row = {
                key: entity,
                'startdate': start_date,
                'enddate': end_date,
            }

            for resource in ['cpus', 'cpu', 'mem', 'maxmem']:
                value = safe_get_value(results.get(resource), resource, entity)
                if value is not None:
                    row[resource] = value

            if len(row) > 3:
                processed_data.append(row)

    return processed_data

# Generate General CSV Response
def generate_csv_response(data, query_type, start_date, end_date):
    if query_type == "all":
        fieldnames = ['startdate', 'enddate', 'cpus', 'cpu', 'mem', 'maxmem']
    elif query_type == "per-node":
        fieldnames = ['nodename', 'startdate', 'enddate', 'cpus', 'cpu', 'mem', 'maxmem']
    elif query_type == "per-class":
        fieldnames = ['classname', 'startdate', 'enddate', 'cpus', 'cpu', 'mem', 'maxmem']
    
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        if query_type == "per-node":
            row['nodename'] = row.pop('nodename')
        elif query_type == "per-class":
            row['classname'] = row.pop('classname')
        writer.writerow(row)
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="resource_usage_{query_type}_{start_date}_to_{end_date}.csv"'},
    )
    response.write(csv_buffer.getvalue())
    return response
