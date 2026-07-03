from App.models import LabelData, Product
from App.salla.models import SallaShipmentPayloadData


def split_customer_name(full_name: str):
    parts = (full_name or "").strip().split()

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def get_district_name(district):
    if not district:
        return ""

    if isinstance(district, str):
        return district

    return district.name or ""


def money_amount(value: dict | None):
    if not value:
        return 0

    return value.get("amount", 0) or 0


def weight_value(value: dict | None):
    if not value:
        return 1

    return value.get("value", 1) or 1


def map_salla_to_label_data(
    data: SallaShipmentPayloadData,
    sender_id: int,
    template_id: int,
) -> LabelData:

    shipment = data.shipments[0] if data.shipments else None

    ship_to = shipment.ship_to if shipment and shipment.ship_to else None
    order_date_value = data.date

    if isinstance(order_date_value, dict):
        order_date_value = order_date_value.get("date") or ""
    customer_name = ""
    customer_phone = ""

    if ship_to:
        customer_name = ship_to.name or ""
        customer_phone = ship_to.phone or ""

    if data.customer:
        customer_name = customer_name or data.customer.name or ""
        customer_phone = customer_phone or data.customer.mobile or ""

    first_name, last_name = split_customer_name(customer_name)

    order_number = str(
        data.shipment_reference
        or data.reference_id
        or data.number
        or data.id
        or (shipment.id if shipment else "")
        or ""
    )

    cod_amount = money_amount(
        shipment.cash_on_delivery if shipment else None
    )

    total_weight = weight_value(
        shipment.total_weight if shipment else None
    )

    shipment_count = 1
    if data.policy_options:
        shipment_count = int(data.policy_options.get("boxes", 1) or 1)

    products = [
        Product(
            name=item.name or "",
            quantity=item.quantity or 1
        )
        for item in data.items
    ]
    receiver_city = ship_to.city if ship_to else ""
    receiver_district = get_district_name(ship_to.district) if ship_to else ""
    receiver_national_address = ship_to.short_address if ship_to else None
    receiver_address = ship_to.address_line if ship_to else ""

    if not receiver_address:
        receiver_address = " - ".join(
            part for part in [
                receiver_city,
                receiver_district,
                receiver_national_address
            ]
            if part
        )

    return LabelData(
        store_name="",
        store_logo=None,
        order_date=str(order_date_value or data.created_at or ""),
        sender_id=sender_id,
        template_id=template_id,

        order_number=order_number,

        receiver_country=ship_to.country if ship_to else "السعودية",
        receiver_first_name=first_name,
        receiver_last_name=last_name,
        receiver_phone=customer_phone,

        receiver_city=receiver_city,
        receiver_district=receiver_district,
        receiver_address=receiver_address,
        receiver_national_address=receiver_national_address,

        shipment_count=shipment_count,
        weight=float(total_weight),

        cod_enabled=float(cod_amount) > 0,
        cod_amount=float(cod_amount),

        products=products,
        notes=""
    )