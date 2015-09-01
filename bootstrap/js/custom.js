/**
 * Created by Delvin on 30/8/2015.
 */

jQuery(document).ready(function($) {

    $(".clickable-row").click(function() {

        window.document.location = $(this).data("url"),
            {
          nric_num: "S8888888A"
         }
    });
});
/*jQuery(document).ready(function($) {

    $(".clickable-row").click(function() {
$.post($(this).data("url"), {
    nric_num: "S8888888A"
    //selected_country_name: $('#id_country_name').val(),
    //selected_city_name: $('#id_city_name').val()
});
         });
});*/
