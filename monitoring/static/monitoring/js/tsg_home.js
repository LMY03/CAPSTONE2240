$(document).ready(function () {
    function init() {
        $.ajax({
            type: 'GET',
            url: 'monitoring/aggregateData/',
            data: {},
            datatype: 'json',
            sucess: function (response) {

            },
            error: function (response) {
                console.log(response);
            }
        })
    }

    init();
})