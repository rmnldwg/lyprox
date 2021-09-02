from django import forms

from lymph_interface.loggers import FormLoggerMixin
from patients.models import Patient, Tumor, Diagnose


class ThreeWayToggle(forms.ChoiceField):
    """A toggle switch than can be in three different states: Positive/True, 
    unkown/None and negative/False."""
    
    def __init__(self, 
                 widget=None, 
                 attrs={"class": "radio is-hidden",
                        "onchange": "changeHandler();"},
                 choices=[( 1 , "plus"),
                          ( 0 , "ban"), 
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



class DashboardForm(FormLoggerMixin, forms.Form):
    """Form for querying the database."""
    
    # select modalities to show
    modalities = forms.MultipleChoiceField(
        required=False, 
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"}
        ), 
        choices=Diagnose.Modalities.choices,
        initial=[1,2]
    )
    modality_combine = forms.ChoiceField(
        widget=forms.Select(attrs={"onchange": "changeHandler();"}),
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
    subsite__in = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"},
        ),
        choices=[("base", "base of tongue"),
                 ("tonsil", "tonsil"), 
                 ("rest" , "other/multiple")],
        initial=["base", "tonsil", "rest"]
    )
    t_stage__in = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"}
        ),
        choices=Patient.T_stages.choices,
        initial=[1,2,3,4]
    )
    central = ThreeWayToggle()
    extension = ThreeWayToggle()
    
    # checkbutton for switching to percent
    show_percent = forms.BooleanField(
        required=False, initial=False, 
        widget=forms.widgets.RadioSelect(
            attrs={"class": "radio is-hidden", "onchange": "changeHandler();"},
            choices=[(True, "percent"), (False, "absolute")]
        )
    )
    
    
    def __init__(self, *args, **kwargs):
        """Extend default initialization to create lots of fields for the 
        LNLs from a list."""
        super(DashboardForm, self).__init__(*args, **kwargs)
        for side in ["ipsi", "contra"]:
            for lnl in Diagnose.LNLs:
                if lnl in ['I', 'II']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": ("bothClickHandler(this);"
                                           "changeHandler();")})
                elif lnl in ['Ia', 'Ib', 'IIa', 'IIb']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": ("subClickHandler(this);"
                                           "changeHandler();")})
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()
                    
                    
    def _to_bool(self, value: int):
        """Transform values of -1, 0 and 1 to False, None and True respectively. 
        Anything else is just passed through."""
        if value == 1:
            return True
        elif value == -1:
            return False
        elif value == 0:
            return None
        else:
            return value
           
                
    def clean(self):
        """Make sure LNLs I & II have correct values corresponding to their 
        sublevels a & b. Also convert tstages from list of str to list of int."""
        cleaned_data = super(DashboardForm, self).clean()
        
        # map all -1,0,1 fields to False,None,True
        cleaned_data = {
            key: self._to_bool(value) for key,value in cleaned_data.items()
        }
        
        # make sure LNLs I & II arent in conflict with their sublevels
        for side in ["ipsi", "contra"]:
            for lnl in ["I", "II"]:
                a = cleaned_data[f"{side}_{lnl}a"]
                b = cleaned_data[f"{side}_{lnl}b"]
                
                # make sure data regarding sublevels is not conflicting
                if a is True or b is True:
                    cleaned_data[f"{side}_{lnl}"] = True
                if a is False and b is False:
                    cleaned_data[f'{side}_{lnl}'] = False

        # map `central` from False,None,True to the respective list of sides
        if cleaned_data['central'] is True:
            cleaned_data['side__in'] = ['central']
        elif cleaned_data['central'] is False:
            cleaned_data["side__in"] = ['left', 'right']
        else:
            cleaned_data["side__in"] = ['left', 'right', 'central']
        
        # map subsites 'base','tonsil','rest' to list of ICD codes.
        subsites = cleaned_data["subsite__in"]
        subsite_dict = {"base":   ["C01.9"], 
                        "tonsil": ["C09.0", "C09.1", "C09.8", "C09.9"],
                        "rest":   ["C10.0", "C10.1", "C10.2", "C10.3", "C10.4", 
                                   "C10.8", "C10.9", "C12.9", "C13.0", "C13.1", 
                                   "C13.2", "C13.8", "C13.9", "C32.0", "C32.1", 
                                   "C32.2", "C32.3", "C32.8", "C32.9"]}
        icd_codes = []
        for sub in subsites:
            icd_codes += subsite_dict[sub]
        cleaned_data["subsite__in"] = icd_codes
        
        # make sure T-stages are list of ints
        str_list = cleaned_data["t_stage__in"]
        cleaned_data["t_stage__in"] = [int(s) for s in str_list]
        
        # make sure list of modalities is list of ints
        str_list = cleaned_data["modalities"]
        cleaned_data["modalities"] = [int(s) for s in str_list]
        
        self.logger.debug(f'cleaned data: {cleaned_data}')
        return cleaned_data