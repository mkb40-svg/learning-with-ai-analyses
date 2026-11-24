# Error processing, help timing and generative AI: secondary analyses of open learning data

Kibriyo Mukhamadieva, Uzbekistan State World Languages University, Tashkent, Uzbekistan.
ORCID: https://orcid.org/0000-0002-4436-6333

This repository holds the analysis plans, code and results behind three preprints (2026):

| Preprint | Hypotheses | Plan | Code | Results |
| --- | --- | --- | --- | --- |
| 1. Slowing down after errors: a stable learner trait that predicts faster mastery in school and adult tutoring logs | Study 1: SH1–SH4; Study 2: H1–H2 | plans/analysis_plan_v1.md; plans/analysis_plan_v2.md (A2) | common.py, run_assistments.py, run_ednet.py, summarise.py, run_h1h2.py | summary.md, assistments_results.json, ednet_results.json, sh4_pooled.json, h1h2_results.json |
| 2. When help comes matters: help before an attempt, revealed answers and explanations after errors in large-scale tutoring logs | H3–H5 | plans/analysis_plan_v2.md (A2, A3) | run_h3h4.py, run_h5.py | h3h4_results.json, h5_results.json |
| 3. Learning from mistakes in Malaysia: quiz review, giving up after errors and ChatGPT use | H6–H8 | plans/analysis_plan_v2.md (5a, A1, A4–A6) | run_h6.py, run_h7.py, run_h8.py | h6_results.json, h7_results.json, h8_results.json |

`results/summary_v2.md` gives all H1–H8 results with Holm correction.

## Transparency about the plans

- `analysis_plan_v1.md` was written on 2026-11-20 before the Study 1 data were downloaded.
- `analysis_plan_v2.md` was written on 2026-11-24 before any v2 hypothesis was analysed. Its amendments A1–A6 are dated and were each recorded before the analysis they concern, after reading only documentation, variable labels or event types.
- The plans were time-stamped locally but **not deposited in a public registry before the analyses**. They were uploaded here on 2026-11-24, after the analyses, together with the code and results. Plan v1 states an intention to upload to OSF before analysis; this did not happen.
- Deviations from plan v1 are listed in Preprint 1 (Section 2.4).

## Data sources (not redistributed here)

| Dataset | Used for | Where to get it | Terms |
| --- | --- | --- | --- |
| ASSISTments 2009–2010 skill-builder data | SH1–SH4, H3, H4 | https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010 | Dataset page terms |
| EdNet-KT1, EdNet-KT3, EdNet contents | SH1–SH4, H1, H2, H5 | https://github.com/riiid/ednet | CC BY-NC 4.0 |
| Student Engagement Dataset (SED), Universiti Malaya | H6 | https://github.com/shahreeza-kassim/SED | BSD-3 |
| PISA 2022 student questionnaire (SPSS) | H7 | https://webfs.oecd.org/pisa2022/STU_QQQ_SPSS.zip | OECD terms |
| Global ChatGPT Student Survey, wave 2 | H8 | https://doi.org/10.17632/nv2343nwsb.2 | CC BY 4.0 |

`results/*_learner_measures.csv` are learner-level measures derived from ASSISTments and EdNet-KT1 (pseudonymous learner ids from the original datasets). The EdNet-derived file follows the EdNet licence (CC BY-NC 4.0).

## How to run

Python 3.12 with numpy 2.2, pandas 3.1, SciPy 1.15, statsmodels 0.15, pyreadstat 1.3 and openpyxl 3.1.

```
python run_assistments.py <sb0910.csv> <results_dir>
python run_ednet.py <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>
python summarise.py <results_dir>
python run_h1h2.py <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>   # needs ednet_learner_measures.csv from Study 1 in results_dir
python run_h3h4.py <sb0910.csv> <results_dir>
python run_h5.py <EdNet-KT3.zip> <EdNet-Contents.zip> <results_dir>
python run_h6.py <SED folder> <results_dir>
python run_h7.py <CY08MSP_STU_QQQ.SAV> <results_dir>
python run_h8.py <final dataset.xlsx> <results_dir>
python summarise_v2.py <results_dir>
```

Random seeds are fixed in the code (2026, 2027, 2028), so the samples and results reproduce.

## Licence

Code (`code/`): MIT, see `LICENSE`. Plans, results and documentation: CC BY 4.0. Files derived from EdNet: CC BY-NC 4.0.
