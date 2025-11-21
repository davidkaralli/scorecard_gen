import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# FIXME: fix these font paths so it works for your system.
font_dir = os.path.join('/', 'mnt', 'c', 'Windows', 'Fonts')
pdfmetrics.registerFont(TTFont('Arial', os.path.join(font_dir, 'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBd', os.path.join(font_dir, 'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('ArialI', os.path.join(font_dir, 'ariali.ttf')))
pdfmetrics.registerFont(TTFont('ArialBI', os.path.join(font_dir, 'arialbi.ttf')))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='ArialBd', italic='ArialI', boldItalic='ArialBI')
