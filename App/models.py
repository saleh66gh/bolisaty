from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class Product(BaseModel):
    name: str
    quantity: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("اسم المنتج إجباري")
        return value.strip()

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError("عدد المنتج يجب أن يكون أكبر من صفر")
        return value


class LabelData(BaseModel):
    store_name: str
    store_logo: Optional[str] = None
    order_number: str
    order_date: date
    sender_id: int
    receiver_country: str
    receiver_first_name: str
    receiver_last_name: Optional[str] = None
    receiver_phone: str
    receiver_city: str
    receiver_district: str
    receiver_address: str
    receiver_national_address: Optional[str] = None

    shipment_count: int
    weight: float
    cod_enabled: bool
    cod_amount: float = 0

    products: List[Product]
    notes: Optional[str] = ""
    template_id: int

    @field_validator("order_number")
    @classmethod
    def validate_order_number(cls, value):
        if not value.isdigit():
            raise ValueError("رقم الطلب يجب أن يكون أرقام فقط")
        return value

    @field_validator("receiver_phone")
    @classmethod
    def validate_phone(cls, value):
        cleaned = value.replace("+", "")
        if not cleaned.isdigit():
            raise ValueError("رقم الهاتف يجب أن يحتوي أرقام فقط مع إمكانية +")
        if len(cleaned) < 10:
            raise ValueError("رقم الهاتف غير صحيح")
        return value

    @field_validator("receiver_country", "receiver_city", "receiver_district")
    @classmethod
    def validate_required_text(cls, value):
        if not value or not str(value).strip():
            raise ValueError("هذا الحقل إجباري")
        return str(value).strip()

    @field_validator("receiver_national_address")
    @classmethod
    def validate_national_address(cls, value):
        if not value:
            return value
        if not re.fullmatch(r"[A-Za-z]{4}\d{4}", value):
            raise ValueError("العنوان الوطني يجب أن يكون 4 حروف و 4 أرقام")
        return value.upper()

    @field_validator("receiver_address")
    @classmethod
    def validate_address(cls, value):
        if not value or not str(value).strip():
            raise ValueError("العنوان إجباري")
        return str(value).strip()

    @field_validator("shipment_count")
    @classmethod
    def validate_shipment_count(cls, value):
        if value <= 0:
            raise ValueError("عدد الشحنات يجب أن يكون أكبر من صفر")
        return value

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value):
        if value <= 0:
            raise ValueError("الوزن يجب أن يكون أكبر من صفر")
        return value
