"""Types for the contact form (PRD-W section 7)."""

import uuid
from dataclasses import dataclass
from enum import StrEnum


class Topic(StrEnum):
    legacy_modernisation = "legacy_modernisation"
    ai_product_delivery = "ai_product_delivery"
    product_data_early_access = "product_data_early_access"
    partnership = "partnership"
    other = "other"


TOPIC_LABELS: dict[Topic, str] = {
    Topic.legacy_modernisation: "Legacy modernisation",
    Topic.ai_product_delivery: "AI product delivery",
    Topic.product_data_early_access: "Product data early access",
    Topic.partnership: "Partnership",
    Topic.other: "Other",
}


class DataRegion(StrEnum):
    eu_uk = "eu_uk"
    india = "india"
    other = "other"


DATA_REGION_LABELS: dict[DataRegion, str] = {
    DataRegion.eu_uk: "EU or UK",
    DataRegion.india: "India",
    DataRegion.other: "Other",
}


@dataclass(frozen=True)
class EnquiryIn:
    name: str
    email: str
    company: str
    role: str | None
    topic: Topic
    data_region: DataRegion | None
    message: str


@dataclass(frozen=True)
class FieldError:
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class PendingMail:
    id: uuid.UUID
    enquiry: EnquiryIn
    team_pending: bool
    reply_pending: bool
