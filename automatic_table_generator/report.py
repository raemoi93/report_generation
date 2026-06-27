import io
import os
import sys

# Must be before any pyplot import
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Spacer, Image, Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black

# tables.py registers 'KF' font and exports constants
from tables import (
    FONT_PATH, CONTENT_W, MARGIN, NAVY, BLUE, GRAY_TEXT, BLACK,
    build_year_table, build_special_box, build_final_avg_box,
    style_note,
)

# Register in reportlab (tables.py already did it, but safe to be explicit)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
try:
    pdfmetrics.getFont('KF')
except KeyError:
    pdfmetrics.registerFont(TTFont('KF', FONT_PATH))

from grade_data import ALL_SEMESTERS
from calculations import compute_all_averages, compute_final_average
from plot import build_grade_figure


# ── Paragraph styles ─────────────────────────────────────────────────────────
def _ps(name, **kw):
    defaults = dict(fontName='KF', fontSize=10, leading=14, textColor=BLACK)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

style_header     = _ps('header',     fontSize=20, leading=26)
style_sec_num    = _ps('sec_num',    fontSize=36, leading=42, alignment=TA_RIGHT,
                        textColor=HexColor('#CCCCCC'))
style_sec_title  = _ps('sec_title',  fontSize=18, leading=26, textColor=BLACK)


def build_header():
    return Paragraph(
        '<font color="#272C61"><b>EDUPREP</b></font>'
        '&nbsp;'
        '<font color="#0077B6"><b>REPORT</b></font>',
        style_header,
    )


def build_section_title():
    num_cell   = Paragraph('01', style_sec_num)
    title_cell = Paragraph('학년별 성적 분포표', style_sec_title)
    t = Table(
        [[num_cell, title_cell]],
        colWidths=[58, CONTENT_W - 58],
    )
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (1, 0), (1, 0),   8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (0, 0), (0, 0),   0),
    ]))
    return t


def build_graph_image(avgs):
    fig = build_grade_figure(avgs)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_h = CONTENT_W * (4.0 / 15.0)
    img = Image(buf, width=CONTENT_W, height=img_h)
    img.hAlign = 'CENTER'
    return img


_YEAR_STRUCTURE = [
    ('1학년', [('1학년1학기', '1학기'), ('1학년2학기', '2학기')]),
    ('2학년', [('2학년1학기', '1학기'), ('2학년2학기', '2학기')]),
    ('3학년', [('3학년1학기', '1학기')]),
]


def build_report(output_path='grade_report.pdf', semesters=None):
    if semesters is None:
        semesters = ALL_SEMESTERS

    avgs = compute_all_averages(semesters)
    final_simple, final_weighted = compute_final_average(semesters)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
    )

    story = []

    # 1. EDUPREP REPORT header
    story.append(build_header())
    story.append(Spacer(1, 12))

    # 2. Section title
    story.append(build_section_title())
    story.append(Spacer(1, 8))

    # 3. Graph
    story.append(build_graph_image(avgs))
    story.append(Spacer(1, 4))

    # 4. Note line
    story.append(Paragraph('(괄호 평균 : 단위수 반영 평균)', style_note))
    story.append(Spacer(1, 4))

    # 5. Year tables — only include semesters that have regular courses
    year_groups = []
    for year_label, sem_defs in _YEAR_STRUCTURE:
        sems = [
            (fk, dl, semesters[fk])
            for fk, dl in sem_defs
            if fk in semesters and semesters[fk]['정규']
        ]
        if sems:
            year_groups.append((year_label, sems))

    for year_label, sems in year_groups:
        story.append(build_year_table(year_label, sems, avgs))
        story.append(Spacer(1, 3))
        story.append(build_special_box(sems))
        story.append(Spacer(1, 12))

    story.pop()   # replace trailing Spacer(1, 12) with smaller gap
    story.append(Spacer(1, 8))

    # 6. Final average box
    story.append(build_final_avg_box(final_simple, final_weighted))

    doc.build(story)
    if isinstance(output_path, str):
        print(f'Report saved to: {os.path.abspath(output_path)}')


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'grade_report.pdf'
    build_report(out)
