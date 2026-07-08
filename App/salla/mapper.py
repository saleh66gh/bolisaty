from datetime import date
from App.models import LabelData, Product


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

    if isinstance(district, dict):
        return district.get("name") or ""

    return ""


def money_amount(value):
    if not value:
        return 0

    if isinstance(value, dict):
        return value.get("amount", 0) or 0

    return value or 0


def weight_value(value):
    if not value:
        return 1

    if isinstance(value, dict):
        return value.get("value", 1) or 1

    return value or 1


def normalize_order_date(value):
    if not value:
        return date.today().isoformat()

    if isinstance(value, dict):
        value = value.get("date") or ""

    value = str(value)

    if " " in value:
        return value.split(" ")[0]

    if "T" in value:
        return value.split("T")[0]

    return value[:10] or date.today().isoformat()


def build_receiver_address(city, district, national_address, address_line):
    if address_line:
        return address_line

    return " - ".join(
        part for part in [
            city,
            district,
            national_address
        ]
        if part
    )


def map_salla_to_label_data(
    payload: dict,
    template_id: int,
    store_name: str,
) -> LabelData:

    data = payload.get("data", payload)

    ship_to = data.get("ship_to") or {}
    ship_from = data.get("ship_from") or {}
    packages = data.get("packages") or []

    customer_name = ship_to.get("name") or ""
    customer_phone = ship_to.get("phone") or ""

    first_name, last_name = split_customer_name(customer_name)

    order_number = str(
        data.get("order_reference_id")
        or data.get("order_id")
        or data.get("id")
        or ""
    )

    order_date = normalize_order_date(
        data.get("created_at")
        or payload.get("created_at")
    )

    receiver_city = ship_to.get("city") or ""

    receiver_district = (
        get_district_name(ship_to.get("district"))
        or ship_to.get("block")
        or ""
    )

    receiver_national_address = ship_to.get("short_address") or None

    receiver_address = build_receiver_address(
        city=receiver_city,
        district=receiver_district,
        national_address=receiver_national_address,
        address_line=ship_to.get("address_line") or "",
    )

    cod_amount = money_amount(data.get("cash_on_delivery"))
    total_weight = weight_value(data.get("total_weight"))

    shipment_count = int(
        (
            (data.get("meta") or {})
            .get("policy_options") or {}
        ).get("boxes", 1)
        or 1
    )

    products = [
        Product(
            name=item.get("name") or "",
            quantity=item.get("quantity") or 1,
        )
        for item in packages
    ]

    return LabelData(

        # بيانات المتجر
        store_name="",
        store_logo=None,

        # بيانات المرسل (مباشرة من سلة)
        sender_store_name=store_name,
        sender_phone=ship_from.get("phone") or "",
        sender_city=ship_from.get("city") or "",

        sender_district=(
            get_district_name(ship_from.get("district"))
            or ship_from.get("block")
            or ""
        ),

        sender_address=ship_from.get("address_line") or "",
        sender_national_address=ship_from.get("short_address") or "",
        sender_branch=ship_from.get("name") or "",
        sender_logo=None,

        template_id=template_id,

        order_number=order_number,
        order_date=order_date,

        receiver_country=ship_to.get("country") or "السعودية",
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
        notes="",
    )