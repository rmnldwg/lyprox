/**
 * Handle the case when the user select a super-level involvement. E.g., when the '-'
 * is clicked on a super-level's three-way toggle button, all the sub-levels also need
 * to switch to '-'.
 *
 * @param {*} super_radio Radio button element that selects involvement status of super-level
 */
function superClickHandler(super_radio) {
  const radio_a = document.forms["dashboardform"].elements[super_radio.name + "a"];
  const radio_b = document.forms["dashboardform"].elements[super_radio.name + "b"];
  const a_val = radio_a.value;
  const b_val = radio_b.value;

  if (super_radio.value == "True") {
    if (a_val == "False" && b_val == "False") {
      radio_a.value = "";
      radio_b.value = "";
    }
  } else if (super_radio.value == "") {
    if (a_val == "True") {
      radio_a.value = "";
    }
    if (b_val == "True") {
      radio_b.value = "";
    }
    if (a_val == "False" && b_val == "False") {
      radio_a.value = "";
      radio_b.value = "";
    }
  } else if (super_radio.value == "False") {
    if (a_val == "True") {
      radio_a.value = "";
    }
    if (b_val == "True") {
      radio_b.value = "";
    }
  }
};

/**
 * Define what happens when a sub-level's involvement is changed. E.g., when sub-level
 * 'a' is set to '+', the super-level also needs to be set to '+'.
 *
 * @param {*} this_sub_radio Radiobutton element of a lymph node sub-level
 */
function subClickHandler(this_sub_radio) {
  const this_sub_name = this_sub_radio.name;
  const super_name = this_sub_name.slice(0, this_sub_name.length - 1)
  const super_radio = document.forms["dashboardform"].elements[super_name];
  let other_sub_name;

  if (this_sub_name.endsWith('a')) {
    other_sub_name = super_name + 'b';
  } else {
    other_sub_name = super_name + 'a';
  }

  const other_sub_radio = document.forms["dashboardform"].elements[other_sub_name];

  if (this_sub_radio.value == "True") {
    super_radio.value = "True";
  } else if (this_sub_radio.value == "False" && other_sub_radio.value == "False") {
    super_radio.value = "False"
  };
};

/**
 * Allow recomputation after the dashboard's status has been changed through an input.
 */
function changeHandler() {
  $("#compute").removeAttr("disabled");
}

$("#show-help-modal").click(function () {
  $("#help-modal").addClass("is-active");
});

$("#close-help-modal").click(function () {
  $("#help-modal").removeClass("is-active");
});

/**
 * Toggle all checkboxes in a checkbox group.
 * @param {string} name The name of the checkbox group to toggle.
 */
function toggleAll(name) {
  const checkboxes = document.getElementsByName(name);
  const checked = checkboxes[0].checked;
  for (let i = 0; i < checkboxes.length; i++) {
    checkboxes[i].checked = !checked;
  }
  changeHandler();
}

// Add the ability to submit the form via non-AJAX GET request to the server
$(document).keydown(function (event) {
  if (event.altKey && event.key == 'c') {
    console.log("Key registerted")
    $("[name=dashboardform]").submit();
  };
});

/**
 * Synchronize the value of a slider with its output element.
 *
 * @param {*} slider The slider element
 */
function syncSliderValue(slider) {
  const output = $('output[for="' + slider.attr('id') + '"]');
  output.val((100 * slider.val()).toFixed(0) + "%");
}

$("input[type=range]").on('input', function () {
  syncSliderValue($(this));
});

// Insert CSRF token into POST header before sending the request
$(document).ready(function () {
  $("input[type=range]").each(function () {
    syncSliderValue($(this));
  });

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

/**
 * Cast a string to a number or boolean if possible.
 *
 * @param {string} input A string that may be cast to a number or boolean.
 * @returns {string|number|boolean} A number, boolean, or the original string.
 */
function castString(input) {
  if (/^\d+$/.test(input)) {
    return Number(input);
  }

  if (input == "True") {
    return true;
  } else if (input == "False") {
    return false;
  }

  return input;
}

/**
 * Collect form data from all radio boxes and add it to the dictionary `data`.
 *
 * @param {*} data The dictionary to which the radio data will be added.
 */
function collectRadioData(data) {
  $("#dashboard-form *")
    .filter(isRadio)
    .filter(isChecked)
    .each(function () {
      let fieldName = $(this).attr("name");
      let rawValue = $(this).attr("value");

      data[fieldName] = castString(rawValue);
    });
}

/**
 * Collect form data from all checkboxes and add it to the dictionary `data`.
 *
 * @param {*} data The dictionary to which the checkbox data will be added.
 */
function collectCheckboxData(data) {
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
      }
    });
}

/**
 * Collect form data from all dropdowns and add it to the dictionary `data`.
 *
 * @param {*} data The dictionary to which the dropdown data will be added.
 */
function collectDropdownData(data) {
  $("#dashboard-form *")
    .filter(function () {
      return $(this).is("select");
    })
    .each(function () {
      let fieldName = $(this).attr("name");
      let rawValue = $(this).find("option:selected").attr("value");

      data[fieldName] = castString(rawValue);
    });
}

/**
 * Collect form data from all range sliders and add it to the dictionary `data`.
 *
 * @param {*} data The dictionary to which the range slider data will be added.
 */
function collectRangeSliderData(data) {
  $("#dashboard-form *")
    .filter(function () {
      return $(this).is("input[type=range]");
    })
    .each(function () {
      let fieldName = $(this).attr("name");
      let rawValue = $(this).val();

      data[fieldName] = castString(rawValue);
    });
}

/**
 * Collect form data from all hidden inputs and add it to the dictionary `data`.
 *
 * @param {*} data The dictionary to which the hidden input data will be added.
 */
function collectHiddenInputData(data) {
  $("#dashboard-form *")
    .filter(function () {
      return $(this).is("input[type=hidden]");
    })
    .each(function () {
      let fieldName = $(this).attr("name");
      let rawValue = $(this).val();

      data[fieldName] = castString(rawValue);
    });
}

/**
 * Collect data from all the fields in the form and return it as a JSON string.
 *
 * @returns A JSON string of the data collected from the form.
 */
function collectDataFromFields() {
  var data = {};

  collectRadioData(data);
  collectCheckboxData(data);
  collectDropdownData(data);
  collectRangeSliderData(data);
  collectHiddenInputData(data);

  var jsonData = JSON.stringify(data);
  console.log(data);
  return jsonData;
}

/**
 * Map the data-key field values "True", "False", and "" to true, false, null
 * respectively and return anything else unchanged.
 *
 * @param {string} strKey The 'data-key' value from the form.
 * @returns The value this maps to: true, false, null or the original value.
 */
function mapDataKey(strKey) {
  if (strKey == "True") {
    return true;
  } else if (strKey == "False") {
    return false;
  } else if (strKey == "None") {
    return null;
  };

  return strKey;
}

/**
 * Take the server response in JSON form and populate all `.stats` fields in the
 * dashboard with the values from the JSON response. Also, populate the tooltips.
 *
 * @param {object} response JSON response from the server
 */
function populateFields(response) {
  console.log(response);
  const totalNum = response.total;
  const type = response.type;

  function percent(value) {
    return 100 * value / totalNum;
  };

  function updateBarplotStyle(element, field) {
    const involved = response[field][true];
    const unknown = response[field][null];
    const side = field.split("_")[0] + "lateral";
    const lnl = field.split("_")[1];

    let newStyle = "";
    newStyle += "background-size: " + percent(involved) + "% 100%, ";
    newStyle += percent(involved) + percent(unknown) + "% 100%, 100% 100%;";
    $(element).attr("style", newStyle);

    if (type == "stats") {
      const newTooltip = (
        `${unknown} of ${totalNum} (${percent(unknown).toFixed(0)}%) `
        + `patients have unknown involvement in LNL ${lnl} ${side}.`
      );
      $(element).attr("data-tooltip", newTooltip);
    }
  };

  function updateBarplotLegend(element, field, key) {
    const fieldVal = response[field][key];
    const side = field.split("_")[0] + "lateral";
    const lnl = field.split("_")[1];

    const toggle = (key) ? "" : "do not ";

    if (type == "stats") {
      const newTooltip = (
        `${fieldVal} of ${totalNum} (${percent(fieldVal).toFixed(0)}%) `
        + `patients ${toggle}have metastases in LNL ${lnl} ${side}.`
      );
      $(element).attr("data-tooltip", newTooltip);
    }
  };

  $(".stats").each(function () {
    const field = $(this).data("statfield");
    const key = mapDataKey($(this).data("key"));
    const showPercent = $('input[name="show_percent"]:checked').val();
    let newValue;

    if (key === undefined) {
      newValue = response[field];
    } else if (key in response[field]) {
      newValue = response[field][key];
    } else {
      newValue = 0;
    };

    const isBarplot = $(this).hasClass("barplot");
    if (isBarplot) {updateBarplotStyle(this, field)};

    const isBarplotLegend = $(this).hasClass("barplot-legend");
    if (isBarplotLegend) {updateBarplotLegend(this, field, key)};

    if (type == "stats") {
      const isTotal = $(this).data("statfield") == "total";
      if (showPercent == "True" && !isTotal) {
        $(this).html(percent(newValue).toFixed(0) + "%");
      } else {
        if (newValue == 0) {
          $(this).html("");
        } else {
          $(this).html(newValue.toFixed(0));
        }
      };
    } else if (key !== null) {
      $(this).html(newValue.toFixed(0) + "%");
    } else {
      $(this).html("±" + newValue.toFixed(0) + "%");
    }
  });
};


/**
 * Assemble AJAX request.
 */
function createAJAXrequest() {
  console.log("Creating POST request...");

  $.ajax({
    url: "ajax/",
    type: "POST",
    data: collectDataFromFields(),
    dataType: "json",
    contentType: "application/json",
    success: function (response) {
      console.log("Success! Processing response.");
      populateFields(response);
    },
    error: function (response) {
      console.log(response.responseJSON.error);
    },
  });
};

/**
 * Use AJAX instead of normal form action to send request to server.
 *
 * @param {*} event
 */
function handleSubmit(event) {
  event.preventDefault();
  console.log("Form submission button clicked.");
  createAJAXrequest();
};

$("#compute").click(handleSubmit);
