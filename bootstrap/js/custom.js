jQuery(document).ready(function($) {

    $(".clickable-row").click(function() {

         var item = $(this).find(".nric_field")     // Gets a descendent with class="nr"
                       .text();
        $("#nric_num").val(item.trim());
        $("#hidden-form").submit();
        /*window.location.href = $(this).data("url"),
            {
              nric_num: $item
            }*/

        // $.post( "/listall", { nric_field: "123456"} );
    });
});