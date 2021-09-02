from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.views import generic

from .forms import UserForm, InstitutionForm
from .models import Institution