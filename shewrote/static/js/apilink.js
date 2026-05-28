(function() {
    // Gather maps using the field name taken from the container ID
    if("L" in window) {  // Leaflet must be loaded
        window.maps = {};
        L.Map.addInitHook(function () {
            window.maps[this._container.id.slice(3,-4)] = this;
        });
    }

    django.jQuery(document).ready(() => {
        // Set zoom for all maps
        if("L" in window) {  // Leaflet must be loaded
            for(const [fieldName, map] of Object.entries(window.maps)) {
                const map_textarea = django.jQuery('#id_'+fieldName);
                const form_id = map_textarea.parents('form')[0].id
                if(map_textarea.text() == '') {
                    // Creating
                    if(form_id.startsWith('country')) {
                        map.setZoom(4);
                    } else if(form_id.startsWith('place')) {
                        map.setZoom(6);
                    } else {
                        map.setZoom(7);
                    }
                } else {
                    // Editing
                    if(form_id.startsWith('country')) {
                        map.setZoom(5);
                    } else if(form_id.startsWith('place')) {
                        map.setZoom(9);
                    } else {
                        map.setZoom(13);
                    }
                }
            }
        }

        // Allow HTML in options
        django.jQuery('.django-select2-apilink').djangoSelect2({
            templateResult: (option) => { return django.jQuery(option.text) },
            templateSelection: (option) => { return django.jQuery(option.text) }
        });

        // Change API link
        django.jQuery('.django-select2-apilink').on('change', (e) => {
            // Show/hide the API block: link and fill button
            const fieldName = e.currentTarget.id.slice("id_".length);
            const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value;
            const link = django.jQuery('#apilink_'+fieldName);
            link.attr("href", link.attr("href_base")+id);
            django.jQuery('#api_block_'+fieldName)[0].style.display = id ? 'inline' : 'none';

            // Check whether an object exists given the Django model name and ID
            const api_duplicate_indicator = django.jQuery('#api_object_exists_'+fieldName);
            const django_model = api_duplicate_indicator.data('django-model');
            django.jQuery.ajax({
                url: "/object_exists_wikidata/"+django_model+"/"+id+"/",
                beforeSend: function() {
                    api_duplicate_indicator[0].style.display = 'none';
                },
                success: function(result) {
                    api_duplicate_indicator[0].style.display = result['exists'] == true ? 'inline' : 'none';
                }
            });
        });

        // Fill in button
        django.jQuery('.fill-button').on('click', (e) => {
            const elem = e.currentTarget;
            const original_elem_text = elem.innerText;
            const fieldName = elem.id.slice("fillbutton_".length);
            const fillFieldName = elem.getAttribute('data-fill-field-name');
            const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value;

            django.jQuery.ajax({
                url: "/fill_fields/"+fillFieldName+"/?api_id="+id,
                beforeSend: function() {
                    elem.innerText = 'Fetching data...';
                },
                success: function(result) {
                    django.jQuery.each(result, (fieldName, data) => {
                        const field = django.jQuery('#id_'+fieldName);
                        if (field.hasClass("select2-hidden-accessible")) {
                            if (field.find("option[value='" + data.id + "']").length) {
                                field.val(data.id).trigger('change');
                            } else {
                                // Create a DOM Option and pre-select by default
                                var newOption = new Option(data.text, data.id, true, true);
                                // Append it to the select
                                field.append(newOption).trigger('change');
                            }
                        } else {
                            field.val(data);
                        }
                    });
                },
                complete: function() {
                    elem.innerText = original_elem_text;
                }
            });
        });
    });
})();