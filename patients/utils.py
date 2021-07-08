from django.db import IntegrityError
from django.forms import ValidationError
from django.db.models import Q, F, QuerySet

import numpy as np
import dateutil
import time
from collections import defaultdict
from typing import List, Union, Optional, Dict, Any
import logging
logger = logging.getLogger(__name__)

from .models import Patient, Diagnose, Tumor, T_STAGES, N_STAGES, M_STAGES, MODALITIES, LNLs



def compute_hash(*args):
    """Compute a hash vlaue from three patient-specific fields that must be 
    removed due for repecting the patient's privacy."""
    return hash(args)


def nan_to_None(sth):
    if sth != sth:
        return None
    else:
        return sth


def create_from_pandas(data_frame, anonymize=True):
    """Create a batch of new patients from a pandas `DataFrame`."""
    num_new = 0
    num_skipped = 0
    _ = nan_to_None

    for i, row in data_frame.iterrows():
        # PATIENT
        # privacy-related fields that also serve identification purposes
        if anonymize:
            # first_name = row[("patient", "general", "first_name")]
            # last_name = row[("patient", "general", "last_name")]
            # birthday = row[("patient", "general", "birthday")]
            kisim_id = row[("patient", "general", "ID")]
            hash_value = compute_hash(kisim_id)
        else:
            hash_value = row[("patient", "general", "ID")]

        gender = _(row[("patient", "general", "gender")])
        age = _(row[("patient", "general", "age")])
        diagnose_date = dateutil.parser.parse(
            _(row[("patient", "general", "diagnosedate")]))

        alcohol_abuse = _(row[("patient", "abuse", "alcohol")])
        nicotine_abuse = _(row[("patient", "abuse", "nicotine")])
        hpv_status = _(row[("patient", "condition", "HPV")])
        neck_dissection = _(row[("patient", "condition", "neck-dissection")])

        t_stage = 0
        n_stage = _(row[("patient", "stage", "N")])
        m_stage = _(row[("patient", "stage", "M")])

        new_patient = Patient(hash_value=hash_value,
                              gender=gender,
                              age=age,
                              diagnose_date=diagnose_date,
                              alcohol_abuse=alcohol_abuse,
                              nicotine_abuse=nicotine_abuse,
                              hpv_status=hpv_status,
                              neck_dissection=neck_dissection,
                              t_stage=t_stage,
                              n_stage=n_stage,
                              m_stage=m_stage)
        
        try:
            new_patient.save()
        except IntegrityError:
            msg = f"Patient already in database. Skipping row {i+1}."
            logger.debug(msg)
            num_skipped += 1
            continue
            

        try:
            # TUMORS
            stages_list = [tuple[1] for tuple in T_STAGES]

            count = 1
            while ("tumor", f"{count}", "location") in data_frame.columns:
                location = _(row["tumor", f"{count}", "location"])
                subsite = _(row[("tumor", f"{count}", "ICD-O-3")])
                position = _(row[("tumor", f"{count}", "side")])
                extension = _(row[("tumor", f"{count}", "extension")])
                size = _(row[("tumor", f"{count}", "size")])
                stage_prefix = _(row[("tumor", f"{count}", "prefix")])
                t_stage = _(row[("tumor", f"{count}", "stage")])

                # TODO: deal with location (must be validated so that it 
                #   matches the subsite and vice versa)
                new_tumor = Tumor(subsite=subsite,
                                  position=position,
                                  extension=extension,
                                  size=size,
                                  t_stage=t_stage,
                                  stage_prefix=stage_prefix)
                new_tumor.patient = new_patient

                new_tumor.save()

                if new_tumor.t_stage > new_patient.t_stage:
                    new_patient.t_stage = new_tumor.t_stage
                    new_patient.save()

                count += 1

            # DIAGNOSES
            # first, find out which diagnoses are present in this DataFrame
            header_first_row = list(set([item[0] for item in data_frame.columns]))
            pat_index = header_first_row.index("patient")
            header_first_row.pop(pat_index)
            tum_index = header_first_row.index("tumor")
            header_first_row.pop(tum_index)

            for modality in header_first_row:
                modality_list = [item[1] for item in MODALITIES]
                modality_idx = modality_list.index(modality)

                # can be empty...
                try:
                    diagnose_date = dateutil.parser.parse(
                        _(row[(f"{modality}", "info", "date")]))
                except:
                    diagnose_date = None

                if diagnose_date is not None:
                    for side in ["right", "left"]:
                        I   = _(row[(f"{modality}", f"{side}", "I")])
                        Ia  = _(row[(f"{modality}", f"{side}", "Ia")])
                        Ib  = _(row[(f"{modality}", f"{side}", "Ib")])
                        II  = _(row[(f"{modality}", f"{side}", "II")])
                        IIa = _(row[(f"{modality}", f"{side}", "IIa")])
                        IIb = _(row[(f"{modality}", f"{side}", "IIb")])
                        III = _(row[(f"{modality}", f"{side}", "III")])
                        IV  = _(row[(f"{modality}", f"{side}", "IV")])
                        V   = _(row[(f"{modality}", f"{side}", "V")])
                        VII = _(row[(f"{modality}", f"{side}", "VII")])

                        new_diagnose = Diagnose(modality=modality_idx,
                                                diagnose_date=diagnose_date,
                                                side=side,
                                                I=I,
                                                Ia=Ia,
                                                Ib=Ib,
                                                II=II,
                                                IIa=IIa,
                                                IIb=IIb,
                                                III=III,
                                                IV=IV,
                                                V=V,
                                                VII=VII)

                        new_diagnose.patient = new_patient
                        new_diagnose.save()
            
            msg = f"parsed row {i+1} and created patient {new_patient}"
            logger.debug(msg)
            
            num_new += 1
            
        except:
            msg = f"Unable to add Tumor/Diagnose. Skipping row {i+1}."
            logger.warning(msg)
            new_patient.delete()
            num_skipped += 1
            continue

    return num_new, num_skipped


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
    
    
def pos2arr(pos):
    """Map position to one-hot-array of length three. A one in the first place 
    means unknown lateralization, in the second place it means the tumor is 
    central and in the last place corresponds to a laterlalized tumor (right or 
    left)."""
    if pos == "central":
        return np.array([0, 1, 0], dtype=int)
    elif (pos == "left") or (pos == "right"):
        return np.array([0, 0, 1], dtype=int)
    else:
        return np.array([1, 0, 0], dtype=int)


def oneminusone_to_bool(num: int) -> bool:
    """Transform 1 to `True` and -1 to `False`."""
    if num == 1:
        return True
    elif num == -1:
        return False
    else:
        raise ValueError("Only use this function inside an if-clause that "
                         "catches the case == 0.")

# TODO: How to do type hinting for multiple return values
def query(data: Dict[str, Any], 
          assign_central: str = "left",
          modality_combine: str = "OR"):
    """"""
    patient_queryset = Patient.objects.all()
    _ = oneminusone_to_bool  # neccessary cause radio buttons return 1, 0 or -1
    
    # PATIENT specific fields
    if (na := data["nicotine_abuse"]) != 0:
        patient_queryset = patient_queryset.filter(nicotine_abuse=_(na))
    if (hpv := data["hpv_status"]) != 0:
        patient_queryset = patient_queryset.filter(hpv_status=_(hpv))
    if (nd := data["neck_dissection"]) != 0:
        patient_queryset = patient_queryset.filter(neck_dissection=_(nd))
        
    # TUMOR specific queries
    patient_queryset = patient_queryset.filter(
        tumor__subsite__in=data["subsite_icds"]
    )
    patient_queryset = patient_queryset.filter(
        tumor__t_stage__in=data["tstages"]
    )

    if (ce := data["central"]) == 1:
        patient_queryset = patient_queryset.filter(tumor__position="central")
    elif ce == -1:
        patient_queryset = patient_queryset.exclude(tumor__position="central")

    if (me := data["midline_extension"]) != 0:
        patient_queryset = patient_queryset.filter(tumor__extension=_(me))
        
    # DIAGNOSES
    d = Diagnose.objects.all().filter(patient__in=patient_queryset,
                                      modality__in=data['modalities'])
    q_ipsi = (Q(side=F("patient__tumor__position"))
              | (Q(patient__tumor__position="central")
                 & Q(side=assign_central)))
    
    diagnose_querysets = {
        'ipsi'  : d.filter(q_ipsi).select_related('patient').values(),
        'contra': d.exclude(q_ipsi).select_related('patient').values()
    }
    
    diagnose_tables = {
        'ipsi'  : defaultdict(),
        'contra': defaultdict()
    }
    
    selected_diagnose = {    # via form selected diagnoses will be stored here
        'ipsi'  : np.array([None] * len(LNLs)),
        'contra': np.array([None] * len(LNLs))
    }
    
    # sort diags into patient bins...
    combination = {'ipsi'  : defaultdict(),
                   'contra': defaultdict()}
    for side in ['ipsi', 'contra']:
        for i,lnl in enumerate(LNLs):
            if (selected_inv := data[f'{side}_{lnl}']) != 0:
                selected_diagnose[side][i] = _(selected_inv)
        
        for diagnose in diagnose_querysets[side]:
            patient_pk = diagnose['patient_pk']
            diag_array = np.array([diagnose[f'{lnl}'] for lnl in LNLs])
            
            try:
                diagnose_tables[side][patient_pk] = np.stack([
                    diagnose_tables[side][patient_pk],
                    diag_array
                ])
            except KeyError:
                diagnose_tables[side][patient_pk] = diag_array
        
        # ...and aggregate/combine each patient's diag    
        for pat_pk, diag_table in diagnose_tables[side].items():
            if modality_combine == 'OR':
                combine = any
            elif modality_combine == 'AND':
                combine = all
            else:
                msg = ("Modalities can only be combined using logical OR or "
                       "logical AND")
                logger.error(msg)
                raise ValueError(msg)
            
            combination[side][pat_pk] = np.array(
                [combine(col) for col in diag_table],
                dtype=object
            )
            # when all observations yield 'unknown' for a LNL, report 'unknown'
            all_none_idx = np.all(diag_table == None, axis=0)
            combination[side][pat_pk][all_none_idx] = None
            
            # match the combination against what is selected in the data
            mask = np.all(
                np.stack([combination[side][pat_pk] != None, 
                          selected_diagnose[side] != None]),
                axis=0
            )
            match = np.all(np.equal(combination[side][pat_pk], 
                                    selected_diagnose[side],
                                    where=mask))
            if not match:   # if it does not match, remove patient from queryset
                patient_queryset.exclude(pk=pat_pk)
                diagnose_tables['ipsi'].pop(pat_pk, None)
                diagnose_tables['contra'].pop(pat_pk, None)

    # prefetch patients and important fields for performance
    patients = patient_queryset.prefetch_related('tumor').values(
        'pk',
        'nicotine_abuse',
        'hpv_status',
        'neck_dissection',
        'tumor__subsite',
        'tumor__t_stage',
        'tumor__position',
        'tumor__extension',
    )
    counts = {   # initialize counts of patient- & tumor-related fields
        'total': len(patients),
         
        'nicotine_abuse': np.zeros(shape=(3,), dtype=int),
        'hpv_status': np.zeros(shape=(3,), dtype=int),
        'neck_dissection': np.zeros(shape=(3,), dtype=int),
        
        'subsites': np.zeros(shape=(3,), dtype=int),
        't_stages': np.zeros(shape=(len(T_STAGES),), dtype=int),
        'central': np.zeros(shape=(3,), dtype=int),
        'midline_extension': np.zeros(shape=(3,), dtype=int), 
    }
    for side in ['ipsi', 'contra']:
        for lnl in LNLs:
            counts[f'{side}_{lnl}'] = np.zeros(shape=(3,), dtype=int)
            
    # loop through patients to populate the counts dictionary
    for patient in patients:
        # PATIENT specific counts
        counts['nicotine_abuse'] += tf2arr(patient['nicotine_abuse'])
        counts['hpv_status'] += tf2arr(patient['hpv_status'])
        counts['neck_dissection'] += tf2arr(patient['neck_dissection'])
        
        # TUMOR specific counts
        counts['subsites'] += subsite2arr(patient['tumor__subsite'])
        counts['t_stages'][patient['tumor__t_stage']-1] += 1
        counts['central'] += pos2arr(patient['tumor__position'])
        counts['midline_extension'] += tf2arr(patient['tumor__extension'])
        
        # DIAGNOSE specific (involvement) counts
        for side in ['ipsi', 'contra']:
            for i,lnl in enumerate(LNLs):
                combined_involvement = diagnose_tables[side][patient['pk']][i]
                counts[f'{side}_{lnl}'] += tf2arr(combined_involvement)
                
    return patient_queryset, counts
