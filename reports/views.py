from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.db.models import Sum, Count
from proxmoxer import ProxmoxAPI
from influxdb_client import InfluxDBClient
from collections import defaultdict
from io import StringIO
import json, csv
from decouple import config

from ticketing.models import RequestEntry, RequestUseCase
from proxmox.models import VirtualMachines

from CAPSTONE2240.utils import download_csv

from .forms import TicketingReportForm

INFLUX_ADDRESS = config('INFLUX_ADDRESS')
token = config('INFLUX_TOKEN')
org = config('INFLUXDB_ORG')
bucket = config('INFLUXDB_BUCKET')
proxmox_password = config('PROXMOX_PASSWORD')

# Parse date to InfluxDB compatible, fit timezone
def parse_form_date(date_string, is_start):
    print(f"date_string: {date_string}")
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        adjusted_dt = dt - timedelta(hours=8)
        if is_start:
            adjusted_dt = adjusted_dt - timedelta(hours=8)
        return adjusted_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")

# seconds to HMS
def seconds_to_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"        

# Get Report Page
def index(request):
    return render(request, 'reports/reports.html')

def reports(request):
    return render(request, 'reports/reports_new.html')

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
    print(f"query statement: {query}")

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

    start_date_str = request.GET.get('startdate')
    end_date_str = request.GET.get('enddate')
    
    start_date = parse_form_date(start_date_str)
    end_date = parse_form_date(end_date_str)

    # TODO: add uptime
    queries = generate_vm_resource_query(start_date, end_date)

    # process result, 
    results = {}
    if queries:
        for resource, query in queries.items():
            result = query_api.query(query=query)
            # print(f"result: {result}")
            results[resource] = result

    # process result
    processed_data = []
    if results:
        processed_data = process_vm_resource_data(results, start_date, end_date)
        # print(f"processed_data: {processed_data}")

    influxdb_client.close()
    
    print(f"processed_data: {processed_data}")

    return generate_detail_csv_response(processed_data, start_date_str, end_date_str)


# Process Detail Query Result
def process_vm_resource_data(results, start_date, end_date):
    processed_data = {}
    print(f"Debug: Results keys: {results.keys()}")

    def safe_get_value(result, resource, identifier):
        try:
            if result:
                for table in result:
                    for record in table.records:
                        if (record.values.get('vmid') == identifier[0] and record.values.get('host') == identifier[1] and record.values.get('nodename') == identifier[2] and record.values.get('object') == identifier[3] ):
                            return record.values.get('_value', 0)
            return None
        except (IndexError, AttributeError):
            print(f"No data for {resource} on host {host}")
            return None

    all_identifiers  = set()
    for resource, result in results.items():
        if result:
            for table in result:
                for record in table.records:
                    identifier = (record.values.get('vmid'), record.values.get('host'), record.values.get('nodename'), record.values.get('object'), record.values.get('_time'))
                    if all(identifier):
                        if resource == "cpus": # so that it add only once 
                            all_identifiers.add(identifier)
    
    # print(f"all_identifiers: {all_identifiers}")
    for vmid, host, nodename, machineType, time in all_identifiers:
        identifier = (vmid, host, nodename, machineType, time)
        dt_adjusted = time + timedelta(hours=8)
        adjusted_time = dt_adjusted.strftime("%Y-%m-%d %H:%M:%S")
        row = {
            'vmid': vmid,
            'host': host,
            'nodename': nodename,
            'machineType': machineType,
            'until_time': adjusted_time
        }
        for resource in ['cpus', 'cpu', 'mem', 'maxmem', 'uptime']:
            value = safe_get_value(results.get(resource), resource, identifier)
            if value is not None:
                if resource == "cpus":
                    value = str(value) + " cores"
                if resource == "cpu": 
                    value = str(round(value * 100, 2)) + "%"
                if resource == "mem":
                    value = str(round(value, 2)) + "%"
                if resource == "maxmem":
                    value = str(round(value, 2)) + "G"
                if resource == "uptime":
                    if value < 0:
                        value = 0
                    value = seconds_to_hms(value)
                row[resource] = value
        if len(row) > 5:  # Ensure we have at least one resource value
            processed_data[identifier] = row
    
    return list(processed_data.values())

# Generate Detail CSV Response
def generate_detail_csv_response(data, start_date, end_date):
    # TODO: add uptime
    fieldnames = ['vmid', 'host', 'nodename', 'machineType', 'until_time', 'cpus', 'cpu', 'mem', 'maxmem', 'uptime']
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

    start_date = parse_form_date(start_date_str)
    end_date = parse_form_date(end_date_str)


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


def process_pernode_query_result(results, query_result, column_name):
    for table in query_result:
        for record in table.records:
            nodename = record.values.get('nodename')
            value = record.values.get('_value', 0)
            for result in results:
                if result["nodename"] == nodename:
                    result[column_name] = value
                    break

def process_perclass_query_result(results, query_result, column_name):
    for table in query_result:
        for record in table.records:
            classname = record.values.get('class')
            value = record.values.get('_value', 0)
            for result in results:
                if result["class"] == classname:
                    result[column_name] = value
                    break

def process_indiv_query_result(results, query_result, column_name):
    for table in query_result:
        for record in table.records:
            vmid = record.values.get('vmid')
            value = record.values.get('_value', 0)
            for result in results:
                if result["vmid"] == vmid:
                    result[column_name] = value
                    break

def get_time_window(start_datetime, end_datetime):
    start = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

    start, end = min(start, end), max(start, end)
    
    time_diff = end - start
    print(f"start: {start}")
    print(f"end: {end}")

    if time_diff < timedelta(minutes=30):
        return "5m"
    elif time_diff <= timedelta(days=1):
        return "30m"
    elif timedelta(days=1) < time_diff <= timedelta(days=5):
        return "3h"
    elif timedelta(days=5) < time_diff <= timedelta(days=60):
        return "1d"
    else:
        return "5d"

def convert_time_format(time_value):
    if isinstance(time_value, datetime):
        return time_value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(time_value, (int, float)):
        return datetime.fromtimestamp(time_value / 1e9).strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(time_value, str):
        try:
            dt = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return time_value
    else:
        return str(time_value)


def formdata(request): 

    # connect to influxdb
    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    # TODO: change this. The received start_date format is YYYY-MM-DD HH:MM:SS
    # TODO: also change parse_form_date function
    start_time_str = request.GET.get('start_time')
    end_time_str = request.GET.get('end_time')
    # TODO: change this. Now is date
    start_date = parse_form_date(start_time_str, 1)
    end_date = parse_form_date(end_time_str, 0)
    print(f"start_date:{start_date}")
    print(f"end_date:{end_date}")
    
    # get template vm
    template_hosts_ids = get_template_hosts_ids(start_date, end_date)
    excluded_vmids_str = '|'.join(map(str, template_hosts_ids))


    ################################ SYSTEM ###############################
    data = []
    result = {}
    result["type"] = "system"
    result["name"] = "system"
    result["nodename"] = "none"
    result["class"] = "none"
    result["vmid"] = -1
    
    # vm num
    vm_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => r["object"] == "qemu")
        |> distinct(column: "vmid")
        |> count()
        |> group()
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=vm_query)
    for table in query_result:
        for record in table.records:
            result["vm number"] = record.values.get('_value', 0)

    # lxc num
    lxc_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => r["object"] == "lxc")
        |> distinct(column: "vmid")
        |> count()
        |> group()
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=lxc_query)
    for table in query_result:
        for record in table.records:
            result["lxc number"] = record.values.get('_value', 0)

    # cpus cores
    cpus_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["_measurement"] == "cpustat")
        |> last()
        |> group()
        |> sum()
    '''
    query_result = query_api.query(query=cpus_query)
    for table in query_result:
        for record in table.records:
            result["cpu"] = record.values.get('_value', 0)

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
    '''
    query_result = query_api.query(query=cpu_query)
    for table in query_result:
        for record in table.records:
            result["cpu usage"] = record.values.get('_value', 0)

    # maxmem data
    maxmem_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "memory")
        |> filter(fn: (r) => r["_field"] == "memtotal")
        |> last()
        |> group()
        |> sum()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        |> yield(name: "maxmem_total")
    '''
    query_result = query_api.query(query=maxmem_query)
    for table in query_result:
        for record in table.records:
            result["mem"] = record.values.get('_value', 0)

    # mem usage data
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
    '''
    query_result = query_api.query(query=mem_query)
    for table in query_result:
        for record in table.records:
            result["mem usage"] = record.values.get('_value', 0)

    # storage
    storage_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "total")
        |> filter(fn: (r) => r["host"] == "local")
        |> last()
        |> group()
        |> sum(column: "_value")
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''
    query_result = query_api.query(query=storage_query)
    for table in query_result:
        for record in table.records:
            result["storage"] = record.values.get('_value', 0)

    # storage usage
    storage_used_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "used")
        |> filter(fn: (r) => r["host"] == "local")
        |> last()
        |> group()
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=storage_used_query)
    for table in query_result:
        for record in table.records:
            result["storage usage"] = record.values.get('_value', 0)

    # netin data
    netin_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group()
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=netin_query)
    for table in query_result:
        for record in table.records:
            result["netin"] = record.values.get('_value', 0)


    # netout data
    netout_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group()
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=netout_query)
    for table in query_result:
        for record in table.records:
            result["netout"] = record.values.get('_value', 0)

    # uptime
    result["uptime"] = "none"
    data.append(result)

    ################################ NODES ###############################
    nodes = []
    results = []

    # vm number
    vm_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => r["object"] == "qemu")
        |> distinct(column: "vmid")
        |> count()
        |> group(columns: ["nodename"])
        |> sum()
    '''
    query_result = query_api.query(query=vm_query)
    for table in query_result:
        for record in table.records:
            nodename = record.values.get('nodename')
            value = record.values.get('_value', 0)
            if nodename not in nodes:    # node is not included yet in the list
                nodes.append(nodename)
                result = {"type": "node", "name": nodename, "nodename": nodename, "class": "none", "vmid": -1,
                        "vm number": value, "lxc number": 0,
                        "cpu": 0, "cpu usage": 0.0,
                        "mem": 0, "mem usage": 0.0,
                        "storage": 0.0, "storage usage": 0.0,
                        "netin": 0.0, "netout": 0.0,
                        "uptime": "none"}
                results.append(result)

    # lxc num
    lxc_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => r["object"] == "lxc")
        |> distinct(column: "vmid")
        |> count()
        |> group(columns: ["nodename"])
        |> sum()
    '''
    query_result = query_api.query(query=lxc_query)
    process_pernode_query_result(results, query_result, "lxc number")

    # cpu cores
    cpus_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "cpustat")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> last()
        |> rename(columns: {{host: "nodename"}})
    '''
    query_result = query_api.query(query=cpus_query)
    process_pernode_query_result(results, query_result, "cpu")

    # cpu usage
    cpu_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "cpustat")
        |> filter(fn: (r) => r["_field"] == "cpu")
        |> group(columns: ["host"])
        |> mean()
        |> rename(columns: {{host: "nodename"}})
        |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
    '''
    query_result = query_api.query(query=cpu_query)
    process_pernode_query_result(results, query_result, "cpu usage")

    # total mem
    mem_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "memory")
        |> filter(fn: (r) => r["_field"] == "memtotal")
        |> last()
        |> rename(columns: {{host: "nodename"}})
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''
    query_result = query_api.query(query=mem_query)
    process_pernode_query_result(results, query_result, "mem")
    
    # mem usage
    mem_usage_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "memory")
        |> filter(fn: (r) => r["_field"] == "memused" or r["_field"] == "memtotal")
        |> group(columns: ["_field", "host"])
        |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with _value: (r.memused / r.memtotal) * 100.0 }}))
        |> keep(columns: ["host", "_value"])
        |> rename(columns: {{host: "nodename"}})
    '''
    query_result = query_api.query(query=mem_usage_query)
    process_pernode_query_result(results, query_result, "mem usage")

    # storage
    storage_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "total")
        |> filter(fn: (r) => r["host"] == "local")
        |> last()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''
    query_result = query_api.query(query=storage_query)
    process_pernode_query_result(results, query_result, "storage")

    # storage usage
    storage_used_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "used" or r["_field"] == "total")
        |> filter(fn: (r) => r["host"] == "local")
        |> group(columns: ["_field", "nodename"])
        |> pivot(rowKey: ["nodename"], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with _value: (r.used / r.total) * 100.0 }}))
    '''
    query_result = query_api.query(query=storage_used_query)
    process_pernode_query_result(results, query_result, "storage usage")

    # netin data
    netin_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group(columns: ["nodename"])
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=netin_query)
    process_pernode_query_result(results, query_result, "netin")

    # netout data
    netout_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> keep(columns: ["_time", "_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group(columns: ["nodename"])
        |> sum(column: "_value")
    '''
    query_result = query_api.query(query=netout_query)
    process_pernode_query_result(results, query_result, "netout")

    # add to data
    for r in results:
        data.append(r)

    ################################ SUBJECTS ###############################
    results = []
    raw_class_list = RequestUseCase.objects.all().exclude(
        request_use_case__icontains="Research"
    ).exclude(
        request_use_case__icontains="Test"
    ).exclude(
        request_use_case__icontains="Thesis"
    ).values_list('request_use_case', flat=True)

    class_list = []
    for entry in raw_class_list:
        classname = entry.split('_')[0]
        if classname not in class_list:
            class_list.append(classname)
            result = {"type": "subject", "name": classname, "nodename": "none", "class": classname, "vmid": -1,
                "vm number": 0, "lxc number": 0,
                "cpu": 0, "cpu usage": 0.0,
                "mem": 0, "mem usage": 0.0,
                "storage": 0.0, "storage usage": -1,
                "netin": 0.0, "netout": 0.0,
                "uptime": "none"}
            results.append(result)
            
            
    class_filters = ' or '.join([f'r["host"] =~ /{class_name}/' for class_name in class_list])
    class_map = ' '.join([f'if r["host"] =~ /{class_name}/ then "{class_name}" else' for class_name in class_list]) + ' "Unknown"'
        
    # get template
    template_hosts_ids = get_template_hosts_ids(start_date, end_date)
    excluded_vmids_str = '|'.join(map(str, template_hosts_ids))
    print(f"excluded_vmids_str: {excluded_vmids_str}")

    # vm number
    vm_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["object"] == "qemu")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> distinct(column: "vmid")
        |> count()
        |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> map(fn: (r) => ({{ _value: r.cpus, class: r.class }}))
        |> group(columns: ["class"])
        |> sum()
    '''
    query_result = query_api.query(query=vm_query)
    process_perclass_query_result(results, query_result, "vm number")

    # lxc number
    lxc_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["object"] == "lxc")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> distinct(column: "vmid")
        |> count()
        |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> map(fn: (r) => ({{ _value: r.cpus, class: r.class }}))
        |> group(columns: ["class"])
        |> sum()
    '''
    query_result = query_api.query(query=lxc_query)
    process_perclass_query_result(results, query_result, "lxc number")

    # cpu cores
    cpu_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> last()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> group(columns: ["class"])
        |> sum()
    '''    
    query_result = query_api.query(query=cpu_query)
    process_perclass_query_result(results, query_result, "cpu")

    # cpu usage
    cpu_usage_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpu")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> mean()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> group(columns: ["class"])
        |> sum()
        |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
    '''    
    query_result = query_api.query(query=cpu_usage_query)
    process_perclass_query_result(results, query_result, "cpu usage")

    # memory
    mem_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "maxmem")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> last()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> group(columns: ["class"])
        |> sum()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''    
    query_result = query_api.query(query=mem_query)
    process_perclass_query_result(results, query_result, "mem")


    # mem usage
    mem_usage_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> group(columns: ["host", "_field"])
        |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> group(columns: ["class", "_field"])
        |> mean()
    '''
    query_result = query_api.query(query=mem_usage_query)
    process_perclass_query_result(results, query_result, "mem usage")

    # storage 
    storage_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "maxdisk")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> last()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> group(columns: ["class"])
        |> sum()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''
    query_result = query_api.query(query=storage_query)
    process_perclass_query_result(results, query_result, "storage")  

    # netin data
    netin_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> keep(columns: ["_value", "class", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> keep(columns: ["_value", "class", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        class: r.class_first,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group(columns: ["class"])
        |> sum()
    ''' 
    query_result = query_api.query(query=netin_query)
    process_perclass_query_result(results, query_result, "netin")  

    # netout data
    netout_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> last()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> keep(columns: ["_value", "class", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> filter(fn: (r) => {class_filters})
        |> group(columns: ["nodename", "host", "object", "vmid"])
        |> first()
        |> map(fn: (r) => ({{ r with class: {class_map} }}))
        |> keep(columns: ["_value", "class", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        class: r.class_first,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
        |> group(columns: ["class"])
        |> sum()
    ''' 
    query_result = query_api.query(query=netout_query)
    process_perclass_query_result(results, query_result, "netout")  

    # add to data
    for r in results:
        data.append(r)

    ################################ INDIVIDUAL VMS/CONTAINERS ####################################
    
    results = []
    vms = []

    def check_vmname_class(vmname, class_list):
        for class_name in class_list:
            if class_name in vmname:
                return class_name
        return "unknown"

    # cpu cores
    cpus_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpus")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
    '''    
    query_result = query_api.query(query=cpus_query)
    for table in query_result:
        for record in table.records:
            vmname = record.values.get('host')
            nodename = record.values.get('nodename')
            # if vmname 中有包含 class_list 里面
            classname = check_vmname_class(vmname, class_list)
            vm_type = record.values.get('object')
            vmid = record.values.get('vmid')
            value = record.values.get('_value', 0)
            if (nodename, vm_type, vmid, vmname) not in vms:    
                vms.append((nodename, vm_type, vmid, vmname))
                result = {"type": "vm", "name": vmname, "nodename": nodename, "class": classname, "vmid": vmid, 
                        "vm number": 0, "lxc number": 0,
                        "cpu": value, "cpu usage": 0.0,
                        "mem": 0, "mem usage": 0.0,
                        "storage": 0.0, "storage usage": -1,
                        "netin": 0.0, "netout": 0.0,
                        "uptime": "none"}
                if vm_type == "qemu":
                    result["vm number"] = 1
                elif vm_type == "lxc":
                    result["lxc number"] = 1
                results.append(result)

    # cpu data
    cpu_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "cpu")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> mean()
        |> map(fn: (r) => ({{ r with _value: r._value * 100.0 }}))
    '''
    query_result = query_api.query(query=cpu_query)
    process_indiv_query_result(results, query_result, "cpu usage")

    # memory
    mem_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "maxmem")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''    
    query_result = query_api.query(query=mem_query)
    process_indiv_query_result(results, query_result, "mem")

    # mem usage
    mem_usage_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> group(columns: ["host", "vmid", "_field"])
        |> pivot(rowKey: [], columnKey: ["_field"], valueColumn: "_value")
        |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
        |> mean()
    '''
    query_result = query_api.query(query=mem_usage_query)
    process_indiv_query_result(results, query_result, "mem usage")

    # storage 
    storage_query = f'''
        from(bucket:"{bucket}")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "maxdisk")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
    '''
    query_result = query_api.query(query=storage_query)
    process_indiv_query_result(results, query_result, "storage")  

    # netin data
    netin_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netin")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> first()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
    ''' 
    query_result = query_api.query(query=netin_query)
    process_indiv_query_result(results, query_result, "netin")  

    # netout data
    netout_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "netout")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> first()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
    ''' 
    query_result = query_api.query(query=netout_query)
    process_indiv_query_result(results, query_result, "netout")  

    # uptime
    uptime_query = f'''
        last = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "uptime")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> last()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        first = from(bucket: "proxmox")
        |> range(start: {start_date}, stop: {end_date})
        |> filter(fn: (r) => r["_measurement"] == "system")
        |> filter(fn: (r) => r["_field"] == "uptime")
        |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
        |> first()
        |> keep(columns: ["_value", "nodename", "host", "object", "vmid"])

        join(
        tables: {{last: last, first: first}},
        on: ["nodename", "host", "object", "vmid"]
        )
        |> map(fn: (r) => ({{
        _time: r._time_last,
        nodename: r.nodename,
        host: r.host,
        object: r.object,
        vmid: r.vmid,
        first_value: r._value_first,
        last_value: r._value_last,
        _value: r._value_last - r._value_first
        }}))
    ''' 
    query_result = query_api.query(query=uptime_query)
    process_indiv_query_result(results, query_result, "uptime")  


    # add to data
    for r in results:
        data.append(r)

    # process data
    for item in data:
        if 'cpu usage' in item:
            item['cpu usage'] = round(item['cpu usage'],2)
        if 'mem' in item:
            item['mem'] = round(item['mem'],2)
        if 'mem usage' in item:
            item['mem usage'] = round(item['mem usage'],2)
        if 'storage' in item:
            item['storage'] = round(item['storage'],2)
        if 'storage usage' in item:
            item['storage usage'] = round(item['storage usage'],2)
        if 'netin' in item:
            item['netin'] = round(item['netin'] / 1024, 2)
        if 'netout' in item:
            item['netout'] = round(item['netout'] / 1024, 2)

    # CONSOLIDATE RESULT 
    output = {}
    if (len(data) > 0) :
        output["code"] = 0
    else:
        output["code"] = -1

    output["count"] = len(data)
    output["data"] = data
    
    return JsonResponse(output)



def graphdata(request):

    # connect to influxdb
    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()


    output = {}
    data = []

    # get type, name, nodename, class, vmid, startdate and enddate
    type_received = request.GET.get('type', "system")
    type_received = "vm"
    name = request.GET.get('name', "system")
    nodename = request.GET.get('nodename', "none")
    subject = request.GET.get('class', "none")
    vmid = request.GET.get('vmid', "-1")

    # start_date_str = request.GET.get('start_date')
    # end_date_str = request.GET.get('end_date')
    start_date_str = request.GET.get('start_time')
    end_date_str = request.GET.get('end_time')
    window = get_time_window(start_date_str, end_date_str)

    start_date = parse_form_date(start_date_str, 1)
    end_date = parse_form_date(end_date_str, 0)

    
    print(f"window: {window}")
    
    result = defaultdict(dict)
    # determine the type -> system? node? class? indiv?
    if type_received == "system":
        
        
        # cpu cores
        cpus_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''   
        query_result = query_api.query(query=cpus_query)

        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["cpu"] += value


        # cpu usage
        cpu_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=cpu_usage_query)
        
        cpu_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}                
                if time not in cpu_usage_count:
                    cpu_usage_count[time] = 0
                result[time]["cpu usage"] += value
                cpu_usage_count[time] += 1

        # Calculate average CPU usage
        for time in result:
            if cpu_usage_count.get(time, 0) > 0:
                result[time]["cpu usage"] /= cpu_usage_count[time] 

        
        # mem
        mem_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memtotal")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=mem_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["mem"] += value

        # mem usage
        mem_usage_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memused" or r["_field"] == "memtotal")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> group(columns: ["_field", "host", "_time"])
            |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.memused / r.memtotal) * 100.0 }}))
        '''
        query_result = query_api.query(query=mem_usage_query)
        
        mem_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in mem_usage_count:
                    mem_usage_count[time] = 0
                result[time]["mem usage"] += value
                mem_usage_count[time] += 1

        # Calculate average memory usage
        for time in result:
            if mem_usage_count.get(time, 0) > 0:
                result[time]["mem usage"] /= mem_usage_count[time]

        # storage
        storage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "total")
            |> filter(fn: (r) => r["host"] == "local")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=storage_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["storage"] += value

        # storage usage
        storage_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "used" or r["_field"] == "total")
            |> filter(fn: (r) => r["host"] == "local")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
            |> group(columns: ["_field", "nodename", "_time"])
            |> pivot(rowKey: ["nodename"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.used / r.total) * 100.0 }}))
        '''
        query_result = query_api.query(query=storage_usage_query)

        storage_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in storage_usage_count:
                    storage_usage_count[time] = 0
                result[time]["storage usage"] += value
                storage_usage_count[time] += 1

        # Calculate average storage usage
        for time in result:
            if storage_usage_count.get(time, 0) > 0:
                result[time]["storage usage"] /= storage_usage_count[time]

        # netin
        netin_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netin_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netin"] += value

        # netout
        netout_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netout_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netout"] += value

        # Convert result to list and sort by time
        data = list(result.values())
        data.sort(key=lambda x: x['time'])
    elif type_received == "node":
        # nodename = "pve"
        
        # cpu cores
        cpus_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["host"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''   
        query_result = query_api.query(query=cpus_query)

        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["cpu"] += value
        # cpu usage
        cpu_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "cpustat")
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["host"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=cpu_usage_query)
        
        cpu_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}                
                if time not in cpu_usage_count:
                    cpu_usage_count[time] = 0
                result[time]["cpu usage"] += value
                cpu_usage_count[time] += 1

        # Calculate average CPU usage
        for time in result:
            if cpu_usage_count.get(time, 0) > 0:
                result[time]["cpu usage"] /= cpu_usage_count[time] 

        
        # mem
        mem_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memtotal")
            |> filter(fn: (r) => r["host"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=mem_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["mem"] += value

        # mem usage
        mem_usage_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "memory")
            |> filter(fn: (r) => r["_field"] == "memused" or r["_field"] == "memtotal")
            |> filter(fn: (r) => r["host"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> group(columns: ["_field", "host", "_time"])
            |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.memused / r.memtotal) * 100.0 }}))
        '''
        query_result = query_api.query(query=mem_usage_query)
        
        mem_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in mem_usage_count:
                    mem_usage_count[time] = 0
                result[time]["mem usage"] += value
                mem_usage_count[time] += 1

        # Calculate average memory usage
        for time in result:
            if mem_usage_count.get(time, 0) > 0:
                result[time]["mem usage"] /= mem_usage_count[time]

        # storage
        storage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "total")
            |> filter(fn: (r) => r["host"] == "local")
            |> filter(fn: (r) => r["nodename"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=storage_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["storage"] += value

        # storage usage
        storage_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "used" or r["_field"] == "total")
            |> filter(fn: (r) => r["host"] == "local")
            |> filter(fn: (r) => r["nodename"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
            |> group(columns: ["_field", "nodename", "_time"])
            |> pivot(rowKey: ["nodename"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.used / r.total) * 100.0 }}))
        '''
        query_result = query_api.query(query=storage_usage_query)

        storage_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in storage_usage_count:
                    storage_usage_count[time] = 0
                result[time]["storage usage"] += value
                storage_usage_count[time] += 1

        # Calculate average storage usage
        for time in result:
            if storage_usage_count.get(time, 0) > 0:
                result[time]["storage usage"] /= storage_usage_count[time]

        # netin
        netin_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> filter(fn: (r) => r["nodename"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netin_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netin"] += value

        # netout
        netout_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> filter(fn: (r) => r["nodename"] == "{nodename}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netout_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netout"] += value

        # Convert result to list and sort by time
        data = list(result.values())
        data.sort(key=lambda x: x['time'])

    elif type_received == "class":
        # subject = "CCINFOM"

        # get template
        template_hosts_ids = get_template_hosts_ids(start_date, end_date)
        excluded_vmids_str = '|'.join(map(str, template_hosts_ids))

        # cpu cores
        cpu_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''    
        query_result = query_api.query(query=cpu_query)
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["cpu"] += value


        # cpu usage
        cpu_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=cpu_usage_query)
        
        cpu_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}                
                if time not in cpu_usage_count:
                    cpu_usage_count[time] = 0
                result[time]["cpu usage"] += value
                cpu_usage_count[time] += 1

        # Calculate average CPU usage
        for time in result:
            if cpu_usage_count.get(time, 0) > 0:
                result[time]["cpu usage"] /= cpu_usage_count[time] 

        
        # mem
        mem_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxmem")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=mem_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["mem"] += value

        # mem usage
        mem_usage_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> group(columns: ["_field", "host", "_time"])
            |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
        '''
        query_result = query_api.query(query=mem_usage_query)
        
        mem_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in mem_usage_count:
                    mem_usage_count[time] = 0
                result[time]["mem usage"] += value
                mem_usage_count[time] += 1

        # Calculate average memory usage
        for time in result:
            if mem_usage_count.get(time, 0) > 0:
                result[time]["mem usage"] /= mem_usage_count[time]

        # storage
        storage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxdisk")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''
        query_result = query_api.query(query=storage_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["storage"] += value
                result[time]["storage usage"] = 0

        # netin
        netin_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netin_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netin"] += value

        # netout
        netout_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{subject}/)
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netout_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netout"] += value


        data = list(result.values())
        data.sort(key=lambda x: x['time'])

    elif type_received == "vm":
        # name = "Jade"
        # cpu cores
        cpu_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''    
        query_result = query_api.query(query=cpu_query)
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["cpu"] += value


        # cpu usage
        cpu_usage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpu")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=cpu_usage_query)
        
        cpu_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}                
                if time not in cpu_usage_count:
                    cpu_usage_count[time] = 0
                result[time]["cpu usage"] += value
                cpu_usage_count[time] += 1
        
        # Calculate average CPU usage
        for time in result:
            if cpu_usage_count.get(time, 0) > 0:
                result[time]["cpu usage"] /= cpu_usage_count[time] 


        # mem
        mem_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxmem")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        '''
        query_result = query_api.query(query=mem_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["mem"] += value

        # mem usage
        mem_usage_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "mem" or r["_field"] == "maxmem")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
            |> group(columns: ["_field", "host", "_time"])
            |> pivot(rowKey: ["host"], columnKey: ["_field"], valueColumn: "_value")
            |> map(fn: (r) => ({{ r with _value: (r.mem / r.maxmem) * 100.0 }}))
        '''
        query_result = query_api.query(query=mem_usage_query)
        
        mem_usage_count = {}
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                if time not in mem_usage_count:
                    mem_usage_count[time] = 0
                result[time]["mem usage"] += value
                mem_usage_count[time] += 1

        # Calculate average memory usage
        for time in result:
            if mem_usage_count.get(time, 0) > 0:
                result[time]["mem usage"] /= mem_usage_count[time]

        # storage
        storage_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxdisk")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''
        query_result = query_api.query(query=storage_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["storage"] += value
                result[time]["storage usage"] = 0

        # netin
        netin_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netin_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netin"] += value

        # netout
        netout_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> filter(fn: (r) => r["host"] == "{name}")
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        '''
        query_result = query_api.query(query=netout_query)
        
        for table in query_result:
            for record in table.records:
                time = record.values.get('_time')
                value = record.values.get('_value')
                
                if time not in result:
                    result[time] = {"time": time, "cpu": 0, "cpu usage": 0, "mem": 0, "mem usage": 0, 
                                    "storage": 0, "storage usage": 0, "netin": 0, "netout": 0}
                result[time]["netout"] += value


        data = list(result.values())
        data.sort(key=lambda x: x['time'])

    else:
        output["code"] = -1
        output["count"] = 0
        output["data"] = []
        return JsonResponse(output) 
    
    for item in data:
        if 'time' in item:
            item['time'] = convert_time_format(item['time'])

    output["code"] = 0
    output["count"] = len(data)
    output["name"] = name
    output["data"] = data

    return JsonResponse(output)
############################### Ticketing ###############################

def fetch_ticketing_report_data(form : TicketingReportForm):

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        use_cases = form.cleaned_data['use_case']
        class_course_search = form.cleaned_data['class_course_search']

        print(use_cases)

        data = VirtualMachines.objects.filter(
            request__requestusecase__request_use_case__in=use_cases,
            request__ongoing_date__range=(start_date, end_date),
        )
        
        if not data : print('empty')
        return data
    
    else:
        print(form.errors)

def generate_general_ticketing_report(raw_data):
    data = raw_data.aggregate(
        total_vms=Count('vm_id'),
        total_ram=Sum('ram'),
        total_cores=Sum('cores'),
        total_storage=Sum('storage'),
    )
    
    headers = [
        'Total VMs', 
        'Total Memory', 
        'Total Cores', 
        'Total Storage',
    ]

    return headers, data

def generate_detailed_ticketing_report(raw_data):
    data = raw_data
    
    headers = [
    ]

    return headers, data

def render_ticketing_report(request):

    context = {
        'form' : TicketingReportForm(),
    }

    if request.method == 'POST':
        form = TicketingReportForm(request.POST)

        raw_data = fetch_ticketing_report_data(form)
        
        if raw_data:

            headers, data = generate_general_ticketing_report(form)
    
    return render(request, 'reports/ticketing.html', context)

    
def download_general_ticketing_report(request):

    if request.method == 'POST':

        form = TicketingReportForm(request.POST)

        raw_data = fetch_ticketing_report_data(form)

        if raw_data:

            headers, data = generate_general_ticketing_report(form)

            return download_csv('general request report', headers, data)
    
    return redirect('reports:ticketing_report')

def download_detailed_ticketing_report(request):

    if request.method == 'POST':

        form = TicketingReportForm(request.POST)

        raw_data = fetch_ticketing_report_data(form)

        if raw_data:

            headers, data = generate_detailed_ticketing_report(form)

            return download_csv('general request report', headers, data)
    
    return redirect('reports:ticketing_report')
