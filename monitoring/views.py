import datetime
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from proxmoxer import ProxmoxAPI
from influxdb_client import InfluxDBClient, Point, WritePrecision
import csv
from io import StringIO
from decouple import config

token = config('INFLUX_TOKEN')
org = config('INFLUXDB_ORG')
bucket = config('INFLUXDB_BUCKET')
proxmox_password = config('PROXMOX_PASSWORD')

# Create your views here.
def index(request):
    proxmox = ProxmoxAPI('10.1.200.11', user='root@pam', password=proxmox_password, verify_ssl=False)
    nodes = proxmox.nodes.get()
    strNodes = []
    
    #Appends nodes in a list
    for node in nodes:
        strNodes.append(node['node'])
    return render(request, 'monitoring/monitoring.html', {'nodeList' : strNodes})

def getData(request):
    #Connection between Proxmox API and application
    proxmox = ProxmoxAPI('10.1.200.11', user='root@pam', password='cap2240', verify_ssl=False)
    client = InfluxDBClient(url="http://192.168.1.3:8086", token=token, org=org)

    #Get VM Info from Proxmox API
    vmids = proxmox.cluster.resources.get(type='vm')
    VMList= []
    
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
        VMList.append(VMDict)
    
    #Query to get all nodes being used
    query_api = client.query_api()
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


    # list declarations
    serverCoreResultList = []
    serverCpuResultList = []
    usedMemResultList = []
    totalMemoryResultList = []
    localUsageResultList = []
    totalStorageUsedResultList = []

    # loop through nodes
    for node in nodes:
        # add node filter: if node == request.GET['nodeFilter'] or request.GET['nodeFilter'] == 'All nodes':

        # serverCoreResultList -> Compute for total Cores
        core_flux_query = f'''
                                from(bucket: "{bucket}")
                                |> range(start: -5m)
                                |> filter(fn: (r) => r._measurement == "cpustat" and r._field == "cpus")
                                |> filter(fn: (r) => r.host == "{node}")
                                '''
        
        core_result = query_api.query(query=core_flux_query)
        serverCoreResult = {}
        serverCoreResult["node"] = node
        serverCoreResult["data"] = []
        for table in core_result:
            for record in table.records:
                serverCoreResult["data"].append({
                    "time": record.get_time(),
                    "core": record.get_value()
                })
        serverCoreResultList.append(serverCoreResult)


        # serverCpuResultList -> Compute for CPU utilization
        cpu_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -5m)
                            |> filter(fn: (r) => r._measurement == "cpustat")
                            |> filter(fn: (r) => r._field == "cpu")
                            |> filter(fn: (r) => r.host == "{node}")
                            |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        '''
        cpu_result = query_api.query(query=cpu_flux_query)

        serverCpuResult = {}
        serverCpuResult["node"] = node
        serverCpuResult["data"] = []
        for table in cpu_result:
            for record in table.records:
                serverCpuResult["data"].append({
                    "time": record.get_time(),
                    "cpu": record.get_value()
                })
        serverCpuResultList.append(serverCpuResult)
        
        # usedMemResultList
        mem_flux_query = f'''
                        from(bucket: "{bucket}")
                        |> range(start: -5m)
                        |> filter(fn: (r) => r._measurement == "memory")
                        |> filter(fn: (r) => r._field == "memused")
                        |> filter(fn: (r) => r.host == "{node}")
                        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        |> map(fn: (r) => ({{ r with _value: r._value / 1073741824.0 }}))  // To GB
                        '''
        mem_result = query_api.query(query=mem_flux_query)

        usedMemResult = {}
        usedMemResult["node"] = node
        usedMemResult["data"] = []
        for table in mem_result:
            for record in table.records:
                usedMemResult["data"].append({
                    "time": record.get_time(),
                    "memused": record.get_value()
                })

        usedMemResultList.append(usedMemResult)

        # totalMemoryResultList
        total_memory_flux_query = f'''
                        from(bucket: "{bucket}")
                        |> range(start: -5m)  
                        |> filter(fn: (r) => r._measurement == "memory")
                        |> filter(fn: (r) => r._field == "memtotal")
                        |> filter(fn: (r) => r.host == "{node}")
                        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        |> map(fn: (r) => ({{ r with _value: r._value / 1073741824.0 }}))  // To GB
                        '''
        total_memory_result = query_api.query(query=total_memory_flux_query)

        totalMemoryResult = {}
        totalMemoryResult["node"] = node
        totalMemoryResult["data"] = []
        for table in total_memory_result:
            for record in table.records:
                totalMemoryResult["data"].append({
                    "time": record.get_time(),
                    "memtotal": record.get_value()
                })

        totalMemoryResultList.append(totalMemoryResult)


        # localUsageResultList
        usage_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -5m)
                            |> filter(fn: (r) => r._measurement == "system")
                            |> filter(fn: (r) => r.host == "local")
                            |> filter(fn: (r) => r._field == "used")
                            |> filter(fn: (r) => r.nodename == "{node}")
                            |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
                            |> yield(name: "last")
                        '''
        usage_result = query_api.query(query=usage_flux_query)

        localUsageResult = {}
        localUsageResult["node"] = node
        localUsageResult["data"] = []
        for table in usage_result:
            for record in table.records:
                localUsageResult["data"].append({
                    "time": record.get_time(),
                    "used": record.get_value()
                })
        localUsageResultList.append(localUsageResult)

        # totalStorageUsedResultList
        storage_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -5m)
                            |> filter(fn: (r) => r._measurement == "system")
                            |> filter(fn: (r) => r.host == "local")
                            |> filter(fn: (r) => r._field == "total")
                            |> filter(fn: (r) => r.nodename == "{node}")
                            |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
                            |> yield(name: "last")
                        '''
        # 执行查询
        storage_result = query_api.query(query=storage_flux_query)

        # 封装结果
        totalStorageUsedResult = {}
        totalStorageUsedResult["node"] = node
        totalStorageUsedResult["data"] = []
        for table in storage_result:
            for record in table.records:
                totalStorageUsedResult["data"].append({
                    "time": record.get_time(),
                    "total": record.get_value()
                })
        totalStorageUsedResultList.append(totalStorageUsedResult)


        
    return JsonResponse({
        'serverCoreResultList': serverCoreResultList,
        'serverCpuResultList': serverCpuResultList,
        'usedMemResultList': usedMemResultList,
        'localUsageResultList': localUsageResultList, 
        'totalMemoryResultList': totalMemoryResultList,
        'totalStorageUsedResultList': totalStorageUsedResultList,
        'vmList': VMList
    })


def aggregatedData (request): 
    flux_query = f'''
                    from(bucket:"{bucket}")
                    |> range(start: -5m)
                    |> filter(fn: (r) => r._measurement == "system")
                    |> filter(fn: (r) => r.object == "nodes")
                    |> group(columns: ["host"])
                    |> distinct(column: "host")
                    '''
    
    client = InfluxDBClient(url="http://192.168.1.3:8086", token=token, org=org)

    query_api = client.query_api()
    result = query_api.query(query=flux_query)
    nodes = []
    for table in result:
        for record in table.records:
            nodes.append(record.values.get("host", ""))
    cores = []
    memory_free_list = []
    memory_used_list = []
    storage_list = []
    network_in_list = []
    network_out_list = []
    for node in nodes:
        coreFluxQuery= f'''
                    from(bucket: "{bucket}")
                        |> range(start: -30m)
                        |> filter(fn: (r) => r["_measurement"] == "cpustat")
                        |> filter(fn: (r) => r["object"] == "nodes")
                        |> filter(fn: (r) => r["_field"] == "cpu")
                        |> filter(fn: (r) => r["host"] == "{node}")
                        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        |> yield(name: "mean")
                    '''
        core_result = query_api.query(query=coreFluxQuery)
        
        for table in core_result:
            for record in table.records:
                cpu = {
                    'host': record['host'],
                    "time": record.get_time(),
                    'cpu': record.get_value()  
                }
                cores.append(cpu)

        memory_free_flux_query = f'''
                        from(bucket: "{bucket}")
                        |> range(start: -30m)  
                        |> filter(fn: (r) => r["_measurement"] == "memory")
                        |> filter(fn: (r) => r["_field"] == "memfree"  )
                        |> filter(fn: (r) => r["host"] == "{node}")
                        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        |> map(fn: (r) => ({{ r with _value: r._value / 1073741824.0 }}))
                        |> yield(name: "mean")
                          // To GB
                        '''
        
        memory_used_flux_query = f'''
                        from(bucket: "{bucket}")
                        |> range(start: -30m)  
                        |> filter(fn: (r) => r["_measurement"] == "memory")
                        |> filter(fn: (r) => r["_field"] == "memused")
                        |> filter(fn: (r) => r["host"] == "{node}")
                        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                        |> map(fn: (r) => ({{ r with _value: r._value / 1073741824.0 }})) 
                        |> yield(name: "mean")
                        
                        '''

        memory_free_result = query_api.query(query=memory_free_flux_query)
        memory_used_result = query_api.query(query=memory_used_flux_query)
    

        for table in memory_free_result:
            for record in table.records:
                memory = {
                    'host': record ['host'],
                    'time': record.get_time(),
                    'memory_free' : record.get_value()
                }

                memory_free_list.append(memory)

        for table in memory_used_result:
            for record in table.records:
                memory = {
                    'host': record ['host'],
                    'time': record.get_time(),
                    'memory_used' : record.get_value()
                }
                memory_used_list.append(memory)

        storage_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -30m)
                            |> filter(fn: (r) => r._measurement == "system")
                            |> filter(fn: (r) => r.host == "local")
                            |> filter(fn: (r) => r._field == "total")
                            |> filter(fn: (r) => r.nodename == "{node}")
                            |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                            |> map(fn: (r) => ({{ r with _value: r._value / 1073741824.0 }}))  // To GB
                            |> yield(name: "mean")
                        '''
        
        storage_result = query_api.query(query=storage_flux_query)

        for table in storage_result:
            for record in table.records:
                storage = {
                    'host': record['host'],
                    "time": record.get_time(),
                    'storage': record.get_value()
                }
                storage_list.append(storage)

        network_in_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -30m)
                            |> filter(fn: (r) => r._measurement == "nics")
                            |> filter(fn: (r) => r["_field"]== "netin")
                            |> filter(fn: (r) => r.nodename == "{node}")
                            |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                            |> map(fn: (r) => ({{ r with _value: r._value / 1048576.0 }})) //MB
                            |> yield(name: "mean")
                            '''
        
        network_out_flux_query = f'''
                            from(bucket: "{bucket}")
                            |> range(start: -30m)
                            |> filter(fn: (r) => r._measurement == "nics")
                            |> filter(fn: (r) => r["_field"] == "netout")
                            |> filter(fn: (r) => r.nodename == "{node}")
                            |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
                            |> map(fn: (r) => ({{ r with _value: r._value / 1048576.0 }})) //MB
                            |> yield(name: "mean")
                            '''
        try: 
            network_out_result = query_api.query(query= network_out_flux_query)
            network_in_result = query_api.query(query= network_in_flux_query)
            for table in network_in_result:
                for record in table.records:
                    network= {
                        'host' : record['host'],
                        'time' : record.get_time(),
                        'network_in' : record.get_value()
                    }
                    network_in_list.append(network)

            for table in network_out_result:
                for record in table.records:
                    network = {
                        'host' : record['host'],
                        'time' : record.get_time(),
                        'network_in' : record.get_value()                        
                    }
                    network_out_list.append(network)
        except Exception as e :
            print (e)
        
        
    return JsonResponse({
      'coresResultList' : cores,
      'memoryFreeResultList' : memory_free_list,
      'memoryUsedResultList' : memory_used_list,
      'storageResultList' : storage_list,
      'networkInResultList' : network_in_list,
      'networkOutResultList' : network_out_list
    })