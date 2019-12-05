$(function () {
    $('.js-sweetalert button').on('click', function () {
        var type = $(this).data('type');
        var id = $(this).val();
        var record = $(this).data('record');
        if (type === 'confirm') {
            showConfirmMessage(id, record);
        }
    });
});

function showConfirmMessage(id, record) {
    if (record == 'customer') {
        swal({
            title: "Are you sure?",
            text: "You will not be able to recover this Customer!",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Yes, delete it!",
            closeOnConfirm: false
        }, function () {
            // window.location = '/delete_product/' + String(id);
            // swal("Deleted!", "Your Product has been deleted.", "success");
    
            var form = document.createElement("form");
            form.method = "POST";
            form.action = "/delete_customer/" + String(id);
            document.body.appendChild(form);
            form.submit();
        });
    }
    else {
        swal({
            title: "Are you sure?",
            text: "You will not be able to recover this Product!",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Yes, delete it!",
            closeOnConfirm: false
        }, function () {
            // window.location = '/delete_product/' + String(id);
            // swal("Deleted!", "Your Product has been deleted.", "success");
    
            var form = document.createElement("form");
            form.method = "POST";
            form.action = "/delete_product/" + String(id);
            document.body.appendChild(form);
            form.submit();
        });
    }
    
}