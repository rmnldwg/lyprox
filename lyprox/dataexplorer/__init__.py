"""The app that makes the data interactively explorable by the user.

As an overview, here is a general overview over how the data explorer works:

1. The user navigates to the data explorer, which sends a GET request to the
   `render_data_stats` view.
2. The view creates a `DataexplorerForm` instance with the data from the GET request
   (or using a POST request, in case the user changed some selections and hit the
   "Compute" button).
3. The view then calls `execute_query` with the cleaned form data. In this function,
   the selected dataset specifications are loaded from the SQLite database. Using
   these specs, the actual `pandas.DataFrame` is loaded from the GitHub repository
   or from the `joblib` cache.
4. The view then returns the `BaseStatistics.from_table` object to the frontend.
5. Lastly, the frontend JavaScript code updates the view with the new data.

We recommend you look at all the modules in this app in that order, too. That way you
will best understand the data explorer's functionality.
"""
