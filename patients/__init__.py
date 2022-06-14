"""
The `patients` app manages the database and its access. It allows the user
to create, edit and delete new entries in the database and ensures that it is
always consistent.

In short, there are four django models that make up the patient-related part
of the database:

1.  A dataset (`patients.models.Dataset`) of patients (no. 2 below). This model
    interfaces with the CSV table format of LyProX, decides which user can see
    which patients in the list and dashboard as well as ensures the integrity of
    the database. The latter means it e.g. notices if a CSV file that was used to
    batch-import a number of patients into the database has been changed after
    that import. Something like this would compromise the trustworthiness of the
    interface.

2.  The patient itself (`patients.models.Patient`), storing basic and
    demographic data about a patient with a squamous cell carcinoma in the head
    and neck region

3.  A squamous cell carcinoma (`patients.models.Tumor`). This model contains
    specific information about a patient's tumor. Tumors always belong to a
    patient.

4.  Diagnoses of the lymphatic system (`patients.models.Diagnose`). This model
    stores which diagnostic modality was used to diagnose the lymphatic
    involvement of the patient and which lymph node levels where diagnosed to
    be healthy, metastatic or unkown

The app also contains an methods for importing and exporting a database from
and to a CSV table. The format of CSV tables is what we chose to publish our
lymphatic progression patterns in.
"""
