from dataclasses import dataclass, field


@dataclass
class DemoConfig:
    name: str
    collection: str
    data_dir: str
    system_prompt: str
    example_queries: list[str] = field(default_factory=list)
    fetch_script: str = ""
