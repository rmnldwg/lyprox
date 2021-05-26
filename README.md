# Lymph Interface

This web app is for clinitians who are faced with the task of electively defining clinical target volumes (CTV-N). It allows the user to view a database of detailed patterns of lymphatic involvements and contribute to it. Also, the database can be used for building probabilistic models that can predict risks of involvements based on diagnoses and various patient characterisitcs. For example, the work based on Bayesian networks by [(Pouymayou et al., 2019)](), or the work by [(Roman Ludwig et al., 2021)]() using hidden Markov models.

## Installing prerequisites

In order to start the interface's server, you need to have [django](https://www.djangoproject.com/) installed. The easiest way to install django (or most python packages for that matter) is through [miniconda](https://docs.conda.io/en/latest/miniconda.html). Simply download & install the miniconda version for your OS (not the Python 2.7 version though) and afterwards, fire up a terminal to create a new environment:

```
conda create -n newenv python=3.9
```

You can of course give it any name you like instead of ``newenv``. After it has been created, activate the environment

```
conda activate newenv
```

and then install django

```
conda install -c anaconda django
```

## Downloading & running the interface

First, clone the repository by entering in a terminal:

```
git clone https://github.com/rmnldwg/lymph-interface.git
```

Then - after entering username & password, ``cd`` into the newly created directory named ``lymph-interface``. Go one step deeper into a folder named ``lymph_interface`` and execute the following commands:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Make sure the environment where you have django installed is active. You can check this by looking at the prefix of the current line in the terminal. It should be ``(newenv)``, not ``(base)``.