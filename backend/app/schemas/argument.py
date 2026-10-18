from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# Argument Evidence
# ---------------------------------------------------------


class ArgumentEvidenceCreate(BaseModel):
    result_type: str = Field(
        min_length=1,
        max_length=50,
    )

    result_id: int = Field(
        ge=1,
    )

    reference: str | None = Field(
        default=None,
        max_length=255,
    )

    source_id: int | None = Field(
        default=None,
        ge=1,
    )

    role: str = Field(
        default="supporting",
        min_length=1,
        max_length=50,
    )

    note: str | None = None


class ArgumentEvidenceUpdate(BaseModel):
    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    note: str | None = None


class ArgumentEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    result_type: str
    result_id: int
    reference: str | None
    source_id: int | None
    role: str
    note: str | None

    resolved: dict | None = None

# ---------------------------------------------------------
# Argument Category
# ---------------------------------------------------------


class ArgumentCategoryBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    slug: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = None


class ArgumentCategoryCreate(ArgumentCategoryBase):
    pass


class ArgumentCategoryResponse(ArgumentCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------------------------------------------------------
# Argument Premises
# ---------------------------------------------------------


class ArgumentPremiseBase(BaseModel):
    number: int = Field(ge=1)

    statement: str = Field(
        min_length=1,
    )

    description: str | None = None


class ArgumentPremiseCreate(ArgumentPremiseBase):
    pass


class ArgumentPremiseResponse(ArgumentPremiseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    evidence: list[ArgumentEvidenceResponse] = Field(
        default_factory=list,
    )


# ---------------------------------------------------------
# Argument Responses
# ---------------------------------------------------------


class ArgumentResponseBase(BaseModel):
    number: int = Field(ge=1)

    statement: str = Field(
        min_length=1,
    )

    description: str | None = None


class ArgumentResponseCreate(ArgumentResponseBase):
    pass


class ArgumentResponseResponse(ArgumentResponseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    evidence: list[ArgumentEvidenceResponse] = Field(
        default_factory=list,
    )


# ---------------------------------------------------------
# Argument Objections
# ---------------------------------------------------------


class ArgumentObjectionBase(BaseModel):
    number: int = Field(ge=1)

    statement: str = Field(
        min_length=1,
    )

    description: str | None = None


class ArgumentObjectionCreate(ArgumentObjectionBase):
    responses: list[ArgumentResponseCreate] = Field(
        default_factory=list,
    )


class ArgumentObjectionResponse(ArgumentObjectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    responses: list[ArgumentResponseResponse] = Field(
        default_factory=list,
    )


# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------


class ArgumentBase(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    question: str = Field(
        min_length=1,
    )

    summary: str | None = None
    claim: str | None = None
    conclusion: str | None = None

    status: str = Field(
        default="draft",
        pattern="^(draft|review|published|archived)$",
    )


class ArgumentCreate(ArgumentBase):
    category_id: int

    premises: list[ArgumentPremiseCreate] = Field(
        default_factory=list,
    )

    objections: list[ArgumentObjectionCreate] = Field(
        default_factory=list,
    )


class ArgumentResponse(ArgumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    category_id: int

    category: ArgumentCategoryResponse

    premises: list[ArgumentPremiseResponse] = Field(
        default_factory=list,
    )

    objections: list[ArgumentObjectionResponse] = Field(
        default_factory=list,
    )