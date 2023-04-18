from django.contrib import admin

from .models import Dataset, Diagnose, Patient, Tumor

# Register your models here.
admin.site.register(Patient)
admin.site.register(Tumor)
admin.site.register(Diagnose)
admin.site.register(Dataset)
