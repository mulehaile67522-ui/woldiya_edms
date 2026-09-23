from django.utils import timezone
import io
import os


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
    Generate a QR code PNG as bytes.
    If logo_path is provided and Pillow is available, embed the logo
    in the centre of the QR code (the Woldiya City emblem).
    Returns raw PNG bytes.
    """
    try:
        import qrcode
        from qrcode.image.styledimage import StyledPilImage
        from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    except ImportError:
        # qrcode not installed – return a placeholder 1×1 transparent PNG
        return _placeholder_png()

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
        )
        img = img.convert('RGBA')
    except Exception:
        img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')

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
            img.paste(logo, pos, logo)
        except Exception:
            pass  # logo embedding failed — still return a valid QR

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _placeholder_png():
    """1×1 transparent PNG for when qrcode lib is missing."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
