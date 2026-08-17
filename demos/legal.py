from demos import DemoConfig

config = DemoConfig(
    name="Legal & HR Document Assistant",
    collection="legal",
    data_dir="data/legal",
    fetch_script="scripts/fetch_legal.py",
    system_prompt=(
        "You are a legal and HR document assistant helping business owners, "
        "office managers, and HR teams understand contracts, employment law, "
        "and workplace policies. "
        "Answer questions based strictly on the provided documents. "
        "Cite the exact document filename and page number for every claim. "
        "When referencing legal obligations, quote the relevant clause or section directly. "
        "Always clarify that your answers are informational only and not legal advice — "
        "recommend consulting a qualified attorney for decisions with legal consequences."
    ),
    example_queries=[
        "What are an employer's basic safety and health responsibilities under OSHA?",
        "How do I conduct a job hazard analysis for my workplace?",
        "What are the OSHA hazard communication requirements for chemicals?",
        "What ergonomics measures must employers take to prevent workplace injuries?",
        "What are the minimum wage and pay requirements under federal law?",
    ],
)
