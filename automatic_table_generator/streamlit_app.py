"""
EDUPREP grade input UI.
Run from the sort_photos directory:
    streamlit run automatic_table_generator/streamlit_app.py
"""
import io
import os
import sys

import fitz  # pymupdf — cross-platform PDF → JPEG
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import build_report

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title='EDUPREP 성적 입력', layout='wide')
st.title('EDUPREP 성적 입력')

# ── Constants ─────────────────────────────────────────────────────────────────
SEMESTER_DEFS = [
    ('1학년1학기', '1학년 1학기'),
    ('1학년2학기', '1학년 2학기'),
    ('2학년1학기', '2학년 1학기'),
    ('2학년2학기', '2학년 2학기'),
    ('3학년1학기', '3학년 1학기'),
]
DEFAULT_REG = 6
DEFAULT_SPC = 3

# ── Session state defaults ─────────────────────────────────────────────────────
for sk, _ in SEMESTER_DEFS:
    st.session_state.setdefault(f'{sk}_n_reg', DEFAULT_REG)
    st.session_state.setdefault(f'{sk}_n_spc', DEFAULT_SPC)

# ── Per-semester input sections ────────────────────────────────────────────────
all_semesters = {}

for sem_key, sem_label in SEMESTER_DEFS:
    with st.expander(sem_label, expanded=False):

        # ── Regular courses ──────────────────────────────────────────────────
        st.markdown('**정규 과목**')
        h0, h1, h2 = st.columns([5, 2, 2])
        h0.caption('과목명')
        h1.caption('단위수')
        h2.caption('석차등급 (1~9)')

        regular = []
        for i in range(st.session_state[f'{sem_key}_n_reg']):
            c0, c1, c2 = st.columns([5, 2, 2])
            name  = c0.text_input('_', placeholder='과목명',  key=f'{sem_key}_r{i}n', label_visibility='collapsed')
            units = c1.text_input('_', placeholder='단위수',  key=f'{sem_key}_r{i}u', label_visibility='collapsed')
            grade = c2.text_input('_', placeholder='1 ~ 9',  key=f'{sem_key}_r{i}g', label_visibility='collapsed')

            if name.strip():
                try:    units_v = int(units.strip())
                except: units_v = 1
                try:    grade_v = int(grade.strip())
                except: grade_v = None
                regular.append({'과목명': name.strip(), '단위수': units_v, '석차등급': grade_v})

        if st.button('＋ 정규 과목', key=f'{sem_key}_add_reg'):
            st.session_state[f'{sem_key}_n_reg'] += 1
            st.rerun()

        st.divider()

        # ── Special (선택) courses ────────────────────────────────────────────
        st.markdown('**선택 과목** (알파벳 등급)')
        h0, h1, h2, h3 = st.columns([5, 2, 2, 3])
        h0.caption('과목명')
        h1.caption('단위수')
        h2.caption('등급')
        h3.caption('구분')

        special = []
        for i in range(st.session_state[f'{sem_key}_n_spc']):
            c0, c1, c2, c3 = st.columns([5, 2, 2, 3])
            name  = c0.text_input('_', placeholder='과목명',    key=f'{sem_key}_s{i}n', label_visibility='collapsed')
            units = c1.text_input('_', placeholder='단위수',    key=f'{sem_key}_s{i}u', label_visibility='collapsed')
            grade = c2.text_input('_', placeholder='A / B / C', key=f'{sem_key}_s{i}g', label_visibility='collapsed')
            cat   = c3.selectbox('_', ['진로선택', '체육예술'],  key=f'{sem_key}_s{i}c', label_visibility='collapsed')

            if name.strip():
                try:    units_v = int(units.strip())
                except: units_v = 1
                special.append({
                    '과목명': name.strip(),
                    '단위수': units_v,
                    '등급': grade.strip().upper() or 'A',
                    '구분': cat,
                })

        if st.button('＋ 선택 과목', key=f'{sem_key}_add_spc'):
            st.session_state[f'{sem_key}_n_spc'] += 1
            st.rerun()

        all_semesters[sem_key] = {'정규': regular, '특별': special}

# ── Generate section ──────────────────────────────────────────────────────────
st.divider()
fn_col, btn_col = st.columns([4, 1])
filename = fn_col.text_input('파일명', value='grade_report', placeholder='파일명 (확장자 제외)')

if btn_col.button('보고서 생성', type='primary'):
    valid = {k: v for k, v in all_semesters.items() if v['정규']}

    if not valid:
        st.error('최소 한 학기의 정규 과목을 입력하세요.')
    else:
        with st.spinner('보고서 생성 중...'):
            try:
                # 1. Generate PDF into memory
                pdf_buf = io.BytesIO()
                build_report(output_path=pdf_buf, semesters=valid)

                # 2. Rasterise PDF → JPEG in memory via PyMuPDF (300 DPI)
                pdf_doc = fitz.open(stream=pdf_buf.getvalue(), filetype='pdf')
                page = pdf_doc[0]
                mat = fitz.Matrix(300 / 72, 300 / 72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                jpeg_bytes = pix.tobytes('jpeg', jpg_quality=90)
                pdf_doc.close()

                # 3. Save to disk
                out_path = os.path.abspath(f'{filename}.jpeg')
                with open(out_path, 'wb') as f:
                    f.write(jpeg_bytes)

                st.success(f'저장 완료 → {out_path}')
                st.image(io.BytesIO(jpeg_bytes))
                st.download_button(
                    '⬇ 다운로드',
                    jpeg_bytes,
                    file_name=f'{filename}.jpeg',
                    mime='image/jpeg',
                )

            except Exception as e:
                st.error(f'생성 오류: {e}')
                raise
