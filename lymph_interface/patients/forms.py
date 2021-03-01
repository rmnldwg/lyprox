from django import forms
from django.conf import settings
from django.forms.widgets import NumberInput
from django.db import IntegrityError
from django.utils.translation import gettext as _

from .models import Patient, Tumor, Diagnose
from .utils import compute_hash

import numpy as np
from pathlib import Path
import pandas
import os



class PatientForm(forms.ModelForm):
    
    first_name = forms.CharField()
    last_name = forms.CharField()
    birthday = forms.DateField(widget=NumberInput(attrs={"type": "date"}))
    
    class Meta:
        model = Patient
        fields = ["gender", 
                  "diagnose_date", 
                  "alcohol_abuse", 
                  "nicotine_abuse", 
                  "hpv_status", 
                  "n_stage",
                  "m_stage"]
        widgets = {"diagnose_date": NumberInput(attrs={"type": "date"})}
        
        
    def save(self, commit=True):
        """Compute hashed ID and age from name, birthday and diagnose date."""
        patient = super(PatientForm, self).save(commit=False)

        patient.identifier = self.cleaned_data["identifier"]
        patient.age = self._compute_age()
        
        if commit:
            patient.save()
            
        return patient
    
    
    def clean(self):
        """Override superclass clean method to raise a ValidationError when a 
        duplicate identifier is found."""
        cleaned_data = super(PatientForm, self).clean()
        unique_identifier = self._get_identifier(cleaned_data)
        
        try:
            previous_patient = Patient.objects.get(identifier=unique_identifier)
            raise forms.ValidationError(_("Identifier already exists in "
                                          "database. Possible duplicate?"))
        except Patient.DoesNotExist: 
            cleaned_data["identifier"] = unique_identifier
            return cleaned_data
        
    
    def _compute_age(self):
        """Compute age of patient at diagnose/admission."""
        bd = self.cleaned_data["birthday"]
        dd = self.cleaned_data["diagnose_date"]
        age = dd.year - bd.year
        
        if (dd.month < bd.month) or (dd.month == bd.month and dd.day < bd.day):
            age -= 1
            
        return age
    
    
    def _get_identifier(self, cleaned_data):
        """Compute the (potentially hashed) identifier from fields that are of 
        provacy concern."""
        identifier = compute_hash(cleaned_data["first_name"], 
                                  cleaned_data["last_name"], 
                                  cleaned_data["birthday"])
        cleaned_data.pop("first_name")
        cleaned_data.pop("last_name")
        return identifier
        
        
        
class TumorForm(forms.ModelForm):
    class Meta:
        model = Tumor
        fields = ["t_stage",
                  "stage_prefix",
                  "location", 
                  "position",
                  "extension",
                  "size"]
        
        
    def save(self, pk, commit=True):
        """Save tumor to existing patient."""
        tumor = super(TumorForm, self).save(commit=False)
        tumor.patient = Patient.objects.get(pk=pk)
        
        if commit:
            tumor.save()
            
        return tumor
        
        
        
class DiagnoseForm(forms.ModelForm):
    class Meta:
        model = Diagnose
        fields = ["diagnose_date",
                  "modality",
                  "lnl_I",
                  "lnl_II",
                  "lnl_III",
                  "lnl_IV"]
        widgets = {"diagnose_date": NumberInput(attrs={"type": "date"})}
        
        
    def save(self, pk, commit=True):
        """Save diagnose to existing patient."""
        diagnose = super(DiagnoseForm, self).save(commit=False)
        diagnose.patient = Patient.objects.get(pk=pk)
        
        if commit:
            diagnose.save()
            
        return diagnose
    
    
    
class DataFileForm(forms.Form):
    data_file = forms.FileField()
    
    def clean(self):
        cleaned_data = super(DataFileForm, self).clean()
        
        suffix = cleaned_data["data_file"].name.split(".")[-1]
        if suffix != "csv":
            raise ValidationError(_("File must be of type CSV."))
        
        file_path = Path(getattr(settings, "FILE_UPLOAD_TEMP_DIR")).resolve() / "tmp.csv"
        
        dest = open(file_path, "wb")
        for chunk in cleaned_data["data_file"].chunks():
            dest.write(chunk)
        dest.close()
        
        try:
            data_frame = pandas.read_csv(file_path, header=[0,1,2], 
                                         skip_blank_lines=True)
        except:
            raise forms.ValidationError(_("pandas was unable to parse the " 
                                          "uploaded file. Make sure it is a "
                                          "valid CSV file with 3 header rows."))
            
        os.remove(file_path)
            
        cleaned_data["data_frame"] = data_frame
        return cleaned_data
