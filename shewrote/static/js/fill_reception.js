/**
 * When the 'is_same_as_work` select is changed, the info of the selected Work is retrieved
 * to fill the `title` and `date_of_reception` fields.
 */

document.addEventListener("DOMContentLoaded", function() {
    is_same_as_work_select = django.jQuery('#id_is_same_as_work');
    title_field = django.jQuery('#id_title');
    date_of_reception_field = django.jQuery('#id_date_of_reception');

    is_same_as_work_select.on('change', function() {
        current_work_id = is_same_as_work_select.find(":selected").val();
        if(current_work_id != '') {
            django.jQuery.ajax({
                url: work_info_url.replace(uuid_dummy, current_work_id),
                type: 'GET',
                dataType: 'json',
                success: (data) => {
                    console.log(data);
                    if(title_field.val() == '') {
                        title_field.val(data.title);
                    }
                    if(date_of_reception_field.val() == '') {
                        date_of_reception_field.val(data.date_of_publication);
                    }
                },
                error: (error) => {
                    console.log(error);
                }
            });
        }
    });
});
