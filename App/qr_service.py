import qrcode
from pathlib import Path


def generate_phone_qr(phone: str, output_path: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2
    )

    qr.add_data(phone)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

    return output_path