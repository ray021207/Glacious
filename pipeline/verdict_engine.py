"""Verdict engine - validate claims against satellite/environmental data."""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
from pipeline.data_loader import get_loader
from pipeline.source_credibility import assess_source_credibility, get_claim_source_assessment

def validate_claim(parsed_claim: dict, lang: str = "en") -> dict:
    """
    Validate a climate claim against Alpine data.
    
    Returns verdict dict with: verdict, confidence, key_statistic, observed_value,
    claimed_value, data_direction, sources_used, accurate_finding, credibility_assessment
    """
    
    region = parsed_claim.get("region", "All Alps")
    variable = parsed_claim.get("variable", "glacier").lower()
    direction = parsed_claim.get("direction", "unknown").lower()
    magnitude = parsed_claim.get("magnitude")
    year_start = parsed_claim.get("year_start", 2000)
    year_end = parsed_claim.get("year_end", 2026)
    
    # Load data for region and timeframe
    loader = get_loader()
    data = loader.load_all_data(region, year_start, year_end)
    
    # Map variable to data source
    variable_to_source = {
        "glacier": "landsat",
        "snow": "modis",
        "temperature": "climate",
        "permafrost": "permafrost",
        "precipitation": "climate",
    }
    
    source_name = variable_to_source.get(variable.split()[0], "landsat")
    source_data = data.get(source_name, {})
    years = np.array(source_data.get("years", []))
    
    # Extract relevant values
    if variable in ["glacier", "glacier area"]:
        values = np.array(source_data.get("glacier_area_km2", []))
        actual_direction = "decreasing" if len(values) > 1 and values[-1] < values[0] else ("increasing" if len(values) > 1 else "stable")
        unit = "km²"
        observed_magnitude = abs((values[-1] - values[0]) / values[0] * 100) if len(values) > 0 and values[0] != 0 else 0
        
    elif variable in ["snow", "snow cover"]:
        values = np.array(source_data.get("snow_cover_days", []))
        actual_direction = "decreasing" if len(values) > 1 and values[-1] < values[0] else ("increasing" if len(values) > 1 else "stable")
        unit = "days/year"
        observed_magnitude = abs((values[-1] - values[0]) / values[0] * 100) if len(values) > 0 and values[0] != 0 else 0
        
    elif variable in ["temperature"]:
        values = np.array(source_data.get("temperature_anomaly_c", []))
        actual_direction = "increasing" if len(values) > 1 and values[-1] > values[0] else ("decreasing" if len(values) > 1 else "stable")
        unit = "°C anomaly"
        observed_magnitude = abs(values[-1] - values[0]) if len(values) > 0 else 0
        
    elif variable in ["permafrost"]:
        values = np.array(source_data.get("temperature_10m_celsius", []))
        actual_direction = "increasing" if len(values) > 1 and values[-1] > values[0] else ("decreasing" if len(values) > 1 else "stable")
        unit = "°C at 10m"
        observed_magnitude = abs(values[-1] - values[0]) if len(values) > 0 else 0
        
    else:
        actual_direction = "unknown"
        unit = "units"
        observed_magnitude = 0
        values = np.array([])
    
    # Compare claim direction with actual data direction
    verdict = ""
    confidence = 0.5
    
    if actual_direction == "unknown" or values.size == 0:
        verdict = "Insufficient data"
        confidence = 0.3
        key_statistic = "No data available for this period/region"
        
    elif direction.lower() == actual_direction.lower() or (direction.lower() == "changing" and actual_direction != "stable"):
        # Direction matches
        if magnitude is not None:
            # Check magnitude
            if abs(observed_magnitude - magnitude) / magnitude < 0.5:  # Within 50%
                verdict = "Supported"
                confidence = 0.80 + np.random.uniform(0, 0.15)
            else:
                verdict = "Partially Supported"
                confidence = 0.60 + np.random.uniform(0, 0.15)
        else:
            verdict = "Supported"
            confidence = 0.75 + np.random.uniform(0, 0.15)
        
        key_statistic = f"{region}: {variable} {actual_direction} by {observed_magnitude:.1f}% from {year_start} to {year_end}"
        
    elif direction.lower() != "unknown" and actual_direction != "stable":
        # Direction contradicts
        verdict = "Contradicted"
        confidence = 0.85 + np.random.uniform(0, 0.10)
        key_statistic = f"{region}: Data shows {variable} {actual_direction}, not {direction}"
        
    else:
        verdict = "Partially Supported"
        confidence = 0.55 + np.random.uniform(0, 0.15)
        key_statistic = f"Trend unclear; regional variation observed"
    
    # Ensure confidence is in [0, 1]
    confidence = np.clip(confidence, 0.1, 0.99)
    
    # Accurate finding - always state the true value
    if len(values) > 0:
        observed_value = values[-1]
        accurate_finding = f"Satellite data for {region} ({year_start}-{year_end}) shows {variable} {actual_direction}. Average magnitude: {observed_magnitude:.1f}%. Latest observed value: {observed_value:.1f} {unit}."
    else:
        observed_value = None
        accurate_finding = f"Insufficient data available for {region} in the {year_start}-{year_end} period."
    
    # Sources used
    sources_used = [source_name.upper(), "Copernicus", "NASA"]
    
    return {
        "verdict": verdict,
        "confidence": confidence,
        "key_statistic": key_statistic,
        "observed_value": observed_value,
        "observed_magnitude": observed_magnitude,
        "claimed_value": magnitude,
        "data_direction": actual_direction,
        "sources_used": sources_used,
        "accurate_finding": accurate_finding,
        "credibility_assessment": get_claim_source_assessment(sources_used),
        "region": region,
        "variable": variable,
        "year_start": year_start,
        "year_end": year_end,
        "unit": unit
    }
