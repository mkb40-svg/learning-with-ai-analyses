# Secondary analysis v2: results summary

Plan: analysis_plan_v2.md (v2.0 with amendments A1-A6, all recorded before the analysis they concern).
Holm correction within H1-H5 and within H6-H7; H8 is exploratory (no correction).

| | Hypothesis | Estimate (95% CI) | N | p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | E1 -> faster mastery (EdNet fresh sample) | HR 1.076 per SD (1.059-1.094) | 19,883 learners | 3.4e-19 | 1e-18 | supported |
| H2 | Split-half r of E1 >= 0.30 | r 0.311 (0.271-0.352) | 18,580 learners | 0.045 | 0.045 | supported |
| H3 | Help-first share -> slower mastery (ASSISTments) | HR 0.542 per SD (0.513-0.572) | 1,309 pupils | 3.7e-110 | 1.5e-109 | supported |
| H4 | Answer shown -> next same-skill problem correct less often | -20.3 pp (-21.5 to -19.0) | 175,499 problems | 1.9e-164 | 9.5e-164 | supported |
| H5 | Explanation after error -> next same-tag answer correct (EdNet-KT3) | +1.8 pp (+1.2 to +2.4) | 1,756,776 errors | 2.4e-09 | 4.9e-09 | supported |
| H6 | Quiz attempt review -> final course mark (UM Moodle) | +1.67 marks for 0->1 share (+0.20 to +3.14) | 14,090 student-courses | 0.026 | 0.026 | supported |
| H7 | 'I give up after mistakes' -> mathematics (PISA 2022 Malaysia) | -6.1 points per step (-8.9 to -3.3) | 3,404 pupils | 2.5e-05 | 5.1e-05 | supported |
| H8 | Substitution vs study use of ChatGPT -> perceived critical thinking gain (exploratory) | -0.010 per point (-0.103 to +0.083) | 330 students | 0.83 |  | exploratory: no association |

## Exploratory checks

- H3 within learner: after a help-first problem the next same-skill problem is correct -22.1 pp less often.
- H4 among incorrectly answered problems only: -12.8 pp.
- H5 with mode (source) fixed effect: +0.9 pp (p = 0.0019).
- H5 time on explanation (per SD of log seconds, among viewed errors): -1.6 pp (p = 2.6e-57; n = 1,691,398).
- H6 returning review (>60 s after submission): +0.79 marks for 0->1 share (p = 0.014).
- H8 context, all 108 countries: -0.003 (p = 0.7).

## Caveats

- All data are observational: associations, not causal effects.
- H3 is partly mechanical: ASSISTments scores a hint-first problem as incorrect (A2, C11).
- H5 'viewing' is mostly automatic in practice mode (A3); H6 'review' is mostly an automatic Moodle redirect (A4).
- H7 uses 3,404 of 7,069 Malaysian pupils: the perseverance items were asked of a subsample.
- H8 outcome is a perception of what ChatGPT can do, not a measured skill.
