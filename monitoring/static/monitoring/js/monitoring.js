$(document).ready(function () {

    var vmTable;
    var cpuWarning = new Array();
    var ramWarning = new Array();



    // This function changes the colors of the Number of active VMs Div based on the current usage and thresholds.
    function changeActiveVMDiv(activeVM, vmsLow, vmsMid, vmsHigh, vmsCrit) {
        if (activeVM > 0 && activeVM <= vmsLow) {
            $('div#totalVmCountDiv').css('background-color', 'rgb(0, 155, 0, 0.35');
            $('div#totalVmCountDiv').css('border', '2.5px solid rgb(77,192,77)');
        }
        else if (activeVM > vmsLow && activeVM <= vmsMid) {
            $('div#totalVmCountDiv').css('background-color', 'rgb(253, 223, 46, 0.51');
            $('div#totalVmCountDiv').css('border', '2.5px solid rgb(232,204,39)');
        }
        else if (activeVM > vmsMid && activeVM <= vmsHigh) {
            $('div#totalVmCountDiv').css('background-color', 'rgb(259, 155, 0, 0.5');
            $('div#totalVmCountDiv').css('border', '2.5px solid rgb(239,155,0)');
        }
        else if (activeVM > vmsHigh && activeVM <= vmsCrit) {
            $('div#totalVmCountDiv').css('background-color', 'rgb(204, 0, 0, 0.5');
            $('div#totalVmCountDiv').css('border', '2.5px solid rgb(204,0,0)');
        } else if (activeVM == 0) {
            $('div#totalVmCountDiv').css('background-color', '#FFFFFF');
            $('div#totalVmCountDiv').css('border', '');
        }
    }

    // This function changes the colors of the Number of LXCs Div based on the current usage and thresholds.
    function changeActiveLXCDiv(activeLXC, lxcLow, lxcMid, lxcHigh, lxcCrit) {
        if (activeLXC > 0 && activeLXC <= lxcLow) {
            $('div#totalLxcCountDiv').css('background-color', 'rgb(0, 155, 0, 0.35');
            $('div#totalLxcCountDiv').css('border', '2.5px solid rgb(77,192,77)');
        }
        else if (activeLXC > lxcLow && activeLXC <= lxcMid) {
            $('div#totalLxcCountDiv').css('background-color', 'rgb(253, 223, 46, 0.51');
            $('div#totalLxcCountDiv').css('border', '2.5px solid rgb(232,204,39)');
        }
        else if (activeLXC > lxcMid && activeLXC <= lxcHigh) {
            $('div#totalLxcCountDiv').css('background-color', 'rgb(259, 155, 0, 0.5');
            $('div#totalLxcCountDiv').css('border', '2.5px solid rgb(239,155,0)');
        }

        else if (activeLXC > lxcHigh && activeLXC <= lxcCrit) {
            $('div#totalLxcCountDiv').css('background-color', 'rgb(204, 0, 0, 0.5');
            $('div#totalLxcCountDiv').css('border', '2.5px solid rgb(204,0,0)');
        } else if (activeLXC == 0) {
            $('div#totalLxcCountDiv').css('background-color', '#FFFFFF');
            $('div#totalLxcCountDiv').css('border', '');
        }
    }

    // This function counts the number of active VMs and LXCs.
    function runningCount(vmList, vmsLow, vmsMid, vmsHigh, vmsCrit, lxcLow, lxcMid, lxcHigh, lxcCrit) {
        var vmCount = 0
        var lxcCount = 0
        var vmActive = 0
        var lxcActive = 0

        for (i = 0; i < vmList.length; i++) {

            if (vmList[i].type == 'qemu') {
                vmCount++;

                if (vmList[i].uptime != 0)
                    vmActive++;
            } else if (vmList[i].type == 'lxc') {
                lxcCount++;

                if (vmList[i].uptime != 0)
                    lxcActive++;
            }

        }

        $('h1#vmCount').html(vmActive);
        $('h4#totalVm').html("out of " + vmCount);

        $('h1#lxcCount').html(lxcActive);
        $('h4#totalLxc').html("out of " + lxcCount);

        changeActiveVMDiv((vmActive / vmCount) * 100, vmsLow, vmsMid, vmsHigh, vmsCrit)
        changeActiveLXCDiv((lxcActive / lxcCount) * 100, lxcLow, lxcMid, lxcHigh, lxcCrit)
    }

    // This function changes the colors of the CPU Usage Div based on the current usage and thresholds.
    function changeCpuDiv(usedSwapNum, cpuLow, cpuMid, cpuHigh, cpuCrit) {
        if (usedSwapNum > 0 && usedSwapNum <= cpuLow) {
            $('div#serverCpuDiv').css('background-color', 'rgb(0, 155, 0, 0.35');
            $('div#serverCpuDiv').css('border', '2.5px solid rgb(77,192,77)');
        }
        else if (usedSwapNum > cpuLow && usedSwapNum <= cpuMid) {
            $('div#serverCpuDiv').css('background-color', 'rgb(253, 223, 46, 0.51');
            $('div#serverCpuDiv').css('border', '2.5px solid rgb(232,204,39)');
        }

        else if (usedSwapNum > cpuMid && usedSwapNum <= cpuHigh) {
            $('div#serverCpuDiv').css('background-color', 'rgb(259, 155, 0, 0.5)');
            $('div#serverCpuDiv').css('border', '2.5px solid rgb(239,155,0)');
        }
        else if (usedSwapNum > cpuHigh && usedSwapNum <= cpuCrit) {
            $('div#serverCpuDiv').css('background-color', 'rgb(204, 0, 0, 0.5');
            $('div#serverCpuDiv').css('border', '2.5px solid rgb(204,0,0)');
        }

    }

    // This function changes the colors of the Memory Usage Div based on the current usage and thresholds.
    function changeMemDiv(usedMemNum, totalMemNum, memLow, memMid, memHigh, memCrit) {
        var pct = (usedMemNum / totalMemNum) * 100

        if (pct > 0 && pct <= memLow) {
            $('div#usedMemDiv').css('background-color', 'rgb(0, 155, 0, 0.35)');
            $('div#usedMemDiv').css('border', '2.5px solid rgb(77,192,77)');
        }
        else if (pct > memLow && pct <= memMid) {
            $('div#usedMemDiv').css('background-color', 'rgb(253, 223, 46, 0.51');
            $('div#usedMemDiv').css('border', '2.5px solid rgb(232,204,39)');
        }

        else if (pct > memMid && pct <= memHigh) {
            $('div#usedMemDiv').css('background-color', 'rgb(259, 155, 0, 0.5');
            $('div#usedMemDiv').css('border', '2.5px solid rgb(239,155,0)');
        }
        else if (pct > memHigh && pct <= memHigh) {
            $('div#usedMemDiv').css('background-color', 'rgb(204, 0, 0, 0.5');
            $('div#usedMemDiv').css('border', '2.5px solid rgb(204,0,0)');
        }
    }

    // This function changes the colors of the Storage Div based on the current usage and thresholds.
    function changeStorageDiv(usedMemNum, stoLow, stoMid, stoHigh, stoCrit) {
        if (usedMemNum > 0 && usedMemNum <= stoLow) {
            $('div#localMemDiv').css('background-color', 'rgb(0, 155, 0, 0.35');
            $('div#localMemDiv').css('border', '2.5px solid rgb(77,192,77)');
        }
        else if (usedMemNum > stoLow && usedMemNum <= stoMid) {
            $('div#localMemDiv').css('background-color', 'rgb(253, 223, 46, 0.51');
            $('div#localMemDiv').css('border', '2.5px solid rgb(232,204,39)');
        }
        else if (usedMemNum > stoMid && usedMemNum <= stoHigh) {
            $('div#localMemDiv').css('background-color', 'rgb(259, 155, 0, 0.5');
            $('div#localMemDiv').css('border', '2.5px solid rgb(239,155,0)');
        }

        else if (usedMemNum > stoHigh && usedMemNum <= stoCrit) {
            $('div#localMemDiv').css('background-color', 'rgb(204, 0, 0, 0.5');
            $('div#localMemDiv').css('border', '2.5px solid rgb(204,0,0)');
        }
    }

    // This function updates the values per row inside the Virtual Machine table 
    // The function compares the ID of each machine in the vmList, if the ID is not found then it adds another row to the table
    function updateVmTable(vmList, rowNum, cpuLow, cpuMid, cpuHigh, cpuCrit, memLow, memMid, memHigh, memCrit, stoLow, stoMid, stoHigh, stoCrit) {
        var flag = 0;

        vmTable.rows().every(function () {

            if (this.data()[0] == vmList.id) {
                let vmInfo = [vmList.id, vmList.name, vmList.type, vmList.node];

                var disk = (vmList.maxdisk) / (1024 * 1024 * 1024)

                vmInfo.push(disk + "GB");

                var converted = (vmList.maxmem) / (1024 * 1024 * 1024);

                var cpu = (vmList.cpu * 100).toFixed(2)
                var mem = ((vmList.mem / vmList.maxmem) * 100).toFixed(2)

                if (cpu > cpuHigh)
                    cpuWarning.push([vmList.id, vmList.name])
                if (mem > memHigh)
                    ramWarning.push([vmList.id, vmList.name])

                vmInfo.push(mem + "%")
                vmInfo.push(converted + " GiB")

                vmInfo.push(cpu + "%")
                vmInfo.push(vmList.maxcpu + " CPUs")

                if (vmList.uptime == 0) {
                    var uptime = "inactive";
                    vmInfo.push(uptime);
                } else {
                    var seconds = vmList.uptime
                    var uptime = moment.duration(seconds, 'seconds');
                    vmInfo.push(uptime.format("hh:mm:ss"));
                }

                let network_in = (vmList.network_in / (1024 * 1024)).toFixed(2);
                let network_out = (vmList.network_out / (1024 * 1024)).toFixed(2);

                vmInfo.push(network_in + "MB");
                vmInfo.push(network_out + "MB");
                this.data(vmInfo);
                flag = 1;

                vmTable.draw();

                // // changes border and div color of the 'Disk Usage' cell in the row
                // if (disk > 0 && disk <= stoLow) {
                //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
                //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(77,192,77)');
                // } else if (disk > stoLow && disk <= stoMid) {
                //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
                //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(232,204,39)');
                // } else if (disk > stoMid && disk <= stoHigh) {
                //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
                //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(239,155,0)');
                // } else if (disk > stoHigh && disk <= stoCrit) {
                //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
                //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(204,0,0)');
                // } else if (disk == 0) {
                //     $(vmTable.cell(rowNum, 4).node()).css('background-color', '#FFFFFF');
                //     $(vmTable.cell(rowNum, 4).node()).css('border', '');
                // }

                // changes border and div color of the 'CPU Usage' cell in the row
                if (cpu > 0 && cpu <= cpuLow) {
                    $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
                    $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(77,192,77)');
                } else if (cpu > cpuLow && cpu <= cpuMid) {
                    $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
                    $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(232,204,39)');
                } else if (cpu > cpuMid && cpu <= cpuHigh) {
                    $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
                    $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(239,155,0)');
                } else if (cpu > cpuHigh && cpu <= cpuCrit) {
                    $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
                    $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(204,0,0)');
                } else if (cpu == 0) {
                    $(vmTable.cell(rowNum, 7).node()).css('background-color', '#FFFFFF');
                    $(vmTable.cell(rowNum, 7).node()).css('border', '');
                }

                // changes border and div color of the 'RAM Usage' cell in the row
                if (mem > 0 && mem <= memLow) {
                    $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
                    $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(77,192,77)');
                } else if (mem > memLow && mem <= memMid) {
                    $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
                    $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(232,204,39)');
                } else if (mem > memMid && mem <= memHigh) {
                    $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
                    $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(239,155,0)');
                } else if (mem > memHigh && mem <= memCrit) {
                    $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
                    $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(204,0,0)');
                } else if (mem == 0) {
                    $(vmTable.cell(rowNum, 5).node()).css('background-color', '#FFFFFF');
                    $(vmTable.cell(rowNum, 5).node()).css('border', '');
                }

                return;
            }
        })

        // if the VM ID is not found among the displayed machines in the table, a new row is created using the genVmTable() function
        if (!flag) {
            genVmTable(vmList, rowNum, cpuLow, cpuMid, cpuHigh, cpuCrit, memLow, memMid, memHigh, memCrit, stoLow, stoMid, stoHigh, stoCrit)
            vmTable.draw();
        }
    }

    function setData(serverCoreResultList, serverCpuResultList, cpuLow, cpuMid, cpuHigh, cpuCrit,
        usedMemResultList, totalMemoryResultList, memLow, memMid, memHigh, memCrit,
        localUsageResultList, totalStorageUsedResultList, stoLow, stoMid, stoHigh, stoCrit) {

        // CPU utilization
        var usedSwapNum = 0
        var count = 0;
        for (i = 0; i < serverCpuResultList.length; i++) {
            nodeData = serverCpuResultList[i].data;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                usedSwapNum += nodeData[j].cpu;
            }
        }
        if (count != 0) usedSwapNum /= count;


        // CPU Cores
        var coreNum = 0
        for (i = 0; i < serverCoreResultList.length; i++) {
            var temp = 0
            var count = 0;
            nodeData = serverCoreResultList[i].data;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                temp += nodeData[j].core;
            }
            if (count != 0) {
                temp /= count;
                coreNum += temp
            }
        }

        $('h1#usedSwap').html((usedSwapNum * 100).toFixed(2) + "%");
        $('h4#totalSwap').html("of " + coreNum.toFixed(2) + " CPU(s)");
        changeCpuDiv(usedSwapNum * 100, cpuLow, cpuMid, cpuHigh, cpuCrit);

        // Memory
        var usedMemNum = 0
        for (i = 0; i < usedMemResultList.length; i++) {
            var count = 0;
            var temp = 0;
            nodeData = usedMemResultList[i].data;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                temp += nodeData[j].memused;
            }
            if (count != 0) {
                temp /= count;
                usedMemNum += temp
            }
        }

        var totalMemNum = 0
        for (i = 0; i < totalMemoryResultList.length; i++) {
            nodeData = totalMemoryResultList[i].data;
            var count = 0;
            var temp = 0;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                temp += nodeData[j].memtotal;
            }
            if (count != 0) {
                temp /= count;
                totalMemNum += temp
            }
        }

        $('h1#usedMem').html(((usedMemNum / totalMemNum) * 100).toFixed(2) + "%")
        $('h4#totalMem').html("out of " + (totalMemNum).toFixed(2) + "GiB");

        changeMemDiv(usedMemNum, totalMemNum, memLow, memMid, memHigh, memCrit);



        // Storage
        var usedStorage = 0
        for (i = 0; i < localUsageResultList.length; i++) {
            nodeData = localUsageResultList[i].data;
            var count = 0;
            var temp = 0;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                temp += nodeData[j].used;
            }
            if (count != 0) {
                temp /= count;
                usedStorage += temp
            }
        }

        var localStorage = 0
        for (i = 0; i < totalStorageUsedResultList.length; i++) {
            nodeData = totalStorageUsedResultList[i].data;
            var count = 0;
            var temp = 0;
            for (j = 0; j < nodeData.length; j++) {
                count++;
                temp += nodeData[j].total;
            }
            if (count != 0) {
                temp /= count;
                localStorage += temp
            }
        }

        // Adds the total Storage value of every machine within the virtual environment
        $('h1#localMem').html((usedStorage /= (1024 * 1024 * 1024)).toFixed(2) + "GiB");
        $('h4#usedMem').html("of " + (localStorage / (1024 * 1024 * 1024)).toFixed(2) + "GiB");

        // changeStorageDiv(usedStorage, stoLow, stoMid, stoHigh, stoCrit)

    }

    // Function for updating the dashboard data
    function updateCharts() {
        // Ajax call for getting dashboard data from the backend
        $.ajax({
            type: 'GET',
            url: 'getdata',
            data: {
                // range: range,
                // group: group,
                // nodeFilter: nodeFilter
            },
            datatype: 'json',
            success: function (response) {
                // OVERVIEW OF METRICS
                // TODO: Fix this when all metrics are available
                setData(response.serverCoreResultList, response.serverCpuResultList, cpuLow, cpuMid, cpuHigh, cpuCrit,
                    response.usedMemResultList, response.totalMemoryResultList, memLow, memMid, memHigh, memCrit,
                    response.localUsageResultList, response.totalStorageUsedResultList, stoLow, stoMid, stoHigh, stoCrit)

                runningCount(response.vmList, vmsLow, vmsMid, vmsHigh, vmsCrit, lxcLow, lxcMid, lxcHigh, lxcCrit)


                // Updates the VM table values.
                for (i = 0; i < response.vmList.length; i++)
                    updateVmTable(response.vmList[i], i, cpuLow, cpuMid, cpuHigh, cpuCrit, memLow, memMid, memHigh, memCrit, stoLow, stoMid, stoHigh, stoCrit)

            },
            error: function (response) {
                console.log(response);
            }
        });

    }


    // This function is used as the row generator for the Virtual Machine Table 
    // The data is appended into the row in order to match the labels on the column headers
    function genVmTable(vmList, rowNum, cpuLow, cpuMid, cpuHigh, cpuCrit, memLow, memMid, memHigh, memCrit, stoLow, stoMid, stoHigh, stoCrit) {
        let vmInfo = [vmList.id, vmList.name, vmList.type, vmList.node]

        var disk = (vmList.maxdisk) / (1024 * 1024 * 1024)

        vmInfo.push(disk + "GB");

        var converted_max = (vmList.maxmem) / (1024 * 1024 * 1024);
        var converted_used = (vmList.mem) / (1024 * 1024 * 1024);

        var cpu = (vmList.cpu * 100).toFixed(2)
        var mem = ((converted_used / converted_max) * 100).toFixed(2)

        // if cpu/ram values reach critical levels of usage (based on preference), it is added to an array to be used in the warning Toast
        if (cpu > cpuHigh)
            cpuWarning.push([vmList.id, vmList.name])
        if (mem > memHigh)
            ramWarning.push([vmList.id, vmList.name])

        vmInfo.push(mem + "%")
        vmInfo.push(vmList.maxcpu + " GiB")

        vmInfo.push(cpu + "%")
        vmInfo.push(converted_max + " CPUs")

        if (vmList.uptime == 0) {
            var uptime = "inactive";
            vmInfo.push(uptime);
        } else {
            var seconds = vmList.uptime
            var uptime = moment.duration(seconds, 'seconds');
            vmInfo.push(uptime.format("hh:mm:ss"));
        }

        let network_in = (vmList.network_in / (1024 * 1024)).toFixed(2);
        let network_out = (vmList.network_out / (1024 * 1024)).toFixed(2);

        vmInfo.push(network_in + "MB");
        vmInfo.push(network_out + "MB");
        vmTable.row.add(vmInfo).draw();

        // // changes border and div color of the 'Disk Usage' cell in the row
        // if (disk > 0 && disk <= stoLow) {
        //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
        //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(77,192,77)');
        // } else if (disk > stoLow && disk <= stoMid) {
        //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
        //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(232,204,39)');
        // } else if (disk > stoMid && disk <= stoHigh) {
        //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
        //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(239,155,0)');
        // } else if (disk > stoHigh && disk <= stoCrit) {
        //     $(vmTable.cell(rowNum, 4).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
        //     $(vmTable.cell(rowNum, 4).node()).css('border', '2.5px solid rgb(204,0,0)');
        // } else if (disk == 0) {
        //     $(vmTable.cell(rowNum, 4).node()).css('background-color', '#FFFFFF');
        //     $(vmTable.cell(rowNum, 7).node()).css('border', '');
        // }

        // changes border and div color of the 'CPU Usage' cell in the row
        if (cpu > 0 && cpu <= cpuLow) {
            $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
            $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(77,192,77)');
        } else if (cpu > cpuLow && cpu <= cpuMid) {
            $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
            $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(232,204,39)');
        } else if (cpu > cpuMid && cpu <= cpuHigh) {
            $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
            $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(239,155,0)');
        } else if (cpu > cpuHigh && cpu <= cpuCrit) {
            $(vmTable.cell(rowNum, 7).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
            $(vmTable.cell(rowNum, 7).node()).css('border', '2.5px solid rgb(204,0,0)');
        } else if (cpu == 0) {
            $(vmTable.cell(rowNum, 7).node()).css('background-color', '#FFFFFF');
            $(vmTable.cell(rowNum, 7).node()).css('border', '');
        }

        // changes border and div color of the 'RAM Usage' cell in the row
        if (mem > 0 && mem <= memLow) {
            $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(0, 155, 0, 0.35');
            $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(77,192,77)');
        } else if (mem > memLow && mem <= memMid) {
            $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(253, 223, 46, 0.51)');
            $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(232,204,39)');
        } else if (mem > memMid && mem <= memHigh) {
            $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(259, 155, 0, 0.5)');
            $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(239,155,0)');
        } else if (mem > memHigh && mem <= memCrit) {
            $(vmTable.cell(rowNum, 5).node()).css('background-color', 'rgb(204, 0, 0, 0.5)');
            $(vmTable.cell(rowNum, 5).node()).css('border', '2.5px solid rgb(204,0,0)');
        } else if (mem == 0) {
            $(vmTable.cell(rowNum, 5).node()).css('background-color', '#FFFFFF');
            $(vmTable.cell(rowNum, 5).node()).css('border', '');
        }
    }


    // This function initializes the dashboard page
    function init() {
        // Ajax call to get the data from the backend.
        $.ajax({
            type: 'GET',
            url: 'getdata',
            data: {
            },
            datatype: 'json',
            success: function (response) {
                // Default settings -> might change based on the settings (threshold, implement later)
                cpuLow = 25
                cpuMid = 50
                cpuHigh = 75
                cpuCrit = 100
                memLow = 25
                memMid = 50
                memHigh = 75
                memCrit = 100
                stoLow = 25
                stoMid = 50
                stoHigh = 75
                stoCrit = 100
                vmsLow = 25
                vmsMid = 50
                vmsHigh = 75
                vmsCrit = 100
                lxcLow = 25
                lxcMid = 50
                lxcHigh = 75
                lxcCrit = 100

                // dashboard

                setData(response.serverCoreResultList, response.serverCpuResultList, cpuLow, cpuMid, cpuHigh, cpuCrit,
                    response.usedMemResultList, response.totalMemoryResultList, memLow, memMid, memHigh, memCrit,
                    response.localUsageResultList, response.totalStorageUsedResultList, stoLow, stoMid, stoHigh, stoCrit)

                runningCount(response.vmList, vmsLow, vmsMid, vmsHigh, vmsCrit, lxcLow, lxcMid, lxcHigh, lxcCrit);

                // Initializes the data table for the Virtual Machines and LXCs
                vmTable = $('table#VMtable').DataTable({
                    "pagingType": "simple_numbers",
                    "autoWidth": "true",
                    "responsive": "true",
                    "select": "true",
                    'columnDefs': [
                        { "type": "numeric", "targets": [0, 4, 6, 8, 10, 11] },
                        { "type": "percent", "targets": [5, 7] },
                        { className: "tdDiskUsage", "targets": [4] },
                        { className: "tdMemoryUsage", "targets": [5] },
                        { className: "tdCpuUsage", "targets": [6] },
                        { className: "tdUptime", type: "natural", "targets": [9] }
                    ]
                });

                // Generates the VM table for each item in the list of machines
                for (i = 0; i < response.vmList.length; i++) {
                    genVmTable(response.vmList[i], i, cpuLow, cpuMid, cpuHigh, cpuCrit, memLow, memMid, memHigh, memCrit, stoLow, stoMid, stoHigh, stoCrit)
                }

                //update charts every 8 seconds
                setInterval(updateCharts, 8000);

            },
            error: function (response) {
                console.log(response);
            }
        })


    }
    init();
})