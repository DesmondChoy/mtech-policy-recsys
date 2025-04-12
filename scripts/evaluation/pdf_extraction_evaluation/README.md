# PDF Extraction Evaluation Scripts

This directory contains scripts related to evaluating the accuracy and completeness of the structured data extracted from policy PDF documents.

## Scripts

-   **`eval_pdf_extraction.py`**: Compares a processed policy JSON file against its source PDF using a multi-modal LLM to verify the extraction quality. It performs a two-way check (JSON vs. PDF and PDF vs. JSON) and outputs a structured JSON report detailing matches, mismatches, and missing information.
