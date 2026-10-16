from django.utils import timezone
from django.utils import timezone
import io
import os


# ── Ethiopian Calendar ────────────────────────────────────────────────
# Ethiopian month names using Unicode escapes to prevent encoding corruption
ET_MONTHS = [
    '\u1218\u1235\u12a8\u1228\u121d',  # Meskerem
    '\u1325\u1245\u121d\u1275',          # Tikimt
    '\u1215\u12f3\u122d',                # Hidar
    '\u1273\u1215\u1233\u1235',          # Tahsas
    '\u1325\u122d',                      # Tir
    '\u12e8\u12ab\u1272\u1275',          # Yekatit
    '\u1218\u130b\u2262\u1275',          # Megabit
    '\u121a\u12eb\u12da\u12eb',          # Miyazya
    '\u130d\u1295\u1266\u1275',          # Ginbot
    '\u1230\u1290',                      # Sene
    '\u1220\u121d\u1208',                # Hamle
    '\u1290\u1240\u1230',                # Nehase
    '\u1333\u1309\u121c',                # Pagume
]


def to_ethiopian(date):
    """
    Convert a Gregorian date to Ethiopian calendar.
    Returns a dict with year, month, day, month_name, full string.
    """
    import datetime
    if not date:
        return None
    if hasattr(date, 'date'):
        date = date.date()

    # Ethiopian New Year falls on Sep 11 (or Sep 12 in leap years)
    gc_year  = date.year
    gc_month = date.month
    gc_day   = date.day

    # Ethiopian year offset
    et_year = gc_year - 8 if gc_month >= 9 else gc_year - 9

    # Calculate Ethiopian month and day
    # Ethiopian calendar starts Sep 11 (Gregorian)
    import datetime as dt
    et_new_year = dt.date(gc_year if gc_month >= 9 else gc_year - 1, 9, 11)

    delta = (date - et_new_year).days
    et_month = delta // 30 + 1
    et_day   = delta % 30 + 1

    if et_month > 13:
        et_month = 13
    if et_day > 30:
        et_day = 30

    month_name = ET_MONTHS[et_month - 1] if 1 <= et_month <= 13 else ''
    full = f'{et_day} {month_name} {et_year} \u12d3.\u121d'

    return {
        'year':       et_year,
        'month':      et_month,
        'day':        et_day,
        'month_name': month_name,
        'full':       full,
        'short':      f'{et_day}/{et_month}/{et_year}',
    }


def ethiopian_date_str(date):
    """Return Ethiopian date as string like: 5 መስከረም 2017 ዓ.ም"""
    result = to_ethiopian(date)
    return result['full'] if result else ''


def generate_reference_number(doc_type='INCOMING'):
    """
    Auto-generate a reference number in format:
      ወ.ከ.አ/ገቢ/0001/2026
    where the number increments per type per year.
    """
    from .models import Document

    prefixes = {
        'INCOMING': 'ወ.ከ.አ/ገቢ',
        'OUTGOING': 'ወ.ከ.አ/ወጪ',
        'INTERNAL': 'ወ.ከ.አ/ውስጥ',
    }
    prefix = prefixes.get(doc_type, 'ወ.ከ.አ')
    year   = timezone.now().year

    count = Document.objects.filter(
        doc_type=doc_type,
        created_at__year=year,
    ).count()

    seq = str(count + 1).zfill(4)
    return f"{prefix}/{seq}/{year}"


def generate_qr_code(data, logo_path=None, box_size=8, border=3):
    """
    Generate a QR code PNG as bytes with optional logo in centre.
    Returns raw PNG bytes.
    """
    try:
        import qrcode
        from PIL import Image
        import io as _io

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Simple black/white QR image
        img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')

        # Embed logo in the centre if provided
        if logo_path and os.path.exists(logo_path):
            try:
                from PIL import ImageDraw
                logo = Image.open(logo_path).convert('RGBA')
                qr_w, qr_h = img.size
                logo_max = int(min(qr_w, qr_h) * 0.25)
                logo.thumbnail((logo_max, logo_max), Image.LANCZOS)
                logo_w, logo_h = logo.size
                pos = ((qr_w - logo_w) // 2, (qr_h - logo_h) // 2)

                # White circle background behind logo
                bg = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(bg)
                pad = 6
                draw.ellipse(
                    [pos[0] - pad, pos[1] - pad,
                     pos[0] + logo_w + pad, pos[1] + logo_h + pad],
                    fill=(255, 255, 255, 255)
                )
                img = Image.alpha_composite(img, bg)
                img.paste(logo, pos, logo)
            except Exception:
                pass  # logo failed — still return valid QR

        buf = _io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    except Exception:
        return _placeholder_png()



    # Embed logo in the centre
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import Image
            logo = Image.open(logo_path).convert('RGBA')
            qr_w, qr_h = img.size
            logo_max = int(min(qr_w, qr_h) * 0.25)
            logo.thumbnail((logo_max, logo_max), Image.LANCZOS)
            logo_w, logo_h = logo.size
            pos = ((qr_w - logo_w) // 2, (qr_h - logo_h) // 2)

            # White circle background behind logo
            from PIL import ImageDraw
            bg = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(bg)
            pad = 6
            draw.ellipse(
                [pos[0] - pad, pos[1] - pad,
                 pos[0] + logo_w + pad, pos[1] + logo_h + pad],
                fill=(255, 255, 255, 255)
            )
            img = Image.alpha_composite(img, bg)
def _placeholder_png():
    """1×1 transparent PNG for when qrcode lib is missing."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
