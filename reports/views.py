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
from proxmox.models import VirtualMachines, VMTemplates

from CAPSTONE2240.utils import download_csv
from django.db.models import Avg, Max, F, ExpressionWrapper, fields, Case, When
from django.db.models.functions import Abs
from django.utils import timezone
from datetime import datetime
from .forms import TicketingReportForm

INFLUX_ADDRESS = config('INFLUX_ADDRESS')
token = config('INFLUX_TOKEN')
org = config('INFLUXDB_ORG')
bucket = config('INFLUXDB_BUCKET')
proxmox_password = config('PROXMOX_PASSWORD')

# Parse date to InfluxDB compatible
def parse_form_date(date_string):
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        adjusted_dt = dt - timedelta(hours=8)
        # if is_start:
        #     adjusted_dt = adjusted_dt - timedelta(hours=8)
        return adjusted_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")

# Get Report Page
def index(request):
    return render(request, 'reports/reports.html')

def system_report(request):
    return render(request, 'reports/reports_new.html', {'report_type': 'system'})

def subject_report(request):
    return render(request, 'reports/reports_new.html', {'report_type': 'subject'})

def vm_report(request):
    return render(request, 'reports/reports_new.html', {'report_type': 'vm'})

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

    result = query_api.query(query=query)

    template_hosts_ids = []
    for table in result:
        for record in table.records:
            template_hosts_ids.append(record.values["vmid"])

    influxdb_client.close()
    return template_hosts_ids

                

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
            subject = record.values.get('subject')
            value = record.values.get('_value', 0)
            for result in results:
                if result["subject"] == subject:
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

    if time_diff <= timedelta(minutes=120):
        return "1m"
    elif time_diff <= timedelta(minutes=240):
        return "15m"
    elif time_diff <= timedelta(days=1):
        return "30m"
    elif time_diff <= timedelta(days=2):
        return "1h"
    elif time_diff <= timedelta(days=5):
        return "3h"
    elif time_diff <= timedelta(days=60):
        return "1d"
    else:
        return "5d"

def convert_time_format(time_value):
    dt = None
    if isinstance(time_value, datetime):
        dt = time_value
    elif isinstance(time_value, (int, float)):
        dt = datetime.fromtimestamp(time_value / 1e9)
    elif isinstance(time_value, str):
        try:
            dt = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
        except ValueError:
            dt = None
    
    if dt:
        dt += timedelta(hours=8)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return str(time_value)
    

def formdata(request): 

    # connect to influxdb
    influxdb_client = InfluxDBClient(url=INFLUX_ADDRESS, token=token, org=org)
    query_api = influxdb_client.query_api()

    report_type = request.GET.get('type', 'system')
    start_time_str = request.GET.get('start_time')
    end_time_str = request.GET.get('end_time')

    start_date = parse_form_date(start_time_str)
    end_date = parse_form_date(end_time_str)

    # get template
    template_hosts_ids = get_template_hosts_ids(start_date, end_date)
    excluded_vmids_str = '|'.join(map(str, template_hosts_ids))

    raw_class_list = RequestUseCase.objects.all().exclude(
        request_use_case__icontains="Research"
    ).exclude(
        request_use_case__icontains="Test"
    ).exclude(
        request_use_case__icontains="Thesis"
    ).values_list('request_use_case', flat=True)

    class_list = list(set(entry.split('_')[0] for entry in raw_class_list))
    
    valid_classes = []
    
    for class_name in class_list:
        vm_lxc_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["object"] == "qemu" or r["object"] == "lxc")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> filter(fn: (r) => r["host"] =~ /{class_name}/)
            |> distinct(column: "vmid")
            |> count()
            |> group()
            |> sum()
        '''
        result = query_api.query(query=vm_lxc_query)
        for table in result:
            for record in table.records:
                value = record.values.get('_value', 0)
                if value > 0:
                    valid_classes.append(class_name)


    data = []
    ################################ SYSTEM ###############################
    if report_type == 'system':
        print("========= in form data - system ==========")
        result = {"type": "system", "name": "system", "nodename": "-", "subject": "-", "vmid": 0,
                            "vm number": 0, "lxc number": 0,
                            "cpu": 0, "cpu allocated": 0, "cpu usage": 0.0,
                            "mem": 0.0, "mem allocated": 0.0, "mem usage": 0.0,
                            "storage": 0.0, "storage allocated": 0.0, "storage usage": 0.0,
                            "netin": 0.0, "netout": 0.0,
                            "uptime": "-"}

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

        # cpu allocated
        cpu_allocated_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group()
            |> sum()
        '''    
        query_result = query_api.query(query=cpu_allocated_query)
        for table in query_result:
            for record in table.records:
                result["cpu allocated"] = record.values.get('_value', 0)

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


        # memory allocated
        mem_allocated_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxmem")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group()
            |> sum()
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''    
        query_result = query_api.query(query=mem_allocated_query)
        for table in query_result:
            for record in table.records:
                result["mem allocated"] = record.values.get('_value', 0)


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


        # storage allocated
        storage_allocated_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxdisk")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group()
            |> sum()
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''
        query_result = query_api.query(query=storage_allocated_query)
        for table in query_result:
            for record in table.records:
                result["storage allocated"] = record.values.get('_value', 0)


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
            |> group()
            |> mean(column: "_value")
        '''
        query_result = query_api.query(query=storage_used_query)
        for table in query_result:
            for record in table.records:
                result["storage usage"] = record.values.get('_value', 0)

        # netin data
        netin_query = f'''
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
            |> group()
            |> sum()
        '''
        query_result = query_api.query(query=netin_query)
        for table in query_result:
            for record in table.records:
                result["netin"] = record.values.get('_value', 0)


        # netout data
        netout_query = f'''
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
            |> group()
            |> sum()
        '''
        query_result = query_api.query(query=netout_query)
        for table in query_result:
            for record in table.records:
                result["netout"] = record.values.get('_value', 0)

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
                    result = {"type": "node", "name": nodename, "nodename": nodename, "subject": "-", "vmid": 0,
                            "vm number": value, "lxc number": 0,
                            "cpu": 0, "cpu allocated": 0, "cpu usage": 0.0,
                            "mem": 0, "mem allocated": 0.0, "mem usage": 0.0,
                            "storage": 0.0, "storage allocated": 0.0, "storage usage": 0.0,
                            "netin": 0.0, "netout": 0.0,
                            "uptime": "-"}
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

        # cpu allocated
        cpu_allocated_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "cpus")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group(columns: ["nodename"])
            |> sum()
        '''    
        query_result = query_api.query(query=cpu_allocated_query)
        process_pernode_query_result(results, query_result, "cpu allocated")

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

        # memory allocated
        mem_allocated_query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxmem")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group(columns: ["nodename"])
            |> sum()
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''    
        query_result = query_api.query(query=mem_allocated_query)
        process_pernode_query_result(results, query_result, "mem allocated")

        
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

        # storage allocated
        storage_allocated_query = f'''
            from(bucket:"{bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "maxdisk")
            |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
            |> last()
            |> group(columns: ["nodename"])
            |> sum()
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
        '''
        query_result = query_api.query(query=storage_allocated_query)
        process_pernode_query_result(results, query_result, "storage allocated")

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
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
            |> group(columns: ["nodename"])
            |> sum()
        '''
        query_result = query_api.query(query=netin_query)
        process_pernode_query_result(results, query_result, "netin")

        # netout data
        netout_query = f'''
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
            |> group(columns: ["nodename"])
            |> sum()
        '''
        query_result = query_api.query(query=netout_query)
        process_pernode_query_result(results, query_result, "netout")

        # add to data
        for r in results:
            data.append(r)

    ################################ SUBJECTS ###############################

    elif report_type == 'subject':
        results = []
        for classname in valid_classes:
            result = {"type": "subject", "name": classname, "nodename": "-", "subject": classname, "vmid": 0,
                "vm number": 0, "lxc number": 0,
                "cpu": 0, "cpu allocated": 0, "cpu usage": 0.0,
                "mem": 0, "mem usage": 0.0,
                "storage": 0.0, "storage usage": 0,
                "netin": 0.0, "netout": 0.0,
                "uptime": "-"}
            results.append(result)
                
        if len(valid_classes) > 0:
            class_filters = ' or '.join([f'r["host"] =~ /{class_name}/' for class_name in valid_classes])
            class_map = ' '.join([f'if r["host"] =~ /{class_name}/ then "{class_name}" else' for class_name in valid_classes]) + ' "-"'
            
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> map(fn: (r) => ({{ _value: r.cpus, subject: r.subject }}))
                |> group(columns: ["subject"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> map(fn: (r) => ({{ _value: r.cpus, subject: r.subject }}))
                |> group(columns: ["subject"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject", "_field"])
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
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
                |> sum()
                |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
            '''
            query_result = query_api.query(query=storage_query)
            process_perclass_query_result(results, query_result, "storage")  

            # netin data
            netin_query = f'''
                from(bucket: "proxmox")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => r["_field"] == "netin")
                |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
                |> filter(fn: (r) => {class_filters})
                |> increase()
                |> difference()
                |> map(fn: (r) => ({{
                    r with
                    _value: float(v: r._value) / 1024.0
                    }}))
                |> elapsed()
                |> map(fn: (r) => ({{
                    r with
                    _value: float(v: r._value) / float(v: r.elapsed)
                    }}))
                |> mean()
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
                |> sum()
            '''
            query_result = query_api.query(query=netin_query)
            process_perclass_query_result(results, query_result, "netin")  

            # netout data
            netout_query = f'''
                from(bucket: "proxmox")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r["_measurement"] == "system")
                |> filter(fn: (r) => r["_field"] == "netout")
                |> filter(fn: (r) => r["vmid"] !~ /^({excluded_vmids_str})$/)
                |> filter(fn: (r) => {class_filters})
                |> increase()
                |> difference()
                |> map(fn: (r) => ({{
                    r with
                    _value: float(v: r._value) / 1024.0
                    }}))
                |> elapsed()
                |> map(fn: (r) => ({{
                    r with
                    _value: float(v: r._value) / float(v: r.elapsed)
                    }}))
                |> mean()
                |> map(fn: (r) => ({{ r with subject: {class_map} }}))
                |> group(columns: ["subject"])
                |> sum()
            '''
            query_result = query_api.query(query=netout_query)
            process_perclass_query_result(results, query_result, "netout")  

            # add to data
            for r in results:
                data.append(r)

    ################################ INDIVIDUAL VMS/CONTAINERS ####################################
    elif report_type == 'vm':
        print("========= in form data - indiv vm ==========")
        results = []
        vms = []

        def check_vmname_class(vmname, valid_classes):
            for class_name in valid_classes:
                if class_name in vmname:
                    return class_name
            return "-"

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
                classname = check_vmname_class(vmname, valid_classes)
                vm_type = record.values.get('object')
                vmid = record.values.get('vmid')
                value = record.values.get('_value', 0)
                if (nodename, vm_type, vmid, vmname) not in vms:    
                    vms.append((nodename, vm_type, vmid, vmname))
                    result = {"type": "vm", "name": vmname, "nodename": nodename, "subject": classname, "vmid": vmid, 
                            "vm number": 0, "lxc number": 0,
                            "cpu": value, "cpu allocated": 0, "cpu usage": 0.0,
                            "mem": 0, "mem usage": 0.0,
                            "storage": 0.0, "storage usage": 0,
                            "netin": 0.0, "netout": 0.0,
                            "uptime": "-"}
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
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netin")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
        '''
        query_result = query_api.query(query=netin_query)
        process_indiv_query_result(results, query_result, "netin")  

        # netout data
        netout_query = f'''
            from(bucket: "proxmox")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "system")
            |> filter(fn: (r) => r["_field"] == "netout")
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> mean()
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
        if 'mem allocated' in item:
            item['mem allocated'] = round(item['mem allocated'],2)
        if 'mem usage' in item:
            item['mem usage'] = round(item['mem usage'],2)
        if 'storage' in item:
            item['storage'] = round(item['storage'],2)
        if 'storage allocated' in item:
            item['storage allocated'] = round(item['storage allocated'],2)
        if 'storage usage' in item:
            item['storage usage'] = round(item['storage usage'],2)
        if 'netin' in item:
            item['netin'] = round(item['netin'], 2)
        if 'netout' in item:
            item['netout'] = round(item['netout'], 2)

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
    name = request.GET.get('name', "system")
    nodename = request.GET.get('nodename', "-")
    subject = request.GET.get('subject', "-")
    vmid = request.GET.get('vmid', "0")
    start_date_str = request.GET.get('start_time')
    end_date_str = request.GET.get('end_time')

    window = get_time_window(start_date_str, end_date_str)
    start_date = parse_form_date(start_date_str)
    end_date = parse_form_date(end_date_str)

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
            |> map(fn: (r) => ({{ r with _value: (r._value * 100.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 /1024.0 / 1024.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 /1024.0 / 1024.0 ) }}))
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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
            |> map(fn: (r) => ({{ r with _value: (r._value * 100.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0 ) }}))
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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

    elif type_received == "subject":

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
            |> map(fn: (r) => ({{ r with _value: (r._value * 100.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0 ) }}))
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
            |> group(columns: ["_time"])
            |> sum()
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
            |> map(fn: (r) => ({{ r with _value: (r._value * 100.0 ) }}))
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
            |> map(fn: (r) => ({{ r with _value: (r._value / 1024.0 / 1024.0 / 1024.0) }}))
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
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
            |> increase()
            |> difference()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / 1024.0
                }}))
            |> elapsed()
            |> map(fn: (r) => ({{
                r with
                _value: float(v: r._value) / float(v: r.elapsed)
                }}))
            |> aggregateWindow(
                every: {window}, 
                fn: mean,
                createEmpty: false
            )
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


def generate_general_ticketing_report (request):
    data = request.POST
    start_date = timezone.make_aware(datetime.strptime(data['startdate'], '%Y-%m-%d'))
    end_date = timezone.make_aware(datetime.strptime(data['enddate'], '%Y-%m-%d'))
    request_entries = RequestEntry.objects.filter(request_date__range=[start_date, end_date])
    average_stats = request_entries.aggregate(
        avg_cores=Avg('cores'),
        avg_ram=Avg('ram')
    )
    template_stats = request_entries.select_related('template') \
    .values('template__vm_name') \
    .annotate(total=Count('template_id')) \
    .order_by('-total')

    requester_stats = request_entries.select_related('requester') \
    .values('requester__first_name', 'requester__last_name')\
    .annotate(total=Count('requester_id')) \
    .order_by('-total')

    
    total_request_has_internet = request_entries.filter(has_internet=True).count()
    total_other_config = request_entries.filter(other_config__isnull=False).count()

    request_use_cases = RequestUseCase.objects.filter(request__in = request_entries)
    distinct_request_entries = RequestUseCase.objects.filter(request__in=request_entries)\
                                .values('request_id', 'request_use_case')\
                                .annotate(max_id=Max('id'))\
                                .order_by('max_id')
    request_use_case_stat = request_use_cases.values('request_use_case')\
                            .annotate(total = Count('request_use_case'), vmCount = Sum('vm_count'))\
                            .order_by('-total')
    class_course_stat = {}
    overall_use_case_stat ={}
    vm_count_stat = {}
    use_cases = ['THESIS', 'RESEARCH', 'TEST']
    total_class_course = 0
    total_vm_count_class_course = 0
    for use_case_stat in request_use_case_stat:
        use_case = use_case_stat['request_use_case']
        total = use_case_stat['total']
        
        if use_case in use_cases:
            overall_use_case_stat[use_case] = total
            #vm_count_stat[use_case] = use_case_stat['vmCount']
        else:
            total_class_course = total_class_course + total
            total_vm_count_class_course = use_case_stat['vmCount'] + total_vm_count_class_course
            class_course_stat[use_case] = total
            vm_count_stat[use_case] = use_case_stat['vmCount']
            #vm_count_stat['CLASS COURSE'] = total_vm_count_class_course
            overall_use_case_stat['TOTAL SECTIONS'] = total_class_course

    total_times_requested = {}
    courses_total_times_request ={}
    for distinct_entry in distinct_request_entries:
        use_case = distinct_entry['request_use_case']
        
        if 'CLASS COURSE' not in total_times_requested:
            total_times_requested['CLASS COURSE'] = 0

        if use_case not in ['TEST', 'RESEARCH', 'THESIS']:
            total_times_requested['CLASS COURSE'] += 1
            courses_total_times_request[use_case] = courses_total_times_request.get(use_case, 0) + 1
        else:
            total_times_requested[use_case] = total_times_requested.get(use_case, 0) + 1
    
    total_recurring_tickets = request_entries.filter(expiration_date = '' or None).count()

    request_entries_not_recurring = request_entries.filter(expiration_date__isnull=False)\
                                    .annotate(
                                        due_date=Case(
                                            When(expired_date__isnull=True, then=F('expiration_date')),
                                            default=F('expired_date'),
                                        )
                                    ).values('request_date', 'expired_date', 'expiration_date', 'due_date')

    # Calculate the average turnover in days
    average_turnover = request_entries_not_recurring.aggregate(
        avg_turnover=Abs(Avg(ExpressionWrapper(
            F('due_date') - F('request_date'),
            output_field=fields.DurationField()
        )))
    )

    average_turnover_days = None
    if average_turnover['avg_turnover']:
        average_turnover_days = average_turnover['avg_turnover'].days if isinstance(average_turnover['avg_turnover'], timedelta) else None

    request_entries_accepted = request_entries.filter(ongoing_date__isnull = False)\
                                .annotate(
                                    accepted_turn_over = ExpressionWrapper(F('ongoing_date') - F('request_date'), output_field=fields.DurationField())
                                )
    average_accepted_turnover_days = None
    average_accepted_turnover = request_entries_accepted.aggregate(
        avg_turnover = Avg('accepted_turn_over')
    )

    if average_accepted_turnover['avg_turnover']:
        average_accepted_turnover_days = average_accepted_turnover['avg_turnover'].days if isinstance(average_accepted_turnover['avg_turnover'], timedelta) else None

    return JsonResponse({'status': 'success', 
                         'average_stats': average_stats, 
                         'template_stats': list(template_stats), 
                         'requester_stats': list(requester_stats), 
                         'total_has_internet': total_request_has_internet,
                         'total_other_config':total_other_config,
                         'sections_course_stat': class_course_stat,
                         'overall_use_case_stat':overall_use_case_stat,
                         'total_recurring_tickets': total_recurring_tickets, 
                         'vm_count_stat':vm_count_stat,
                         'total_times_requested': total_times_requested,
                         'courses_total_times_request': courses_total_times_request,
                         'average_turn_over_days_to_due_date': average_turnover_days,
                         'average_accepted_turnover': average_accepted_turnover_days}, content_type='application/json')



# def generate_general_ticketing_report(raw_data):
#     data = raw_data.aggregate(
#         total_vms=Count('vm_id'),
#         total_ram=Sum('ram'),
#         total_cores=Sum('cores'),
#         total_storage=Sum('storage'),
#     )
    
#     headers = [
#         'Total VMs', 
#         'Total Memory', 
#         'Total Cores', 
#         'Total Storage',
#     ]

#     return headers, data

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
