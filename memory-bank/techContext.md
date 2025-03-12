# Technical Context: Multi-Agent System for Insurance Policy Recommendations

## Technologies Used

### Core Technologies
- **Python**: Primary programming language for all components
- **Google Gemini**: LLM for natural language processing and generation
- **Jupyter Notebooks**: Environment for experimentation and development

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **PyPDF2/pdfplumber**: PDF document processing for insurance policies

### Visualization & Analysis
- **Matplotlib/Seaborn**: Data visualization
- **scikit-learn**: Evaluation metrics and clustering analysis

### Web Interface (Potential)
- **Streamlit**: Simple web interface for demonstration purposes

## Development Setup

### Environment
- **Python Version**: 3.8+ recommended
- **Package Management**: requirements.txt for dependency tracking
- **Version Control**: Git

### Project Structure
```
/
├── memory-bank/             # Cline's memory bank
├── notebooks/               # Jupyter notebooks for experimentation
│   ├── exploratory/         # Initial data exploration
│   ├── agent_development/   # Agent-specific experiments
│   ├── integration/         # Testing agent interactions
│   ├── evaluation/          # Performance metrics
│   └── demos/               # Demo notebooks
├── data/                    # Data storage
│   ├── insurance_policies/  # Insurance policy documents
│   ├── transcripts/         # Conversation transcripts
│   ├── processed/           # Processed data
│   └── evaluation/          # Evaluation data
├── src/                     # Source code
│   ├── agents/              # Agent implementations
│   ├── models/              # LLM configurations
│   ├── prompts/             # Prompts for LLM tasks
│   ├── utils/               # Utility functions
│   └── web/                 # Web interface components
├── tests/                   # Test cases
└── scripts/                 # Utility scripts
```

### Development Workflow
1. **Experimentation**: Develop and test components in Jupyter notebooks
2. **Code Migration**: Refactor successful notebook code into Python modules
3. **Integration**: Combine components and test interactions
4. **Evaluation**: Measure system performance against ground truth
5. **Documentation**: Document findings and implementation details

## Technical Constraints

### LLM Constraints
- **API Limits**: Google Gemini API may have rate limits and token constraints
- **Latency**: Multiple LLM calls in the voting system may introduce latency
- **Consistency**: LLM outputs may vary between calls with identical inputs

### Data Constraints
- **Policy Format Variability**: Insurance policies may have different formats and structures
- **Synthetic Data Quality**: Quality of synthetic conversation data may impact system performance
- **Ground Truth Creation**: Creating accurate ground truth labels for evaluation requires domain expertise

### Academic Project Constraints
- **Timeline**: Limited development time as an academic project
- **Scope**: Focus on proof-of-concept rather than production-ready system
- **Resources**: Limited computational resources for extensive experimentation

## Dependencies

### External APIs
- **Google Generative AI**: Primary API for accessing Gemini models
- **Email Service** (optional): For sending recommendations to users

### Python Libraries
```python
# Core
google-generativeai  # Google's Python SDK for Gemini
pandas              # Data processing
numpy               # Numerical computing

# Document Processing
pypdf2              # PDF processing
pdfplumber          # Alternative PDF processing

# Visualization & Analysis
matplotlib          # Data visualization
seaborn             # Enhanced visualization
scikit-learn        # ML utilities and metrics

# Notebook Environment
jupyter             # Notebook environment
ipywidgets          # Interactive widgets for notebooks

# Web Interface (Optional)
streamlit           # Simple web interface
```

## Integration Points

### Between Components
- **CS Agent → Extractor**: Conversation transcript
- **Extractor → Analyzers**: Structured requirements
- **Analyzers → Voting System**: Analysis reports
- **Voting System → Recommender**: Voting results

### External Systems
- **Email Service**: For delivering recommendations
- **Web Interface**: For user interaction
- **Storage System**: For persisting conversation history and recommendations

## Technical Roadmap

### Phase 1: Foundation
- Set up development environment
- Create data structures for policies and requirements
- Implement basic document processing

### Phase 2: Agent Development
- Develop CS Agent for conversation handling
- Implement Requirements Extractor
- Create Policy Analyzer prototype

### Phase 3: Integration
- Implement Voting System
- Develop Recommendation Agent
- Integrate components into pipeline

### Phase 4: Evaluation & Refinement
- Create evaluation framework
- Measure system performance
- Refine components based on results

### Phase 5: Documentation & Presentation
- Document system architecture and performance
- Prepare demonstration materials
- Create final academic report
