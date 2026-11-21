import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors


def draw_pdf_header(p, width, height, subtitle):
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.jpg')
    text_x = 50
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 50, height - 140, width=120, height=120, preserveAspectRatio=True, mask='auto')
        text_x = 185

    p.setFont("Helvetica-Bold", 20)
    p.drawString(text_x, height - 70, "TECH INSTITUTE")
    p.setFont("Helvetica", 11)
    p.drawString(text_x, height - 95, subtitle)
    p.line(50, height - 155, width - 50, height - 155)


def draw_official_stamp(p, x=430, y=130):
    current_date = timezone.localdate().strftime("%d %b %Y").upper()
    stamp_color = colors.HexColor("#1e3a8a")

    p.saveState()
    p.translate(x, y)
    p.rotate(12)

    p.setStrokeColor(stamp_color)
    p.setFillColor(stamp_color)

    p.setLineWidth(2.2)
    p.roundRect(-85, -42, 170, 84, 6, stroke=1, fill=0)
    p.setLineWidth(0.8)
    p.roundRect(-81, -38, 162, 76, 4, stroke=1, fill=0)

    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(0, 20, "TECH INSTITUTE")

    p.line(-72, 13, 72, 13)
    p.line(-72, -10, 72, -10)

    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(0, -2, current_date)

    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(0, -27, "APPROVED")

    p.restoreState()
