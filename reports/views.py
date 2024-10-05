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

def construct_vm_details_flux_query(hosts, metrics, start_date, end_date, window):

    host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
    
    # field_filter includes [network_metrics] and [other metrics]
    network_metrics = [m for m in metrics if m in ['netin', 'netout']]
    other_metrics = [m for m in metrics if m not in ['netin', 'netout']]
    
    query_parts = []
    
    if network_metrics:
        network_metrics_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in network_metrics) if network_metrics else 'true'
        network_query = f'''
                from(bucket:"{bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => {host_filter})
                |> filter(fn: (r) => {network_metrics_filter})
                |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
                |> derivative(unit: 10s, nonNegative: true, columns: ["_value"], timeColumn: "_time")
                |> yield(name: "mean")
                '''
        query_parts.append(network_query)

    if other_metrics:
        other_metrics_filter = ' or '.join(f'r["_field"] == "{metric}"' for metric in other_metrics) if other_metrics else 'true'
        other_query = f'''
                from(bucket:"{bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => {host_filter})
                |> filter(fn: (r) => {other_metrics_filter})
                |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
                '''
        query_parts.append(other_query)

    if len(query_parts) > 1:
        combined_query = f'''
                networkData = {query_parts[0]}

                otherData = {query_parts[1]}

                union(tables: [networkData, otherData])
                |> yield(name: "combined")
                '''
    elif len(query_parts) == 1:
        combined_query = f'''
                {query_parts[0]}
                |> yield(name: "combined")
                '''
    else:
        combined_query = "// No metrics specified"

    return combined_query


# Fix this
def construct_vm_summary_flux_query(hosts, metric, start_date, end_date):
    host_filter = ' or '.join(f'r["host"] == "{host}"' for host in hosts) if hosts else 'true'
    
    is_network_metric = metric in ['netin', 'netout']

    base_query = f'''
                from(bucket:"{bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => {host_filter})
                |> filter(fn: (r) => r["_field"] == "{metric}")
                '''
    
    if is_network_metric:
        query = f'''
                data = {base_query}
                |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
                |> derivative(unit: 1h, nonNegative: true, columns: ["_value"], timeColumn: "_time")
                |> filter(fn: (r) => r._value != 0)
                |> group(columns: ["host"])

                mean = data
                |> mean()
                |> map(fn: (r) => ({{ r with _value: r._value, _field: "mean_{metric}" }}))

                max = data
                |> max()
                |> map(fn: (r) => ({{ r with _value: r._value, _field: "max_{metric}" }}))

                union(tables: [mean, max])
                |> yield(name: "usage_summary")
                '''
    else:
        query = f'''
                data = {base_query}
                |> filter(fn: (r) => r._value != 0)
                |> group(columns: ["host"])

                mean = data
                |> mean()
                |> map(fn: (r) => ({{ r with _value: r._value * 100.0, _field: "mean_{metric}" }}))

                max = data
                |> max()
                |> map(fn: (r) => ({{ r with _value: r._value * 100.0, _field: "max_{metric}" }}))

                union(tables: [mean, max])
                |> yield(name: "usage_summary")
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
        # Prepare and execute queries
        query_api = influxdb_client.query_api()

        # Process request data
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')

        if not start_date_str or not end_date_str:
            return HttpResponse("Start date and end date are required", status=400)

        start_date = parse_form_date(start_date_str, 1)
        end_date = parse_form_date(end_date_str, 0)

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
        vm_query = construct_vm_details_flux_query(selected_vms, selected_metrics, start_date, end_date, '1h')
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
    # formData['vmIdList'] = vmIdList
    formData['startdate'] = startdate
    formData['enddate'] = enddate
    formData['statList'] = neededStatList

    request.session['formData'] = formData

    # TODO: REMOVE!
    # print(f"vmNameList: {formData['vmNameList']}")
    # print(f"nodeNameList: {formData['nodeNameList']}")
    # print(f"startdate: {formData['startdate']}")
    # print(f"enddate: {formData['enddate']}")
    # print(f"statList: {formData['statList']}")

    influxdb_client.close()

    return render(request, 'reports/gen-reports.html')

def report_gen(request):
    try:
        # Get clients
        influxdb_client = get_influxdb_client()
        proxmox_client = get_proxmox_client()
        # Prepare and execute queries
        query_api = influxdb_client.query_api()

        form_data = request.session.get('formData', {})
        start_date = form_data.get('startdate')
        print(f"start_date: {start_date}")
        end_date = form_data.get('enddate')
        date_diff = abs((datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days)
        window = "1d" if date_diff >= 30 else "1h"

        sd = parse_form_date(start_date, 1)
        ed = parse_form_date(end_date, 0)
        
        # node_metrics = ['cpu', 'memused', 'netin', 'netout', 'memtotal', 'swaptotal']
        
        stat_list = form_data['statList']
        metrics = [key for key in ['cpuUsage', 'memoryUsage', 'netin', 'netout'] if key in stat_list]
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
        
        print(f"selected_metrics: {selected_metrics}")

        # node_data = {}
        # for node in form_data.get('nodeNameList', []):
        #     node_query = construct_flux_query('system', node_metrics, [node], start_date, end_date, window)
        #     node_result = query_api.query(node_query)
        #     node_data[node] = process_query_result(node_result, node_metrics)

        vm_list = form_data.get('vmNameList', [])
        print(f"vm_list: {vm_list}")

        cpuUsageList = []
        memUsageList = []
        netInUsageList = []
        netOutUsageList = []

        for vm in vm_list:
            # Query for CPU Usage per VM
            cpuUsageResult = {}
            cpuUsageResult["vmname"] = vm
            cpu_data = query_api.query(construct_vm_details_flux_query([vm], ['cpu'], sd, ed, window))
            cpuUsageResult["data"] = process_query_result(cpu_data, ['cpu'])
            cpu_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'cpu', sd, ed))
            # cpuUsageResult["tableData"] = process_query_result(cpu_data, ['mean_cpu', 'max_cpu'])
            cpuUsageList.append(cpuUsageResult)

            # Query for Memory Used per VM
            memUsageResult = {}
            memUsageResult["vmname"] = vm
            mem_data = query_api.query(construct_vm_details_flux_query([vm], ['mem'], sd, ed, window))
            memUsageResult["data"] = process_query_result(mem_data, ['mem'])
            mem_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'mem', sd, ed))
            # memUsageResult["tableData"] = process_query_result(mem_table_data, ['mean_mem', 'max_mem'])
            memUsageList.append(memUsageResult)

            # Query for Network In per VM
            netInUsageResult = {}
            netInUsageResult["vmname"] = vm
            netin_data = query_api.query(construct_vm_details_flux_query([vm], ['netin'], sd, ed, window))
            netInUsageResult["data"] = process_query_result(netin_data, ['netin'])
            netin_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'netin', sd, ed))
            # netInUsageResult["tableData"] = process_query_result(netin_table_data, ['mean_netin', 'max_netin'])
            netInUsageList.append(netInUsageResult)

            # Query for Network Out per VM
            netOutUsageResult = {}
            netOutUsageResult["vmname"] = vm
            netout_data = query_api.query(construct_vm_details_flux_query([vm], ['netout'], sd, ed, window))
            netOutUsageResult["data"] = process_query_result(netout_data, ['netout'])
            netout_table_data = query_api.query(construct_vm_summary_flux_query([vm], 'netout', sd, ed))
            # netOutUsageResult["tableData"] = process_query_result(netout_table_data, ['mean_netout', 'max_netout'])
            netOutUsageList.append(netOutUsageResult)

        influxdb_client.close()

        return JsonResponse({
            'cpuUsageList':cpuUsageList,
            'memUsageList':memUsageList,
            'netInUsageList':netInUsageList,
            'netOutUsageList':netOutUsageList,
            'dateDiff': date_diff,
            'formData': form_data
        })

    except Exception as e:
        # TODO: logger error - error generating report page
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': 'An error occurred while preparing the report generation page.'}, status=500)


def performance_gen(request):
    return render(request, 'reports/performance_gen.html')

# TODO: 可以直接在这个函数中拓展，加入其他metrics的查询如mem，memmax等
def generate_resource_query(start_date, end_date, query_type, class_list=None):

    resources = {
        "cpus": {"field": "cpus"},         # processer number
        "cpu": {"field": "cpu"},            # cpu usage %
        "mem": {"field": "mem"},
        "maxmem": {"field": "maxmem"},
        "used": {"field": "used"},
        "total": {"field": "total"},
        "netin": {"field": "netin"},
        "netout": {"field": "netout"}
    }

    queries = {}

    for resource, config in resources.items():
        base_query = f'''
                    from(bucket:"{bucket}")
                    |> range(start: {start_date}, stop: {end_date})
                    |> filter(fn: (r) => r["_measurement"] == "system")
                    |> filter(fn: (r) => r["_field"] == "{config['field']}")
                    '''
    
        if query_type == "all":
            query = f'''
                    {base_query}
                    |> last()
                    |> group()
                    |> sum(column: "_value")
                    |> yield(name: "total_{resource}")
                    '''
        # TODO: 根据节点来分组好像不是这样的，是用 |> group(columns: ["host"]) 吗
        elif query_type == "per-node":
            query = f'''
                    {base_query}
                    |> last()
                    |> group(columns: ["host"])
                    |> sum(column: "_value")
                    |> yield(name: "{resource}_per_node")
                    '''
        elif query_type == "per-class":
            if not class_list:
                raise ValueError("Class list is required for 'per class' query type.")
            # TODO: need to get a list of class name for the query (maybe connecting to our own db to get the data)
            # TODO: 貌似不是vm_name, 得去influxdb中看一下vm主机名对应的是什么
            class_filters = ' or '.join([f'r["host"] =~ /{class_name}/' for class_name in class_list])
            class_assignments = ' else '.join([f'if r["host"] =~ /{class_name}/ then "{class_name}"' for class_name in class_list]) + ' else "Unknown"'
            query = f'''
                    {base_query}
                    |> filter(fn: (r) => {class_filters})
                    |> last()
                    |> map(fn: (r) => ({{
                        _value: r._value,
                        class: if {class_assignments}
                    }}))
                    |> group(columns: ["class"])
                    |> sum(column: "_value")
                    |> yield(name: "{resource}_per_class")
                    '''
        else:
            raise ValueError("Invalid query type.")
        
        print(f"query: {query}")
        queries[resource] = query

    return queries


def generate_cpu_usage_query(query_type, start_date, end_date, class_list=None):
    base_query = f'''
                from(bucket:"{bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => r["_field"] == "cpu")
                '''
    
    if query_type == "all":
        query = f'''
                {base_query}
                |> mean()
                |> yield(name: "total_cpu_usage")
                '''

    elif query_type == "per-node":
        query = f'''
                {base_query}
                |> group(columns: ["host"])
                |> mean()
                |> yield(name: "cpu_usage_per_node")
                '''

    elif query_type == "per-class":
        class_filters = ' or '.join([f'r["host"] =~ /{class_name}/' for class_name in class_list])
        class_assignments = ' else '.join([f'if r["host"] =~ /{class_name}/ then "{class_name}"' for class_name in class_list]) + ' else "Unknown"'

        query = f'''
                {base_query}
                |> filter(fn: (r) => {class_filters})
                |> map(fn: (r) => ({{
                    _value: r._value,
                    class: if {class_assignments}
                }}))
                |> group(columns: ["class"])
                |> mean()
                |> yield(name: "cpu_usage_per_class")
                '''
    else:
        raise ValueError("Invalid query type. ")

    return query

# TODO: 如果成了，加上network的数据
# VM detailed resource info
def generate_vm_resource_query(start_date, end_date, query_type, category_values=None):
    if query_type not in ["all", "nodes", "classes"]:
        raise ValueError("Invalid category type. Choose 'all', 'nodes', or 'classes'")
    
    base_query = f'''
                from(bucket:"{bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                '''

    # Add category-specific filters，这里的r["host"]到底是节点还是vm呢？
    if query_type == "nodes" and category_values:
        node_filters = ' or '.join([f'r["host"] == "{node}"' for node in category_values])
        base_query += f'  |> filter(fn: (r) => {node_filters})\n'
    elif query_type == "classes" and category_values:
        class_filters = ' or '.join([f'r["vm_name"] =~ /{class_name}/' for class_name in category_values])
        base_query += f'  |> filter(fn: (r) => {class_filters})\n'

    # Query for CPU count (assuming it's a static value per VM)
    cpu_count_query = f'''
                {base_query}
                |> filter(fn: (r) => r["_field"] == "cpus")
                |> last()
                |> group(columns: ["vm_name"])
                |> yield(name: "cpu_count")
                '''

    # Query for CPU usage
    cpu_usage_query = f'''
                {base_query}
                |> filter(fn: (r) => r["_field"] == "cpu")
                |> mean()
                |> group(columns: ["vm_name"])
                |> yield(name: "cpu_usage")
                '''

    # Query for total memory (assuming it's a static value per VM)
    total_mem_query = f'''
                {base_query}
                |> filter(fn: (r) => r["_field"] == "maxmem")
                |> last()
                |> group(columns: ["vm_name"])
                |> yield(name: "total_memory")
                '''

    # Query for memory usage
    mem_usage_query = f'''{base_query}
                |> filter(fn: (r) => r["_field"] == "mem")
                |> mean()
                |> group(columns: ["vm_name"])
                |> yield(name: "memory_usage")
                '''

    # Combine all queries
    combined_query = f'''
                {cpu_count_query}

                {cpu_usage_query}

                {total_mem_query}

                {mem_usage_query}

                // Join the results
                join(
                tables: {{
                    cpu_count: cpu_count,
                    cpu_usage: cpu_usage,
                    total_memory: total_memory,
                    memory_usage: memory_usage
                }},
                on: ["vm_name"]
                )
                '''

    return combined_query
                

def extract_detail_stat(request):

    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    start_date_str = request.POST.get('startdate')
    end_date_str = request.POST.get('enddate')
    scope = request.POST.get('scope') # All, nodes, classes
    category_values = request.POST.get('category_values') # 前端根据选择的 all, node, class 来生成表格供用户选择

    # TODO: add uptime
    query = generate_vm_resource_query(start_date, end_date, scope, category_values)
    result = query_api.query(query=flux_query)

    # process result, 

    # csv?
    # generate table?

    influxdb_client.close()
    
    return HttpResponse("Extract detail Stat")


def process_resource_data(results, query_type, start_date, end_date):
    processed_data = []
    
    if query_type == "all":
        row = {
            'startdate': start_date,
            'enddate': end_date,
            'cpu cores': results['cpus'][0].records[0].values['_value'],   
            'cpu': results['cpu'][0].records[0].values['_value'],
            'mem': results['mem'][0].records[0].values['_value'],
            'maxmem': results['maxmem'][0].records[0].values['_value'],
            'used': results['used'][0].records[0].values['_value'],
            'total': results['total'][0].records[0].values['_value'],
            'netin': results['netin'][0].records[0].values['_value'],       
            'netout': results['netout'][0].records[0].values['_value'],      
        }
        row['mem_usage(%)'] = (row['mem'] / row['maxmem']) * 100 if row['maxmem'] != 0 else 0
        row['storage_usage(%)'] = (row['used'] / row['total']) * 100 if row['total'] != 0 else 0
        processed_data.append(row)
    
    elif query_type in ["per-node", "per-class"]:
        key = 'host' if query_type == "per-node" else 'class'
        for cpu_record in results['cpus'][0].records:
            node_or_class = cpu_record.values[key]
            row = {
                key: node_or_class,
                'startdate': start_date,
                'enddate': end_date,
                'cpu cores': cpu_record.values['_value'],
                'cpu': next(r.values['_value'] for r in results['cpu'][0].records if r.values[key] == node_or_class),
                'mem': next(r.values['_value'] for r in results['mem'][0].records if r.values[key] == node_or_class),
                'maxmem': next(r.values['_value'] for r in results['maxmem'][0].records if r.values[key] == node_or_class),
                'used': next(r.values['_value'] for r in results['used'][0].records if r.values[key] == node_or_class),
                'total': next(r.values['_value'] for r in results['total'][0].records if r.values[key] == node_or_class),
                'netin': next(r.values['_value'] for r in results['netin'][0].records if r.values[key] == node_or_class),
                'netout': next(r.values['_value'] for r in results['netout'][0].records if r.values[key] == node_or_class),
            }
            row['mem_usage(%)'] = (row['mem'] / row['maxmem']) * 100 if row['maxmem'] != 0 else 0
            row['storage_usage(%)'] = (row['used'] / row['total']) * 100 if row['total'] != 0 else 0
            processed_data.append(row)

    return processed_data

def generate_csv_response(data, query_type, start_date, end_date):
    if query_type == "all":
        fieldnames = ['startdate', 'enddate', 'cpu cores', 'cpu', 'mem', 'maxmem', 'mem_usage(%)', 'used', 'total', 'storage_usage(%)', 'netin', 'netout']
    elif query_type == "per-node":
        fieldnames = ['nodename', 'startdate', 'enddate', 'cpu cores', 'cpu', 'mem', 'maxmem', 'mem_usage(%)', 'used', 'total', 'storage_usage(%)', 'netin', 'netout']
    elif query_type == "per-class":
        fieldnames = ['classname', 'startdate', 'enddate', 'cpu cores', 'cpu', 'mem', 'maxmem', 'mem_usage(%)', 'used', 'total', 'storage_usage(%)', 'netin', 'netout']
    
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        if query_type == "per-node":
            row['nodename'] = row.pop('host')
        elif query_type == "per-class":
            row['classname'] = row.pop('class')
        writer.writerow(row)
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="resource_usage_{query_type}_{start_date}_to_{end_date}.csv"'},
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
    # TODO: Static for now, remove this when we can dynamically get the list of class
    
    
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

    for resource, query in queries.items():
        result = query_api.query(query=query)
        results[resource] = result   

    # process result
    processed_data = process_resource_data(results, query_type, start_date, end_date)
    print(f"processed_data: {processed_data}")

    influxdb_client.close()
    return generate_csv_response(processed_data, query_type, start_date_str, end_date_str)
