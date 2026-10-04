# Auditoria da classificação de exames

Os dez casos foram reconvertidos com 89 observações, classificadas por identidade clínica do exame, independentemente do domínio antigo. Cada observação preserva original_domain, clinical_test, modality e routing_tool. Fatos e cronologia permaneceram iguais; o CT histórico separado previamente no caso 010 continua documentado.

A checagem independente confirmou igualdade literal do valor e available_at de todos os 116 fatos não divididos. Cobertura dos 117 IDs originais verificada pelo conversor. Todos os 89 registros têm categoria/modalidade/ferramenta explícitas.

ECG propriamente dito existe somente em case_002/ecg_005. TTE/TEE possuem modalidade echocardiography; OCT/IVUS e angiografia possuem modalidade própria em radiology. Estudo eletrofisiológico e cateterismo direito são other; DAT é blood, filme periférico é other/blood_morphology, T-SPOT.TB é microbiology, fluido pleural é other_fluid e histologia/citologia são tissue. IDs herdados iniciados por ecg não devem decidir roteamento.

| Caso | ID | Domínio original | Domínio atual | Modalidade | Identidade clínica | Ferramenta |
|---|---|---|---|---|---|---|
| case_001 | physical_exam_005 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_001 | lab_006 | lab | blood | laboratory_blood | inflammation | request_blood_test |
| case_001 | lab_007 | lab | blood | laboratory_blood | coagulation | request_blood_test |
| case_001 | ecg_008 | ecg | bedside | echocardiography | transthoracic_echocardiography | request_bedside_test |
| case_001 | imaging_009 | imaging | radiology | angiography | coronary_angiography | request_radiology |
| case_001 | ecg_010 | ecg | radiology | intravascular_optical_and_ultrasound | intravascular_imaging | request_radiology |
| case_001 | procedure_result_011 | procedure_result | other | invasive_procedure | pericardiocentesis | request_other_investigation |
| case_001 | procedure_result_012 | procedure_result | other | invasive_procedure | device_exploration | request_other_investigation |
| case_001 | microbiology_013 | microbiology | microbiology | microbiology | blood_cultures | request_microbiology |
| case_002 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_002 | ecg_005 | ecg | bedside | electrocardiography | electrocardiogram | request_bedside_test |
| case_002 | lab_006 | lab | blood | laboratory_blood | nt_probnp | request_blood_test |
| case_002 | lab_007 | lab | blood | laboratory_blood | troponin | request_blood_test |
| case_002 | lab_008 | lab | blood | laboratory_blood | d_dimer | request_blood_test |
| case_002 | ecg_009 | ecg | bedside | echocardiography | transthoracic_echocardiography | request_bedside_test |
| case_002 | imaging_010 | imaging | radiology | computed_tomography | ctpa | request_radiology |
| case_002 | imaging_011 | imaging | radiology | computed_tomography | coronary_ct | request_radiology |
| case_002 | procedure_result_012 | procedure_result | other | invasive_procedure | rhc | request_other_investigation |
| case_002 | ecg_013 | ecg | bedside | echocardiography | transesophageal_echocardiography | request_bedside_test |
| case_002 | imaging_014 | imaging | radiology | magnetic_resonance | cardiac_mri | request_radiology |
| case_002 | ecg_015 | ecg | other | invasive_procedure | electrophysiology | request_other_investigation |
| case_003 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_003 | imaging_005 | imaging | radiology | computed_tomography | ct_abdomen | request_radiology |
| case_003 | imaging_006 | imaging | radiology | computed_tomography | ct_chest | request_radiology |
| case_003 | lab_007 | lab | blood | laboratory_blood | cbc | request_blood_test |
| case_003 | lab_008 | lab | blood | laboratory_blood | chemistry | request_blood_test |
| case_003 | lab_009 | lab | blood | laboratory_blood | inflammation | request_blood_test |
| case_003 | lab_010 | lab | blood | laboratory_blood | inflammation_followup | request_blood_test |
| case_003 | lab_011 | lab | blood | laboratory_blood | lactate | request_blood_test |
| case_003 | procedure_result_012 | procedure_result | other | invasive_procedure | laparotomy | request_other_investigation |
| case_003 | physical_exam_013 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_003 | microbiology_014 | microbiology | microbiology | microbiology | blood_cultures | request_microbiology |
| case_003 | microbiology_015 | microbiology | microbiology | microbiology | drain_culture | request_microbiology |
| case_003 | microbiology_016 | microbiology | microbiology | microbiology | urine_culture | request_microbiology |
| case_003 | other_test_017 | other_test | other | retrospective_research | research_cfdna | request_other_investigation |
| case_003 | allergies_018 | allergies | other | followup_observation | drug_reaction | request_other_investigation |
| case_004 | physical_exam_003 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_004 | imaging_004 | imaging | radiology | radiograph | chest_xray | request_radiology |
| case_004 | procedure_result_005 | procedure_result | other | invasive_procedure | thoracentesis | request_other_investigation |
| case_004 | lab_006 | lab | other_fluid | pleural_fluid_laboratory | pleural_fluid_studies | request_other_investigation |
| case_004 | microbiology_007 | microbiology | microbiology | microbiology | pleural_culture | request_microbiology |
| case_004 | imaging_008 | imaging | radiology | computed_tomography | ct_chest | request_radiology |
| case_004 | procedure_result_009 | procedure_result | tissue | histopathology | ebus_biopsy | request_other_investigation |
| case_004 | microbiology_010 | microbiology | microbiology | microbiology | blood_cultures | request_microbiology |
| case_005 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_005 | physical_exam_005 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_005 | lab_006 | lab | blood | laboratory_blood | blood_panel | request_blood_test |
| case_005 | imaging_007 | imaging | radiology | ultrasound | thoracic_ultrasound | request_radiology |
| case_005 | imaging_008 | imaging | radiology | computed_tomography | ct_chest | request_radiology |
| case_005 | procedure_result_009 | procedure_result | tissue | cytopathology | pleural_fluid_cytology_immunohistochemistry | request_other_investigation |
| case_005 | procedure_result_010 | procedure_result | tissue | histopathology | pleural_biopsy | request_other_investigation |
| case_005 | physical_exam_011 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_005 | imaging_012 | imaging | radiology | positron_emission_tomography | pet | request_radiology |
| case_005 | other_test_013 | other_test | genetic | molecular_genetics | tumor_genetics | request_other_investigation |
| case_006 | physical_exam_003 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_006 | lab_004 | lab | blood | laboratory_blood | adrenal_hormones | request_blood_test |
| case_006 | lab_005 | lab | blood | laboratory_blood | metabolic | request_blood_test |
| case_006 | lab_006 | lab | microbiology | microbiology | tspot | request_microbiology |
| case_006 | imaging_007 | imaging | radiology | computed_tomography | adrenal_ct | request_radiology |
| case_006 | imaging_008 | imaging | radiology | ultrasound | adrenal_ultrasound | request_radiology |
| case_006 | procedure_result_009 | procedure_result | tissue | histopathology | adrenal_biopsy | request_other_investigation |
| case_006 | microbiology_010 | microbiology | microbiology | microbiology | adrenal_tb_pcr | request_microbiology |
| case_007 | physical_exam_005 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_007 | lab_006 | lab | blood | laboratory_blood | hemoglobin | request_blood_test |
| case_007 | lab_007 | lab | blood | laboratory_blood | hemolysis | request_blood_test |
| case_007 | lab_008 | lab | blood | laboratory_blood | lactate | request_blood_test |
| case_007 | lab_009 | lab | other | blood_morphology | peripheral_blood_film | request_other_investigation |
| case_007 | lab_010 | lab | blood | laboratory_blood | dat | request_blood_test |
| case_007 | imaging_011 | imaging | radiology | computed_tomography | ct_abdomen | request_radiology |
| case_008 | physical_exam_003 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_008 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_008 | lab_005 | lab | blood | laboratory_blood | cbc | request_blood_test |
| case_008 | lab_006 | lab | blood | laboratory_blood | coagulation | request_blood_test |
| case_008 | imaging_007 | imaging | radiology | magnetic_resonance | brain_mri | request_radiology |
| case_008 | imaging_008 | imaging | radiology | magnetic_resonance | spine_mri | request_radiology |
| case_008 | procedure_result_009 | procedure_result | other | invasive_procedure | hematoma_evacuation | request_other_investigation |
| case_009 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_009 | imaging_005 | imaging | radiology | radiograph | abdominal_xray | request_radiology |
| case_009 | imaging_006 | imaging | radiology | computed_tomography | ct_abdomen | request_radiology |
| case_009 | procedure_result_007 | procedure_result | other | invasive_procedure | laparoscopy / laparotomy | request_other_investigation |
| case_009 | procedure_result_008 | procedure_result | other | invasive_procedure | resection | request_other_investigation |
| case_010 | hpi_001_prior_ct | hpi | radiology | computed_tomography | prior_noncontrast_abdominal_ct | request_radiology |
| case_010 | physical_exam_004 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_010 | physical_exam_005 | physical_exam | physical_exam | clinical_examination | physical_examination | request_physical_exam |
| case_010 | lab_006 | lab | blood | laboratory_blood | pregnancy_test | request_blood_test |
| case_010 | imaging_007 | imaging | radiology | ultrasound | pelvic_ultrasound | request_radiology |
| case_010 | imaging_008 | imaging | radiology | computed_tomography | ct_abdomen | request_radiology |
| case_010 | procedure_result_009 | procedure_result | other | invasive_procedure | laparoscopy | request_other_investigation |
| case_010 | procedure_result_010 | procedure_result | tissue | histopathology | pathology | request_other_investigation |

Asserts de conversão impedem ECG genérico para eco/OCT, conservam DAT em blood e isolam eletrofisiologia, T-SPOT e filme periférico. O executor ainda precisa validar o exame solicitado e pré-requisitos antes da liberação; classificação correta sozinha não garante correspondência semântica correta. Nenhuma chamada de modelo ou modificação de legacy foi feita.
