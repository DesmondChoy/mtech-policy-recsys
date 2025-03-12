# Project Brief: Multi-Agent System for Insurance Policy Recommendations

## Overview
This project aims to develop a multi-agent system for insurance policy recommendations, initially focused on travel insurance but with potential expansion to other insurance types (life, critical illness, etc.). The system addresses common pain points in insurance purchasing by providing personalized, transparent, and objective recommendations.

## Pain Points Addressed
- **Complexity and Jargon**: Insurance policies are difficult to understand due to technical language and intricate details.
- **Information Overload and Asymmetry**: Too much information presented in ways that benefit insurers rather than consumers.
- **Lack of Trust and Transparency**: Consumer skepticism about hidden terms and claim denials.
- **Cognitive Biases**: Mental shortcuts leading to poor choices.
- **Emotional Decision-Making**: Fear and anxiety overriding rational analysis.
- **Time Constraints**: Thorough policy comparison is time-consuming.

## Key Advantages
- **Personalization**: Tailored recommendations based on individual needs.
- **Transparency**: Clear explanations of policy details and comparisons.
- **Objectivity**: Reduced bias from commission-driven sales.
- **Efficiency**: Saves time and effort for the customer.
- **Improved Decision-Making**: Helps customers make more informed choices.

## Technical Workflow
1. **Gather Requirements**: Customer interacts with a Customer Service (CS) agent that collects information.
2. **Document Requirements**: Call transcript is processed to extract key customer requirements.
3. **Policy Analysis**: Customer requirements are compared against insurance policies.
4. **Voting**: Multiple LLM instances analyze and vote on the most suitable policy.
5. **Recommendation**: Results are consolidated and recommendations are sent to the customer.
6. **Follow-up**: Customer can provide additional requirements and receive updated recommendations.

## Data Sources
- Travel insurance policies (public data)
- Customer conversation transcripts (synthetic or real)

## Success Metrics
- Accuracy of system recommendations against ground truth labels
- User satisfaction and decision confidence
- Time saved in the insurance selection process

## Project Scope
- Initial focus on travel insurance
- Python-based implementation
- Google Gemini for LLM components
- Academic project with emphasis on experimentation in Jupyter notebooks
