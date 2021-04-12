$(document).ready(function () {
  $("input[name='can_deliver']").change(function (e) {
    var $checkbox = $(e.target);
    var $form = $checkbox.closest("form");
    var $timerange = $form.find(".dropoff-timerange");
    if (e.target.checked) $timerange.removeClass("d-none");
    else $timerange.addClass("d-none");
  });
});
