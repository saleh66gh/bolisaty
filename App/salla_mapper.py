from App.models import LabelData, Product


def _get(data: dict, path: str, default=None):
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _split_name(full_name: str):
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def map_salla_payload_to_label_data(payload: dict, sender_id: int, template_id: int) -> LabelData:
    data = payload.get("data", payload)

    shipment = (data.get("shipments") or [{}])[0]
    ship_to = shipment.get("ship_to") or data.get("address") or {}
    customer = data.get("customer") or {}

    full_name = ship_to.get("name") or customer.get("name") or ""
    first_name, last_name = _split_name(full_name)

    cod_amount = _get(shipment, "cash_on_delivery.amount", 0) or 0
    weight = _get(shipment, "total_weight.value", 1) or 1

    products = [
        ProductItem(
            name=item.get("name", ""),
            quantity=item.get("quantity", 1)
        )
        for item in (data.get("items") or shipment.get("packages") or [])
    ]

    order_number = str(
        data.get("reference_id")
        or data.get("number")
        or data.get("id")
        or data.get("shipment_reference")
        or shipment.get("id")
        or ""
    )

    return LabelData(
        store_name="بوليصتي",
        store_logo=None,
        sender_id=sender_id,
        order_number=order_number,
        order_date=str(data.get("date") or data.get("created_at") or ""),

        template_id=template_id,

        receiver_country=ship_to.get("country") or "السعودية",
        receiver_first_name=first_name,
        receiver_last_name=last_name,
        receiver_phone=ship_to.get("phone") or customer.get("mobile") or "",
        receiver_city=ship_to.get("city") or _get(data, "address.city", ""),
        receiver_district=(
            _get(ship_to, "district.name")
            or ship_to.get("block")
            or _get(data, "address.block", "")
        ),
        receiver_address=(
            ship_to.get("address_line")
            or _get(data, "address.shipping_address", "")
        ),
        receiver_national_address=(
            ship_to.get("short_address")
            or _get(data, "address.short_address", None)
        ),

        shipment_count=int(_get(data, "policy_options.boxes", 1) or 1),
        weight=float(weight),
        cod_enabled=float(cod_amount) > 0,
        cod_amount=float(cod_amount),

        products=products,
        notes=""
    )