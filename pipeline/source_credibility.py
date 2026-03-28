"""Source credibility assessment for Alpine climate data."""

SOURCE_METADATA = {
    "Sentinel-2": {
        "name": "Sentinel-2 MSI",
        "institution": "European Space Agency / Copernicus",
        "data_type": "Multispectral satellite imagery",
        "spatial_resolution": "10-20m",
        "temporal_coverage": "2015-present",
        "temporal_resolution": "10 days composite",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 1,
        "known_limitations": [
            "Cloud cover gaps require interpolation in some periods",
            "NDSI snow metric performs less reliably on wet snow",
            "Mixed pixels at glacier edges may underestimate extent",
            "Seasonal availability limited in winter by cloud cover"
        ],
        "caution_flags": []
    },
    "MODIS": {
        "name": "MODIS MOD10A1 Snow Cover",
        "institution": "NASA NSIDC",
        "data_type": "Daily satellite snow cover mapping",
        "spatial_resolution": "500m",
        "temporal_coverage": "2000-present",
        "temporal_resolution": "Daily",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 1,
        "known_limitations": [
            "Cloud cover gaps require gap-filling",
            "Algorithm less reliable on wet snow and storm transitions",
            "Spatial resolution limits detection of small snow patches"
        ],
        "caution_flags": ["Seasonal cloud cover may underestimate true snow extent"]
    },
    "WGMS": {
        "name": "World Glacier Monitoring Service",
        "institution": "ETH Zurich / WGMS",
        "data_type": "Field measurements of glacier mass balance",
        "spatial_resolution": "Point measurements at reference glaciers",
        "temporal_coverage": "1945-present (intensive 1961+)",
        "temporal_resolution": "Annual",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 1,
        "known_limitations": [
            "Only ~80-100 glaciers globally under continuous monitoring",
            "Biased toward accessible, lower-altitude glaciers",
            "May not represent remote high-altitude glacier changes",
            "Requires careful field logistics in extreme terrain"
        ],
        "caution_flags": []
    },
    "GRACE": {
        "name": "GRACE Satellite Gravimetry",
        "institution": "JPL NASA / University of Texas",
        "data_type": "Gravity anomaly indicating ice mass loss",
        "spatial_resolution": "~150km",
        "temporal_coverage": "2002-present",
        "temporal_resolution": "Monthly",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 1,
        "known_limitations": [
            "Coarse spatial resolution (~150km) cannot resolve individual glaciers",
            "Cannot distinguish between glacier, groundwater, and other mass changes",
            "Requires independent data to attribute signal to ice loss",
            "Early data carry higher uncertainties"
        ],
        "caution_flags": ["Use results as regional aggregate indicators only"]
    },
    "EEAR-CLIM": {
        "name": "European Environmental Analysis Results - Climate",
        "institution": "Copernicus Climate Change Service",
        "data_type": "Reanalysis daily climate data",
        "spatial_resolution": "30km grid",
        "temporal_coverage": "1979-present",
        "temporal_resolution": "Daily",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 1,
        "known_limitations": [
            "Reanalysis blends observations with model output",
            "High-altitude Alpine stations sparse; model-dependent",
            "Spatial resolution may smooth local climate phenomena",
            "Biases in precipitation reanalysis over mountains"
        ],
        "caution_flags": ["Independent station validation recommended"]
    },
    "Landsat": {
        "name": "Landsat Surface Reflectance",
        "institution": "USGS / NASA",
        "data_type": "Multispectral satellite time series",
        "spatial_resolution": "30m",
        "temporal_coverage": "1984-present",
        "temporal_resolution": "16 days",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Sensor changes across Landsat missions (TM, ETM+, OLI)",
            "Requires radiometric calibration and cross-sensor harmonization",
            "Cloud cover limits Alpine observation frequency",
            "Seasonal snow/ice distribution affects classification accuracy"
        ],
        "caution_flags": []
    },
    "RGI": {
        "name": "Randolph Glacier Inventory",
        "institution": "University of Zurich / Global Glaciers Coalition",
        "data_type": "Glacier outlines database",
        "spatial_resolution": "Variable (1-100m source data)",
        "temporal_coverage": "Various epochs (mostly circa 2000 ± 5)",
        "temporal_resolution": "Static",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Outlines from different time periods and sources (1984-2010)",
            "Requires supplementary time series for change detection",
            "Uncertainty in outline delineation at ice margins",
            "Small glacier areas difficult to represent accurately"
        ],
        "caution_flags": ["Use with time series data for trend analysis, not standalone"]
    },
    "PERMOS": {
        "name": "Permafrost Monitoring Switzerland",
        "institution": "University of Zurich / MeteoSwiss",
        "data_type": "Borehole temperature measurements",
        "spatial_resolution": "Point locations",
        "temporal_coverage": "1987-present (intensive 2000+)",
        "temporal_resolution": "Sub-daily, aggregated annually",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Limited to Switzerland; no northern Alps coverage",
            "Only ~20 boreholes with long-term records",
            "Local site conditions affect representativeness",
            "Installation bias (accessible sites preferred)"
        ],
        "caution_flags": ["Results specific to Alpine permafrost; generalization limited"]
    },
    "GBIF": {
        "name": "Global Biodiversity Information Facility",
        "institution": "GBIF Secretariat / International Consortium",
        "data_type": "Species occurrence observations",
        "spatial_resolution": "Point location variable",
        "temporal_coverage": "Historical to present",
        "temporal_resolution": "Event-based",
        "peer_reviewed": False,
        "open_access": True,
        "credibility_tier": 3,
        "known_limitations": [
            "Observation bias: more records near research centers",
            "Seasonal bias: more observations during field seasons",
            "Variable data quality and identification reliability",
            "Absence of observation doesn't imply absence of species",
            "Taxonomic standardization incomplete"
        ],
        "caution_flags": ["Validate with published field surveys before publication"]
    },
    "Eurostat": {
        "name": "Eurostat Tourism Statistics",
        "institution": "European Commission Statistics Authority",
        "data_type": "Tourism arrivals, accommodation, revenue",
        "spatial_resolution": "Regional NUTS 2 level",
        "temporal_coverage": "1990-present (variable by country)",
        "temporal_resolution": "Annual",
        "peer_reviewed": False,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Definition of 'tourist' and 'overnight stay' varies by country",
            "Ski resort data aggregated; cannot isolate climate impacts",
            "Confounded by economic cycles, infrastructure changes",
            "Missing data for some countries/periods"
        ],
        "caution_flags": ["Isolate climate effects from confounding variables"]
    },
    "Copernicus DEM": {
        "name": "Copernicus Digital Elevation Model",
        "institution": "ESA / Copernicus",
        "data_type": "Radar-derived elevation model",
        "spatial_resolution": "30m",
        "temporal_coverage": "2011-present (2020 processing)",
        "temporal_resolution": "Static reference",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Single epoch (~2012 median); cannot measure elevation changes directly",
            "Requires multi-epoch DEM comparison for change analysis",
            "Radar penetration varies by snow/ice conditions",
            "Vertical accuracy ±10-15m in Alpine terrain"
        ],
        "caution_flags": ["Use with repeat SAR or aerogrammetric data for trend analysis"]
    },
    "NASA GDELT": {
        "name": "Global Database of Events, Language, and Tone",
        "institution": "Google Scholar / Kalev Leetaru",
        "data_type": "News media event database",
        "spatial_resolution": "Geographic coordinates of events",
        "temporal_coverage": "2013-present (1979 historical)",
        "temporal_resolution": "Daily",
        "peer_reviewed": False,
        "open_access": True,
        "credibility_tier": 3,
        "known_limitations": [
            "Automated extraction from news sources; linguistic bias",
            "Overrepresents sources in English and other major languages",
            "Media coverage bias ≠ actual frequency of events",
            "Tone scoring algorithm prone to miscalibration",
            "Dominated by major news outlets and web sources"
        ],
        "caution_flags": ["Use as indicator of media narrative, not climate reality"]
    },
    "NewsAPI": {
        "name": "NewsAPI.org Media Coverage",
        "institution": "NewsAPI",
        "data_type": "News article metadata and content",
        "spatial_resolution": "Text-extracted geographic references",
        "temporal_coverage": "2014-present",
        "temporal_resolution": "Real-time (daily aggregation)",
        "peer_reviewed": False,
        "open_access": False,
        "credibility_tier": 3,
        "known_limitations": [
            "Coverage limited to indexed news sources",
            "Excludes academic publications, grey literature",
            "Subject to news cycle dynamics and media ownership",
            "API limitations on historical backfill",
            "Language coverage 40+ languages but Alps-specific bias unknown"
        ],
        "caution_flags": ["Commercial API; terms of service apply to republication"]
    },
    "Phenology Network": {
        "name": "European Phenology Network / PEP725",
        "institution": "Technical University of Munich",
        "data_type": "Standardized plant/animal phenology observations",
        "spatial_resolution": "Point locations (stations)",
        "temporal_coverage": "1950-present (systematic 1950+)",
        "temporal_resolution": "Event-based (transition dates)",
        "peer_reviewed": True,
        "open_access": True,
        "credibility_tier": 2,
        "known_limitations": [
            "Biased toward accessible sites and institutional networks",
            "Observer changes affect temporal consistency",
            "Definition of phenological events may vary",
            "Alpine coverage sparse compared to lowlands"
        ],
        "caution_flags": []
    },
    "Alpine Research Centers": {
        "name": "University of Zurich / ETH Alpine Labs (Synthetic)",
        "institution": "Multiple Alpine Research Programs",
        "data_type": "Modeled synthesis of satellite + in-situ data",
        "spatial_resolution": "Variable (10-100m)",
        "temporal_coverage": "2000-2026 (as available)",
        "temporal_resolution": "Annual or sub-annual",
        "peer_reviewed": False,
        "open_access": False,
        "credibility_tier": 2,
        "known_limitations": [
            "Proprietary models and methodologies",
            "Limited public documentation of assumptions",
            "Data access may require institutional agreements"
        ],
        "caution_flags": ["Verify institutional sources before publication"]
    }
}

def assess_source_credibility(source_name: str) -> dict:
    """Get credibility assessment for a data source."""
    if source_name not in SOURCE_METADATA:
        return {
            "name": source_name,
            "credibility_tier": 3,
            "credibility_statement": f"Data source '{source_name}' not formally assessed. Verify independently.",
            "known_limitations": ["Unknown source; verification required"]
        }
    
    metadata = SOURCE_METADATA[source_name]
    tier_labels = {1: "Tier 1 (Highest)", 2: "Tier 2 (Medium)", 3: "Tier 3 (Lower)"}
    
    credibility_statement = f"This is a {tier_labels[metadata['credibility_tier']]} peer-reviewed dataset " if metadata['peer_reviewed'] else f"This is a {tier_labels[metadata['credibility_tier']]} dataset "
    credibility_statement += f"with {metadata['spatial_resolution']} spatial resolution and {metadata['temporal_coverage']} temporal coverage. "
    
    if metadata['known_limitations']:
        credibility_statement += f"Readers should be aware that {metadata['known_limitations'][0].lower()}."
    
    if metadata['caution_flags']:
        credibility_statement += f" Important: {metadata['caution_flags'][0]}"
    
    return {
        **metadata,
        "credibility_statement": credibility_statement
    }

def get_claim_source_assessment(sources_used: list) -> str:
    """Generate overall credibility statement for sources used in claim verdict."""
    if not sources_used:
        return "No sources consulted for this assessment."
    
    tier_counts = {1: 0, 2: 0, 3: 0}
    for source in sources_used:
        meta = SOURCE_METADATA.get(source, {})
        tier = meta.get("credibility_tier", 3)
        tier_counts[tier] += 1
    
    if tier_counts[1] > 0:
        return f"This verdict is based on {tier_counts[1]} Tier 1 peer-reviewed data sources with high spatial and temporal resolution, providing strong evidentiary support."
    elif tier_counts[1] == 0 and tier_counts[2] > 0:
        return f"This verdict relies on {tier_counts[2]} Tier 2 sources with medium credibility. Additional Tier 1 data would strengthen the assessment."
    else:
        return "This verdict is based primarily on lower-tier sources. Independent verification with peer-reviewed data is strongly recommended before publication."
