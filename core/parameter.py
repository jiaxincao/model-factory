from dataclasses import dataclass
import typing


@dataclass
class ParameterGroup:
    name: str
    parameters: typing.Optional[typing.List[str]] = None


class Parameter:
    def __init__(self, name, default=None, mandatory=True, help_msg=""):
        self.name = name
        self.default = default
        self.mandatory = mandatory and default is None
        self.help_msg = help_msg
