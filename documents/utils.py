# coding: utf-8
from django.utils import timezone
import io
import os


# Ethiopian month names (Unicode escapes to prevent git encoding corruption)
ET_MONTHS = [
    '\u1218\u1235\u12a8\u1228\u121d',  # Meskerem
    '\u1325\u1245\u121d\u1275',         # Tikimt
    '\u1215\u12f3\u122d',               # Hidar
    '\u1273\u1215\u1233\u1235',         # Tahsas
    '\u1325\u122d',                     # Tir
    '\u12e8\u12ab\u1272\u1275',         # Yekatit
    '\u1218\u130b\u2262\u1275',         # Megabit
    '\u121a\u12eb\u12da\u12eb',         # Miyazya
    '\u130d\u1295\u1266\u1275',         # Ginbot
    '\u1230\u1290',                     # Sene
    '\u1220\u121d\u1208',               # Hamle
    '\u1290\u1240\u1230',               # Nehase
    '\u1333\u1309\u121c',               # Pagume
]


def to_ethiopian(date):
    """Convert Gregorian date to Ethiopian calendar dict."""
    import datetime as dt
    if not date:
        return None
    if hasattr(date, 'date'):
        date = date.date()

    gc_year  = date.year
    gc_month = date.month

    et_year = gc_year - 8 if gc_month >= 9 else gc_year - 9
    et_new_year = dt.date(gc_year if gc_month >= 9 else gc_year - 1, 9, 11)

    delta    = (date - et_new_year).days
    et_month = min(delta // 30 + 1, 13)
    et_day   = min(delta % 30 + 1, 30)

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
    """Return full Ethiopian date string."""
    result = to_ethiopian(date)
    return result['full'] if result else ''


def generate_reference_number(doc_type='INCOMING'):
    """Auto-generate reference number with transaction lock to prevent race conditions."""
    from .models import Document
    from django.db import transaction

    prefixes = {
        'INCOMING': '\u12c8.\u12a8.\u12a0/\u1308\u2262',
        'OUTGOING': '\u12c8.\u12a8.\u12a0/\u12c8\u131a\u12ca',
        'INTERNAL': '\u12c8.\u12a8.\u12a0/\u12c9\u1235\u1325',
    }
    prefix = prefixes.get(doc_type, '\u12c8.\u12a8.\u12a0')
    year   = timezone.now().year

    with transaction.atomic():
        count = Document.objects.select_for_update().filter(
            doc_type=doc_type,
            created_at__year=year,
        ).count()

    seq = str(count + 1).zfill(4)
    return f"{prefix}/{seq}/{year}"


def generate_qr_code(data, logo_path=None, box_size=8, border=3):
    """Generate a QR code PNG as bytes with optional logo in centre."""
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

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
                pass

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    except Exception:
        return _placeholder_png()


def _placeholder_png():
    """1x1 transparent PNG fallback."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
