function bothClickHandler(radio_both) {
    both_name = radio_both.name;
    sub_a_name = both_name + "a";
    sub_b_name = both_name + "b";

    radio_a = document.forms["dashboardform"].elements[sub_a_name];
    radio_b = document.forms["dashboardform"].elements[sub_b_name];
    a_val = radio_a.value;
    b_val = radio_b.value;

    if (radio_both.value == 1) {
        if (a_val == -1 && b_val == -1) {
            radio_a.value = 0;
            radio_b.value = 0;
        };
    } else if (radio_both.value == 0) {
        if (a_val == 1 ) {
            radio_a.value = 0;
        };
        if (b_val == 1) {
            radio_b.value = 0;
        };
        if (a_val == -1 && b_val == -1) {
            radio_a.value = 0;
            radio_b.value = 0;
        };
    } else if (radio_both.value == -1) {
        if (radio_a.value == 1) {
            radio_a.value = 0;
        };
        if (radio_b.value == 1) {
            radio_b.value = 0;
        };
    };
};

function subClickHandler(radio_sub) {
    sub_name = radio_sub.name;
    both_name = sub_name.slice(0, sub_name.length-1)
    radio_both = document.forms["dashboardform"].elements[both_name];

    if (sub_name.slice(sub_name.length-1, sub_name.length) === 'a') {
        other_sub_name = both_name + 'b';
    } else {
        other_sub_name = both_name + 'a';
    }

    radio_other_sub = document.forms["dashboardform"].elements[other_sub_name];

    if (radio_sub.value == 1) {
        radio_both.value = 1;
    } else if (radio_sub.value == -1 && radio_other_sub.value == -1) {
        radio_both.value = -1
    };
};

function modalityClickHandler(check_mod) {
    if (check_mod.value == 6 && check_mod.checked) {
        document.forms["dashboardform"].elements["id_modalities_0"].checked = true;
        document.forms["dashboardform"].elements["id_modalities_1"].checked = true;
        document.forms["dashboardform"].elements["id_modalities_2"].checked = true;
        document.forms["dashboardform"].elements["id_modalities_3"].checked = true;
    } else if (check_mod.value <= 4 && !check_mod.checked) {
        document.forms["dashboardform"].elements["id_modalities_6"].checked = false;
    }
    changeHandler();
}

function changeHandler() {
    $("#compute").removeAttr("disabled");
}

$("#show-help-modal").click(function () {
    $("#help-modal").addClass("is-active");
});

$("#close-help-modal").click(function () {
    $("#help-modal").removeClass("is-active");
});

document.onkeyup = function (e) {
    if (e.altKey && e.key == 'c') {
        $("[name=dashboardform]").submit();
    };
};