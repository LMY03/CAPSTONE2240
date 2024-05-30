// Function to format date as YYYY-MM-DD
function formatDate(date) {
    const d = new Date(date);
    let month = '' + (d.getMonth() + 1);
    let day = '' + d.getDate();
    const year = d.getFullYear();

    if (month.length < 2)
        month = '0' + month;
    if (day.length < 2)
        day = '0' + day;

    return [year, month, day].join('-');
}

// Set the min and max dates
window.onload = function () {
    const today = new Date();
    const dateNeededMin = new Date(today);
    dateNeededMin.setDate(today.getDate() + 3); // 3 days from today

    const expirationDateMax = new Date(today);
    const expirationDateMin = new Date(today);
    expirationDateMax.setFullYear(today.getFullYear() + 1); // 1 year from today
    expirationDateMin.setMonth(today.getMonth() + 3);

    document.getElementById('date_needed').setAttribute('min', formatDate(dateNeededMin));
    document.getElementById('expiration_date').setAttribute('max', formatDate(expirationDateMax));
    document.getElementById('expiration_date').setAttribute('min', formatDate(expirationDateMin));
}
