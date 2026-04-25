from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class CheckMetadata(BaseModel):
    """A single validation check applied to a column."""

    name: str = Field(description="Check function name, e.g. 'greater_than'")
    statistics: dict[str, Any] = Field(default_factory=dict, description="Check parameters")
    description: Optional[str] = Field(None, description="Human-readable description")
    error: Optional[str] = Field(None, description="Custom error message")


class ColumnMetadata(BaseModel):
    """Metadata for one column in a DataFrame schema."""

    name: str = Field(description="Column name")
    dtype: Optional[str] = Field(None, description="Pandas dtype string, e.g. 'int64'")
    nullable: bool = Field(False, description="Whether NaN/None values are allowed")
    required: bool = Field(True, description="Whether the column must be present")
    checks: list[CheckMetadata] = Field(default_factory=list, description="Validation checks")
    title: Optional[str] = Field(None, description="Short display label")
    description: Optional[str] = Field(None, description="Column documentation")


class IndexMetadata(BaseModel):
    """Metadata for the DataFrame index."""

    name: Optional[str] = Field(None, description="Index name")
    dtype: Optional[str] = Field(None, description="Index dtype")
    nullable: bool = False
    checks: list[CheckMetadata] = Field(default_factory=list)


class SchemaMetadata(BaseModel):
    """Full metadata for one Pandera schema (DataFrameSchema or DataFrameModel subclass)."""

    name: str = Field(description="Schema name")
    var_name: str = Field(description="Python variable or class name in source file")
    file_path: str = Field(description="File path relative to the scanned project root")
    source_class: Optional[str] = Field(
        None,
        description="Class name if defined via DataFrameModel",
    )
    title: Optional[str] = Field(None, description="Short display title")
    description: Optional[str] = Field(None, description="Schema documentation")
    coerce: bool = Field(False, description="Whether dtypes are coerced automatically")
    columns: list[ColumnMetadata] = Field(default_factory=list)
    index: Optional[IndexMetadata] = None
    metadata_source: Literal["runtime", "ast"] = Field(
        "runtime",
        description="'runtime' = imported and inspected; 'ast' = statically parsed (import failed)",
    )
