"""TariffCheck web app. Only display code lives here; every dollar comes from compare.py."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from tariffcheck.compare import compare_plans, to_cents
from tariffcheck.loader import UsageFileError, load_usage
from tariffcheck.plans import GLOBIRD_BLOCK, NECTR_FLAT, NECTR_TOU
from tariffcheck.usage import (
    average_daily_kwh,
    days_covered,
    hourly_profile,
    share_in_window,
)

SAMPLE = Path(__file__).parent / "data" / "sample_usage.csv"
PEAK = NECTR_TOU.windows[0]

# Text shown on each card. Prices themselves come from the plan objects.
PLAN_INFO = {
    NECTR_FLAT.name: ("Nectr", "Flat rate", "NTR1154691MRE1", "24.48c/kWh all day"),
    GLOBIRD_BLOCK.name: (
        "GloBird",
        "Block",
        "GLO1212438MRE1",
        "22.44c first 15 kWh/day, then 25.30c",
    ),
    NECTR_TOU.name: (
        "Nectr",
        "Time of use",
        "NTR1154695MRE1",
        "35.86c 4–9pm · 14.42c 11am–4pm · 20.75c other",
    ),
}
PLANS = {p.name: p for p in (NECTR_FLAT, GLOBIRD_BLOCK, NECTR_TOU)}

CSS = """
<style>
.tc-bar {background:#595753;color:#fff;padding:14px 20px;border-radius:12px;margin-bottom:12px}
.tc-bar b {color:#FBE53A}
.tc-ribbon {background:#FBE53A;color:#1A1A1A;font-weight:600;padding:6px 12px;
            border-radius:8px;display:inline-block;margin-bottom:6px}
.tc-note {background:#FFFEA4;padding:10px 12px;border-radius:8px;font-size:0.9rem}
.tc-chip {background:#F1F1EE;border:1px solid #D9D8D0;border-radius:99px;
          padding:2px 10px;font-size:0.8rem}
</style>
"""

st.set_page_config(page_title="TariffCheck", page_icon="⚡", layout="wide")
st.html(CSS)
st.html(
    '<div class="tc-bar"><b>⚡ TariffCheck</b> · compare Queensland electricity plans on your own usage</div>'
)

side, main = st.columns([1, 3], gap="large")

with side:
    st.subheader("1 · Your usage")
    upload = st.file_uploader("Half-hourly CSV (timestamp,kwh)", type="csv")
    source = upload if upload is not None else SAMPLE
    try:
        readings = load_usage(source)
    except UsageFileError as error:
        st.error(f"We couldn't read that file. {error}")
        st.stop()
    if upload is None:
        st.caption("Showing sample data. Upload your own file above.")
    days = days_covered(readings)
    st.markdown(
        f"**{days} days** of readings  \n"
        f"**{average_daily_kwh(readings):.1f} kWh** a day on average  \n"
        f"**{share_in_window(readings, PEAK):.0%}** used 4–9 pm"
    )

    st.subheader("2 · Choose plans")
    chosen = [name for name in PLANS if st.checkbox(name, value=True)]
    st.html(
        '<div class="tc-note">Estimates use your own readings and current published prices, '
        "before discounts and GST rounding.</div>"
    )

with main:
    if not chosen:
        st.warning("Tick at least one plan to compare.")
        st.stop()
    result = compare_plans(readings, [PLANS[n] for n in chosen])

    st.subheader(f"3 · {len(chosen)} plans, cheapest first")
    for row in result.rows:
        retailer, kind, plan_id, rates = PLAN_INFO[row.name]
        with st.container(border=True):
            if row.name in result.cheapest and len(chosen) > 1:
                st.html(
                    f'<span class="tc-ribbon">Cheapest for your usage · saves '
                    f"${result.yearly_saving:,.2f} a year</span>"
                )
            left, right = st.columns([2, 1])
            left.markdown(
                f"**{retailer}** · {row.name} <span class='tc-chip'>{kind}</span>",
                unsafe_allow_html=True,
            )
            left.caption(
                f"{rates} · supply {PLANS[row.name].supply_c}c/day · Plan ID {plan_id}"
            )
            right.metric("Estimated per year", f"${row.yearly:,.2f}")
            right.caption(f"about ${to_cents(row.yearly / 12):,.2f} a month")
            left.caption(
                f"{days}-day bill: ${row.total} = energy ${row.energy} + supply ${row.supply}"
            )

    st.subheader("Estimated yearly cost")
    costs = pd.DataFrame(
        {
            "plan": [r.name for r in result.rows],
            "yearly": [float(r.yearly) for r in result.rows],  # float only for drawing
            "cheapest": [r.name in result.cheapest for r in result.rows],
        }
    )
    st.altair_chart(
        alt.Chart(costs)
        .mark_bar()
        .encode(
            x=alt.X("yearly:Q", title="$ per year"),
            y=alt.Y("plan:N", sort=None, title=None),
            color=alt.Color(
                "cheapest:N",
                scale=alt.Scale(domain=[True, False], range=["#595753", "#C9C8C0"]),
                legend=None,
            ),
            tooltip=["plan", alt.Tooltip("yearly:Q", format="$,.2f")],
        ),
        use_container_width=True,
    )

    st.subheader("When you use power")
    hours = pd.DataFrame(
        {
            "hour": range(24),
            "kwh": [float(k) for k in hourly_profile(readings)],
            "period": [
                NECTR_TOU.window_at(pd.Timestamp(2026, 1, 1, h).time()).name
                for h in range(24)
            ],
        }
    )
    st.altair_chart(
        alt.Chart(hours)
        .mark_bar()
        .encode(
            x=alt.X("hour:O", title="Hour of day"),
            y=alt.Y("kwh:Q", title="Average kWh"),
            color=alt.Color(
                "period:N",
                scale=alt.Scale(
                    domain=["peak", "off-peak", "shoulder"],
                    range=["#595753", "#F2D555", "#C9C8C0"],
                ),
                title="Time-of-use period",
            ),
        ),
        use_container_width=True,
    )
    st.caption(
        "Dark bars are the 4–9 pm peak. The more of your usage falls there, the more time of use costs."
    )

st.divider()
st.caption(
    "TariffCheck is a student project and does not sell or switch plans. "
    "Prices from Energy Made Easy (energymadeeasy.gov.au), 9 Nov 2026."
)
