import logging
from typing import Tuple

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import Institution
from core.loggers import FormLoggerMixin
from patients.models import Diagnose, Patient, Tumor

logger = logging.getLogger(__name__)


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
        try:
            return int(value)
        except ValueError:
            return value
        except TypeError:
            raise ValidationError("Expects a number")


class InstitutionModelChoiceIndexer:
    """Custom class with which one can access additional information from
    the model that is chosen by the :class:`InstitutionMultipleChoiceField`."""

    def __init__(self, field) -> None:
        self.field = field
        self.queryset = field.queryset

    def __getitem__(self, key):
        obj = self.queryset[key]
        return self.info(obj)

    def info(self, obj: Institution) -> Tuple[int, str]:
        return (
            self.field.label_from_instance(obj),
            self.field.logo_url_from_instance(obj)
        )


class InstitutionMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Customize label description and add method that returns the logo URL for
    institutions. The implementation is inspired by how the ``choices`` are
    implemented. But since some other functionality depends on how those
    choices are implemented, it cannot be changed easily."""

    #: Allows one to extract more info about the objects. E.g. name and logo url
    name_and_url_indexer = InstitutionModelChoiceIndexer

    def label_from_instance(self, obj: Institution) -> str:
        """Institution name as label."""
        return obj.name

    def logo_url_from_instance(self, obj: Institution) -> str:
        """Return URL of Institution's logo."""
        return obj.logo.url

    @property
    def names_and_urls(self):
        return self.name_and_url_indexer(self)


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
        initial=["CT", "MRI", "PET", "FNA", "DC"]
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
    n_status = ThreeWayToggle()
    institution__in = InstitutionMultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            # doesn't do anythin since it's written by hand
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"}
        ),
        queryset=Institution.objects.all().filter(is_hidden=False),
        initial=Institution.objects.all().filter(is_hidden=False)
    )

    # tumor specific info
    subsite_oropharynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"},
        ),
        choices=[("base", "base of tongue"),  # choices here must match entries
                 ("tonsil", "tonsil"),        # in the Tumor.SUBSITE_DICT keys
                 ("rest_oro" , "other")],
        initial=["base", "tonsil", "rest_oro"]
    )
    subsite_hypopharynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"},
        ),
        choices=[("rest_hypo" , "all")],   # choices here must match entries in
        initial=["rest_hypo"]              # the Tumor.SUBSITE_DICT keys
    )
    subsite_larynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "checkbox is-hidden",
                   "onchange": "changeHandler();"},
        ),
        choices=[("glottis", "glottis"),      # choices here must match entries
                 ("rest_larynx" , "other")],  # in the Tumor.SUBSITE_DICT keys
        initial=["glottis", "rest_larynx"]
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
        LNLs from a list and hide some datasets for unauthenticated users.
        """
        user = kwargs.pop("user")
        super(DashboardForm, self).__init__(*args, **kwargs)

        # dynamically define which institutions should be selectable
        if user.is_authenticated:
            self.fields["institution__in"].queryset = Institution.objects.all()
            self.fields["institution__in"].initial = Institution.objects.all()

        # add all LNL ToggleButtons so I don't have to write a myriad of them
        for side in ["ipsi", "contra"]:
            for lnl in Diagnose.LNLs:
                if lnl in ['I', 'II']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": ("bothClickHandler(this);"
                                           "changeHandler();")}
                    )
                elif lnl in ['Ia', 'Ib', 'IIa', 'IIb']:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        attrs={"class": "radio is-hidden",
                               "onclick": ("subClickHandler(this);"
                                           "changeHandler();")}
                    )
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()

    def get_modalities_values(self):
        return [value for value, _ in self.fields["modalities"].choices]

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

        # necessary to prevent errors from processing invalid data
        if len(self.errors) != 0:
            return {}

        # map all -1,0,1 fields to False,None,True
        cleaned_data = {
            key: self._to_bool(value) for key,value in cleaned_data.items()
        }

        # make sure LNLs I & II aren't in conflict with their sublevels
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
        subsites = (cleaned_data["subsite_oropharynx"]
                    + cleaned_data["subsite_hypopharynx"]
                    + cleaned_data["subsite_larynx"])

        icd_codes = []
        for sub in subsites:
            icd_codes += Tumor.SUBSITE_DICT[sub]
        cleaned_data["subsite__in"] = icd_codes

        # make sure T-stages are list of ints
        str_list = cleaned_data["t_stage__in"]
        cleaned_data["t_stage__in"] = [int(s) for s in str_list]

        self.logger.debug(f'cleaned data: {cleaned_data}')
        return cleaned_data