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
            background: rgba(248, 251, 255, 0.96);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(26, 58, 74, 0.28);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }

        /* Ensure high contrast text inside highlighted result cards */
        .frosted-glass,
        .frosted-glass p,
        .frosted-glass h1,
        .frosted-glass h2,
        .frosted-glass h3,
        .frosted-glass span,
        .frosted-glass strong {
            color: #102331 !important;
        }

        /* Improve contrast for section headers in dark mode */
        [data-testid="stHeadingWithActionElements"] h1,
        [data-testid="stHeadingWithActionElements"] h2,
        [data-testid="stHeadingWithActionElements"] h3 {
            color: #DDEAF6 !important;
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
    st.markdown(f"""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 48px; margin: 0;'>⛰</h1>
        <h2 style='color: #1A5276; margin-top: 0;'>Glacious</h2>
        <p style='color: #2E86C1; font-size: 12px; margin: 0;'>{t("app_subtitle", st.session_state.language)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Language selector
    language_options = ["en", "de", "fr", "it", "sl", "rm", "hr", "fur", "es", "pt", "ru", "zh", "ja", "ar", "ko", "nl", "pl", "tr", "hi", "sv", "no", "da"]
    current_lang = st.session_state.language if st.session_state.language in language_options else "en"
    current_idx = language_options.index(current_lang)
    language = st.selectbox(
        "🌍 " + t("language_select_label", current_lang),
        language_options,
        format_func=lambda x: {
            "en": "English", "de": "Deutsch", "fr": "Français", "it": "Italiano",
            "sl": "Slovenščina", "rm": "Rumantsch", "hr": "Hrvatski", "fur": "Furlan",
            "es": "Español", "pt": "Português", "ru": "Русский", "zh": "中文",
            "ja": "日本語", "ar": "العربية", "ko": "한국어", "nl": "Nederlands",
            "pl": "Polski", "tr": "Türkçe", "hi": "हिन्दी", "sv": "Svenska",
            "no": "Norsk", "da": "Dansk"
        }.get(x, x),
        index=current_idx,
        key="language_selector"
    )
    st.session_state.language = language
    
    # Region selector
    regions = ["All Alpine ranges", "Swiss Alps", "French Alps", "Italian Alps", "Austrian Alps",
               "Slovenian Alps", "Dolomites", "Mont Blanc Massif", "Pennine Alps", "Bernese Alps"]
    region = st.selectbox(t("region_select_label", language), regions)
    
    # Year range selector
    col1, col2 = st.columns(2)
    with col1:
        year_start = st.number_input(t("start_year_label", language), value=2000, min_value=1984, max_value=2026)
    with col2:
        year_end = st.number_input(t("end_year_label", language), value=2026, min_value=1984, max_value=2026)
    
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
        **Glacious** {t("about_line_1", language)}
        
        {t("about_line_2", language)}
        
        {t("coverage_label", language)}: {", ".join(regions)} {t("across_8_countries", language)}.
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
        {subtitle}
    </p>
</div>
""".format(subtitle=t("app_subtitle", language)), unsafe_allow_html=True)

# Key statistics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(t("glaciers_lost", language), "50%", t("since_1900", language), delta_color="inverse")

with col2:
    st.metric(t("temp_rise", language), "+2.1°C", t("since_1880", language), delta_color="off")

with col3:
    st.metric(t("snow_days_lost", language), "~2.3 days/yr", t("average_trend", language), delta_color="inverse")

with col4:
    st.metric(t("permafrost_degrading", language),"+0.18°C/decade", t("at_10m_depth", language), delta_color="off")

st.divider()

# Render trend tabs above the query section.
top_trends_container = st.container()

# ============================================================================
# INPUT SECTION
# ============================================================================

st.subheader(t("input_placeholder", language).split("...")[0])

# Placeholder examples
placeholders = [
    t("placeholder_example_1", language),
    t("placeholder_example_2", language),
    t("placeholder_example_3", language),
    t("placeholder_example_4", language),
]

# Input area
user_input = st.text_area(
    t("input_placeholder", language),
    value=st.session_state.input_text,
    height=100,
    placeholder=random.choice(placeholders),
    key="user_input"
)

# Check button
check_button = st.button(t("check_btn", language), use_container_width=True, type="primary")

# ============================================================================
# PROCESSING & RESULTS (BEFORE VISUALIZATIONS)
# ============================================================================

if check_button and user_input:
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
# DISPLAY RESULTS (BEFORE VISUALIZATIONS)
# ============================================================================

if st.session_state.last_result:
    result = st.session_state.last_result
    
    # Mode indicator
    if result["mode"] == "query":
        mode_pill = f'<div style="display: inline-block; background-color: #2E86C1; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">🔍 {t("mode_query_label", language)}</div>'
    else:
        mode_pill = f'<div style="display: inline-block; background-color: #FF9800; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">✓ {t("mode_validation_label", language)}</div>'
    
    st.markdown(mode_pill, unsafe_allow_html=True)
    
    st.divider()
    
    # QUERY MODE RESPONSE
    if result["mode"] == "query":
        st.subheader(t("analysis_results_header", language))
        
        # Answer box
        st.info(result.get("answer", ""))
        
        # Key fact callout
        st.markdown(f"""
        <div class='frosted-glass'>
            <h3 style='margin-top: 0;' color: #1A5276;'>⭐ {t("key_finding_label", language)}</h3>
            <p style='font-size: 16px; font-weight: bold; margin: 0;'>{result.get("key_fact", "")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Causes & outcomes
        try:
            causes = get_causes_context(result.get("variable", "glacier"), region, language)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(t("root_causes_label", language))
                with st.expander(t("regional_global_drivers", language)):
                    for cause in causes.get("regional_causes", []):
                        st.write(f"• {cause}")
                    st.divider()
                    for cause in causes.get("global_causes", []):
                        st.write(f"• {cause}")
                
                with st.expander(t("human_accelerators", language)):
                    for item in causes.get("anthropogenic_expeditors", []):
                        st.write(f"• {item}")
            
            with col2:
                st.subheader(t("consequences_label", language))
                with st.expander(t("ecological_impacts", language)):
                    for outcome in causes.get("ecological_outcomes", []):
                        st.write(f"• {outcome}")
                
                with st.expander(t("social_economic", language)):
                    for outcome in causes.get("social_outcomes", []):
                        st.write(f"• {outcome}")
        except:
            pass
    
    # VALIDATION MODE RESPONSE
    elif result["mode"] == "validation":
        st.subheader(t("verdict_label", language))
        
        # Verdict card
        verdict = result.get("verdict", t("unknown_label", language))
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
            <p style='font-size: 12px; color: #666;'>{t("region_axis_label", language)}: {result.get("region")} | {t("period_label", language)}: {result.get("year_start")}-{result.get("year_end")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Confidence bar
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(confidence, f"{t('confidence_label', language)}: {confidence:.0%}")
        
        # Sources section
        st.subheader(t("sources_label", language))
        
        sources = result.get("sources_used", [])
        for source in sources:
            source_meta = SOURCE_METADATA.get(source, {})
            if source_meta:
                tier_emoji = {"1": "🟢", "2": "🟡", "3": "🔘"}.get(str(source_meta.get("credibility_tier")), "⭕")
                st.write(f"{tier_emoji} **{source}** - {source_meta.get('institution', '')}")
                with st.expander(t("details_label", language)):
                    st.write(f"**{t('resolution_label', language)}:** {source_meta.get('spatial_resolution')}")
                    st.write(f"**{t('coverage_label', language)}:** {source_meta.get('temporal_coverage')}")
                    if source_meta.get('known_limitations'):
                        st.write(f"**{t('limitations_label', language)}:**")
                        for lim in source_meta['known_limitations'][:2]:
                            st.write(f"• {lim}")
        
        st.info(result.get("credibility_assessment", ""))
        
        # Check for similar misinformation
        misinfo_matches = load_misinfo_matches(result.get("accurate_finding", ""))
        if misinfo_matches:
            st.warning("⚠️ " + t("similar_claims_warning", language))
    
    st.divider()

# ============================================================================
# INTERACTIVE TREND VISUALIZATIONS
# ============================================================================

with top_trends_container:
    st.subheader(t("climate_trends_title", language))

    # Load glacier data
    if True:
        with open("data/glaciers.geojson") as f:
            glacier_data = json.load(f)
        
        with open("data/alpine_regions.json") as f:
            regions_data = json.load(f)
        
        # Extract glacier regions for visualization
        glacier_regions = {}
        for feature in glacier_data["features"]:
            props = feature["properties"]
            region = props.get("region", "Unknown")
            if region not in glacier_regions:
                glacier_regions[region] = {
                    "2000": 0,
                    "2024": 0,
                    "decline": 0,
                    "lat": feature["geometry"]["coordinates"][1],
                    "lon": feature["geometry"]["coordinates"][0]
                }
            glacier_regions[region]["2000"] += props.get("glacier_area_2000_km2", 0)
            glacier_regions[region]["2024"] += props.get("glacier_area_2024_km2", 0)
            glacier_regions[region]["decline"] = max(glacier_regions[region]["decline"], 
                                                      props.get("decline_percent", 0))
        
        # Create regions list for all tabs
        regions_list = list(glacier_regions.keys())
        
        # Create visualization tabs - SATELLITE MAP IS FIRST
        viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs([
            "🗺️ " + t("satellite_map_tab", language),
            "📉 " + t("glacier_decline_tab", language),
            "📈 " + t("climate_indicators_tab", language),
            "📋 Policy Guidance",
            "🌍 Socioecological Impacts",
        ])
    
    with viz_tab1:
        # Interactive map with satellite imagery
        st.markdown("**" + t("satellite_map_header", language) + "**")
        st.info("💡 **" + t("map_guide_label", language) + ":** Hover over markers for region details. Use layer control (top-right) to toggle overlays.")
        st.markdown("**" + t("heatmap_about_label", language) + ":** " + t("heatmap_about_text", language))
        
        try:
            if not glacier_regions or not regions_list:
                st.error(t("no_glacier_data", language))
            else:
                center_lat = np.mean([glacier_regions[r]["lat"] for r in regions_list])
                center_lon = np.mean([glacier_regions[r]["lon"] for r in regions_list])
                
                # Build map with SATELLITE as default
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=6,
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    control_scale=True
                )
                
                # Base layers
                folium.TileLayer(
                    tiles='OpenStreetMap',
                    name='🗺️ Map',
                    overlay=False,
                    control=True,
                    show=False
                ).add_to(m)

                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    name='🏔️ Topographic',
                    overlay=False,
                    control=True,
                    show=False
                ).add_to(m)

                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    name='⛰️ Hillshade',
                    overlay=False,
                    control=True,
                    show=False
                ).add_to(m)
                
                # Overlay: Glacier decline heatmap
                heat_data = [
                    [glacier_regions[r]["lat"], glacier_regions[r]["lon"], glacier_regions[r]["decline"]]
                    for r in glacier_regions
                ]
                try:
                    from folium.plugins import HeatMap
                    if heat_data:
                        HeatMap(
                            heat_data,
                            name='🔥 Heatmap',
                            min_opacity=0.25,
                            radius=55,
                            blur=24,
                            max_zoom=10,
                            gradient={0.0: 'blue', 0.3: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'},
                            show=True
                        ).add_to(m)
                except Exception:
                    pass
                
                # Overlay: Vegetation stress proxy
                vegetation_layer = folium.FeatureGroup(name='🌿 Vegetation Index', show=False)
                for region, data in glacier_regions.items():
                    veg_score = max(0.0, min(1.0, 1.0 - (data["decline"] / 50.0)))
                    veg_radius = 12 + (veg_score * 10)
                    folium.CircleMarker(
                        location=[data["lat"], data["lon"]],
                        radius=veg_radius,
                        tooltip=f"<b>{region}</b><br>Vegetation: {veg_score:.2f}",
                        popup=f"<b>{region}</b><br>Vegetation Score: {veg_score:.2f}",
                        color='#1B5E20',
                        fill=True,
                        fillColor='#66BB6A',
                        fillOpacity=0.35,
                        weight=1
                    ).add_to(vegetation_layer)
                vegetation_layer.add_to(m)
                
                # Overlay: Glacier markers - HOVER ENABLED
                markers_layer = folium.FeatureGroup(name='📍 Glacier Regions', show=True)
                for region, data in glacier_regions.items():
                    color = '#E74C3C' if data["decline"] > 30 else '#F39C12' if data["decline"] > 15 else '#27AE60'
                    
                    # Create detailed hover text
                    hover_text = f"""<b>{region}</b><br>
Decline: {data['decline']:.1f}%<br>
2000: {data['2000']:.1f} km²<br>
2024: {data['2024']:.1f} km²"""
                    
                    folium.CircleMarker(
                        location=[data["lat"], data["lon"]],
                        radius=8 + data["decline"]/5,
                        tooltip=hover_text,
                        popup=hover_text,
                        color=color,
                        fillColor=color,
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(markers_layer)
                markers_layer.add_to(m)

                # Overlay: Stream flow layer
                stream_layer = folium.FeatureGroup(name='🌬️ Stream Flow', show=False)
                for region, data in glacier_regions.items():
                    start_lat = data["lat"]
                    start_lon = data["lon"]
                    dx = 0.7 + (data["decline"] / 45.0)
                    dy = 0.2 + (data["decline"] / 130.0)
                    end_lat = start_lat + dy
                    end_lon = start_lon + dx

                    folium.PolyLine(
                        locations=[[start_lat, start_lon], [end_lat, end_lon]],
                        color='#1A5276',
                        weight=2 + data["decline"] / 25.0,
                        opacity=0.85,
                        tooltip=f"{region}: Decline {data['decline']:.1f}%"
                    ).add_to(stream_layer)

                    folium.CircleMarker(
                        location=[end_lat, end_lon],
                        radius=3,
                        color='#1A5276',
                        fill=True,
                        fillColor='#2E86C1',
                        fillOpacity=0.95,
                        weight=1,
                        tooltip=f"{region}: Flow endpoint"
                    ).add_to(stream_layer)

                stream_layer.add_to(m)

                # Add layer control with expanded view
                folium.LayerControl(position='topright', collapsed=False).add_to(m)
                
                # Try st_folium first, fall back to HTML if needed
                try:
                    st_folium(m, width=1350, height=700)
                except Exception:
                    # Fallback to HTML rendering
                    map_html = m.get_root().render()
                    st.components.v1.html(map_html, height=700, scrolling=False)
        
        except Exception as e:
            st.error(f"{t('map_error', language)}: {str(e)}")
    
    with viz_tab2:
        st.markdown("### " + t("glacier_decline_tab", language))
        
        # Glacier area comparison
        st.markdown("#### " + t("glacier_area_decline_title", language))
        st.caption("**Why?** Satellite measurements (Landsat) show cumulative area loss across Alpine regions, indicating the scale and regional variation of glacier retreat.")
        
        areas_2000 = [glacier_regions[r]["2000"] for r in regions_list]
        areas_2024 = [glacier_regions[r]["2024"] for r in regions_list]
        decline_pct = [glacier_regions[r]["decline"] for r in regions_list]
        
        fig = go.Figure(data=[
            go.Bar(name='2000', x=regions_list, y=areas_2000, marker_color='#4A90E2', opacity=0.8),
            go.Bar(name='2024', x=regions_list, y=areas_2024, marker_color='#F5A623', opacity=0.8)
        ])
        
        fig.update_layout(
            title=t("glacier_area_decline_title", language),
            xaxis_title=t("region_axis_label", language),
            yaxis_title=t("glacier_area_axis_label", language),
            barmode='group',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**Trend:** Glacier area has declined dramatically between 2000 and 2024, with accelerating loss concentrated in lower-elevation regions. This pattern signals critical tipping points where smaller glaciers risk disappearance within decades.")
        
        # Decline percentage
        st.markdown("#### " + t("regional_decline_rate_title", language))
        st.caption("**Why?** Percentage decline rates highlight which regions are losing glaciers fastest; areas >30% loss face water scarcity and tourism collapse risks.")
        
        fig2 = go.Figure(data=[
            go.Bar(x=regions_list, y=decline_pct,
                   marker=dict(color=decline_pct, colorscale='Reds', showscale=True,
                              colorbar=dict(title=t("decline_percent_short", language))))
        ])
        
        fig2.update_layout(
            title=t("regional_decline_rate_title", language),
            xaxis_title=t("region_axis_label", language),
            yaxis_title=t("decline_percent_axis_label", language),
            template='plotly_white',
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("**Trend:** Regional vulnerability hotspots emerge across the Alpine chain, with southern Alps experiencing steeper decline rates (>30%) than northern regions. This disparity reflects latitude-dependent warming gradients and elevation-driven sensitivity differences.")
        
        st.divider()
        
        # Snow cover duration trend
        st.markdown("#### Snow Cover Duration Trend")
        st.caption("**Why?** Shorter snow cover seasons reduce meltwater availability for summer hydropower and agriculture; earlier melt increases flood risk during spring.")
        
        data = get_loader().load_all_data(region, int(year_start), int(year_end))
        snow_data = data.get("modis", {})
        if snow_data.get("years"):
            fig_snow = go.Figure()
            fig_snow.add_trace(go.Scatter(
                x=snow_data["years"], y=snow_data["snow_cover_days"],
                mode='lines+markers', name=t("snow_cover_days_series", language),
                line=dict(color='#3498DB', width=3),
                marker=dict(size=6, color='#2E86C1'),
                fill='tozeroy'
            ))
            fig_snow.update_layout(
                title=t("snow_cover_duration_title", language),
                xaxis_title=t("year_axis_label", language),
                yaxis_title=t("days_per_year_axis", language),
                template="plotly_white",
                hovermode="x unified",
                height=350
            )
            st.plotly_chart(fig_snow, use_container_width=True)
            st.caption("**Trend:** Snow season compression (2–3 weeks per decade) directly shortens meltwater availability windows and advances spring flood timing, disrupting hydropower operations and irrigation schedules across downstream communities.")
        
        # Glacier area trend over time
        st.markdown("#### Glacier Area Trend")
        st.caption("**Why?** Long-term area trends reveal cumulative ice loss; steeper declines indicate accelerating retreat linked to atmospheric warming.")
        
        glacier_data = data.get("landsat", {})
        if glacier_data.get("years"):
            fig_glacier = go.Figure()
            fig_glacier.add_trace(go.Scatter(
                x=glacier_data["years"], y=glacier_data["glacier_area_km2"],
                mode='lines+markers', name=t("glacier_area_series", language),
                line=dict(color='#E74C3C', width=3),
                marker=dict(size=6),
                fill='tozeroy'
            ))
            fig_glacier.update_layout(
                title=t("glacier_area_trend_title", language),
                xaxis_title=t("year_axis_label", language),
                yaxis_title=t("area_axis_label", language),
                template="plotly_white",
                hovermode="x unified",
                height=350
            )
            st.plotly_chart(fig_glacier, use_container_width=True)
            st.caption("**Trend:** Glacier area shows markedly non-linear decline—relatively stable 1980–2000 followed by accelerating loss 2000–2024. This trajectory reflects climate system threshold crossing where feedback loops amplify warming impacts on ice mass balance.")
    
    with viz_tab3:
        st.markdown("### " + t("climate_indicators_tab", language))
        
        # Key climate metrics
        st.markdown("#### Key Climate Indicators")
        st.caption("**Why?** These metrics directly drive glacier retreat: temperature controls melt rates, snow loss shortens seasons, and permafrost thaw destabilizes infrastructure.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🌡️ " + t("temp_rise", language),
                "+2.1°C",
                "+0.25°C/decade",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                "❄️ " + t("snow_days_lost", language),
                "~2.3 days/year",
                t("since_1980_delta", language),
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "🧊 " + t("permafrost_degrading", language),
                "+0.18°C/decade",
                t("at_10m_depth", language),
                delta_color="off"
            )
        
        st.divider()
        
        # Temperature and snow trend chart
        st.markdown("#### Temperature anomaly & snow days trend")
        st.caption("**Why?** These coupled trends show accelerating Alpine warming and water cycle disruption; earlier springs mean shifted runoff patterns affecting hydropower and agriculture.")
        
        years = np.array([2000, 2005, 2010, 2015, 2020, 2024])
        temp_anomaly = np.array([0.0, 0.3, 0.6, 1.1, 1.7, 2.1])
        snow_days = np.array([100, 95, 88, 82, 75, 72])
        
        fig_trend = sp.make_subplots(
            specs=[[{"secondary_y": True}]]
        )
        
        fig_trend.add_trace(
            go.Scatter(x=years, y=temp_anomaly, name=t("temperature_anomaly_series", language),
                      line=dict(color='#E74C3C', width=3), mode='lines+markers'),
            secondary_y=False
        )
        
        fig_trend.add_trace(
            go.Scatter(x=years, y=snow_days, name=t("snow_days_series", language),
                      line=dict(color='#3498DB', width=3), mode='lines+markers'),
            secondary_y=True
        )
        
        fig_trend.update_layout(
            title=t("climate_trends_chart_title", language),
            hovermode='x unified',
            template='plotly_white',
            height=400,
            legend=dict(x=0.02, y=0.98)
        )
        
        fig_trend.update_xaxes(title_text=t("year_axis_label", language))
        fig_trend.update_yaxes(title_text=t("temperature_anomaly_axis", language), secondary_y=False)
        fig_trend.update_yaxes(title_text=t("snow_days_axis", language), secondary_y=True)
        
        st.plotly_chart(fig_trend, use_container_width=True)
        st.caption("**Trend:** Temperature and snow reduction show tightly coupled response: each 1°C warming corresponds to ~0.8 days reduction in snow season, creating compounding stress on Alpine water systems and biodiversity migration capacity.")
        
        st.divider()
        
        # Permafrost trend
        st.markdown("#### Permafrost Degradation")
        st.caption("**Why?** Warming permafrost weakens mountain infrastructure (roads, tunnels, buildings); thawing also releases stored carbon, creating feedback loops.")
        
        data = get_loader().load_all_data(region, int(year_start), int(year_end))
        perm_data = data.get("permafrost", {})
        if perm_data.get("years"):
            fig_perm = go.Figure()
            fig_perm.add_trace(go.Scatter(
                x=perm_data["years"], y=perm_data["temperature_10m_celsius"],
                mode='lines+markers', name=t("temperature_10m_series", language),
                line=dict(color='#922B21', width=3),
                marker=dict(size=6),
                fill='tozeroy'
            ))
            fig_perm.update_layout(
                title=t("permafrost_temp_trend_title", language),
                xaxis_title=t("year_axis_label", language),
                yaxis_title=t("temperature_axis_label", language),
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_perm, use_container_width=True)
            st.caption("**Trend:** Permafrost warming at high elevations proceeds faster than valley warming (+0.18°C/decade at 10m depth), destabilizing mountain infrastructure including roads, railroads, and communication systems critical to Alpine communities.")
        
        st.divider()
        
        # Biodiversity shift
        st.markdown("#### Species elevation shifts")
        st.caption("**Why?** Alpine species migrate upslope to stay in cooler zones; loss of summit habitat threatens endemics; range shifts disrupt ecosystems and food webs.")
        
        bio_data = data.get("biodiversity", {})
        if bio_data.get("species_elevation_shifts"):
            fig_bio = go.Figure()
            for species, elevations in bio_data["species_elevation_shifts"].items():
                fig_bio.add_trace(go.Scatter(
                    x=bio_data["years"], y=elevations,
                    mode='lines+markers', name=species.replace('_', ' ').title(),
                    line=dict(width=2)
                ))
            fig_bio.update_layout(
                title=t("species_elevation_shifts_title", language),
                xaxis_title=t("year_axis_label", language),
                yaxis_title=t("elevation_axis_label", language),
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_bio, use_container_width=True)
            st.caption("**Trend:** Alpine species have shifted 30–50m upslope per decade seeking cooler habitats. This rapid migration indicates severe habitat squeeze, where summit-restricted species face complete range loss by 2070 under continued warming scenarios.")
        
        st.divider()
        
        # Economic impact: ski season
        st.markdown("#### Ski season length decline")
        st.caption("**Why?** Shorter seasons reduce tourism revenue and employment; earlier melt compromises snow quality; low elevation resorts face existential pressure.")
        
        econ_data = data.get("tourism", {})
        if econ_data.get("years"):
            fig_econ = go.Figure()
            fig_econ.add_trace(go.Scatter(
                x=econ_data["years"], y=econ_data["ski_season_days"],
                mode='lines+markers', name=t("ski_season_series", language),
                line=dict(color='#2E86C1', width=3),
                marker=dict(size=6),
                fill='tozeroy'
            ))
            fig_econ.update_layout(
                title=t("ski_season_title", language),
                xaxis_title=t("year_axis_label", language),
                yaxis_title=t("days_axis_label", language),
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_econ, use_container_width=True)
            st.caption("**Trend:** Ski season shortening (~4 days per decade) combined with declining snowfall creates economic pressure especially on resorts below 1,500m elevation. Many Alpine communities face existential economic challenges requiring diversification by 2050.")
    
    # Tab 4: Policy Guidance
    with viz_tab4:
        st.markdown("### Policy Guidance & Climate Pathways")
        st.markdown("**Expected sector implications and policy levers for Alpine adaptation**")
        
        # Create sectors with implications
        policy_col1, policy_col2 = st.columns(2)
        
        with policy_col1:
            # Water Supply
            st.markdown(f"#### Water Supply & Hydropower")
            with st.expander("Timetable & Implications (2025–2100)"):
                st.write("**2025–2030**: 10–15% reduction in summer runoff; earlier spring peak")
                st.write("**2030–2050**: 25–35% cumulative snow decline affects hydropower")
                st.write("**2050+**: Alpine water scarcity impacts downstream agriculture")
            
            # Energy
            st.markdown(f"#### Energy Infrastructure")
            with st.expander("Timetable & Implications"):
                st.write("**2025–2030**: Hydropower output variability increases ±8–12% annually")
                st.write("**2030–2050**: Alpine reservoirs need adaptive storage strategies")
                st.write("**2050+**: Renewable energy infrastructure redesign needed")
        
        with policy_col2:
            # Infrastructure
            st.markdown(f"#### Infrastructure & Transport")
            with st.expander("Timetable & Implications"):
                st.write("**2025–2030**: Permafrost thaw destabilizes mountain roads and rail (2–5°C warming)")
                st.write("**2030–2050**: Alpine tunnel & infrastructure maintenance costs rise 30–50%")
                st.write("**2050+**: Major infrastructure relocation required in vulnerable areas")
            
            # Economy
            st.markdown(f"#### Tourism & Economy")
            with st.expander("Timetable & Implications"):
                st.write("**2025–2030**: Alpine tourism shifts; ski season shortens by ~3–4 weeks/decade")
                st.write("**2030–2050**: Regional GDP in Alpine tourism drops 20–40%")
                st.write("**2050+**: Economic diversification becomes survival strategy")
        
        st.divider()
        st.markdown("**Policy Levers & Mitigation Strategies**")
        
        lever_col1, lever_col2 = st.columns(2)
        
        with lever_col1:
            st.markdown(f"#### Emissions Pathways (Current vs. Paris-Aligned)")
            with st.expander("View comparison chart"):
                fig_emissions = go.Figure()
                years_proj = [2024, 2035, 2050, 2100]
                current_traj = [1.3, 1.8, 2.7, 4.5]
                paris_traj = [1.3, 1.5, 1.8, 1.9]
                
                fig_emissions.add_trace(go.Scatter(
                    x=years_proj, y=current_traj,
                    name="Current Trajectory",
                    line=dict(color='#E74C3C', width=3, dash='dash')
                ))
                fig_emissions.add_trace(go.Scatter(
                    x=years_proj, y=paris_traj,
                    name="Paris-Aligned (+1.5°C)",
                    line=dict(color='#27AE60', width=3)
                ))
                fig_emissions.update_layout(
                    title="Warming Pathway Comparison (°C)",
                    xaxis_title="Year",
                    yaxis_title="Temperature (°C)",
                    template='plotly_white', height=300
                )
                st.plotly_chart(fig_emissions, use_container_width=True)
                st.caption("**Trend:** Current emissions trajectory leads to 4.5°C warming by 2100 versus 1.9°C under Paris-aligned pathways. Alpine tipping points occur in both scenarios, but the 2.6°C difference dramatically shifts timelines for critical impacts and adaptation requirements.")
        
        with lever_col2:
            st.markdown(f"#### Adaptation & Mitigation Options")
            st.write("**Water Storage & Management:**")
            st.write("- Alpine dams & underground reservoirs to capture early spring melt")
            st.write("- Mitigate summer droughts; coordinate transboundary water sharing")
            st.write("")
            st.write("**Land Use & Infrastructure Controls:**")
            st.write("- Forest zoning to stabilize permafrost (~0.5–1°C cooling local effect)")
            st.write("- Avalanche setback rules; infrastructure relocation financing")
            st.write("- Agricultural transition support")
        
        st.info("**Data Sources:** Eurostat, Alpine Convention, IPCC AR6, UNFCCC databases")
    
    # Tab 5: Socioecological Impacts
    with viz_tab5:
        st.markdown("### Socioecological Impacts & Risk Indicators")
        
        # Sub-tabs for impacts
        impact_subtabs = st.tabs([
            "Runoff Shifts",
            "Disaster Outcomes",
            "Economic & Human Costs",
            "Risk Indicators"
        ])
        
        # Subtab 1: Runoff Impacts
        with impact_subtabs[0]:
            st.markdown(f"#### Surface Runoff Patterns")
            st.write("• **Flood Risk**: Spring melt peaks 2–4 weeks earlier; peak discharge increases 15–30%")
            st.write("• **Infrastructure Strain**: Hydropower intakes; bridge scour; dam overspill risks")
            st.write("• **Observed Trend**: Alpine flash-flood events +40% frequency (2000–2024)")
            
            st.divider()
            
            st.markdown(f"#### Subsurface Flow & Water Availability")
            st.write("• **Groundwater Recharge**: Earlier snowmelt delays autumn recharge cycles")
            st.write("• **Water Supply Crisis**: Summer groundwater levels 10–20% lower than historical")
            st.write("• **Crop Irrigation**: Alpine farming faces 3–6 week water shortage window")
            st.write("• **Wetland Ecosystems**: Wetlands dry 2–3 weeks earlier → 30–50% biodiversity loss")
            
            st.divider()
            
            st.markdown(f"#### Seasonality Shifts (Regional Data)")
            data_runoff = {
                "Alpine Region": ["Swiss Alps", "Austrian Alps", "French Alps", "Italian Alps"],
                "Peak Flow Shift (weeks)": [3.2, 2.8, 3.5, 2.1],
                "Summer Shortage Risk (%)": [35, 28, 40, 22]
            }
            df_runoff = pd.DataFrame(data_runoff)
            st.dataframe(df_runoff, use_container_width=True)
            st.caption("**Context:** Peak runoff timing shifts vary significantly by region—French Alps experience greatest shift (3.5 weeks) while Italian Alps show least (2.1 weeks). Summer shortage risks exceed 30% across all regions, threatening agriculture and hydropower stability.")
        
        # Subtab 2: Disaster Outcomes
        with impact_subtabs[1]:
            st.markdown(f"#### Flooding Hazard Escalation")
            col_flood1, col_flood2 = st.columns(2)
            with col_flood1:
                st.write(f"**Observed Trend**: ⚠️ INCREASING")
                st.write("• Return periods: 1-in-10 year → 1-in-5 year (2000–2024)")
                st.write("• Affected regions: Swiss Valais (2005, 2021), Austrian Salzburg (2022)")
                st.write("• Affected regions: Veneto Italy (2010), French Isère (2012)")
            with col_flood2:
                st.write(f"**Future Outlook (2030–2050)**: 🔴 HIGH RISK")
                st.write("• Rainfall intensity +20–30% in Alpine storms")
                st.write("• Snowmelt + extreme rain = compound floods")
                st.write("• Economic loss: ~€500M–€1B per major event Alps-wide")
            
            st.divider()
            
            st.markdown(f"#### Landslide & Rock-Fall Risk")
            st.write("• **Trigger**: Permafrost thaw + increased precipitation")
            st.write("• **Threat**: Mountain communities; Alpine infrastructure corridors")
            st.write("• **Frequency**: Rockfall events +60% since 2000")
            
            st.divider()
            
            st.markdown(f"#### Avalanche Dynamics")
            st.write("• **Wet slides increase**: Earlier/wetter springs → heavier snow")
            st.write("• **Season extends**: Autumn avalanches new phenomenon (rare before 2010)")
            st.write("• **Observed**: Fatal avalanche accidents +50% in warm years")
        
        # Subtab 3: Economic & Human Costs
        with impact_subtabs[2]:
            st.markdown(f"#### Alpine Tourism Collapse Risk")
            st.write("• **Low-elevation ski resorts**: <80% ski-able days by 2050 (vs. 120 today)")
            st.write("• **Employment loss**: ~50,000 Alpine workers in ski industry (direct + indirect)")
            st.write("• **Regional GDP exposure**: Swiss Valais, Austrian Tyrol, French Savoy: 15–25% economy tourism-dependent")
            
            st.divider()
            
            st.markdown(f"#### Agricultural Disruption")
            st.write("• **Alpine pastures dry**: Summer water hole failures; livestock stress")
            st.write("• **Crop shifts**: Loss of traditional Alpine cheese/butter production")
            st.write("• **Economic impact**: ~€300M/year Alpine agricultural sector")
            
            st.divider()
            
            st.markdown(f"#### Social & Health Impacts")
            st.write("• **Heat stress**: Summer temperatures +4–6°C in Swiss/Austrian valleys → heat waves")
            st.write("• **Mental health**: Climate anxiety; loss of cultural identity (glaciers, traditions)")
            st.write("• **Migration**: Potential outmigration from nonviable Alpine communities (~10,000–50,000 by 2050)")
        
        # Subtab 4: Risk Indicators
        with impact_subtabs[3]:
            st.markdown(f"#### Multi-Hazard Risk Matrix")
            
            risk_data = {
                "Hazard": ["Glacier Collapse", "Extreme Floods", "Permafrost Thaw", "Avalanches", "Droughts"],
                "Frequency (2024)": ["Increasing", "Very High", "Increasing", "High", "Moderate"],
                "Severity (Impact)": ["Very High", "Very High", "High", "High", "Medium"],
                "Confidence Level": ["95%", "90%", "92%", "88%", "78%"]
            }
            df_risk = pd.DataFrame(risk_data)
            st.dataframe(df_risk, use_container_width=True)
            st.caption("**Context:** Extreme floods and glacier collapse pose highest combined risk (frequency + severity), while droughts represent emerging threat with lower confidence. Multi-hazard cascades (e.g., permafrost thaw triggering landslides during extreme rainfall) amplify overall Alpine disaster risk beyond individual hazard assessment.")
            
            st.divider()
            
            st.markdown(f"#### Critical Tipping Points (When?)") 
            st.write("• **Swiss glaciers—total disappearance**: 2070–2100 (if warming continues)")
            st.write("• **Permafrost Alpine zone stabilization**: 2050 (if Paris-aligned pathway + 1.5°C)")
            st.write("• **Ski industry viability**: 2040–2060 (threshold: <80% operating days)")
            st.write("• **Mountain agriculture collapse**: 2045–2070 (if adaptation fails)")
            
            st.info("💡 **Mitigation potential**: 0.5–1.0°C cooling if global net-zero achieved by 2050 + Alpine nature-based solutions")

# ============================================================================
# REMOVE DUPLICATE SECTIONS BELOW - VISUALIZATIONS END HERE
# Footer
st.divider()
st.caption(f"""
**Glacious** — {t('footer_line_1', language)}
{t('footer_line_2', language)}
""")
