function submitForm(event) {
    event.preventDefault(); // Prevent default form submission

    var form = document.getElementById('start_vm_form');
    var formData = new FormData(form);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', form.action, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            var redirectUrl = response.redirect_url;

            // Open the URL in a new tab
            window.open(redirectUrl, '_blank');
        } else {
            alert('An error occurred!');
        }
    };
    xhr.send(formData);
}