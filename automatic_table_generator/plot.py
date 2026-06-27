import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_CANDIDATES = [
    os.path.join(_THIS_DIR, 'fonts', 'NanumGothic-Regular.ttf'),  # bundled TTF
    os.path.join(_THIS_DIR, 'fonts', 'NotoSansKR-Regular.otf'),   # bundled OTF (matplotlib only)
    '/Library/Fonts/NotoSansCJKkr-Regular.otf',
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
]

_font_path = next(p for p in _FONT_CANDIDATES if os.path.exists(p))
_font_prop = fm.FontProperties(fname=_font_path)

NAVY = (39/255, 44/255, 97/255)
GRAY = (136/255, 136/255, 136/255)


def build_grade_figure(averages):
    """
    averages: dict of semester_key -> {'simple': float, 'weighted': float}
              ordered 1학년1학기 ... 3학년1학기
    Returns a matplotlib Figure.
    """
    labels = list(averages.keys())
    simple_vals = [averages[k]['simple'] for k in labels]
    weighted_vals = [averages[k]['weighted'] for k in labels]

    fig, ax = plt.subplots(figsize=(15.0, 4.87))

    ax.plot(labels, simple_vals, marker='o', linewidth=2, markersize=9,
            color=NAVY, markerfacecolor=NAVY, markeredgecolor='white', markeredgewidth=1)

    for i, (sv, wv) in enumerate(zip(simple_vals, weighted_vals)):
        ax.annotate(f'{sv:.2f}',
                    xy=(i, sv), xytext=(0, 12), textcoords='offset points',
                    ha='center', va='bottom',
                    fontproperties=_font_prop, fontsize=10, color=NAVY)
        ax.annotate(f'({wv:.2f})',
                    xy=(i, sv), xytext=(0, -14), textcoords='offset points',
                    ha='center', va='top',
                    fontproperties=_font_prop, fontsize=9.5, color=GRAY)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(_font_prop)
    ax.tick_params(axis='x', pad=4)

    ax.set_yticks(range(1, 10))
    ax.set_yticklabels([str(i) for i in range(1, 10)], fontsize=10)
    for lbl in ax.get_yticklabels():
        lbl.set_fontproperties(_font_prop)

    ax.invert_yaxis()
    ax.set_ylim(9, 0.85)

    ax.grid(True, which='major', axis='y', linestyle='--', linewidth=0.6, alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(top=False, right=False)

    fig.tight_layout()
    return fig
