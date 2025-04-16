"""The app that makes the data interactively explorable by the user.

The data explorer manages the loading, querying, computation of statistics, and
visualization of the lymphatic progression data that we provide. Below we give a
rough overview over the order in which the various submodules are called when the user
interacts with the dashboard. To better understand the code and be able to modify it,
it probably makes sense to dive into the docs in the order they are listed below:

1. The user navigates to the data explorer, which sends a GET request to the
   `render_data_stats` view. If a user updates the selection in the data explorer's
   dashboard, a POST request is instead sent to the `update_data_stats` view that
   the uses `AJAX`_ to update the rendered HTML. This makes the interface a little
   less clunky, because the user does not have to wait for a full page reload.
   In terms of the logic, both views work nearly identically.
2. Both views create a `DataexplorerForm` instance with the data from the request data.
   The form validates the selections the unser made in the dashboard. Unless the
   validation fails, the form now has an attribute ``cleaned_data`` that contains
   query parameters in a standardized format.
3. The view then calls `execute_query` with this cleaned form data. In this function,
   the selected dataset specifications are loaded from the SQLite database. Using
   these specs, the actual `pandas.DataFrame` is loaded from the GitHub repository (if
   requested for the first time) or from the `joblib` cache (in all subsequent calls).
   It returns a filtered `pandas.DataFrame` that contains only the data that matches
   the user's selection.
4. The view then returns a dynamically created instance of the ``Statistics`` class
   (using the `BaseStatistics.from_table` classmethod). It is a `pydantic.BaseModel`
   that creates a set of statistics (like the count of patients with positive, negative,
   or unknown HPV status) from the filtered dataset. These statistics can then be
   serialized into e.g. JSON format and sent back to the frontend.
5. Lastly, the web app either assembles the HTML from the statistics and returns that
   to the user, or it updates the already loaded HTML with the new serialized stats in
   JSON format, depending on whether a GET or POST request was made.

.. _AJAX: https://en.wikipedia.org/wiki/Ajax_(programming)
"""
