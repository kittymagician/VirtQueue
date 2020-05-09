$(document).ready(function() {
    $('#queue').DataTable({
        "order": [
            [3, "desc"]
        ]
    });
    $('.dataTables_length').addClass('bs-select');
});