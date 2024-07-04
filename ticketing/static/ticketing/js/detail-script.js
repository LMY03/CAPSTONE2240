document.addEventListener("DOMContentLoaded", function () {
    // Get the paragraph element by its ID
    let dVm_countElements = document.querySelectorAll("[id^='vm_count']");
    let dCores = document.getElementById("cores").textContent || document.getElementById("cores").innerText;
    let dRam = document.getElementById("ram").textContent || document.getElementById("ram").innerText;;
    let dStorage = document.getElementById("storage").textContent || document.getElementById("storage").innerText;;

    const regex = /\d+(\.\d+)?/;


    let cores = parseInt(dCores.match(regex)[0]);
    let ram = parseInt(dRam.match(regex)[0]);
    let storage = parseFloat(dStorage.match(regex)[0]);
    let total_vm_count = 0;
    if (section_count != 0) {
        dVm_countElements.forEach(element => {
            total_vm_count += parseInt(element.textContent.match(regex)[0]);
            console.log(parseInt(element.textContent.match(regex)[0]));
        });
    } else {
        total_vm_count = parseInt(dVm_countElements[0].textContent.match(regex)[0])
    }


    let acceptButton = document.getElementById("accept_button");
    console.log(total_vm_count, section_count);

    acceptButton.addEventListener("click", function () {
        let tCores = document.getElementById("totalCores");
        tCores.innerHTML = "<strong>Total Cores: </strong>" + String(cores * total_vm_count);
        let tRam = document.getElementById("totalRam");
        tRam.innerHTML = "<strong>Total Ram: </strong>" + String(ram * total_vm_count) + "MB";
        let tStorage = document.getElementById("totalStorage");
        tStorage.innerHTML = "<strong>Total Storage: </strong>" + String(storage * total_vm_count) + " GB";
    });
});