from pydantic import BaseModel, Field


class Parameter(BaseModel):
    p_name: str = Field(min_length=1)
    p_type: str = Field(min_length=1)

    def __str__(self) -> str:
        return (
            f"\"{self.p_name}\":" "{"
            f"\"type\":\"{self.p_type}\"" "}"
        )


class FunctDef(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(default="")
    parameters: list[Parameter] = Field()
    returns: str = Field(min_length=1)

    def __str__(self) -> str:
        return (
            f"\"name\":\"{self.name}\","
            f"\"description\":\"{self.description}\","
            "\"parameters\":"
            f"{','.join(map(str, self.parameters))}"
            f",\"return type\":\"{self.returns}\"\n"
        )


class DefFunctException(Exception):

    e_len: int

    def __init__(self, e_len: int, *args: object) -> None:
        super().__init__(*args)
        self.e_len = e_len
