from django import forms
from django.forms.widgets import NumberInput
from django.db import IntegrityError
from django.utils.translation import gettext as _
from .models import Patient, Tumor, Diagnose

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
                  "hpv_status"]
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
        identifier = cleaned_data["first_name"]
        cleaned_data.pop("first_name")
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
                  "n_stage",
                  "m_stage",
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