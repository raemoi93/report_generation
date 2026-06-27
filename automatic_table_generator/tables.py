import os
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Font registration ────────────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_CANDIDATES = [
    os.path.join(_THIS_DIR, 'fonts', 'NanumGothic-Regular.ttf'),  # bundled TTF — works everywhere
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',         # macOS fallback
]
FONT_PATH = next(p for p in _FONT_CANDIDATES if os.path.exists(p))
pdfmetrics.registerFont(TTFont('KF', FONT_PATH))

# ── Colors ───────────────────────────────────────────────────────────────────
NAVY      = HexColor('#272C61')
BLUE      = HexColor('#0077B6')
GRAY_GRID = HexColor('#CCCCCC')
GRAY_TEXT = HexColor('#888888')
GRAY_BOX  = HexColor('#BBBBBB')
SOFT_BG   = HexColor('#F7F7F7')
BLACK     = HexColor('#1A1A1A')

# ── Layout constants ─────────────────────────────────────────────────────────
MARGIN     = 42
CONTENT_W  = A4[0] - 2 * MARGIN   # ≈ 511 pt
LEFT_COL_W = 60                    # semester info column

# ── Shared paragraph styles ──────────────────────────────────────────────────
def _style(name, **kw):
    defaults = dict(fontName='KF', fontSize=8.5, leading=12, textColor=BLACK)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

style_sem_cell    = _style('sem_cell',    fontSize=7.5, alignment=TA_CENTER, leading=11)
style_course_name = _style('course_name', fontSize=7,   alignment=TA_CENTER, wordWrap='LTR')
style_grade       = _style('grade',       fontSize=7,   alignment=TA_CENTER, wordWrap='LTR')
style_hdr         = _style('hdr',         fontSize=10,  alignment=TA_CENTER,
                            textColor=white, leading=14)
style_special     = _style('special',     fontSize=7.5, alignment=TA_LEFT,
                            textColor=GRAY_TEXT, leading=12)
style_final       = _style('final_avg',   fontSize=11,  alignment=TA_CENTER,
                            leading=16, textColor=NAVY)
style_note        = _style('note',        fontSize=8,   alignment=TA_RIGHT,
                            textColor=GRAY_TEXT)


def _course_name_str(course):
    name = course['과목명'].replace(' ', ' ')  # non-breaking space prevents mid-name line breaks
    return f"{name}({course['단위수']})"


def _grade_str(course):
    g = course.get('석차등급')
    return f'{g}등급' if g is not None else '-'


def _sem_cell_str(sem_label, simple, weighted):
    return f'{sem_label}<br/>평균 {simple:.2f}<br/>(평균 {weighted:.2f})'


def build_year_table(year_label, semesters_data, avgs):
    """
    year_label:     '1학년' | '2학년' | '3학년'
    semesters_data: list of (full_key, display_label, data_dict)
                    e.g. [('1학년1학기', '1학기', {...}), ...]
    avgs:           dict from compute_all_averages()
    """
    max_courses = max(len(d['정규']) for _, _, d in semesters_data)
    course_col_w = (CONTENT_W - LEFT_COL_W) / max_courses
    col_widths = [LEFT_COL_W] + [course_col_w] * max_courses
    total_cols = 1 + max_courses

    # ── Build table data ──────────────────────────────────────────────────────
    table_data = []

    # Header row
    table_data.append(
        [Paragraph(f'{year_label} 교과성적', style_hdr)] + ['' for _ in range(max_courses)]
    )

    for (full_key, disp_label, data) in semesters_data:
        sem_avg = avgs[full_key]
        sem_text = _sem_cell_str(disp_label, sem_avg['simple'], sem_avg['weighted'])

        regular = data['정규']
        n = len(regular)
        padding = max_courses - n

        # Sub-row 1: course names
        name_row = [Paragraph(sem_text, style_sem_cell)]
        name_row += [Paragraph(_course_name_str(c), style_course_name) for c in regular]
        name_row += [Paragraph('-', style_course_name)] * padding
        table_data.append(name_row)

        # Sub-row 2: grades
        grade_row = ['']   # placeholder for SPAN
        grade_row += [Paragraph(_grade_str(c), style_grade) for c in regular]
        grade_row += [Paragraph('-', style_grade)] * padding
        table_data.append(grade_row)

    # ── TableStyle ───────────────────────────────────────────────────────────
    n_rows = len(table_data)
    cmds = [
        # Header
        ('SPAN',        (0, 0), (total_cols - 1, 0)),
        ('BACKGROUND',  (0, 0), (total_cols - 1, 0), NAVY),
        ('TOPPADDING',  (0, 0), (total_cols - 1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (total_cols - 1, 0), 8),
        ('LEFTPADDING', (0, 0), (total_cols - 1, 0), 6),
        ('RIGHTPADDING', (0, 0), (total_cols - 1, 0), 6),
        # Global defaults
        ('FONTNAME',    (0, 0), (-1, -1), 'KF'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',       (1, 1), (-1, -1), 'CENTER'),
        # Outer box
        ('BOX',         (0, 0), (-1, -1), 1, GRAY_GRID),
        # Inner vertical lines for course columns
        ('INNERGRID',   (1, 1), (-1, -1), 0.5, GRAY_GRID),
        # Padding for content cells
        ('TOPPADDING',  (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 1), (-1, -1), 3),
        ('RIGHTPADDING', (0, 1), (-1, -1), 3),
        # Left semester info cell padding
        ('TOPPADDING',  (0, 1), (0, -1), 8),
        ('BOTTOMPADDING', (0, 1), (0, -1), 8),
    ]

    # SPAN and style for each semester's left cell
    for i, (full_key, disp_label, data) in enumerate(semesters_data):
        name_row_idx  = 1 + i * 2
        grade_row_idx = 2 + i * 2
        cmds += [
            ('SPAN',      (0, name_row_idx), (0, grade_row_idx)),
            ('ALIGN',     (0, name_row_idx), (0, grade_row_idx), 'CENTER'),
            # Thin line between course-name and grade sub-rows
            ('LINEBELOW', (1, name_row_idx), (total_cols - 1, name_row_idx),
             0.5, GRAY_GRID),
        ]
        # Separator between semesters (but not after the last one)
        if i < len(semesters_data) - 1:
            cmds.append(
                ('LINEBELOW', (0, grade_row_idx), (total_cols - 1, grade_row_idx),
                 1, GRAY_GRID)
            )

    # Row heights
    row_heights = [20]  # header
    for _ in semesters_data:
        row_heights += [18, 15]  # name sub-row, grade sub-row

    t = Table(table_data, colWidths=col_widths,
              rowHeights=row_heights,
              style=TableStyle(cmds),
              hAlign='LEFT')
    return t


def build_special_box(semesters_data):
    """
    semesters_data: list of (full_key, display_label, data_dict)
    Returns a Table flowable with dashed border containing special courses text.
    """
    lines = ['<b>— 진로 선택 과목 / 체육·예술 —</b>']

    for (_, disp_label, data) in semesters_data:
        jinro  = [c for c in data['특별'] if c['구분'] == '진로선택']
        cheyuk = [c for c in data['특별'] if c['구분'] == '체육예술']

        jinro_parts  = [f"{c['과목명']}({c['단위수']}) {c['등급']}" for c in jinro]
        cheyuk_parts = [f"{c['과목명']}{c['등급']}" for c in cheyuk]

        jinro_str  = '·'.join(jinro_parts)  if jinro_parts  else '-'
        cheyuk_str = '·'.join(cheyuk_parts) if cheyuk_parts else '-'

        lines.append(f'({disp_label}) {jinro_str} / {cheyuk_str}')

    content = '<br/>'.join(lines)
    para = Paragraph(content, style_special)

    t = Table([[para]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BOX',            (0, 0), (-1, -1), 0.8, GRAY_BOX, 0, (4, 4)),
        ('TOPPADDING',     (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
        ('LEFTPADDING',    (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ('BACKGROUND',     (0, 0), (-1, -1), SOFT_BG),
    ]))
    t.hAlign = 'LEFT'
    return t


def build_final_avg_box(final_simple, final_weighted):
    text = f'최종 평균  {final_simple:.2f}  ({final_weighted:.2f})'
    para = Paragraph(text, style_final)
    t = Table([[para]], colWidths=[170])
    t.setStyle(TableStyle([
        ('BOX',            (0, 0), (-1, -1), 1.5, BLUE),
        ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',     (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 9),
    ]))
    t.hAlign = 'RIGHT'
    return t
