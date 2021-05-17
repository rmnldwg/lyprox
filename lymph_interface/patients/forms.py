from django import forms
from django.conf import settings
from django.forms.widgets import NumberInput
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .models import Patient, Tumor, Diagnose, MODALITIES, LOCATIONS, SUBSITES, T_STAGES, LNLs
from .utils import compute_hash

import numpy as np
from pathlib import Path
import pandas
import os



class PatientForm(forms.ModelForm):
    
    first_name = forms.CharField(
        widget=forms.widgets.TextInput(attrs={"class": "input"}))
    last_name = forms.CharField(
        widget=forms.widgets.TextInput(attrs={"class": "input"}))
    birthday = forms.DateField(widget=NumberInput(attrs={"class": "input", 
                                                         "type": "date"}))
    
    class Meta:
        model = Patient
        fields = ["gender", 
                  "diagnose_date", 
                  "alcohol_abuse", 
                  "nicotine_abuse", 
                  "hpv_status", 
                  "n_stage",
                  "m_stage"]
        widgets = {"gender": forms.Select(attrs={"class": "select"}),
                   "diagnose_date": NumberInput(attrs={"class": "input", 
                                                       "type": "date"}),
                   "alcohol_abuse": forms.Select(choices=[(True, "positive"),
                                                          (False, "negative"),
                                                          (None, "unknown")],
                                                 attrs={"class": "select"}),
                   "nicotine_abuse": forms.Select(choices=[(True, "positive"),
                                                           (False, "negative"),
                                                           (None, "unknown")],
                                                  attrs={"class": "select"}), 
                   "hpv_status": forms.Select(choices=[(True, "positive"),
                                                       (False, "negative"),
                                                       (None, "unknown")],
                                              attrs={"class": "select"}),
                   "n_stage": forms.Select(attrs={"class": "select"}),
                   "m_stage": forms.Select(attrs={"class": "select"})}
        
        
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
        widgets = {
            "t_stage": forms.Select(attrs={"class": "select"}),
            "stage_prefix": forms.Select(attrs={"class": "select"}),
            "subsite": forms.Select(attrs={"class": "select shorten"}),
            "position": forms.Select(attrs={"class": "select"}),
            "extension": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "size": forms.TextInput(attrs={"class": "input"}),
        }
        
        
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
                  "side",]
        
        widgets = {"diagnose_date": forms.NumberInput(attrs={"class": "input",
                                                             "type": "date"}),
                   "modality": forms.Select(attrs={"class": "select"}),
                   "side": forms.Select(attrs={"class": "select"})}
        
        for lnl in LNLs:
            fields.append(lnl)
            widgets[lnl] = forms.Select(choices=[(True, "pos"),
                                                 (False, "neg"),
                                                 (None, "???")],
                                        attrs={"class": "select"})
            

        
        
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
    data_file = forms.FileField(
        widget=forms.widgets.FileInput(attrs={"class": "file-input"})
    )
    
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



class ThreeWayToggle(forms.ChoiceField):
    """A toggle switch than can be in three different states: Positive/True, 
    unkown/None and negative/False."""
    
    def __init__(self, 
                 widget=None, 
                 attrs={"class": "radio is-hidden"},
                 choices=[( 1, "plus"),
                          ( 0, "ban"), 
                          (-1, "minus")],
                 initial=0,
                 required=False,
                 **kwargs):
        """Overwrite the defaults of the ChoiceField."""
        if widget is not None:
            super(ThreeWayToggle, self).__init__(
                widget=widget,
                choices=choices,
                initial=initial,
                required=required,
                **kwargs)
        else:
            super(ThreeWayToggle, self).__init__(
                widget=forms.RadioSelect(attrs=attrs),
                choices=choices,
                initial=initial,
                required=required,
                **kwargs)
    
    def to_python(self, value):
        """Cast the string to an integer."""
        if value not in ["", None]:
            return int(value)
        return 0



class DashboardForm(forms.Form):
    """Form for querying the database."""
    
    def __init__(self, *args, **kwargs):
        """Extend default initialization to create lots of fields for the 
        LNLs from a list."""
        super(DashboardForm, self).__init__(*args, **kwargs)
        for side in ["ipsi", "contra"]:
            for lnl in LNLs:
                if lnl in ['I', 'II']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": "bothClickHandler(this);"})
                elif lnl in ['Ia', 'Ib', 'IIa', 'IIb']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": "subClickHandler(this);"})
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()
           
                
    def clean(self):
        """Make sure LNLs I & II have correct values corresponding to their 
        sublevels a & b. Also convert tstages from list of str to list of int."""
        cleaned_data = super(DashboardForm, self).clean()
        
        for side in ["ipsi", "contra"]:
            for lnl in ["I", "II"]:
                a = cleaned_data[f"{side}_{lnl}a"]
                b = cleaned_data[f"{side}_{lnl}b"]
                
                # make sure data regarding sublevels is not conflicting
                if a * b == 1:
                    cleaned_data[f"{side}_{lnl}"] = a
                elif a * b == -1:
                    cleaned_data[f"{side}_{lnl}"] = 1
                elif a * b == 0:
                    if a + b == 1:
                        cleaned_data[f"{side}_{lnl}"] = 1
                    elif a + b == -1:
                        pass
                    elif a + b == 0:
                        pass
                    else:
                        raise ValidationError(f"Invalid values in LNL {lnl} {side}laterally.")
                else:
                    raise ValidationError(f"Invalid values in LNL {lnl} {side}laterally.")
                                    
        subsites = cleaned_data["subsites"]
        subsite_dict = {"base":   ["C01.9"], 
                        "tonsil": ["C09.0", "C09.1", "C09.8", "C09.9"],
                        "rest":   ["C10.0", "C10.1", "C10.2", "C10.3", "C10.4", 
                                   "C10.8", "C10.9", "C12.9", "C13.0", "C13.1", 
                                   "C13.2", "C13.8", "C13.9", "C32.0", "C32.1", 
                                   "C32.2", "C32.3", "C32.8", "C32.9"]}
        icd_codes = []
        for sub in subsites:
            icd_codes += subsite_dict[sub]
        cleaned_data["subsite_icds"] = icd_codes
                
        str_list = cleaned_data["tstages"]
        cleaned_data["tstages"] = [int(s) for s in str_list]
        
        str_list = cleaned_data["modalities"]
        cleaned_data["modalities"] = [int(s) for s in str_list]
        
        return cleaned_data
        
        
        
    # select modalities to show
    modalities = forms.MultipleChoiceField(
        required=False, 
        widget=forms.CheckboxSelectMultiple(attrs={"class": "checkbox is-hidden"}), 
        choices=MODALITIES,
        initial=[]
    )
    modality_combine = forms.ChoiceField(
        choices=[("AND", "AND"), 
                 ("OR", "OR")],
        label="Combine",
        initial="OR"
    )
    
    
    # patient specific fields
    nicotine_abuse = ThreeWayToggle()
    hpv_status = ThreeWayToggle()
    neck_dissection = ThreeWayToggle()
    
    
    # tumor specific info
    subsites = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "checkbox is-hidden"}),
        choices=[("base", "base of tongue"),
                 ("tonsil", "tonsil"), 
                 ("rest" , "other/multiple")],
        initial=["base", "tonsil", "rest"]
    )
    tstages = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "checkbox is-hidden"}),
        choices=T_STAGES,
        initial=[1,2,3,4]
    )
    central = ThreeWayToggle()
    midline_extension = ThreeWayToggle()
