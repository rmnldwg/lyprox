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


def oneminusone_to_bool(num: int) -> bool:
    """Transform 1 to `True` and -1 to `False`."""
    if num == 1:
        return True
    elif num == -1:
        return False
    else:
        raise ValueError("Only 1 and -1 are allowed.")

# TODO: How to do type hinting for multiple return values
def query(data: Dict[str, Any], 
          assign_central: Dict[str, str] = {"ipsi": "left"}):
    """"""
    patients = Patient.objects.all()
    _ = oneminusone_to_bool  # neccessary cause radio buttons return 1, 0 or -1
    
    # PATIENT specific fields
    if (na := data["nicotine_abuse"]) != 0:
        patients = patients.filter(nicotine_abuse=_(na))
    if (hpv := data["hpv_status"]) != 0:
        patients = patients.filter(hpv_status=_(hpv))
    if (nd := data["neck_dissection"]) != 0:
        patients = patients.filter(neck_dissection=_(nd))
        
    # TUMOR specific queries
    patients = patients.filter(tumor__subsite__in=data["subsite_icds"])
    patients = patients.filter(tumor__t_stage__in=data["tstages"])

    if (ce := data["central"]) == 1:
        patients = patients.filter(tumor__position="central")
    elif ce == -1:
        patients = patients.exclude(tumor__position="central")

    if (me := data["midline_extension"]) != 0:
        patients = patients.filter(tumor__extension=_(me))
        
    # DIAGNOSES
    d = Diagnose.objects.all().filter(patient__in=patients,
                                      modality__in=data['modalities'])
    q_ipsi = (Q(side=F("patient__tumor__position"))
              | (Q(patient__tumor__position="central")
                 & Q(side=assign_central["ipsi"])))
    
    diagnoses = {'ipsi':   d.filter(q_ipsi),
                 'contra': d.exclude(q_ipsi)}
        
    for side in ['ipsi', 'contra']:
        for lnl in LNLs:
            if (inv := data[f'{side}_{lnl}']) != 0:
                diagnoses[side] = diagnoses[side].filter(**{lnl: _(inv)})
                
    patients = patients.filter(diagnose__in=diagnoses['ipsi'])
    patients = patients.filter(diagnose__in=diagnoses['contra'])
    
    # distinct is necessary, bacause the two lines don't seem to successively 
    # reduce the dataset
    return patients.distinct(), diagnoses


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


def query2statistics(match_pats: QuerySet,
                     match_diags: Dict[str, QuerySet],
                     modality_combine: str = 'OR',
                     **kwargs):
    """Create statistics/counts based on Patient & Diagnose QuerySets.
    
    Args:
        match_pats: Patients that match a previously submitted pattern.
        
        match_diags: Contains the keys 'ipsi', for ipsilateral diagnoses that 
            match the previously submitted pattern, and 'contra' for the 
            respective set of contralateral diagnoses.
    """
    
    # initialize dictionary of statistics/counts for patient & tumor
    statistics = {"total": len(match_pats),
                  
                  "nicotine_abuse": np.zeros(shape=(3,), dtype=int),
                  "hpv_status": np.zeros(shape=(3,), dtype=int),
                  "neck_dissection": np.zeros(shape=(3,), dtype=int),
                  
                  "subsites": np.zeros(shape=(3,), dtype=int),
                  "t_stages": np.zeros(shape=(len(T_STAGES),), dtype=int),
                  "central": np.zeros(shape=(3,), dtype=int),
                  "midline_extension": np.zeros(shape=(3,), dtype=int),}
    
    # initialize LNL statistics/counts with zeros
    for side in ["ipsi", "contra"]:
        for lnl in LNLs:
            statistics[f"{side}_{lnl}"] = np.zeros(shape=(3,), dtype=int)
            
    # DIAGNOSES
    # aggregated diagnoses, sorted by side
    agg_diags =   {'ipsi':   defaultdict(np.ndarray),
                   'contra': defaultdict(np.ndarray)}
    for side in ['ipsi', 'contra']:
        match_diags[side] = (match_diags[side]
                             .select_related('patient')
                             .values())
        for diag in match_diags[side]:
            lnl_array = np.array([diag[f'{lnl}'] for lnl in LNLs])
            try:  # stack involvement data of each patient into a 2D array
                agg_diags[side][diag['patient_id']] = np.vstack(
                    [agg_diags[side][diag['patient_id']], lnl_array]
                )
            except TypeError:  # gets raised when there's nothing yet
                agg_diags[side][diag['patient_id']] = np.array([lnl_array])  
            
    # PATIENT & TUMOR         
    # get basic fields and prefetch the tumor. Also, combine the modalities.
    patients = (match_pats
                .prefetch_related('tumor')
                .values(
                    'id',
                    'nicotine_abuse',
                    'hpv_status',
                    'neck_dissection',
                    'tumor__subsite',
                    'tumor__t_stage',
                    'tumor__position',
                    'tumor__extension',
                ))
    for pat in patients:
        statistics["nicotine_abuse"] += tf2arr(pat["nicotine_abuse"])
        statistics["hpv_status"] += tf2arr(pat["hpv_status"])
        statistics["neck_dissection"] += tf2arr(pat["neck_dissection"])
        
        statistics["subsites"] += subsite2arr(pat["tumor__subsite"])
        statistics["t_stages"][pat["tumor__t_stage"]-1] += 1
        statistics["central"] += pos2arr(pat["tumor__position"])
        statistics["midline_extension"] += tf2arr(pat["tumor__extension"])
        
        for side in ['ipsi', 'contra']:
            # I didn't use np.any() and np.all(), because they are not 
            # consistent w.r.t. the ordering of arrays
            if modality_combine == 'OR':
                lnl_states = np.array(
                    [any(col) for col in agg_diags[side][pat['id']].T]
                )
            elif modality_combine == 'AND':
                lnl_states = np.array(
                    [all(col) for col in agg_diags[side][pat['id']].T]
                )
            else:
                lnl_states = np.array([None] * len(LNLs))
                
            for i,lnl in enumerate(LNLs):
                statistics[f'{side}_{lnl}'] += tf2arr(lnl_states[i])
              
    return statistics
