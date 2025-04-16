# UX Web App Data Sources

This document describes the key data sources used by the TravelSafe Recommender System UX web application. This information is intended to aid maintainability, transparency, and onboarding for developers and stakeholders.

## Data Source Overview

- **customer_ids.json**
  - Contains the list of valid customer IDs (UUIDs) available for login and demo.
  - Used to populate the customer ID dropdown and validate manual entries.

- **data/**
  - Contains supporting data files, such as extracted customer requirements and policy documents.
  - Example subfolders:
    - `extracted_customer_requirements/`: JSON files with requirements for each customer/scenario.
    - `policies/raw/`: Raw policy PDF files for all insurers.
    - `transcripts/raw/synthetic/`: JSON transcripts of customer interactions (real or synthetic).

- **results/**
  - Contains output and report files generated for each customer ID (UUID).
  - Example contents:
    - `recommendation_report_{uuid}.md`: Markdown report with personalized recommendations.
    - `policy_comparison_report_{insurer}.md`: Comparison reports for each insurer.

## Integration Points
- The app loads customer IDs from `customer_ids.json` for login and validation.
- After login, the app loads reports and requirements from the `results/` and `data/` folders, based on the selected customer ID.
- All data files are static and bundled in the public directory for MVP/demo purposes.

## Maintenance Notes
- Update `customer_ids.json` and the contents of `data/` and `results/` as new customers, requirements, or reports are generated.
- For production, consider securing sensitive data and/or moving to API-based data delivery.

---

_Last updated: 2025-04-16_
