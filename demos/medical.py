from demos import DemoConfig

config = DemoConfig(
    name="Medical Research",
    collection="pubmed",
    data_dir="data/pubmed",
    fetch_script="scripts/fetch_pubmed.py",
    system_prompt=(
        "You are a medical literature assistant for healthcare professionals. "
        "Answer questions based strictly on the provided research papers. "
        "Cite the exact paper filename and page number for every claim using the required format. "
        "If findings across papers conflict, explicitly note the contradiction. "
        "Never provide clinical advice or speculate beyond what the literature states. "
        "Flag when evidence is limited or findings are from small studies."
    ),
    example_queries=[
        "What are the early diagnostic markers for sepsis?",
        "What treatments have shown the best outcomes for septic shock?",
        "How does procalcitonin compare to lactate as a sepsis biomarker?",
        "What is the recommended antibiotic protocol for sepsis?",
        "What are the long-term outcomes for sepsis survivors?",
    ],
)
