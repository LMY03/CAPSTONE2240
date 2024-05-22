document.addEventListener("DOMContentLoaded", function () {
    // Get the paragraph element by its ID
    let dVm_count = document.getElementById("vm_count").textContent || document.getElementById("vm_count").innerText;
    let dCores = document.getElementById("cores").textContent || document.getElementById("cores").innerText;
    let dRam = document.getElementById("ram").textContent || document.getElementById("ram").innerText;;
    let dStorage = document.getElementById("storage").textContent || document.getElementById("storage").innerText;;

    const regex = /\d+(\.\d+)?/;


    let cores = parseInt(dCores.match(regex)[0]);
    let ram = parseInt(dRam.match(regex)[0]);
    let storage = parseFloat(dStorage.match(regex)[0]);
    let total_vm_count = parseInt(dVm_count.match(regex)[0]);

    let acceptButton = document.getElementById("accept_button");
    console.log(cores, ram, storage);

    acceptButton.addEventListener("click", function () {
        let tCores = document.getElementById("totalCores");
        tCores.innerHTML = "<strong>Total Cores: </strong>" + String(cores * total_vm_count);
        let tRam = document.getElementById("totalRam");
        tRam.innerHTML = "<strong>Total Ram: </strong>" + String(ram * total_vm_count) + " GB";
        let tStorage = document.getElementById("totalStorage");
        tStorage.innerHTML = "<strong>Total Storage: </strong>" + String(storage * total_vm_count) + " GB";
    });
});