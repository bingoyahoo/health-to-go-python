/**
 * Created by Delvin on 30/8/2015.
 */

jQuery(document).ready(function($) {
    $(".clickable-row").click(function() {
        window.document.location = $(this).data("url");
    });
});