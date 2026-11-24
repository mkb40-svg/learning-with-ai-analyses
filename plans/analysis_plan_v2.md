# Secondary analysis plan v2: help timing, offloading and error processing in open tutoring data

Version 2.0 · fixed on 2026-11-24, before any of the analyses below were run.
Author: Kibriyo Mukhamadieva (analysis code prepared with AI assistance; to be declared).
Builds on: analysis_plan.md (v1.0, Study 1), whose pre-registered hypotheses SH1–SH3 were not supported.
Purpose: a preliminary study for the PhD proposal "Learning with AI, not through it", testing on existing data the two design principles of the planned tutor: (1) the learner commits to an attempt before help ("commit first") and (2) the learner processes the error ("learner error analysis").

## 1. What Study 1 showed and what is new here

Study 1 (ASSISTments 2009–10, 1,264 pupils; EdNet-KT1, 18,117 adults) found that post-error slowing (E1) was a moderately stable learner characteristic (split-half r 0.33–0.40) and was associated with FASTER mastery (exploratory, not pre-registered). Those exploratory findings are now tested as confirmatory hypotheses on NEW data: EdNet learners not drawn in Study 1. Help-timing hypotheses (H3–H5) use variables that were not analysed in Study 1.

## 2. Data

| Dataset | Use | Status |
| --- | --- | --- |
| EdNet-KT1, fresh sample | H1, H2 replication | Already downloaded; a new random sample of 20,000 eligible learners excluding all Study 1 learners (seed 2027) |
| ASSISTments 2009–10 skill builder | H3, H4 (hint timing, bottom-out hints) | Already downloaded; columns `first_action`, `hint_count`, `bottom_hint` were not analysed in Study 1 |
| EdNet-KT3 | H5 (explanation viewing before vs after an error) | Not downloaded (≈0.76 GB); requires the candidate's approval |
| Malaysian learner data | Replication in the target population | To be identified (search in progress) |

## 3. Confirmatory hypotheses

- **H1 Error processing (replication).** In a fresh EdNet sample, higher post-error slowing (E1) is associated with faster mastery: Cox hazard ratio per SD of E1 > 1, controlling for baseline K.
- **H2 Stability (replication).** Split-half reliability of E1 (odd vs even opportunities) is r ≥ 0.30.
- **H3 Help before attempt (offloading).** In ASSISTments, learners with a higher share of problems where the first action is a hint request (`first_action` = 1, help before any attempt) reach mastery more slowly, controlling for baseline K.
- **H4 Answer revealed (offloading).** In ASSISTments, after a problem on which the bottom-out hint (answer) was shown, first-attempt correctness on the NEXT problem of the same skill is lower than after a problem solved without the bottom-out hint, within learner (learner fixed effects).
- **H5 Help after own attempt (error processing).** In EdNet-KT3, viewing the explanation after an incorrect own answer is followed by higher correctness on the next question of the same tag than an incorrect answer without explanation viewing, within learner. (Run only if KT3 is downloaded.)

H3–H5 mirror the two manipulated factors of the planned 2×2 experiment.

## 4. Operational definitions

- Baseline K, opportunity, mastery (3 consecutive correct within skill/tag), RT trimming (1 s–10 min), eligibility (≥10 baseline + ≥30 later opportunities): as in v1.0.
- E1: as in v1.0.
- Help-first share (H3): proportion of a learner's post-baseline problems with `first_action` = 1.
- Bottom-out event (H4): `bottom_hint` = 1 on a problem. Outcome: `correct` on the next problem of the same skill.
- Explanation after error (H5): an `enter` action on the explanation of a question within 5 minutes after the learner's incorrect response to it.

## 5. Analysis

- H1: Cox model stratified by tag, robust SE clustered by learner (as in Study 1, corrected implementation). One-sided test, alpha 0.05.
- H2: Pearson split-half r with bootstrap 95% CI; supported if r ≥ 0.30.
- H3: Cox model of opportunities to mastery with learner-level help-first share (z) and K; supported if HR < 1, p < 0.05.
- H4, H5: linear probability models with learner fixed effects and skill/tag fixed effects; cluster-robust SE by learner; supported if the coefficient has the predicted sign, p < 0.05.
- Multiple testing: Holm correction across H1–H5.
- All other analyses are labelled exploratory.

## 5a. Malaysian replication (added 2026-11-24, before any Malaysian data were downloaded or inspected)

| Dataset | Population | Access | Use |
| --- | --- | --- | --- |
| Student Engagement Dataset (SED), Universiti Malaya Moodle logs, Sem II 2018/19 (Kassim, Azizul & Ahmad Fuaad, IEEE Access 2025; github.com/shahreeza-kassim/SED) | ~16,600 Malaysian university students, 2,407 courses, 12.1M log rows | Open, BSD-3 | H6 |
| PISA 2022, Malaysia (OECD) | 7,069 Malaysian 15-year-olds | Open, OECD terms | H7 |
| Global ChatGPT Student Survey, wave 2 (Mendeley Data nv2343nwsb v2) | 443 Malaysian students (subsample) | Open, CC BY 4.0 | H8 (exploratory) |

- **H6 Re-engagement after a low mark (error processing, Malaysian university students).** Within a course, students who re-engage after a low quiz or assignment mark (a new attempt or a course-material view within 7 days after the graded item was released) obtain higher final course grades than students who do not, controlling for their mark on that first graded item. Course fixed effects; SE clustered by student. Exact operationalisation will be fixed from the codebook before any outcome variable is examined, and recorded as an amendment.
- **H7 Giving up after mistakes (Malaysian pupils).** In PISA 2022 Malaysia, stronger agreement with "I give up after making mistakes" (perseverance scale item) is associated with lower mathematics performance, controlling for ESCS and gender. All 10 plausible values and the 80 replicate weights (Fay's BRR) are used.
- **H8 Substitution versus complementary use of ChatGPT (exploratory).** Among Malaysian respondents, using ChatGPT mainly to produce assignments (substitution) rather than to get explanations (complementary) is associated with lower self-reported development of critical thinking. Self-report only; labelled exploratory.

**Amendment A1 to H6 (2026-11-24, made from the dataset README only, before downloading or inspecting any SED data).** The SED grade files contain final grades per student and course, not marks per quiz, so the original H6 cannot be computed. H6 is replaced by: *students who more often review their quiz attempts after submitting them (share of Moodle `attempt submitted` events followed by an `attempt reviewed` event by the same student in the same course within 24 hours) obtain higher final course grades, controlling for course fixed effects and the student's total number of logged actions in that course.* Reviewing one's own graded attempt is the closest available behavioural trace of learner error processing. The log file (≈700 MB, Google Drive link in the SED repository) requires the candidate's approval to download.

No Malaysian dataset links AI use to a measured performance outcome, so H6–H8 test the error-processing and offloading principles only indirectly. A direct test requires the planned experiment.

## 6. Limitations stated in advance

Observational data: help timing is chosen by learners, so H3–H5 test associations, not causal effects. This is why the PhD includes a randomised experiment. Datasets differ in age, subject and platform; no claim about age is made.

## 7. Amendment A2: implementation clarifications (2026-11-24, before any v2 hypothesis was run)

Recorded after inspecting only the coding of predictor columns (ASSISTments `first_action` takes 0 = attempt, 1 = hint, 2 = scaffolding; `bottom_hint` is missing when no hint was requested) and dataset documentation. No outcome was examined.

- **C8 (H1, H2 sample).** Study 1 learners are all 20,359 EdNet-KT1 files drawn in Study 1 (seed-2026 order replayed). The fresh sample draws the remaining files in a seed-2027 random order with the Study 1 procedure (files ≥ 40 responses kept until 20,000; eligibility then applied as in v1.0).
- **C9 (H1).** Learners need E1 and baseline K (E2 is not required). The Cox model is the Study 1 model with z(E1) in place of z(E). One-sided p for HR > 1.
- **C10 (H2).** Supported if the split-half r of E1 is ≥ 0.30. The p-value entered in the Holm procedure is a one-sided Fisher-z test of ρ > 0.30.
- **C11 (H3).** Help-first share uses post-baseline main problems of eligible learners; z-scored. Two-sided p. Known limitation: ASSISTments scores a hint-first problem as incorrect, so H3 is partly mechanical. An exploratory within-learner check is added: correctness on the next problem of the same skill after a help-first versus an attempt-first problem.
- **C12 (H4).** `bottom_hint` missing (no hint requested) counts as no bottom-out hint. Post-baseline rows of eligible learners with a next problem of the same skill. Linear probability model, learner and skill fixed effects absorbed by alternating projections, cluster-robust (CR1) SE by learner, two-sided. Exploratory check: the same model restricted to problems answered incorrectly.
- **C13 (H5).** KT3 learners are drawn in a seed-2028 random order; files with ≥ 40 responses are kept until 20,000. A response is the last `respond` action on a question before the bundle's `submit`; its time is the `submit` time; correctness uses `correct_answer`; the tag is the first tag (as C5). Explanation viewing = an `enter` action on that question's `explanation_id` within 300 s after the `submit`. Analysis uses incorrect post-baseline responses (eligibility as v1.0) that have a next response of the same tag. Same model as H4. If the KT3 columns differ from the published EdNet documentation, a further amendment is recorded before running.
- **Multiple testing.** Holm is applied within two families: H1–H5 (as pre-specified) and the Malaysian confirmatory hypotheses H6–H7. H8 is exploratory and not corrected.

## 8. Amendment A3: KT3 explanation viewing (2026-11-24, after H1–H4 were run, before H5 was run)

A parser check on one KT3 learner file (action sequence only, no outcome analysed) showed that in the app's practice mode (`source` = `sprint`) the explanation is opened automatically after every submitted answer, correct or not, while in the diagnostic test it is not. "Viewing" therefore mainly reflects the mode, not the learner's choice. H5 is run unchanged as pre-registered and interpreted with this caveat. Two exploratory analyses are added: (a) the H5 model with an additional fixed effect for `source`; (b) among incorrect responses whose explanation was opened, the log time spent on the explanation (from its `enter` to the next `quit` of the same explanation, kept if 1 s–10 min, z-scored) as the predictor. Analysis (b) is the closer behavioural trace of learner error processing.

## 9. Amendment A4: SED quiz review events (2026-11-24, before any grade was examined)

Inspection of the SED log (event types and timing only; no grade analysed) found 54,801 `mod_quiz / submitted / attempt` events in 287 courses (14,459 student–course pairs). For 91% of submissions the first `reviewed` event follows within 2 seconds, i.e. Moodle opens the review page automatically after submission when the quiz settings allow it. The A1 measure therefore mainly reflects quiz settings rather than the student's choice. Clarifications for H6: grades are `formatted agreed mark` (0–100) from Student_grade_detailed.csv, linked by student and course id; the control is log(total logged actions of the student in that course); the predictor is the A1 share (0–1); course fixed effects, CR1 SE clustered by student, two-sided. H6 is run unchanged. Added exploratory measure: **returning review** = share of submissions followed by a `reviewed` event more than 60 s and at most 7 days after the submission (the student came back to the reviewed attempt), same model.

## 10. Amendment A5: PISA coding for H7 (2026-11-24, from variable labels only, before any Malaysian score was examined)

The item is `ST307Q06JA` ("Agree/disagree: I give up after making mistakes", 1 = strongly disagree … 5 = strongly agree), entered as a linear predictor; codes 95–99 are missing. Controls: `ESCS` and male (`ST004D01T` = 2). Sample: `CNT` = MYS, listwise deletion on item and controls. Weighted least squares with `W_FSTUWT`; sampling variance from the 80 Fay BRR replicates `W_FSTURWT1–80` (k = 0.5, variance = Σ(θr − θ)² / 20); the 10 plausible values `PV1MATH–PV10MATH` combined by Rubin's rules; two-sided test.

## 11. Amendment A6: survey coding for H8 (2026-11-24, from the questionnaire and country/usage codes only, before any outcome was examined)

The questionnaire has no item on producing assignments versus getting explanations. The closest items are used: substitution = Q18a (how often ChatGPT is used for academic writing: "writing assignments, research papers"), complementary = Q18i ("study assistance: practising for exams"), both 1 = never … 5 = always. Predictor = relative substitution, Q18a − Q18i. Controls: the mean of Q18a and Q18i, and overall use Q15 (1 = rarely … 5 = extensively). Outcome = Q29e ("ChatGPT can improve my critical thinking skills", 1–5). Sample: Q4 (country of study) = Malaysia and Q13a = 1 (has used ChatGPT); listwise deletion. OLS with HC3 SE, two-sided, exploratory. Context analysis (also exploratory): the same model on all respondents with country-of-study fixed effects and SE clustered by country. The outcome is a perception of what ChatGPT can do, not a measured skill.

## 12. Amendment A7: post hoc robustness checks (2026-11-24, AFTER all confirmatory results were known)

These checks were defined after H1–H8 had been analysed, to answer foreseeable reviewer questions. They are reported as post hoc and do not change any confirmatory verdict.

- **Preprint 1 (H1, H2).** (a) Mastery defined as 2 or 4 consecutive correct responses instead of 3. (b) E1 recomputed on response times adjusted for item time demand (log time minus the item's mean log time in the sample). (c) E1-only Cox models in ASSISTments and the Study 1 EdNet sample, for comparison with Study 2. (d) Added later the same day, after (a)–(c) were run: "robust" post-error slowing following Dutilh et al. (2012), i.e. the learner's median of log RT after minus log RT before errors that are surrounded by correct responses (at least five such errors), with its split-half reliability (at least three per half) and Cox model. (e) Added after (d) showed that robust slowing was unrelated to mastery: an exploratory test of whether the traditional E1 association reflects disengaged rapid responding. Rapid response = response time below 10% of the item's median response time in the sample (normative-threshold approach); the learner's post-baseline share of rapid responses is added to the H1 Cox model, and E1 is correlated with it.
- **Preprint 2 (H3–H5).** (a) H4 and the help-first check with controls for the leave-one-out difficulty of the current and the next problem and for current correctness. (b) H4 on the second-next problem of the same skill. (c) H5 and the time-on-explanation analysis with controls for current and next question difficulty. (d) Learner-averaged next-step correctness by type of help, for figures.
- **Preprint 3 (H6, H7).** (a) PISA: the perseverance index `PERSEVAGR` instead of the single item; the item entered as categories; weighted mathematics means by response category, for a figure. *Note added on running:* `PERSEVAGR` is missing for all 7,069 Malaysian students in the PISA 2022 database, so the index check was replaced by the related item of the same scale, "I give up easily" (`ST307Q10JA`). (b) SED: H6 with a control for the number of quiz submissions, and restricted to courses where the review share varies.
