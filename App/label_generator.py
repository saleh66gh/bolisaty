import os
from pathlib import Path
from html import escape
from urllib.parse import quote

import pdfkit

from App.models import LabelData
from App.qr_service import generate_phone_qr
from App.config import WKHTMLTOPDF_PATH, LABELS_DIR, QR_DIR


# المتغيرات المتاحة داخل قالب HTML:
# {{store_logo}}
# {{store_name}}
# {{order_number}}
# {{order_date}}
# {{receiver_name}}
# {{receiver_phone}}
# {{receiver_city}}
# {{receiver_district}}
# {{receiver_address}}
# {{receiver_national_address}}
# {{sender_store_name}}
# {{sender_phone}}
# {{sender_address}}
# {{sender_branch}}
# {{shipment_count}}
# {{weight}}
# {{cod_enabled}}
# {{cod_amount}}
# {{products}}
# {{notes}}
# {{qr_phone}}
# {{qr_location}}
# {{font_cairo_regular}}
# {{font_cairo_bold}}


def _safe(value):
    if value is None:
        return ""
    return escape(str(value))


def _file_uri(path):
    if not path:
        return ""

    try:
        p = Path(path)
        if p.exists():
            return p.resolve().as_uri()
    except Exception:
        pass

    # إذا كان الشعار رابط خارجي، نرجعه كما هو
    return str(path)


def _build_products_html(products):
    return "".join(
        f"<div>{_safe(product.quantity)} × {_safe(product.name)}</div>"
        for product in products[:4]
    )


def _replace_template_variables(template_html: str, variables: dict):
    html = template_html

    for key, value in variables.items():
        html = html.replace("{{" + key + "}}", str(value if value is not None else ""))

    return html


def generate_shipping_label(
    data: LabelData,
    sender,
    store=None,
    template_html: str | None = None,
):
    """
    يولد ملف HTML و PDF من قالب HTML محفوظ في قاعدة البيانات.

    مهم:
    - لا يوجد قالب ثابت داخل هذا الملف.
    - يجب تمرير template_html من قاعدة البيانات.
    - store اختياري لكن يستخدم للشعار واسم المتجر إذا توفر.
    """

    if not template_html:
        raise ValueError("Label template HTML is required")

    os.makedirs(LABELS_DIR, exist_ok=True)
    os.makedirs(QR_DIR, exist_ok=True)

    pdf_path = f"{LABELS_DIR}/label_{data.order_number}.pdf"
    html_path = f"{LABELS_DIR}/label_{data.order_number}.html"

    phone_qr_path = f"{QR_DIR}/phone_qr_{data.order_number}.png"
    location_qr_path = f"{QR_DIR}/location_qr_{data.order_number}.png"

    phone_number = (data.receiver_phone or "").replace("+", "").replace(" ", "").strip()
    whatsapp_url = f"https://api.whatsapp.com/send/?phone={phone_number}"

    map_query = data.receiver_national_address or data.receiver_address or ""
    maps_url = f"https://www.google.com/maps/place/{quote(map_query)}"

    generate_phone_qr(whatsapp_url, phone_qr_path)
    generate_phone_qr(maps_url, location_qr_path)

    cairo_regular = Path("App/fonts/Cairo-Regular.ttf").resolve().as_uri()
    cairo_bold = Path("App/fonts/Cairo-Bold.ttf").resolve().as_uri()

    phone_qr_uri = Path(phone_qr_path).resolve().as_uri()
    location_qr_uri = Path(location_qr_path).resolve().as_uri()

    receiver_name = f"{data.receiver_first_name} {data.receiver_last_name}".strip()

    store_name = getattr(store, "store_name", None) or getattr(sender, "store_name", "")
    store_logo = getattr(store, "store_logo", None)

    store_logo_html = ""
    if store_logo:
        store_logo_html = f'<img src="{_file_uri(store_logo)}" class="store-logo">'

    variables = {
        "store_logo": store_logo_html,
        "store_name": _safe(store_name),

        "order_number": _safe(data.order_number),
        "order_date": _safe(data.order_date),

        "receiver_name": _safe(receiver_name),
        "receiver_phone": _safe(data.receiver_phone),
        "receiver_city": _safe(data.receiver_city),
        "receiver_district": _safe(data.receiver_district),
        "receiver_address": _safe(data.receiver_address),
        "receiver_national_address": _safe(data.receiver_national_address),

        "sender_store_name": _safe(getattr(sender, "store_name", "")),
        "sender_phone": _safe(getattr(sender, "store_phone", "")),
        "sender_address": _safe(getattr(sender, "merchant_address", "")),
        "sender_branch": _safe(getattr(sender, "sender_branch", "")),

        "shipment_count": _safe(data.shipment_count),
        "weight": _safe(data.weight),
        "cod_enabled": "نعم" if data.cod_enabled else "لا",
        "cod_amount": _safe(f"{data.cod_amount} ريال" if data.cod_enabled else "0 ريال"),

        "products": _build_products_html(data.products),
        "notes": _safe(data.notes),

        "qr_phone": phone_qr_uri,
        "qr_location": location_qr_uri,

        "font_cairo_regular": cairo_regular,
        "font_cairo_bold": cairo_bold,
    }

    html = _replace_template_variables(template_html, variables)

    with open(html_path, "w", encoding="utf-8") as file:
        file.write(html)

    config = pdfkit.configuration(
        wkhtmltopdf=WKHTMLTOPDF_PATH
    )

    options = {
        "page-width": "100mm",
        "page-height": "150mm",
        "margin-top": "0mm",
        "margin-right": "0mm",
        "margin-bottom": "0mm",
        "margin-left": "0mm",
        "encoding": "UTF-8",
        "enable-local-file-access": "",
        "print-media-type": "",
        "zoom": "1",
    }

    pdfkit.from_file(
        html_path,
        pdf_path,
        configuration=config,
        options=options
    )

    return pdf_path, html_path
