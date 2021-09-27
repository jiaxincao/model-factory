from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Pipeline:
    name: str
    docker_base_image: str
    main_operator_id: str
    dependent_pipelines: Optional[List[str]] = None
