"""
The `dataexplorer` app makes the data interactively explorable by the user.

It defines everything that is necessary to query and display the data we have on
lymphatic progression patterns in head and neck squamous cell carcinoma (HNSCC).

The main components of the `dataexplorer` app are:

- the `apps` module is required by Django to load the app. This contains only
  boilerplate code;
- the `forms` which defines what the user can query, and how some parts of the main
  dashboard are displayed;
- the `query` module which defines how the data is queried and filtered. It also
  provides a pydantic class `Statistics` to compute statistics from the queried data;
- the `views` module which defines the functions that orchestrate the querying and
  displaying of the data;
- the `loader` module which defines the `DataInterface` class. This is a singleton
  class, meaning that calling `DataInterface()` multiple times will will return a
  new object only the first time, and then return the same object every time after
  that. It provides a unified interface to load the available patient records;
- in the `subsites` module, we define the `Subsites` class, which is a collection of
  enums for different tumor locations and ICD-10 codes.
"""
