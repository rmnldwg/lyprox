function syncSliderValue(element) {
    var name = element.attr('name');
    var value = element.val();
    var valuePercentDisplay = $(`#${name}-display`);
    valuePercentDisplay.text((100 * value).toFixed(0) + '%');
}

$(document).ready(function() {
    $("input[type=range]").each(function() {
        syncSliderValue($(this));
    });
});

$("input[type=range]").on('input', function() {
    syncSliderValue($(this));
});
