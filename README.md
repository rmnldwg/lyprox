# Lymph Interface

This web app is for clinitians who are faced with the task of electively defining clinical target volumes (CTV-N). It allows the user to view a database of detailed patterns of lymphatic involvements that was extracted mainly by Jean-Marc Hofmann and we will soon publish a paper on it. Also, the database can be used for building probabilistic models that can predict risks of involvements based on diagnoses and various patient characterisitcs. For example, the work based on Bayesian networks by [(Pouymayou et al., 2019)](https://iopscience.iop.org/article/10.1088/1361-6560/ab2a18/meta), or the work by [(Roman Ludwig et al., 2021)](https://www.nature.com/articles/s41598-021-91544-1) using hidden Markov models.

## Set up environment

When working with python, it is always recommended to set up a virtual environment. You can do this with [``pip``](https://pypi.org/project/pip/) or [Anaconda](https://www.anaconda.com/products/individual) (I'd recommend [miniconda](https://docs.conda.io/en/latest/miniconda.html), because most of the stuff in Anaconda won't be needed here or in general). 

Let's assume you went with miniconda, then - after you have successfully installed it = fire up a terminal and enter the following command to create a new environment with the latest version of python installed:

```
conda create -n yournewenvironment python=3.9 pip
```

where you can replace ``yournewenvironment`` with the name you want to give to your new environment.

Conda then tells you how to activate this environment, which is by typing

```
conda activate yournewenvironment
```

## Cloning the repo

Now it's time to get the repository. Enter in a terminal

```
git clone https://github.com/rmnldwg/lymph-interface.git
```

and provide your credentials when prompted. Afterwards, ``cd`` into ``lymph-interface``.

## Installing prerequisites

In order to start the interface's server, you need to have [django](https://www.djangoproject.com/) along with several other prerequisites installed. The repository comes with a ``requirements.txt`` file, which one can use to install everything that is necessary. While inside the ``lymph-interface`` folder, type

```
pip install -r requirements.txt
```

## Running the interface

Now you should be ready to execute the following commands:

```
python manage.py makemigrations
python manage.py migrate
```

This will prepare django's database. If that worked, it is finally time to launch the server locally:

```
python manage.py runserver
```

If everything goes according to plan, django will ouput a link to the locally hosted web server. It usually runs at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).