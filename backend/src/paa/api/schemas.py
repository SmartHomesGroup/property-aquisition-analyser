"""Response models. Every statistic carries its bracket: n, window, radius, reference date."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

PropertyType = Literal["A", "D", "S", "T", "F"]
Precision = Literal["postcode", "street", "district"]
WINDOWS: tuple[int, ...] = (12, 24, 60)

PROPERTY_TYPE_LABEL: dict[str, str] = {
    "A": "all types",
    "D": "detached",
    "S": "semi-detached",
    "T": "terraced",
    "F": "flats",
}


class BuildInfo(BaseModel):
    built_at: str | None
    ref_date: date | None = Field(description="Latest sale held; time windows count back from here")
    hpi_ref_month: date | None = Field(description="Prices are HPI-adjusted to this month")
    sales_total: int | None
    sales_matched: int | None
    sales_enriched: int | None
    cells: int | None
    synthetic: bool = Field(description="True when floor areas include development-only fakes")
    listing_analysis: bool = Field(description="Whether POST /listings/analyse is available")
    attribution: list[str]


class PostcodeLocation(BaseModel):
    postcode: str
    lat: float
    lon: float
    easting: int
    northing: int
    district_code: str | None
    positional_quality: int


class Sale(BaseModel):
    transaction_id: str
    address: str
    postcode: str
    date_of_transfer: date
    price: int
    price_adj: int | None
    floor_area_m2: float
    ppm2: int
    ppm2_adj: int | None
    property_type: str
    new_build: bool
    energy_rating: str | None
    distance_m: int


class Bracket(BaseModel):
    """What the numbers are based on. Shown verbatim in the UI."""

    radius_m: int
    window_months: int
    property_type: PropertyType
    property_type_label: str
    since: date
    until: date
    hpi_ref_month: date | None
    n: int


class Distribution(BaseModel):
    p10: int | None
    p25: int | None
    median: int | None
    p75: int | None
    p90: int | None
    median_floor_area_m2: float | None


class Subject(BaseModel):
    """The pinned property, when the user supplied a price and floor area."""

    asking_price: int
    floor_area_m2: float
    ppm2: int
    vs_median_pct: float | None = Field(description="(subject - median) / median * 100")
    percentile: float | None = Field(description="Share of local sales with lower £/m², 0..100")


class AreaStats(BaseModel):
    bracket: Bracket
    ppm2_adj: Distribution
    subject: Subject | None
    recent_sales: list[Sale]


class Comparables(BaseModel):
    bracket: Bracket
    floor_area_m2: float
    tolerance_pct: int
    sales: list[Sale]


class ListingProperty(BaseModel):
    """What we could identify about the listed property from the engine's output."""

    address: str | None
    postcode: str | None = Field(description="Formatted, e.g. 'PR1 2AB', when found")
    asking_price: int | None
    property_type: Literal["D", "S", "T", "F"] | None
    bedrooms: int | None
    location: PostcodeLocation | None = Field(
        description="Where to drop the pin: postcode centroid, street centroid or district centroid"
    )
    precision: Precision | None = Field(
        description="How `location` was found; street is ~100s of m, district is kilometres"
    )


class ListingAnalysis(BaseModel):
    id: int
    url: str
    requested_at: str
    cached: bool = Field(description="True when a stored analysis of this URL was re-used")
    duration_ms: int | None
    engine: str
    property: ListingProperty
    fields: dict[str, Any] = Field(description="The engine's response, verbatim")
