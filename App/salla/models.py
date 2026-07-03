# App/salla/models.py

from pydantic import BaseModel
from typing import Optional, List, Any


class SallaMoney(BaseModel):
    amount: float | int = 0
    currency: str = "SAR"


class SallaDistrict(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class SallaAddress(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    district: Optional[SallaDistrict | str] = None
    address_line: Optional[str] = None
    address_line_two: Optional[str] = None
    street_number: Optional[str] = None
    block: Optional[str] = None
    short_address: Optional[str] = None
    building_number: Optional[str] = None
    additional_number: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    branch_id: Optional[int] = None


class SallaItem(BaseModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    name: str = ""
    sku: Optional[str] = None
    quantity: int = 1
    weight: Optional[float] = None


class SallaShipment(BaseModel):
    id: Optional[int] = None
    courier_id: Optional[int] = None
    courier_name: Optional[str] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    total_weight: Optional[dict] = None
    cash_on_delivery: Optional[dict] = None
    ship_from: Optional[SallaAddress] = None
    ship_to: Optional[SallaAddress] = None
    packages: List[Any] = []


class SallaCustomer(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None


class SallaShipmentPayloadData(BaseModel):
    id: Optional[int] = None
    reference_id: Optional[str | int] = None
    number: Optional[str | int] = None
    created_at: Optional[str] = None
    date: Optional[str] = None
    shipment_reference: Optional[str | int] = None
    policy_options: Optional[dict] = None

    customer: Optional[SallaCustomer] = None
    address: Optional[dict] = None
    items: List[SallaItem] = []
    shipments: List[SallaShipment] = []


class SallaEventPayload(BaseModel):
    event: Optional[str] = None
    merchant: Optional[str | int] = None
    created_at: Optional[str] = None
    data: Optional[dict] = None