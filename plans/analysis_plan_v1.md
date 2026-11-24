# Secondary analysis plan: ego-related interference and rate of mastery in open tutoring data

Version 1.0 · fixed on 2026-11-20, before any of the data below were downloaded or inspected.
Author: Kibriyo Mukhamadieva (analysis code prepared with AI assistance; to be declared).
Intended use: preliminary study for the PhD thesis (Section 4.10) and a journal article. To be uploaded to OSF as a secondary-data pre-registration before analysis.

## 1. Aim

To test, on existing open data, whether behavioural indicators of ego-related interference (E) are stable individual characteristics and whether they predict a slower rate of mastery, and to compare these patterns across three learner groups. Intellectual humility (H) cannot be tested: no open dataset contains it.

## 2. Datasets and groups

| Group | Dataset | Domain | Licence / terms |
| --- | --- | --- | --- |
| G1 School pupils | ASSISTments 2009–2010 skill-builder data (corrected version) | Mathematics | Free for research; cite the dataset page |
| G2 University students | StudyChat (Fall 2024, Spring 2025): labelled dialogues and normalised grades | AI course with an LLM chatbot | CC BY 4.0; gated (account + terms) |
| G3 Adult learners | EdNet-KT1 + contents table | TOEIC English | CC BY-NC 4.0, research only |

Age is known only at dataset level. Group differences mix age with domain, platform and country; no causal claim about age will be made.

## 3. Secondary hypotheses

- **SH1 Stability.** In each of G1 and G3, the E composite computed on odd-numbered opportunities correlates with the E composite on even-numbered opportunities at r ≥ 0.30.
- **SH2 Association.** In each of G1 and G3, a higher E composite is associated with slower mastery (more opportunities to reach mastery), controlling for baseline K.
- **SH3 Functional form.** Learner-level mastery rate is predicted better (lower 10-fold learner-grouped cross-validated RMSE) by the ratio form Va = b·K/(1 + c·E) than by a linear additive model in K and E. Power-law and exponential practice curves are fitted as reference models.
- **SH4 Group comparison (exploratory).** The standardised effect of E on mastery rate is compared across G1 and G3 and pooled with a random-effects model; heterogeneity (I², τ²) is reported.
- **SH5 LLM use (G2, exploratory).** A higher share of solution-seeking requests (offloading proxy) and of defensive messages is associated with lower exam grades, controlling for assignment grades.

## 4. Operational definitions

- **Opportunity:** one problem (G1) or one question (G3) answered by a learner, in time order.
- **K (baseline):** proportion correct on the learner's first 10 opportunities; these opportunities are excluded from all outcome measures.
- **E1 post-error slowing:** within learner, median log response time on the opportunity after an incorrect response minus median log response time after a correct response. G1: `ms_first_response`; G3: `elapsed_time`.
- **E2 error perseveration:** within learner, probability of an incorrect response on the next opportunity of the same skill (G1) or tag (G3) after an incorrect response, minus the learner's overall error rate.
- **E composite:** mean of z-standardised E1 and E2 within dataset.
- **E3 (G1 only, exploratory):** after an error, proportion of next problems in the same skill answered incorrectly without requesting a hint (help avoidance).
- **Mastery:** three consecutive correct responses within a skill (G1, the ASSISTments rule) or tag (G3). Opportunities to mastery are counted per skill/tag; non-mastery is treated as censored.
- **Mastery rate (learner level):** mean over skills/tags of 1 / opportunities-to-mastery, for skills/tags with at least 3 opportunities.
- **G2 measures:** message categories from the dataset's own labels where available; otherwise keyword rules plus LLM-assisted classification accepted only if agreement with a 200-message human-coded sample reaches Cohen's kappa ≥ 0.70.

## 5. Exclusions and sampling

- Learners with fewer than 30 opportunities after the baseline window.
- Response times below 1 s or above 10 min are set to missing for E1.
- G3: a random sample of 20,000 eligible learners (seed 2026) to keep computation feasible; the full set is used for a robustness check if feasible.
- Duplicate rows (as documented for ASSISTments) are removed before analysis.

## 6. Analysis

- SH1: Pearson and Spearman split-half correlations, Spearman–Brown corrected, with bootstrap 95% CIs.
- SH2: per-skill Cox models of opportunities to mastery with learner-level E and K and random effects for skill; learner-level linear models of mastery rate as a check.
- SH3: nonlinear least squares for the ratio form vs OLS for the additive form; 10-fold cross-validation grouped by learner.
- SH4: standardised coefficients per dataset, random-effects pooling (DerSimonian–Laird and REML).
- SH5: linear regression of exam grade on message shares, controlling for assignment grades.
- All code is written in Python, version-controlled, and released with the results. Deviations from this plan will be reported as such.
