from django.db.models import Q, F, QuerySet

import numpy as np
import logging
from typing import Optional, List, Dict

from patients.models import Patient, Diagnose, Tumor

logger = logging.getLogger(__name__)


def tf2arr(value):
    """Map `True`, `False` & `None` to one-hot-arrays of length 3. This 
    particular mapping comes from the fact that in the form `True`, `None`, 
    `False` are represented by integers 1, 0, -1. So, the one-hot encoding 
    uses an array of length 3 that is one only at these respective indices, 
    where -1 is the last item."""
    if value is None:
        return np.array([1, 0, 0], dtype=int)
    else:
        if value:
            return np.array([0, 1, 0], dtype=int)
        else:
            return np.array([0, 0, 1], dtype=int)
        
        
def subsite2arr(subsite):
    """Map different subsites to an one-hot-array of length three. A one in the 
    first place means "base of tongue", at the second place is "tonsil" and at 
    the tird place it's "rest"."""
    if subsite in ["C01.9"]:
        return np.array([1, 0, 0], dtype=int)
    elif subsite in ["C09.0", "C09.1", "C09.8", "C09.9"]:
        return np.array([0, 1, 0], dtype=int)
    else:
        return np.array([0, 0, 1], dtype=int)
    
    
def side2arr(side):
    """Map side to one-hot-array of length three. A one in the first place 
    means unknown lateralization, in the second place it means the tumor is 
    central and in the last place corresponds to a laterlalized tumor (right or 
    left)."""
    if side == "central":
        return np.array([0, 1, 0], dtype=int)
    elif (side == "left") or (side == "right"):
        return np.array([0, 0, 1], dtype=int)
    else:
        return np.array([1, 0, 0], dtype=int)



def patient_specific(
    patient_queryset: QuerySet = Patient.objects.all(),
    nicotine_abuse: Optional[bool] = None,
    hpv_status: Optional[bool] = None,
    neck_dissection: Optional[bool] = None,
    **rest
) -> QuerySet:
    """Filter `QuerySet` of `Patient`s based on patient-specific properties.
    """
    kwargs = locals()              # extract keyword arguments and...
    kwargs.pop('patient_queryset') # ...remove the patient queryset and...
    kwargs.pop('rest')             # ...any other kwargs from this dictionary.
    for key, value in kwargs.items():   # iterate over provided kwargs and ...
        if value is not None:             # ...if it's of interest, then filter
            patient_queryset = patient_queryset.filter(**{key: value})
    
    return patient_queryset


def tumor_specific(
    patient_queryset: QuerySet = Patient.objects.all(),
    subsite__in: List[str] = ["C01.9",
                              "C09.0", "C09.1", "C09.8", "C09.9",
                              "C10.0", "C10.1", "C10.2", "C10.3", "C10.4", 
                              "C10.8", "C10.9", "C12.9", "C13.0", "C13.1", 
                              "C13.2", "C13.8", "C13.9", "C32.0", "C32.1", 
                              "C32.2", "C32.3", "C32.8", "C32.9"],
    t_stage__in: List[int] = [1,2,3,4],
    side__in: List[str] = ['left', 'right', 'central'],
    extension: Optional[bool] = None,
    **rest
) -> QuerySet:
    """Filter `QuerySet` of `Patient`s based on tumor-specific properties.
    """
    kwargs = locals()              # extract keyword arguments and...
    kwargs.pop('patient_queryset') # ...remove the patient queryset and...
    kwargs.pop('rest')             # ...any other kwargs from this dictionary.
    for key, value in kwargs.items():   # iterate over provided kwargs and ...
        if value is not None:             # ...if it's of interest, then filter
            patient_queryset = patient_queryset.filter(**{f'tumor__{key}': value})
    
    return patient_queryset


def diagnose_specific(
    patient_queryset: QuerySet = Patient.objects.all(),
    assign_central: str = "left",
    **kwargs
):
    """"""
    # DIAGNOSES
    d = Diagnose.objects.all().filter(patient__in=patient_queryset,
                                      modality__in=kwargs['modalities'])
    q_ipsi = (Q(side=F("patient__tumor__side"))
              | (Q(patient__tumor__side="central")
                 & Q(side=assign_central)))
    
    diagnose_querysets = {
        'ipsi'  : d.filter(q_ipsi).select_related('patient').values(),
        'contra': d.exclude(q_ipsi).select_related('patient').values()
    }
    
    diagnose_tables = {
        'ipsi'  : {},
        'contra': {}
    }
    
    patient_queryset = patient_queryset.filter(
        Q(diagnose__in=d.filter(q_ipsi)) | Q(diagnose__in=d.exclude(q_ipsi))
    ).distinct()
    
    selected_diagnose = {    # via form selected diagnoses will be stored here
        'ipsi'  : np.array([None] * len(Diagnose.LNLs)),
        'contra': np.array([None] * len(Diagnose.LNLs))
    }
    
    # sort diags into patient bins...
    combined_involvement = {'ipsi'  : {},
                            'contra': {}}
    for side in ['ipsi', 'contra']:
        for i,lnl in enumerate(Diagnose.LNLs):
            if (selected_inv := kwargs[f'{side}_{lnl}']) is not None:
                selected_diagnose[side][i] = selected_inv
                
        for diagnose in diagnose_querysets[side]:
            patient_id = diagnose['patient_id']
            # note the double square brackets below to make sure the 
            # `diag_array` is two-dimensional. Without it, the 
            # `np.all(, axis=0)` below would not work properly.
            diag_array = np.array([[diagnose[f'{lnl}'] for lnl in Diagnose.LNLs]])
            
            try:
                diagnose_tables[side][patient_id] = np.vstack([
                    diagnose_tables[side][patient_id],
                    diag_array
                ])
            except KeyError:
                diagnose_tables[side][patient_id] = diag_array
        
        # ...and aggregate/combine each patient's diag    
        for pat_id, diag_table in diagnose_tables[side].items():
            if kwargs['modality_combine'] == 'OR':
                combine = any
            elif kwargs['modality_combine'] == 'AND':
                combine = all
            else:
                msg = ("Modalities can only be combined using logical OR or "
                       "logical AND")
                logger.error(msg)
                raise ValueError(msg)
            
            try:
                combined_involvement[side][pat_id] = np.array(
                    [combine(col) for col in diag_table.T],
                    dtype=object
                )
            except TypeError:  # difference: square bracket around `col`
                combined_involvement[side][pat_id] = np.array(
                    [combine([col]) for col in diag_table.T],
                    dtype=object
                )
            # when all observations yield 'unknown' for a LNL, report 'unknown'
            all_none_idx = np.all(diag_table == None, axis=0)
            combined_involvement[side][pat_id][all_none_idx] = None
            
            mask = selected_diagnose[side] != None
            match = np.all(np.equal(combined_involvement[side][pat_id], 
                                    selected_diagnose[side],
                                    where=mask,
                                    out=np.ones_like(mask, dtype=bool)))
            if not match:   # if it does not match, remove patient from queryset
                patient_queryset = patient_queryset.exclude(id=pat_id)
    
    return patient_queryset, combined_involvement


def count_patients(
    patient_queryset: QuerySet,
    combined_involvement: Dict[str, Dict[str, np.ndarray]]
):
    """Count how often patients have various characteristics like HPV status, 
    certain lymph node level involvement, and so on.
    """
    # prefetch patients and important fields for performance
    patients = patient_queryset.prefetch_related('tumor_set')
    counts = {   # initialize counts of patient- & tumor-related fields
        'total': len(patients),
         
        'nicotine_abuse': np.zeros(shape=(3,), dtype=int),
        'hpv_status': np.zeros(shape=(3,), dtype=int),
        'neck_dissection': np.zeros(shape=(3,), dtype=int),
        
        'subsites': np.zeros(shape=(3,), dtype=int),
        't_stages': np.zeros(shape=(len(Patient.T_stages),), dtype=int),
        'central': np.zeros(shape=(3,), dtype=int),
        'extension': np.zeros(shape=(3,), dtype=int), 
    }
    for side in ['ipsi', 'contra']:
        for lnl in Diagnose.LNLs:
            counts[f'{side}_{lnl}'] = np.zeros(shape=(3,), dtype=int)
            
    # loop through patients to populate the counts dictionary
    for patient in patients:
        # PATIENT specific counts
        counts['nicotine_abuse'] += tf2arr(patient.nicotine_abuse)
        counts['hpv_status'] += tf2arr(patient.hpv_status)
        counts['neck_dissection'] += tf2arr(patient.neck_dissection)
        
        # TUMOR specific counts
        tumor = patient.tumor_set.first()
        counts['subsites'] += subsite2arr(tumor.subsite)
        counts['t_stages'][tumor.t_stage-1] += 1
        counts['central'] += side2arr(tumor.side)
        counts['extension'] += tf2arr(tumor.extension)
        
        # DIAGNOSE specific (involvement) counts
        for side in ['ipsi', 'contra']:
            for i,lnl in enumerate(Diagnose.LNLs):
                tmp = combined_involvement[side][patient.id][i]
                counts[f'{side}_{lnl}'] += tf2arr(tmp)
                
    return patient_queryset, counts