import numpy as np


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
    num_new = len(data_frame)

    for i, row in data_frame.iterrows():
        # PATIENT
        # privacy-related fields that also serve identification purposes
        if anonymize:
            # first_name = row[("patient", "general", "first_name")]
            # last_name = row[("patient", "general", "last_name")]
            # birthday = row[("patient", "general", "birthday")]
            kisim_id = row[("patient", "general", "ID")]
            identifier = compute_hash(kisim_id)
        else:
            identifier = row[("patient", "general", "ID")]

        gender = _(row[("patient", "general", "gender")])
        age = _(row[("patient", "general", "age")])
        diagnose_date = dateutil.parser.parse(
            _(row[("patient", "general", "date")]))

        alcohol_abuse = _(row[("patient", "abuse", "alcohol")])
        nicotine_abuse = _(row[("patient", "abuse", "nicotine")])
        hpv_status = _(row[("patient", "condition", "HPV")])

        t_stage = 0
        n_stage = _(row[("patient", "stage", "N")])
        m_stage = _(row[("patient", "stage", "M")])

        new_patient = Patient(identifier=identifier,
                              gender=gender,
                              age=age,
                              diagnose_date=diagnose_date,
                              alcohol_abuse=alcohol_abuse,
                              nicotine_abuse=nicotine_abuse,
                              hpv_status=hpv_status,
                              t_stage=t_stage,
                              n_stage=n_stage,
                              m_stage=m_stage)
        new_patient.save()

        # TUMORS
        location_list = [tuple[1] for tuple in LOCATIONS]
        stages_list = [tuple[1] for tuple in T_STAGES]

        count = 1
        while ("tumor", f"{count}", "location") in data_frame.columns:
            location = _(location_list.index(
                row[("tumor", f"{count}", "location")]))
            position = _(row[("tumor", f"{count}", "side")])
            extension = _(row[("tumor", f"{count}", "extension")])
            size = _(row[("tumor", f"{count}", "size")])
            stage_prefix = _(row[("tumor", f"{count}", "prefix")])
            t_stage = _(row[("tumor", f"{count}", "stage")])

            new_tumor = Tumor(location=location,
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
                    lnl_I = _(row[(f"{modality}", f"{side}", "I")])
                    lnl_II = _(row[(f"{modality}", f"{side}", "II")])
                    lnl_III = _(row[(f"{modality}", f"{side}", "III")])
                    lnl_IV = _(row[(f"{modality}", f"{side}", "IV")])

                    new_diagnose = Diagnose(modality=modality_idx,
                                            diagnose_date=diagnose_date,
                                            side=side,
                                            lnl_I=lnl_I,
                                            lnl_II=lnl_II,
                                            lnl_III=lnl_III,
                                            lnl_IV=lnl_IV)

                    new_diagnose.patient = new_patient
                    new_diagnose.save()

    return num_new