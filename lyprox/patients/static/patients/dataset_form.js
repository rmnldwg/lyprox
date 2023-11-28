$("input[type=file]").change(function() {
    let filename = $(this)[0].files[0].name;
    $("#file-label-text").text(filename);
});

$("button[type=submit]").click(function() {
    $(this).addClass("is-loading");
});
