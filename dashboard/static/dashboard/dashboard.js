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
		if (a_val == 1) {
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
	both_name = sub_name.slice(0, sub_name.length - 1)
	radio_both = document.forms["dashboardform"].elements[both_name];

	if (sub_name.slice(sub_name.length - 1, sub_name.length) === 'a') {
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

function changeHandler() {
	$("#compute").removeAttr("disabled");
}

$("#show-help-modal").click(function () {
	$("#help-modal").addClass("is-active");
});

$("#close-help-modal").click(function () {
	$("#help-modal").removeClass("is-active");
});

// Add the ability to submit the form via non-AJAX GET request to the server
$(document).keydown(function(event) {
	if (event.altKey && event.key == 'c') {
		console.log("Key registerted")
		$("[name=dashboardform]").submit();
	};
});

$(document).ready(function () {
	let csrftoken = $('input[name="csrfmiddlewaretoken"]').attr("value")
	$.ajaxSetup({
		beforeSend: function (xhr, settings) {
			if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
				console.log("Inserting CSRF Token")
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			};
		},
	});
});

/**
 * Check if the `element` is a radio box.
 * 
 * @param {*} index 
 * @param {*} element 
 * @returns `true` if `element` is a radio box and `false` otherwise.
 */
function isRadio(index, element) {
	return $(element).is("input[type=radio]");
};

/**
 * Check if the `element` is a checkbox box.
 * 
 * @param {*} index 
 * @param {*} element 
 * @returns `true` if `element` is a checkbox box and `false` otherwise.
 */
function isCheckbox(index, element) {
	return $(element).is("input[type=checkbox]");
};

/**
 * Check if the `element` is checked.
 * 
 * @param {*} index 
 * @param {*} element 
 * @returns `true` if `element` is checked and `false` otherwise.
 */
function isChecked(index, element) {
	return $(element).is(":checked");
};

function castString(input) {
	if (/^\d+$/.test(input)) {
		return Number(input);
	}

	if (input === "True" || input === "False") {
		return Boolean(input);
	}

	return input;
}

/**
 * Iterate through all checked input elements in the form and collect their values in
 * a dictionary.
 */
function collectDataFromFields() {
	var data = {};

	// Get all the radio boxes' values
	$("#dashboard-form *")
		.filter(isRadio)
		.filter(isChecked)
		.each(function () {
			let fieldName = $(this).attr("name");
			let rawValue = $(this).attr("value");

			data[fieldName] = castString(rawValue);
		});

	// Get the list of values for the checkbox options
	$("#dashboard-form *")
		.filter(isCheckbox)
		.filter(isChecked)
		.each(function () {
			let fieldName = $(this).attr("name");
			let rawValue = $(this).attr("value");

			if (fieldName in data) {
				data[fieldName].push(castString(rawValue));
			} else {
				data[fieldName] = [castString(rawValue)];
			};
		});

	// Get the selected values from dropdown menus (there's only one right now)
	$("#dashboard-form *")
		.filter(function () {
			return $(this).is("select");
		})
		.each(function () {
			let fieldName = $(this).attr("name");
			let rawValue = $(this).find("option:selected").attr("value");

			data[fieldName] = castString(rawValue);
		});

	jsonData = JSON.stringify(data)
	console.log(jsonData);
	return jsonData;
};

function populateFieldsWithResponse() {
	console.log("This should not happen yet.")
};

function createGET() {
	console.log("Creating POST request...");

	$.ajax({
		url: "ajax/",
		type: "POST",
		data: collectDataFromFields(),
		dataType: "json",
		contentType: "application/json",
		success: function (response) {
			console.log("SUCCESS");
		}
	});
};

function handleSubmit(event) {
	event.preventDefault();
	console.log("Form submission button clicked.");
	createGET();
};

$("#compute").click(handleSubmit);
