from demos import DemoConfig

config = DemoConfig(
    name="Tech Support (FastAPI Docs)",
    collection="tech_support",
    data_dir="data/tech_support",
    fetch_script="scripts/fetch_docs.py",
    system_prompt=(
        "You are a technical support assistant for FastAPI developers. "
        "Answer questions based strictly on the provided documentation pages. "
        "Always cite the source URL and section for every answer. "
        "Provide numbered step-by-step instructions where applicable. "
        "If the documentation does not cover the question, say so explicitly — do not guess. "
        "Use code examples from the docs when they are relevant."
    ),
    example_queries=[
        "How do I define path parameters in FastAPI?",
        "How do I add request body validation with Pydantic?",
        "What is dependency injection in FastAPI and how do I use it?",
        "How do I add authentication to a FastAPI endpoint?",
        "How do I handle file uploads in FastAPI?",
    ],
)
