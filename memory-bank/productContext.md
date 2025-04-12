# Product Context

## Why This Project Exists

This project addresses significant challenges in the travel insurance market:

1. **Consumer Challenges**:
   - Insurance policies are complex and filled with technical jargon
   - Information overload makes comparison difficult
   - Cognitive biases affect decision-making
   - Emotional factors influence purchasing decisions
   - Limited time for thorough comparison

2. **Market Gaps**:
   - Lack of personalized recommendation tools
   - Existing solutions often have inherent biases
   - Limited transparency in recommendation processes
   - Insufficient tools for iterative refinement based on evolving needs

3. **Insurance Company Needs**:
   - Deeper insights into customer preferences
   - Better understanding of competitive product positioning
   - More effective ways to match products to customer needs

## Problems It Solves

1. **For Consumers**:
   - Simplifies the complex process of comparing insurance policies
   - Provides personalized recommendations based on individual needs
   - Offers transparent justifications for recommendations
   - Reduces cognitive load and decision fatigue
   - Saves time in the insurance selection process

2. **For Insurance Companies**:
   - Generates insights on product positioning
   - Identifies market gaps and opportunities
   - Improves customer satisfaction through better matching
   - Provides data on customer preferences and priorities

3. **For the Market**:
   - Increases transparency in insurance recommendations
   - Reduces information asymmetry
   - Promotes fair competition based on actual policy value

## How It Should Work (Current Implementation & Vision)

The system currently operates through a series of interconnected scripts and a single agent, focusing on data processing, extraction, and comparison. The original multi-agent conversational vision is not yet implemented.

1.  **Data Generation**:
    *   Synthetic conversation transcripts are generated using LLMs (`scripts/data_generation/generate_transcripts.py`), incorporating defined scenarios, coverage requirements, and customer personalities.

2.  **Transcript Evaluation**:
    *   Generated transcripts are evaluated for quality and coverage using LLMs (`scripts/evaluation/transcript_evaluation/`) before further processing. This acts as a quality gate.

3.  **Information Extraction**:
    *   An Extractor agent (`src/agents/extractor.py` using CrewAI/OpenAI) processes the *evaluated and parsed* transcripts.
    *   Key customer requirements are identified and structured into a validated JSON customer profile (`data/extracted_customer_requirements/`).

4.  **Policy Extraction**:
    *   A script (`scripts/extract_policy_tier.py` using LLMService/Gemini) processes raw policy PDFs.
    *   It extracts structured details about coverage, limits, conditions, and source references into JSON format (`data/policies/processed/`).

5.  **Policy Comparison & Reporting**:
    *   A script (`scripts/generate_policy_comparison.py` using LLMService/Gemini) compares the extracted customer requirements (JSON) against the structured policy data (JSON).
    *   It generates detailed Markdown reports comparing policies at the insurer level, selecting the best tier per insurer and providing justifications.

6.  **Further Evaluation (Planned)**:
    *   Additional evaluation steps are planned to assess the accuracy of the policy extraction and the quality of the comparison reports.

7.  **Iterative Refinement (Manual)**:
    *   Developers can manually update inputs (scenarios, requirements definitions, prompts) and re-run the scripts to refine the outputs (transcripts, extractions, reports). Direct user interaction for refinement is not currently implemented.

8.  **Machine Learning Integration (Future)**:
    *   Supervised ML models are planned to analyze patterns in extracted requirements and comparison results.
    *   Insights on feature importance will inform future development or business strategy.

## User Experience Goals (Developer/Analyst Focused Currently)

While the end-goal includes a user-friendly conversational interface, the current focus delivers value primarily to developers and analysts running the scripts.

1.  **Automation**:
    *   Automates the tedious tasks of transcript generation, requirement extraction, policy data extraction, and comparison.

2.  **Consistency**:
    *   Ensures requirements and policy data are extracted into standardized, structured formats (JSON).
    *   Provides consistent comparison reports based on defined logic.

3.  **Transparency (Code & Reports)**:
    *   The logic is contained within Python scripts and agent prompts.
    *   Comparison reports aim to provide clear justifications (though direct user interaction is missing).

4.  **Data Quality Assurance**:
    *   Evaluation steps (transcript evaluation, planned policy/comparison evaluation) provide checks on the quality of intermediate data.

5.  **Efficiency**:
    *   Significantly faster than manual extraction and comparison.
    *   Batch processing capabilities in scripts enhance throughput.

6.  **Adaptability (Code Level)**:
    *   The script-based nature allows modification of prompts, models, and logic to adapt to changing needs or improve performance.
