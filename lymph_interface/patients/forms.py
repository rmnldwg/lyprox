from django import forms
from django.conf import settings
from django.forms.widgets import NumberInput
from django.db import IntegrityError
from django.utils.translation import gettext as _

from .models import Patient, Tumor, Diagnose, MODALITIES, LOCATIONS, SUBSITES, T_STAGES, LNLs
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

        patient.hash_value = self.cleaned_data["hash_value"]
        patient.age = self._compute_age()
        
        if commit:
            patient.save()
            
        return patient
    
    
    def clean(self):
        """Override superclass clean method to raise a ValidationError when a 
        duplicate identifier is found."""
        cleaned_data = super(PatientForm, self).clean()
        unique_hash = self._get_identifier(cleaned_data)
        
        try:
            previous_patient = Patient.objects.get(hash_value=unique_hash)
            raise forms.ValidationError(_("Identifier already exists in "
                                          "database. Possible duplicate?"))
        except Patient.DoesNotExist: 
            cleaned_data["hash_value"] = unique_hash
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
        """Compute the hashed undique identifier from fields that are of 
        provacy concern."""
        hash_value = compute_hash(cleaned_data["first_name"], 
                                  cleaned_data["last_name"], 
                                  cleaned_data["birthday"])
        cleaned_data.pop("first_name")
        cleaned_data.pop("last_name")
        return hash_value
        
        
        
class TumorForm(forms.ModelForm):
    class Meta:
        model = Tumor
        fields = ["t_stage",
                  "stage_prefix",
                  "subsite", 
                  "position",
                  "extension",
                  "size"]
        
        
    def save(self, pk, commit=True):
        """Save tumor to existing patient."""
        tumor = super(TumorForm, self).save(commit=False)
        tumor.patient = Patient.objects.get(pk=pk)
        
        # automatically extract location from subsite
        subsite_dict = dict(SUBSITES)
        location_list = [tpl[1] for tpl in LOCATIONS]
        
        for i, loc in enumerate(location_list):
            loc_subsites = [tpl[1] for tpl in subsite_dict[loc]]
            if tumor.get_subsite_display() in loc_subsites:
                tumor.location = i
        
        # update patient's T-stage to be the worst of all its tumors'
        if tumor.t_stage > tumor.patient.t_stage:
            tumor.patient.t_stage = tumor.t_stage 
            tumor.patient.save()
        
        if commit:
            tumor.save()
            
        return tumor
        
        
        
class DiagnoseForm(forms.ModelForm):
    class Meta:
        model = Diagnose
        fields = ["diagnose_date",
                  "modality",
                  "side",
                  ]
        for lnl in LNLs:
            fields.append(lnl)
            
        widgets = {"diagnose_date": NumberInput(attrs={"type": "date"})}
        
        
    def save(self, pk, commit=True):
        """Save diagnose to existing patient."""
        diagnose = super(DiagnoseForm, self).save(commit=False)
        diagnose.patient = Patient.objects.get(pk=pk)
        
        if diagnose.Ia or diagnose.Ib:
            diagnose.I = True
            
        if diagnose.IIa or diagnose.IIb:
            diagnose.II = True
        
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
                                         skip_blank_lines=True, infer_datetime_format=True)
        except:
            raise forms.ValidationError(_("pandas was unable to parse the " 
                                          "uploaded file. Make sure it is a "
                                          "valid CSV file with 3 header rows."))
            
        os.remove(file_path)
            
        cleaned_data["data_frame"] = data_frame
        return cleaned_data



class DashboardForm(forms.Form):
    modality_checkboxes = forms.MultipleChoiceField(
        required=False, 
        widget=forms.CheckboxSelectMultiple, 
        choices=MODALITIES,
    )
    modality_combine = forms.ChoiceField(
        choices=[("AND", "AND"), 
                 ("OR", "OR"), 
                 ("XOR", "XOR")],
        label="Combine")
    
    
    nicotine_abuse = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(True, "add"),
                 (None, "not_interested"),
                 (False, "remove")]
    )
    hpv_status = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(True, "add"),
                 (None, "not_interested"),
                 (False, "remove")]
    )
    neck_dissection = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(True, "add"),
                 (None, "not_interested"),
                 (False, "remove")]
    )
    
    
    subsite_radiobuttons = forms.ChoiceField(
        choices=[("C01.9", "base of tongue, nos"),
                 ("C09.9", "tonsil, nos"), 
                 ("rest" , "other and/or multiple")],
        widget=forms.RadioSelect
    )
    tstage_checkboxes = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=T_STAGES,
    )
    central = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(True, "add"),
                 (None, "not_interested"),
                 (False, "remove")]
    )
    midline_extension = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(True, "add"),
                 (None, "not_interested"),
                 (False, "remove")]
    )
