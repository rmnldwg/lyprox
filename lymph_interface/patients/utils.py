from django.db import IntegrityError
from django.db.models import F

import numpy as np
import dateutil
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
                              t_stage=t_stage,
                              n_stage=n_stage,
                              m_stage=m_stage)
        
        try:
            new_patient.save()
        except IntegrityError:
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
            
            num_new += 1
            
        except:
            new_patient.delete()
            raise

    return num_new, num_skipped


def oneminusone_to_bool(num: int) -> bool:
    """Transform 1 to `True` and -1 to `False`."""
    if num == 1:
        return True
    elif num == -1:
        return False
    else:
        raise ValueError("Only 1 and -1 are allowed.")


def query_patients(data):
    """Query the patient database for the requested fields."""
    q = Patient.objects.all()  # first, collect all patients, then restrict
    _ = oneminusone_to_bool  # neccessary because radio buttons return 1, 0 or -1
    
    # PATIENT specific fields
    # nictoine abuse
    if (na := data["nicotine_abuse"]) != 0:
        q = q.filter(nicotine_abuse=_(na))
        
    # hpv status
    if (hpv := data["hpv_status"]) != 0:
        q = q.filter(hpv_status=_(hpv))
        
    # neck dissection
    if (nd := data["neck_dissection"]) != 0:
        q = q.filter(neck_dissection=_(nd))
        
    # TUMOR specific queries
    # (oropharynx) subsite
    tumor_filter_kwargs = {}
    subsite_dict = {"base":   ["C01.9"], 
                    "tonsil": ["C09.0", "C09.1", "C09.8", "C09.9"]}
    if (sub := data["subsites"]) == "rest":
        q = q.exclude(tumor__subsite__in=subsite_dict["base"])
        q = q.exclude(tumor__subsite__in=subsite_dict["tonsil"])
    else:
        q = q.filter(tumor__subsite__in=subsite_dict[sub])
        
    # T-stages
    q = q.filter(tumor__t_stage__in=data["tstages"])
        
    # central location
    if (ce := data["central"]) == 1:
        q = q.filter(tumor__position="central")
    elif ce == -1:
        q = q.exclude(tumor__position="central")
        
    # check midline extension
    if (me := data["midline_extension"]) != 0:
        q = q.filter(tumor__extension=_(me))
        
    # DIAGNOSES filtering
    q_list = []  # I think that's bad python...
    for mod in data["modalities"]:
        # kreate kwrags dictionary for the filtering, so that I can loop 
        # through the LNLs and simply append what I am looking for to that dict.
        ipsi_kwargs = {"modality": mod,
                       "side": F("patient__tumor__position")}
        contra_kwargs = {"modality": mod}
        # loop through the LNLs
        for lnl in LNLs:
            if (inv := data[f"ipsi_{lnl}"]) != 0:
                ipsi_kwargs[f"{lnl}"] = _(inv)
            if (inv := data[f"contra_{lnl}"]) != 0:
                contra_kwargs[f"{lnl}"] = _(inv)
            
        d_ipsi = Diagnose.objects.filter(
            **ipsi_kwargs
        )
        q_ipsi = q.filter(diagnose__in=d_ipsi)
        
        d_contra = Diagnose.objects.filter(
            **contra_kwargs
        ).exclude(
            side=F("patient__tumor__position")
        )
        q_contra = q.filter(diagnose__in=d_contra)
        
        q_list.append(q_ipsi.intersection(q_contra))
        
    if data["modality_combine"] == "OR":
        q = Patient.objects.none().union(*q_list)
    elif data["modality_combine"] == "AND":
        q = Patient.objects.all().intersection(*q_list)
    
    return q