"""
Glacious - Satellite-powered Alpine climate intelligence for journalists
Main Streamlit application
"""

# Load environment variables FIRST before any other imports
from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
import folium
from streamlit_folium import st_folium
import json
import random

# Import pipeline modules
from pipeline.mode_classifier import classify_mode
from pipeline.claim_parser import parse_claim
from pipeline.verdict_engine import validate_claim
from pipeline.query_handler import handle_query
from pipeline.causes_engine import get_causes_context
from pipeline.misinfo_matcher import load_misinfo_matches
from pipeline.language import t, detect_language, UI_STRINGS
from pipeline.data_loader import get_loader
from pipeline.source_credibility import SOURCE_METADATA

# ============================================================================
# PAGE CONFIGURATION & THEMING
# ============================================================================

st.set_page_config(
    page_title="Glacious",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for icy glacial theme
def inject_custom_css():
    """Inject custom CSS for glacial theme."""
    css = """
    <style>
        /* Color scheme */
        :root {
            --bg-primary: #F0F4F8;
            --bg-secondary: #FFFFFF;
            --border-color: #C8D8E8;
            --accent-primary: #1A5276;
            --accent-secondary: #2E86C1;
            --alert-color: #85929E;
            --success-color: #1A7A4A;
            --danger-color: #922B21;
            --sidebar-bg: #1A3A4A;
            --sidebar-text: #FFFFFF;
        }
        
        /* Global styles */
        body {
            background-color: var(--bg-primary);
            font-family: system-ui, -apple-system, sans-serif;
        }
        
        /* Main content background */
        .main {
            background-color: var(--bg-primary);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--sidebar-text);
        }
        
        [data-testid="stSidebar"] label {
            color: var(--sidebar-text) !important;
        }
        
        /* Cards and containers */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 1px 4px rgba(26, 82, 118, 0.08);
            margin: 10px 0;
        }
        
        /* Frosted glass effect for verdict cards */
        .frosted-glass {
            background: rgba(240, 244, 248, 0.85);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(200, 216, 232, 0.6);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }
        
        /* Headers */
        h1, h2, h3 {
            letter-spacing: 0.03em;
            font-weight: 500;
            color: var(--accent-primary);
        }
        
        /* Buttons */
        .stButton > button {
            background-color: var(--accent-primary) !important;
            color: white !important;
            border-radius: 6px;
            border: none;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: var(--accent-secondary) !important;
            box-shadow: 0 4px 12px rgba(30, 144, 255, 0.2);
        }
        
        /* Metrics */
        .metric-card {
            background: var(--bg-secondary);
            border-left: 4px solid var(--accent-primary);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        /* Alerts */
        .alert-success {
            background-color: #E8F5E9;
            border-left: 4px solid var(--success-color);
            padding: 12px;
            border-radius: 4px;
        }
        
        .alert-danger {
            background-color: #FFEBEE;
            border-left: 4px solid var(--danger-color);
            padding: 12px;
            border-radius: 4px;
        }
        
        .alert-warning {
            background-color: #FFF3E0;
            border-left: 4px solid #FF9800;
            padding: 12px;
            border-radius: 4px;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# ============================================================================
# SESSION STATE & INITIALIZATION
# ============================================================================

if "language" not in st.session_state:
    st.session_state.language = "en"

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

with st.sidebar:
    # Logo and title
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 48px; margin: 0;'>⛰</h1>
        <h2 style='color: #1A5276; margin-top: 0;'>Glacious</h2>
        <p style='color: #2E86C1; font-size: 12px; margin: 0;'>Satellite-powered climate intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Language selector
    language = st.selectbox(
        "🌍 Language",
        ["en", "de", "fr", "it", "sl", "rm", "hr", "fur"],
        format_func=lambda x: {"en": "English", "de": "Deutsch", "fr": "Français", "it": "Italiano",
                               "sl": "Slovenščina", "rm": "Rumantsch", "hr": "Hrvatski", "fur": "Furlan"}.get(x, x),
        index=0
    )
    st.session_state.language = language
    
    # Region selector
    regions = ["All Alpine ranges", "Swiss Alps", "French Alps", "Italian Alps", "Austrian Alps",
               "Slovenian Alps", "Dolomites", "Mont Blanc Massif", "Pennine Alps", "Bernese Alps"]
    region = st.selectbox(t("region_select_label", language), regions)
    
    # Year range selector
    col1, col2 = st.columns(2)
    with col1:
        year_start = st.number_input("Start year", value=2000, min_value=1984, max_value=2026)
    with col2:
        year_end = st.number_input("End year", value=2026, min_value=1984, max_value=2026)
    
    st.divider()
    
    # Demo mode toggle
    demo_mode = st.toggle(t("demo_mode_label", language), value=False)
    st.session_state.demo_mode = demo_mode
    
    st.divider()
    
    # Data sources expander
    with st.expander(t("data_sources_label", language)):
        for tier, color in [(1, "green"), (2, "orange"), (3, "gray")]:
            tier_sources = [f"🔘 {name}" for name, meta in SOURCE_METADATA.items() 
                          if meta.get("credibility_tier") == tier]
            for source in tier_sources[:5]:
                st.markdown(f"<small>{source}</small>", unsafe_allow_html=True)
    
    # About section
    with st.expander(t("about_label", language)):
        st.markdown(f"""
        **AlpineCheck** is a satellite-powered climate analysis tool for Alpine journalists.
        
        It answers climate questions and validates factual claims using multi-source satellite data,
        ground measurements, and scientific expertise. Every verdict includes source credibility assessment.
        
        Coverage: {", ".join(regions)} across 8 Alpine countries.
        """)
    
    st.divider()
    st.caption(f"© 2026 Glacious | Version 1.0 | {language.upper()}")

# ============================================================================
# MAIN APP HEADER
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 30px 0;'>
    <h1 style='font-size: 48px; color: #1A5276; margin: 0;'>⛰ Glacious</h1>
    <p style='color: #2E86C1; font-size: 16px; margin: 10px 0;'>
        Satellite-powered climate intelligence for Alpine journalism
    </p>
</div>
""", unsafe_allow_html=True)

# Key statistics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(t("glaciers_lost", language), "50%", "Since 1900", delta_color="inverse")

with col2:
    st.metric(t("temp_rise", language), "+2.1°C", "Since 1880", delta_color="off")

with col3:
    st.metric(t("snow_days_lost", language), "~2.3 days/yr", "Average trend", delta_color="inverse")

with col4:
    st.metric(t("permafrost_degrading", language),"+0.18°C/decade", "At 10m depth", delta_color="off")

st.divider()

# ============================================================================
# INPUT SECTION
# ============================================================================

st.subheader("🔬 " + t("input_placeholder", language).split("...")[0])

# Placeholder examples
placeholders = [
    "How much snow cover has been lost in the Italian Alps in the past 10 years?",
    "Snow cover has receded by 10% in the last 2 years in the Swiss Alps. Is this true?",
    "What is happening to permafrost in the Austrian Alps?",
    "Are glaciers in the Dolomites melting faster than average?",
]

# Input area
user_input = st.text_area(
    t("input_placeholder", language),
    value=st.session_state.input_text,
    height=100,
    placeholder=random.choice(placeholders),
    key="user_input"
)

# Quick example buttons (3 columns for select examples)
st.caption("📋 Quick examples:")
col1, col2, col3 = st.columns(3)

quick_examples = [
    ("🌨️ Snow query", "How much snow cover has declined in the past decade?"),
    ("❓ Temperature claim", "Is Alpine temperature warming faster than the global average?"),
    ("🧊 Glacier check", "Have Swiss Alpine glaciers lost more than 25% since 2000?"),
]

for idx, (label, example) in enumerate(quick_examples):
    with [col1, col2, col3][idx]:
        if st.button(label, use_container_width=True):
            st.session_state.input_text = example
            st.rerun()

# Analyze button
col1, col2 = st.columns([3, 1])
with col2:
    analyze_button = st.button(t("analyze_btn", language), use_container_width=True, type="primary")

# ============================================================================
# PROCESSING & RESULTS
# ============================================================================

if analyze_button and user_input:
    with st.spinner(random.choice([
        "Querying satellite archives...",
        "Cross-referencing glacier records...",
        "Consulting ice cores...",
        "Verifying against ground stations..."
    ])):
        
        # Demo mode - use pre-baked responses
        if st.session_state.demo_mode:
            mode_result = {"mode": random.choice(["query", "validation"])}
            if mode_result["mode"] == "query":
                st.session_state.last_result = {
                    "mode": "query",
                    "region": region,
                    "answer": "The Italian Alps have experienced a reduction in snow cover duration of approximately 3.2 days per year since the 1980s. This is above the Alpine average of 2.3 days/year, reflecting the southern Alps' higher sensitivity to warming. Temperature increases of +2.4°C and precipitation changes contribute to earlier melt onset and shorter seasons. This directly impacts tourism, avalanche risk, and water availability for downstream communities across northern Italy and beyond.",
                    "key_fact": "Italian Alps snow season shortened by ~3.2 days/year—well above Alpine average.",
                    "sources_used": ["MODIS", "Sentinel-2", "Alpine Research Centers"]
                }
            else:
                st.session_state.last_result = {
                    "mode": "validation",
                    "verdict": "Supported",
                    "confidence": 0.82,
                    "region": region,
                    "accurate_finding": "Swiss Alpine glaciers have lost approximately 28% area since 2000, based on satellite data."
                }
        
        else:
            # Real processing
            try:
                # Classify mode
                mode_result = classify_mode(user_input)
                
                if mode_result["mode"] == "query":
                    # Query mode - answer the question
                    data = get_loader().load_all_data(region, int(year_start), int(year_end))
                    response = handle_query(user_input, region, int(year_start), int(year_end), language, data)
                    st.session_state.last_result = {"mode": "query", **response}
                
                else:
                    # Validation mode - check the claim
                    parsed = parse_claim(user_input)
                    parsed["region"] = region
                    parsed["year_start"] = int(year_start)
                    parsed["year_end"] = int(year_end)
                    
                    verdict = validate_claim(parsed, language)
                    st.session_state.last_result = {"mode": "validation", **verdict}
            
            except Exception as e:
                st.error(f"Error processing input: {str(e)}")
                st.session_state.last_result = None

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

if st.session_state.last_result:
    result = st.session_state.last_result
    
    # Mode indicator
    if result["mode"] == "query":
        mode_pill = '<div style="display: inline-block; background-color: #2E86C1; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">🔍 Query mode — answering your question</div>'
    else:
        mode_pill = '<div style="display: inline-block; background-color: #FF9800; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">✓ Validation mode — checking your claim</div>'
    
    st.markdown(mode_pill, unsafe_allow_html=True)
    
    st.divider()
    
    # QUERY MODE RESPONSE
    if result["mode"] == "query":
        st.subheader("📊 Analysis Results")
        
        # Answer box
        st.info(result.get("answer", ""))
        
        # Key fact callout
        st.markdown(f"""
        <div class='frosted-glass'>
            <h3 style='margin-top: 0;' color: #1A5276;'>⭐ Key Finding</h3>
            <p style='font-size: 16px; font-weight: bold; margin: 0;'>{result.get("key_fact", "")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Causes & outcomes
        try:
            causes = get_causes_context(result.get("variable", "glacier"), region, language)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌍 Root Causes")
                with st.expander("Regional & Global Drivers"):
                    for cause in causes.get("regional_causes", []):
                        st.write(f"• {cause}")
                    st.divider()
                    for cause in causes.get("global_causes", []):
                        st.write(f"• {cause}")
                
                with st.expander("Human Accelerators"):
                    for item in causes.get("anthropogenic_expeditors", []):
                        st.write(f"• {item}")
            
            with col2:
                st.subheader("⚠️ Consequences")
                with st.expander("Ecological Impacts"):
                    for outcome in causes.get("ecological_outcomes", []):
                        st.write(f"• {outcome}")
                
                with st.expander("Social & Economic"):
                    for outcome in causes.get("social_outcomes", []):
                        st.write(f"• {outcome}")
        except:
            pass
    
    # VALIDATION MODE RESPONSE
    elif result["mode"] == "validation":
        st.subheader("⚖️ " + t("verdict_label", language))
        
        # Verdict card
        verdict = result.get("verdict", "Unknown")
        confidence = result.get("confidence", 0.5)
        
        color_map = {
            "Supported": "#1A7A4A",
            "Partially Supported": "#FF9800",
            "Contradicted": "#922B21"
        }
        
        color = color_map.get(verdict, "#85929E")
        
        st.markdown(f"""
        <div class='frosted-glass' style='border-left: 6px solid {color};'>
            <h2 style='margin-top: 0; color: {color};'>{verdict.upper()}</h2>
            <p>{result.get("accurate_finding", "")}</p>
            <p style='font-size: 12px; color: #666;'>Region: {result.get("region")} | Period: {result.get("year_start")}-{result.get("year_end")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Confidence bar
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(confidence, f"{t('confidence_label', language)}: {confidence:.0%}")
        
        # Sources section
        st.subheader("📚 " + t("sources_label", language))
        
        sources = result.get("sources_used", [])
        for source in sources:
            source_meta = SOURCE_METADATA.get(source, {})
            if source_meta:
                tier_emoji = {"1": "🟢", "2": "🟡", "3": "🔘"}.get(str(source_meta.get("credibility_tier")), "⭕")
                st.write(f"{tier_emoji} **{source}** - {source_meta.get('institution', '')}")
                with st.expander("Details"):
                    st.write(f"**Resolution:** {source_meta.get('spatial_resolution')}")
                    st.write(f"**Coverage:** {source_meta.get('temporal_coverage')}")
                    if source_meta.get('known_limitations'):
                        st.write("**Limitations:**")
                        for lim in source_meta['known_limitations'][:2]:
                            st.write(f"• {lim}")
        
        st.info(result.get("credibility_assessment", ""))
        
        # Check for similar misinformation
        misinfo_matches = load_misinfo_matches(result.get("accurate_finding", ""))
        if misinfo_matches:
            st.warning("⚠️ Similar claims found in misinformation database - verify carefully")

    # ================================================================
    # VISUALIZATIONS (TABBED VIEW)
    # ================================================================
    
    st.divider()
    st.subheader("📈 Data Visualizations")
    
    # Load data for visualizations
    data = get_loader().load_all_data(region, int(year_start), int(year_end))
    
    tabs = st.tabs([
        t("snow_cover_tab", language),
        t("temperature_tab", language),
        t("permafrost_tab", language),
        t("biodiversity_tab", language),
        t("economic_tab", language),
        "Media"
    ])
    
    # Tab 1: Snow & Glaciers
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            # Snow cover duration
            snow_data = data.get("modis", {})
            if snow_data.get("years"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=snow_data["years"], y=snow_data["snow_cover_days"],
                    mode='lines+markers', name='Snow Cover Days',
                    line=dict(color='#1A5276', width=2),
                    marker=dict(size=6, color='#2E86C1')
                ))
                fig.update_layout(
                    title="Snow Cover Duration",
                    xaxis_title="Year",
                    yaxis_title="Days/Year",
                    template="plotly_white",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Glacier area
            glacier_data = data.get("landsat", {})
            if glacier_data.get("years"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=glacier_data["years"], y=glacier_data["glacier_area_km2"],
                    mode='lines+markers', name='Glacier Area',
                    line=dict(color='#1A7A4A', width=2),
                    marker=dict(size=6, color='#2E86C1')
                ))
                fig.update_layout(
                    title="Glacier Area Trend",
                    xaxis_title="Year",
                    yaxis_title="Area (km²)",
                    template="plotly_white",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Climate
    with tabs[1]:
        climate_data = data.get("climate", {})
        if climate_data.get("years"):
            fig = go.Figure()
            
            temps = climate_data["temperature_anomaly_c"]
            fig.add_trace(go.Bar(
                x=climate_data["years"],
                y=temps,
                marker=dict(color=['#922B21' if t > 0 else '#1A5276' for t in temps]),
                name='Temperature Anomaly'
            ))
            
            fig.update_layout(
                title="Temperature Anomaly vs 1980-2010 Baseline",
                xaxis_title="Year",
                yaxis_title="Anomaly (°C)",
                template="plotly_white",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 3: Permafrost
    with tabs[2]:
        perm_data = data.get("permafrost", {})
        if perm_data.get("years"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=perm_data["years"], y=perm_data["temperature_10m_celsius"],
                mode='lines+markers', name='Temperature at 10m',
                line=dict(color='#922B21', width=2),
                marker=dict(size=6)
            ))
            fig.update_layout(
                title="Permafrost Temperature Trend",
                xaxis_title="Year",
                yaxis_title="Temperature (°C)",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 4: Biodiversity
    with tabs[3]:
        bio_data = data.get("biodiversity", {})
        if bio_data.get("species_elevation_shifts"):
            fig = go.Figure()
            for species, elevations in bio_data["species_elevation_shifts"].items():
                fig.add_trace(go.Scatter(
                    x=bio_data["years"], y=elevations,
                    mode='lines', name=species.replace('_', ' ').title()
                ))
            fig.update_layout(
                title="Alpine Species Elevation Shifts",
                xaxis_title="Year",
                yaxis_title="Elevation (m)",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 5: Economic
    with tabs[4]:
        econ_data = data.get("tourism", {})
        if econ_data.get("years"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=econ_data["years"], y=econ_data["ski_season_days"],
                mode='lines+markers', name='Ski Season Length',
                line=dict(color='#2E86C1', width=2)
            ))
            fig.update_layout(
                title="Alpine Ski Season Length",
                xaxis_title="Year",
                yaxis_title="Days",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 6: Media
    with tabs[5]:
        st.write("Media coverage landscape and sentiment analysis would be displayed here.")
        st.info("GDELT and NewsAPI data integration coming soon.")

    # ================================================================
    # INTERACTIVE MAP
    # ================================================================
    
    st.divider()
    st.subheader("🗺️ " + t("map_title", language))
    
    # Create folium map
    map_center = [46.8, 10.2]
    m = folium.Map(
        location=map_center,
        zoom_start=6,
        tiles="OpenStreetMap"
    )
    
    # Add Alpine region markers
    regions_data = [
        {"name": "Swiss Alps", "lat": 46.8, "lon": 8.5, "loss": 28},
        {"name": "French Alps", "lat": 45.5, "lon": 6.2, "loss": 32},
        {"name": "Italian Alps", "lat": 46.2, "lon": 11.0, "loss": 35},
        {"name": "Austrian Alps", "lat": 47.5, "lon": 12.5, "loss": 30},
        {"name": "Slovenian Alps", "lat": 46.3, "lon": 13.8, "loss": 22},
    ]
    
    for reg in regions_data:
        loss = reg["loss"]
        if loss > 40:
            color = "#8B0000"
        elif loss > 25:
            color = "#FF8C00"
        elif loss > 10:
            color = "#FFD700"
        else:
            color = "#228B22"
        
        folium.CircleMarker(
            location=[reg["lat"], reg["lon"]],
            radius=12,
            popup=f"{reg['name']}: {loss}% glacier loss",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    st_folium(m, width=1400, height=500)
    
    # ================================================================
    # FULL REPORT GENERATOR
    # ================================================================
    
    st.divider()
    st.subheader("📄 Generate Full Report")
    
    with st.expander("Create journalist-ready report"):
        col1, col2 = st.columns(2)
        
        with col1:
            report_lang = st.selectbox("Report language", ["English", "Deutsch", "Français"])
        
        with col2:
            report_format = st.radio("Format", ["Brief", "Technical"])
        
        if st.button("Generate Report"):
            report_text = f"""
# AlpineCheck Report: {region}
Generated for {report_lang}

## Executive Summary
This report presents satellite-based climate analysis for {region} covering {year_start}-{year_end}.

## Key Findings
- Glacier decline: ~30% since 1980
- Snow cover reduction: ~2.3 days/year
- Temperature warming: +2.1°C since 1880

## Data Sources
{', '.join(result.get('sources_used', []))}

---
Report generated by AlpineCheck © 2026
            """
            
            st.text_area("Report", value=report_text, height=300)
            
            st.download_button(
                label="Download as .txt",
                data=report_text,
                file_name=f"alpinecheck_{region.replace(' ', '_')}_{year_end}.txt",
                mime="text/plain"
            )

# Footer
st.divider()
st.caption("""
**Glacious** — Satellite-powered climate intelligence for Alpine journalists.
Data sources: Sentinel-2, MODIS, Landsat, GRACE, PERMOS, GBIF, Eurostat, and Alpine research centers.
""")
