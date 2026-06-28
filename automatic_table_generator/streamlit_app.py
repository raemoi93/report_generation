"""
EDUPREP grade input UI.
Run: streamlit run automatic_table_generator/streamlit_app.py
"""
import datetime
import io
import os
import sys

import fitz
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import build_report

st.set_page_config(page_title='EDUPREP 성적 입력', layout='wide')
st.title('EDUPREP 성적 입력')

SEMESTER_DEFS = [
    ('1학년1학기', '1학년 1학기'),
    ('1학년2학기', '1학년 2학기'),
    ('2학년1학기', '2학년 1학기'),
    ('2학년2학기', '2학년 2학기'),
    ('3학년1학기', '3학년 1학기'),
]
DEFAULT_REG = 6
DEFAULT_SPC = 3

_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(_THIS_DIR, 'profiles')

# ── Profile helpers ────────────────────────────────────────────────────────────

def list_profiles():
    os.makedirs(PROFILES_DIR, exist_ok=True)
    return sorted(f[:-4] for f in os.listdir(PROFILES_DIR) if f.endswith('.txt'))


def _profile_to_text(name):
    """Serialize current session state to human-readable profile text."""
    lines = [f'프로필: {name}', f'저장일: {datetime.date.today()}', '']
    for sk, sl in SEMESTER_DEFS:
        n_reg = st.session_state.get(f'{sk}_n_reg', DEFAULT_REG)
        n_spc = st.session_state.get(f'{sk}_n_spc', DEFAULT_SPC)
        lines += [f'=== {sl} ===', f'-- 정규 과목 ({n_reg}행) --']
        for i in range(n_reg):
            n = st.session_state.get(f'{sk}_r{i}n', '')
            u = st.session_state.get(f'{sk}_r{i}u', '')
            g = st.session_state.get(f'{sk}_r{i}g', '')
            lines.append(f'{n}, {u}, {g}')
        lines.append(f'-- 선택 과목 ({n_spc}행) --')
        for i in range(n_spc):
            n = st.session_state.get(f'{sk}_s{i}n', '')
            u = st.session_state.get(f'{sk}_s{i}u', '')
            g = st.session_state.get(f'{sk}_s{i}g', '')
            c = st.session_state.get(f'{sk}_s{i}c', '진로선택')
            lines.append(f'{n}, {u}, {g}, {c}')
        lines.append('')
    return '\n'.join(lines)


def _save_profile(name):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f'{name}.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(_profile_to_text(name))


def _clear_inputs():
    """Blank out all grade input cells."""
    for sk, _ in SEMESTER_DEFS:
        max_reg = st.session_state.get(f'{sk}_n_reg', DEFAULT_REG) + 10
        max_spc = st.session_state.get(f'{sk}_n_spc', DEFAULT_SPC) + 10
        st.session_state[f'{sk}_n_reg'] = DEFAULT_REG
        st.session_state[f'{sk}_n_spc'] = DEFAULT_SPC
        for i in range(max_reg):
            st.session_state[f'{sk}_r{i}n'] = ''
            st.session_state[f'{sk}_r{i}u'] = ''
            st.session_state[f'{sk}_r{i}g'] = ''
        for i in range(max_spc):
            st.session_state[f'{sk}_s{i}n'] = ''
            st.session_state[f'{sk}_s{i}u'] = ''
            st.session_state[f'{sk}_s{i}g'] = ''
            st.session_state[f'{sk}_s{i}c'] = '진로선택'


def _apply_text(text):
    """Parse profile text and apply to session state."""
    _clear_inputs()
    sl_to_sk = {sl: sk for sk, sl in SEMESTER_DEFS}
    sk = None
    section = None
    ri = si = 0

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('프로필:') or line.startswith('저장일:'):
            continue
        if line.startswith('=== ') and line.endswith(' ==='):
            sk = sl_to_sk.get(line[4:-4])
            section = None
            ri = si = 0
        elif sk and line.startswith('-- 정규 과목 ('):
            section = 'reg'
            try:
                st.session_state[f'{sk}_n_reg'] = int(line.split('(')[1].split('행')[0])
            except Exception:
                pass
        elif sk and line.startswith('-- 선택 과목 ('):
            section = 'spc'
            try:
                st.session_state[f'{sk}_n_spc'] = int(line.split('(')[1].split('행')[0])
            except Exception:
                pass
        elif sk and section == 'reg':
            p = [x.strip() for x in line.split(',', 2)]
            st.session_state[f'{sk}_r{ri}n'] = p[0] if len(p) > 0 else ''
            st.session_state[f'{sk}_r{ri}u'] = p[1] if len(p) > 1 else ''
            st.session_state[f'{sk}_r{ri}g'] = p[2] if len(p) > 2 else ''
            ri += 1
        elif sk and section == 'spc':
            p = [x.strip() for x in line.split(',', 3)]
            cat = p[3] if len(p) > 3 else '진로선택'
            st.session_state[f'{sk}_s{si}n'] = p[0] if len(p) > 0 else ''
            st.session_state[f'{sk}_s{si}u'] = p[1] if len(p) > 1 else ''
            st.session_state[f'{sk}_s{si}g'] = p[2] if len(p) > 2 else ''
            st.session_state[f'{sk}_s{si}c'] = cat if cat in ('진로선택', '체육예술') else '진로선택'
            si += 1


def _load_profile(name):
    with open(os.path.join(PROFILES_DIR, f'{name}.txt'), encoding='utf-8') as f:
        _apply_text(f.read())


# ── Profile management UI ──────────────────────────────────────────────────────
st.session_state.setdefault('current_profile', None)

st.subheader('학생 프로필')
profiles = list_profiles()

# Guard: if stored selectbox value is no longer in options, reset it
options = profiles + ['+ 새 프로필']
if st.session_state.get('_sel') not in options:
    st.session_state.pop('_sel', None)

cur = st.session_state['current_profile']
default_idx = profiles.index(cur) if cur in profiles else len(profiles)

sel_col, name_col, btn_col, dl_col = st.columns([3, 2, 1, 2])

selected = sel_col.selectbox(
    '프로필',
    options,
    index=default_idx,
    key='_sel',
    label_visibility='collapsed',
)

if selected == '+ 새 프로필':
    new_name = name_col.text_input('이름', placeholder='학생 이름 입력', key='_new_name',
                                   label_visibility='collapsed')
    if btn_col.button('생성', key='_create'):
        nm = new_name.strip()
        if nm:
            if cur:
                _save_profile(cur)        # auto-save current before switching
            _clear_inputs()
            _save_profile(nm)
            st.session_state['current_profile'] = nm
            st.session_state['_sel'] = nm
            st.rerun()
else:
    if selected != cur:                   # profile switch
        if cur:
            _save_profile(cur)            # auto-save before switching
        _load_profile(selected)
        st.session_state['current_profile'] = selected
        st.rerun()

# Download current profile
if st.session_state['current_profile']:
    dl_col.download_button(
        '⬇ 프로필 다운로드',
        _profile_to_text(st.session_state['current_profile']).encode('utf-8'),
        file_name=f'{st.session_state["current_profile"]}.txt',
        mime='text/plain',
        key='_dl',
    )

# Upload profile
with st.expander('프로필 업로드 (.txt)'):
    uploaded = st.file_uploader('파일 선택', type='txt', label_visibility='collapsed', key='_ul')
    if uploaded and st.session_state.get('_last_ul') != uploaded.name:
        text = uploaded.read().decode('utf-8')
        first = next((l for l in text.splitlines() if l.strip()), '')
        uname = first.replace('프로필:', '').strip() if first.startswith('프로필:') else uploaded.name[:-4]
        if cur:
            _save_profile(cur)
        os.makedirs(PROFILES_DIR, exist_ok=True)
        with open(os.path.join(PROFILES_DIR, f'{uname}.txt'), 'w', encoding='utf-8') as f:
            f.write(text)
        _apply_text(text)
        st.session_state['current_profile'] = uname
        st.session_state['_sel'] = uname
        st.session_state['_last_ul'] = uploaded.name
        st.rerun()

st.divider()

# ── Per-semester input sections ────────────────────────────────────────────────
for sk, _ in SEMESTER_DEFS:
    st.session_state.setdefault(f'{sk}_n_reg', DEFAULT_REG)
    st.session_state.setdefault(f'{sk}_n_spc', DEFAULT_SPC)

all_semesters = {}

for sem_key, sem_label in SEMESTER_DEFS:
    with st.expander(sem_label, expanded=False):

        # Regular courses
        st.markdown('**정규 과목**')
        h0, h1, h2 = st.columns([5, 2, 2])
        h0.caption('과목명'); h1.caption('단위수'); h2.caption('석차등급 (1~9)')

        regular = []
        for i in range(st.session_state[f'{sem_key}_n_reg']):
            c0, c1, c2 = st.columns([5, 2, 2])
            name  = c0.text_input('_', placeholder='과목명', key=f'{sem_key}_r{i}n', label_visibility='collapsed')
            units = c1.text_input('_', placeholder='단위수', key=f'{sem_key}_r{i}u', label_visibility='collapsed')
            grade = c2.text_input('_', placeholder='1 ~ 9', key=f'{sem_key}_r{i}g', label_visibility='collapsed')
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

        # Special (선택) courses
        st.markdown('**선택 과목** (알파벳 등급)')
        h0, h1, h2, h3 = st.columns([5, 2, 2, 3])
        h0.caption('과목명'); h1.caption('단위수'); h2.caption('등급'); h3.caption('구분')

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
                    '과목명': name.strip(), '단위수': units_v,
                    '등급': grade.strip().upper() or 'A', '구분': cat,
                })

        if st.button('＋ 선택 과목', key=f'{sem_key}_add_spc'):
            st.session_state[f'{sem_key}_n_spc'] += 1
            st.rerun()

        all_semesters[sem_key] = {'정규': regular, '특별': special}

# ── Generate section ──────────────────────────────────────────────────────────
st.divider()
fn_col, btn_col = st.columns([4, 1])
default_filename = st.session_state.get('current_profile', 'grade_report') or 'grade_report'
filename = fn_col.text_input('파일명', value=default_filename, placeholder='파일명 (확장자 제외)')

if btn_col.button('보고서 생성', type='primary'):
    valid = {k: v for k, v in all_semesters.items() if v['정규']}
    if not valid:
        st.error('최소 한 학기의 정규 과목을 입력하세요.')
    else:
        # Auto-save profile before generating
        if st.session_state['current_profile']:
            _save_profile(st.session_state['current_profile'])

        with st.spinner('보고서 생성 중...'):
            try:
                pdf_buf = io.BytesIO()
                build_report(output_path=pdf_buf, semesters=valid)

                pdf_doc = fitz.open(stream=pdf_buf.getvalue(), filetype='pdf')
                pix = pdf_doc[0].get_pixmap(matrix=fitz.Matrix(300/72, 300/72), alpha=False)
                jpeg_bytes = pix.tobytes('jpeg', jpg_quality=90)
                pdf_doc.close()

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
