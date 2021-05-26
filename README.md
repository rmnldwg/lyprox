# Lymph Interface

This web app is for clinitians who are faced with the task of electively defining clinical target volumes (CTV-N). It allows the user to view a database of detailed patterns of lymphatic involvements and contribute to it. Also, the database can be used for building probabilistic models that can predict risks of involvements based on diagnoses and various patient characterisitcs. For example, the work based on Bayesian networks by [(Pouymayou et al., 2019)](), or the work by [(Roman Ludwig et al., 2021)]() using hidden Markov models.

## Quickstart

First, clone the repository by entering

```
git clone https://github.com/rmnldwg/lymph-interface.git
```

in a terminal. Then - after entering username & password, ``cd`` into the newly created directory named ``lymph-interface``. Go one step deeper into a folder named ``lymph_interface`` and execute the following commands:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
