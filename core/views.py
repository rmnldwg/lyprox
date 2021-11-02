from django.shortcuts import render
from django.views import generic

def index(request):
    return render(request, "index.html", {})

def versions(request):
    context = {
        "versions": [
            {"title": "stable", "info": "this is fine"},
            {"title": "frozen", "info": "this is cool"},
        ]
    }
    return render(request, "versions.html", context)