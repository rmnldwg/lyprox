$(document).ready(function() {
  $('input[type="range"]').each(function() {
      const slider = $(this);
      const output = $('output[for="' + slider.attr('id') + '"]');

      // Initialize the output value
      output.val((100 * slider.val()).toFixed(0) + "%");

      // Update the output value when the slider value changes
      slider.on('input', function() {
          output.val((100 * slider.val()).toFixed(0) + "%");
      });
  });
});
