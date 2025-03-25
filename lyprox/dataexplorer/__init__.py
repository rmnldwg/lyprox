"""The app that makes the data interactively explorable by the user.

What happens roughly in that order is that 1) at startup, Django loads the data
explorer via the `apps` module, which 2) also triggers the loading of all available
datasets via the `loader` module. 3) As soon as a user navigates to the data explorer
app, a GET request is delegated to the `views` module (by the `urls` module), which 4)
uses the `forms` module to build and render the dashboard with all its buttons and
checkboxes. 5) when the user selects some options and sends that back to the server for
querying, the `views` module initiates the validation and cleaning defined in the
`forms` module and 6) sends the cleaned data to the `query` module for filtering the
dataset. Finally, 7) statistics of the filtered data are computed (also by the `query`)
module and 8) are displayed in the dashboard.

We recommend you look at all the modules in this app in that order, too. That way you
will best understand the data explorer's functionality.
"""
