$(document).ready(function () {
    $(".yaml-source").each(function () {
        var yaml = $(this).data("yaml");
        var yaml_formatted = prettier.format(yaml, {
            parser: "yaml",
            plugins: prettierPlugins,
        });
        $(this).find("code").text(yaml_formatted);
    });

    hljs.highlightAll();
});
