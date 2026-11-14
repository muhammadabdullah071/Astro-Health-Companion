# **NASA OSDR Dataset Exploration and Data-Access Note**

**Provenance statement:** The project's dashboard measurements are **SIMULATED**. No restricted human or astronaut participant-level data were accessed or used. The application provides **decision support only; not medical diagnosis**.

## **1. Purpose and conclusion**

This review examines the NASA Open Science Data Repository (OSDR) as a source of research context, experimental metadata, and potentially reusable public scientific data for Astro-Health Companion. It **does not** claim that the prototype's 30-day wearable time series originated in OSDR.

**Conclusion:** OSDR contains authentic spaceflight biology and some human spaceflight studies, including Inspiration4. However, the sources reviewed did **not establish a freely accessible, synchronized, day-by-day astronaut time series** containing all four fields required for the prototype: resting heart rate, SpO2, sleep duration, and wearable skin temperature. Therefore, the project uses separately generated, clearly labelled **SIMULATED** readings and cites OSDR for research context only. [1–5]

## **2. What NASA OSDR contains**

OSDR brings together NASA GeneLab molecular/omics research and the Ames Life Sciences Data Archive (ALSDA), with physiological, phenotypic, behavioral, bioimaging, and environmental research data. Experiments may be flown in space or conducted in ground-based space-relevant analogs. Public study metadata describe experiment design, organism, mission, conditions, sample collection, assays, and associated files. [1, 2]

- **Molecular datasets:** genomics, transcriptomics, proteomics, metabolomics, and microbiome-related assays.
- **Non-molecular datasets:** physiological and phenotypic measurements, behavioral observations, bioimaging, and environmental measurements, depending on study.
- **Subjects:** substantial research involving rodents, microbes, plants, cell lines and other model organisms, alongside human/civilian-astronaut studies. **No current, precisely calculated human-vs-model-organism percentage was established in this review; no 2026 percentage is claimed.**
- **Access:** many studies and metadata are public. Access to each *specific file* may be open or restricted. The existence of an openly listed study does not grant access to its controlled human-derived files. [1, 3]

## **3. Field availability assessment**

| Proposed health or research field                                    | Status in the reviewed sources                                                                                            | Interpretation for Astro-Health Companion                                                                  |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Resting heart rate (bpm)                                             | Physiological research is within OSDR scope; a suitable open daily astronaut series **not found in the sources reviewed** | Generated synthetically; not copied from OSDR                                                              |
| Blood pressure (mmHg)                                                | Possible in study-specific physiological work; directly suitable astronaut daily data **not verified**                    | Not part of MVP                                                                                            |
| Respiratory rate (breaths/min)                                       | Suitable openly accessible astronaut time series **not found in the sources reviewed**                                    | Not part of MVP                                                                                            |
| SpO2 (%)                                                             | Suitable open daily astronaut pulse-oximetry series **not found in the sources reviewed**                                 | Generated synthetically                                                                                    |
| Sleep duration (hours/night)                                         | OSDR accommodates behavioral/physiological data; suitable daily astronaut sleep series **not verified**                   | Generated synthetically                                                                                    |
| Wearable skin temperature (°C)                                       | A suitably comparable, openly accessible astronaut wrist-sensor series **not found in the sources reviewed**              | Generated synthetically; distinct from core temperature                                                    |
| Core body temperature (°C)                                           | Relevant to physiological research but suitable open daily astronaut readings **not verified**                            | Separate manual confirmatory concept; not part of synthetic wearable CSV                                   |
| Physical activity / behavior                                         | Study-dependent behavioral and phenotypic data are part of OSDR scope [1, 3]                                              | Not part of current four-metric CSV                                                                        |
| Blood biochemistry / immune biomarkers                               | **Confirmed** for Inspiration4 OSD-575: serum comprehensive metabolic panel and immune/cardiovascular cytokine assays [5] | Real human study example, *not* wearable vital signs                                                       |
| Omics (RNA, chromatin accessibility, plasma proteomics, metabolites) | **Confirmed** in Inspiration4 study metadata, including OSD-570 and OSD-571 [5]                                           | Research context only; no training on restricted raw human files                                           |
| Imaging / microscopy                                                 | Bioimaging is within repository scope [1]                                                                                 | Not an astronaut face-video fatigue dataset                                                                |
| Annotated astronaut face video for drowsiness                        | **Not found in the sources reviewed**                                                                                     | Computer-vision fatigue detection is *future work only*, using a separate non-astronaut dataset if pursued |
| Organism, mission, assay, study design, sample schedule, files       | **Confirmed as searchable metadata categories** [2, 3]                                                                    | Useful for study discovery and citation, not numerical calibration of wearable readings                    |

**Meaning of “not found”:** This is a scoped review of official repository documentation and the specified example records, *not* proof that no NASA dataset of that kind exists anywhere.

## **4. Human spaceflight examples: Inspiration4**

NASA's publicly accessible Inspiration4 dataset announcement identifies several human spaceflight studies. These demonstrate that genuine human biomedical research is represented in OSDR without establishing the availability of a continuous astronaut-wearable vital-sign dataset. [5]

| Accession   | Study contents described by NASA                                                      | Relevance to this prototype                                                                      |
| ----------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **OSD-570** | Peripheral blood mononuclear cells (PBMC), for cellular and molecular profiling.      | Human biological research; not a daily wearable time series.                                     |
| **OSD-571** | Blood plasma samples and molecular analyses.                                          | Human molecular profiling; not a direct source of our dashboard's vital signs.                   |
| **OSD-575** | Blood-serum comprehensive metabolic panels and immune/cardiovascular cytokine assays. | Human biochemical measurements, not daily heart rate, SpO2, sleep, or wearable skin temperature. |

NASA describes the Inspiration4 mission as a short-duration civilian spaceflight, with biospecimens collected at distinct time points before, during, and after flight. Its sampling design should not be equated with the prototype's 30-day daily-monitoring simulation. [5]

## **5. Public metadata versus controlled-access human data**

NASA states that much of OSDR is publicly accessible, including processed results from some astronaut studies, whereas sensitive astronaut sequence data can be subject to controlled access. Whether data are restricted depends on the study and file, not merely on whether an astronaut appears in the study description. [3, 5]

NASA's official controlled-access tutorial describes the process: identify locked files; submit a study-specific request, including an IRB document and a Data User Agreement; verify institutional affiliation; and undergo curation and Data Access Committee review before authorized access. This is **NASA OSDR's own application process**, not evidence of a direct dbGaP application. [4]

**Project access statement:** The Astro-Health Companion team did not request, obtain, download, or train on controlled-access human/astronaut participant files for this prototype. The presence of public metadata, open processed products, or an OSDR accession identifier does not change the provenance of our generated dashboard readings.

## **6. How OSDR metadata and its public API support source verification**

NASA provides a public Biological Data API with a JSON-oriented REST interface and a metadata/query interface supporting tabular outputs. These allow researchers to inspect dataset, assay, sample, file and mission metadata. [2]

The appropriate workflow is to identify a study and examine its organism, collection schedule, measurement technology, biospecimen, units and public/restricted file status. Only **actual, verified downloadable numerical measurements** could justify a fitted simulation parameter, and such provenance would need the original dataset accession, file name, variable/unit, population and extraction method.

**This project did not fit its simulated ranges to any OSDR numerical observations.** Therefore, the API supports *study discovery and scientific traceability*, not claims that the prototype's heart-rate, oxygen, sleep or temperature values are NASA-derived. All simulator ranges and variation settings are independently specified as synthetic engineering assumptions rather than estimated from OSDR human observations.

## **7. Implemented synthetic-data policy and limitations**

The prototype uses a reproducible Python generator with two fictional profiles and **30 daily observations each (60 in total)**. Its outputs include CSV/JSON datasets, separate traceability records, and expected-alert fixtures. The data-import CSV follows this schema:

```
timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c
```

Here `body_temp_c` means **simulated wearable wrist skin temperature**, represented by the existing import field name; it must not be interpreted as core temperature. Sleep hours are attributed to the night ending at the timestamped 08:00 UTC reading. Additional `profile_id`, mission day, anomaly labels and signal-quality fields are kept in the separate traceability data rather than added silently to the frozen five-field CSV contract.

For the synthetic demonstration, the team selected illustrative ordinary-day intervals: resting heart rate 56–68 bpm, SpO2 96–99%, and sleep 6.5–7.5 hours. These are **prototype generation settings, not NASA OSDR astronaut reference ranges or clinically validated normal ranges**. The example wearable wrist skin-temperature set points (33.2 and 33.4°C), variation, timestamps, and fixed random seed are likewise synthetic engineering settings, not values extracted from an OSDR study.

The demonstrator includes a day-20 resting-heart-rate example (78 versus a seven-day baseline of 62 bpm), reduced sleep on days 24–26, and an isolated poor-quality SpO2 reading. These are **deliberately inserted test scenarios**, not observed medical events. Thresholds are transparent *prototype workflow rules*, not clinically validated diagnostic cut-offs.

**Limits:** synthetic values cannot establish astronaut population norms, performance in microgravity, device accuracy, sensitivity/specificity, clinical safety, or disease prediction. A single poor-quality oxygen reading is not a validated physiological event. The system is **offline decision support, not medical diagnosis**. Astronaut facial-drowsiness detection, SANS model training and clinical predictions are **not part of the MVP**.

## **8. Sources reviewed**


1. NASA Science, *About OSDR*: [https://science.nasa.gov/biological-physical/data/osdr/](https://science.nasa.gov/biological-physical/data/osdr/?utm_source=chatgpt.com)
2. NASA, *OSDR Biological Data API*: [https://visualization.osdr.nasa.gov/biodata/api/](https://visualization.osdr.nasa.gov/biodata/api/?utm_source=chatgpt.com)
3. NASA Science, *OSDR — Frequently Asked Questions*: [https://science.nasa.gov/reference/osdr-faq/](https://science.nasa.gov/reference/osdr-faq/?utm_source=chatgpt.com)
4. NASA, *Requesting Controlled Access Datasets*: [https://www.nasa.gov/reference/osdr-tutorials-requesting-controlled-access-datasets/](https://www.nasa.gov/reference/osdr-tutorials-requesting-controlled-access-datasets/?utm_source=chatgpt.com)
5. NASA, *Inspiration4 Mission Datasets*: [https://www.nasa.gov/osdr-latest-news-i4-mission-datasets/](https://www.nasa.gov/osdr-latest-news-i4-mission-datasets/?utm_source=chatgpt.com)