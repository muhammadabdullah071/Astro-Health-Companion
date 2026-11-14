# Limitations

This prototype is not a medical device and must not be used as a substitute for qualified clinical or
mission-control decisions.

We do not claim clinical validation, diagnostic performance, real astronaut data, or proven prediction of any
condition.

## Data

- All data is simulated. The two profiles (ASTRO-01 and ASTRO-02) are fictional, with engineering values chosen
  for the demo, not distributions fitted to human spaceflight data.
- One reading per day at 08:00 UTC. Real telemetry would be denser, noisier and affected by device artefacts,
  circadian rhythm and context that are not modelled here.
- NASA OSDR was used for context only. None of its values appear in the generated files.
- Sensor quality is carried in a separate sidecar file. The plain five-column readings file cannot express it.

## Alert rules

- The numeric triggers are prototype workflow rules, not medical thresholds, and have no clinical validation.
- The curated sources do not establish universal astronaut normal ranges or validated thresholds, so the app reports
  deviation from each person's own baseline only.
- Rules based only on a personal baseline can miss a slow drift, because the baseline moves with the person.
- The TEMP-01 threshold (0.5 C) is provisional and is pending review against the accuracy and variability of the
  chosen wearable sensor.
- Alerts are monitoring flags, not diagnoses. Operational severity levels (NOTICE, WATCH, ATTENTION) are not
  clinical acuity labels.

## Measurements

- Skin temperature is not core temperature. It depends on sensor placement, contact and conditions, and cannot
  establish a fever or an infection. Manual core-temperature entry is not implemented; if added it must be stored
  separately and never combined with skin readings.
- Wearable proxies cannot diagnose immune dysfunction, radiation injury or bone loss.
- Sleep alone does not diagnose a behavioural-health or psychiatric condition.

## Assistant

- The scientific library is small (nine sources) and mixes astronaut, analogue and animal evidence. Several
  sources have limited access (for example abstract-level only).
- Answers use only retrieved passages, so they are limited by what the library contains. They can still be
  incomplete or wrong. When evidence is missing the assistant says so instead of guessing.
- A small local model runs on a laptop and is less capable than a hosted one. When it is unavailable the assistant
  shows cited excerpts only (retrieval-only mode).

## Engineering scope

- No login or access control. The server listens on the local machine only. Real health data would need
  authentication, role-based access and encryption at rest.
- The API serves one astronaut at a time (set with `ASTRO_ID`). There is no profile switcher.
- Alerts are computed when the database is seeded, not continuously from live sensors.
- There is no integration with real wearables or flight hardware.
- Offline operation has been verified only on the demo setup, after models and papers were downloaded.
- Computer-vision fatigue detection and SANS-style imaging models are future work and are not part of this
  prototype.
