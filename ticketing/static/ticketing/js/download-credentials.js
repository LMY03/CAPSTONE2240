function clear_credential() {
    fetch("{% url 'ticketing:clear_credential' %}", {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    });
}
window.addEventListener('beforeunload', function (e) {
    if (!document.activeElement.href.includes('generate_txt')) clear_credential()
});