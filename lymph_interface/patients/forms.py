import datetime.datetime as dt

from django import forms
from .models import Patient, Tumor, Diagnose

class PatientForm(forms.ModelForm):
    
    first_name = forms.CharField()
    last_name = forms.CharField()
    birthday = forms.DateField()
    
    class Meta:
        model = Patient
        fields = ["gender", 
                  "diagnose_date", 
                  "alcohol_abuse", 
                  "nicotine_abuse", 
                  "hpv_status"]
        
    def save(self, commit=True):
        """Compute hashed ID and age from name, birthday and diagnose date."""
        patient = super(PatientForm, self).save(commit=False)
        patient.identifier = self.cleaned_data["first_name"]
        patient.age = self._compute_age()
        
        if commit:
            patient.save()
            
        return patient
    
    
    def _compute_age(self):
        """Compute age of patient at diagnose/admission."""
        bd = self.cleaned_data["birthday"]
        dd = self.cleaned_data["diagnose_date"]
        age = dd.year - bd.year
        
        if (dd.month < bd.month) or (dd.month == bd.month and dd.day < bd.day):
            age -= 1
            
        return age
        
        
        
class TumorForm(forms.ModelForm):
    class Meta:
        model = Tumor
        fields = ["location", 
                  "position",
                  "extension",
                  "size",
                  "t_stage",
                  "stage_prefix"]
        
        
        
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