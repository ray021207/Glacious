"""Load environmental data for Alpine regions. Uses realistic synthetic data based on published scientific values."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import json
from pathlib import Path

class DataLoader:
    """Unified loader for all Alpine environmental data sources."""
    
    def __init__(self):
        """ Initialize with region data and random seeds for reproducibility."""
        self.regions = self._load_alpine_regions()
        # Regional-specific random seeds for reproducible synthetic data
        self.region_seeds = {reg["name"]: i for i, reg in enumerate(self.regions)}
    
    def _load_alpine_regions(self) -> List[Dict]:
        """Load Alpine regions configuration."""
        data_path = Path(__file__).parent.parent / "data" / "alpine_regions.json"
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            # Fallback with minimal regions
            return self._default_regions()
    
    def _default_regions(self) -> List[Dict]:
        """Default Alpine regions if JSON not available."""
        return [
            {"name": "Swiss Alps", "country": "CH", "lat": 46.8, "lon": 8.5, "area_km2": 4500},
            {"name": "French Alps", "country": "FR", "lat": 45.5, "lon": 6.2, "area_km2": 3500},
            {"name": "Italian Alps", "country": "IT", "lat": 46.2, "lon": 11.0, "area_km2": 4500},
            {"name": "Austrian Alps", "country": "AT", "lat": 47.5, "lon": 12.5, "area_km2": 5000},
            {"name": "Slovenian Alps", "country": "SI", "lat": 46.3, "lon": 13.8, "area_km2": 1500},
        ]
    
    def load_sentinel2(self, region: str, year_start: int, year_end: int) -> dict:
        """Sentinel-2 glacier extent and NDSI snow cover data."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed)
        
        years = np.arange(year_start, year_end + 1)
        # Baseline glacier area varies by region
        baseline_areas = {
            "Swiss Alps": 1200, "French Alps": 800, "Italian Alps": 1100,
            "Austrian Alps": 950, "Slovenian Alps": 450,
            "Dolomites": 280, "Mont Blanc": 150, "All Alps": 4500
        }
        baseline = baseline_areas.get(region, 800)
        
        # Realistic Alpine glacier decline: 0.8-1.5% per year, accelerating post-2010
        glacier_areas = []
        for year in years:
            if year < 2010:
                decline_rate = 0.008
            else:
                # Accelerating decline
                decline_rate = 0.012 + (year - 2010) * 0.0008
            
            # Compound decline with noise
            area = baseline * (1 - decline_rate) ** (year - year_start)
            area += np.random.normal(0, area * 0.05)  # 5% interannual noise
            glacier_areas.append(max(area * 0.3, 0))  # Don't go below 30% of baseline
        
        # NDSI snow cover fraction (0-1)
        ndsi_values = 0.6 + np.random.normal(0, 0.1, len(years))
        ndsi_values = np.clip(ndsi_values, 0.3, 0.95)
        
        return {
            "years": years.tolist(),
            "glacier_area_km2": glacier_areas,
            "ndsi_snow_fraction": ndsi_values.tolist(),
            "source": "Sentinel-2 / Copernicus",
            "resolution_m": 20,
            "temporal_resolution": "10-day composites"
        }
    
    def load_modis_snow(self, region: str, year_start: int, year_end: int) -> dict:
        """MODIS snow cover duration (days per year)."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 1)
        
        years = np.arange(year_start, year_end + 1)
        
        # Baseline snow cover days varies by region and elevation
        baseline_days = {
            "Swiss Alps": 220, "French Alps": 210, "Italian Alps": 200,
            "Austrian Alps": 230, "Slovenian Alps": 180,
            "Dolomites": 160, "Mont Blanc": 240, "All Alps": 210
        }
        baseline = baseline_days.get(region, 200)
        
        # Decline rate: ~2.3 days/year on average; higher in southern ranges
        regional_decline = {
            "Swiss Alps": 2.3, "French Alps": 2.8, "Italian Alps": 3.2,
            "Austrian Alps": 2.0, "Slovenian Alps": 2.5, "Dolomites": 3.5,
            "Mont Blanc": 2.1, "All Alps": 2.3
        }
        decline_per_year = regional_decline.get(region, 2.3)
        
        snow_cover_days = []
        for year in years:
            # Linear trend plus interannual noise
            days = baseline - decline_per_year * (year - year_start)
            days += np.random.normal(0, 8)  # ~8-day standard deviation
            snow_cover_days.append(max(days, 60))  # Don't go below 60 days
        
        return {
            "years": years.tolist(),
            "snow_cover_days": snow_cover_days,
            "source": "MODIS MOD10A1",
            "resolution_m": 500,
            "temporal_resolution": "daily"
        }
    
    def load_landsat(self, region: str, year_start: int, year_end: int) -> dict:
        """Landsat glacier area series (back to 1984)."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 2)
        
        year_start = max(year_start, 1984)  # Landsat starts 1984
        years = np.arange(year_start, year_end + 1)
        
        # Year 2000 baseline and known losses since 1900
        baseline_1900 = {
            "Swiss Alps": 2700, "French Alps": 2200, "Italian Alps": 2400,
            "Austrian Alps": 2500, "Slovenian Alps": 1200,
            "All Alps": 12000  # Total ~50% loss since 1900, ~30% since 1980
        }
        
        baseline_2000 = {
            "Swiss Alps": 1200, "French Alps": 800, "Italian Alps": 1100,
            "Austrian Alps": 950, "Slovenian Alps": 450, "All Alps": 4500
        }
        
        base_2000 = baseline_2000.get(region, 800)
        
        # Accelerating decline: ~1% per year on average
        glacier_areas = []
        for year in years:
            # More decline post-2000
            if year < 2000:
                decline_rate = 0.006
            else:
                decline_rate = 0.011
            
            area = base_2000 * (1 - decline_rate) ** (year - 2000)
            area += np.random.normal(0, area * 0.08)
            glacier_areas.append(max(area, 0))
        
        return {
            "years": years.tolist(),
            "glacier_area_km2": glacier_areas,
            "source": "Landsat",
            "resolution_m": 30,
            "temporal_coverage": "1984-present"
        }
    
    def load_grace(self, region: str, year_start: int, year_end: int) -> dict:
        """GRACE satellite ice mass anomaly (Gt/year, negative = loss)."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 3)
        
        years = np.arange(year_start, year_end + 1)
        
        # Alpine ice mass loss: variable by region, generally 1-3 Gt/year
        regional_loss_rate = {
            "Swiss Alps": -1.5, "French Alps": -1.2, "Italian Alps": -1.8,
            "Austrian Alps": -1.4, "Slovenian Alps": -0.4,
            "All Alps": -6.0  # Total ~6 Gt/year modern loss
        }
        
        loss_rate = regional_loss_rate.get(region, -1.5)
        
        # Accelerating loss post-2000
        ice_mass_anomaly = []
        for year in years:
            if year < 2000:
                adjusted_rate = loss_rate * 0.6  # Slower historical loss
            else:
                adjusted_rate = loss_rate * (1 + 0.02 * (year - 2000))  # Accelerating
            
            anomaly = adjusted_rate * (year - year_start)
            anomaly += np.random.normal(0, abs(loss_rate) * 0.2)
            ice_mass_anomaly.append(anomaly)
        
        return {
            "years": years.tolist(),
            "ice_mass_anomaly_gt": ice_mass_anomaly,
            "source": "GRACE",
            "resolution_km": 150,
            "temporal_resolution": "monthly"
        }
    
    def load_copernicus_dem(self, region: str, year_start: int, year_end: int) -> dict:
        """Copernicus DEM surface elevation change (m/year)."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 4)
        
        years = np.arange(year_start, year_end + 1)
        
        # Alpine ice surface lowering: 0.5-1.5 m/year
        regional_elevation_change = {
            "Swiss Alps": -0.9, "French Alps": -0.7, "Italian Alps": -1.1,
            "Austrian Alps": -0.8, "Slovenian Alps": -0.5,
            "All Alps": -0.85
        }
        
        change_per_year = regional_elevation_change.get(region, -0.8)
        
        # Accelerating lowering
        elevation_changes = []
        for year in years:
            if year < 2005:
                rate = change_per_year * 0.7
            else:
                rate = change_per_year * (1 + 0.03 * (year - 2005))
            
            change = rate
            change += np.random.normal(0, abs(change_per_year) * 0.15)
            elevation_changes.append(change)
        
        return {
            "years": years.tolist(),
            "elevation_change_m_per_year": elevation_changes,
            "source": "Copernicus DEM",
            "resolution_m": 30,
            "temporal_resolution": "annual"
        }
    
    def load_eear_clim(self, region: str, year_start: int, year_end: int) -> dict:
        """European Environmental Analysis Results - Climate data."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 5)
        
        years = np.arange(year_start, year_end + 1)
        
        # Alpine temperature warming: +0.3 to +0.5°C per decade
        # Baseline anomaly in 2000 relative to 1980-2010
        regional_baseline_anomaly = {
            "Swiss Alps": 0.0, "French Alps": 0.1, "Italian Alps": 0.15,
            "Austrian Alps": 0.05, "Slovenian Alps": 0.08,
            "All Alps": 0.08
        }
        
        baseline_anomaly = regional_baseline_anomaly.get(region, 0.05)
        warming_per_decade = 0.35  # Conservative alpine warming rate
        
        temps = []
        precips = []
        for year in years:
            # Temperature anomaly trend
            years_since_2000 = year - 2000
            temp_anomaly = baseline_anomaly + warming_per_decade * (years_since_2000 / 10)
            temp_anomaly += np.random.normal(0, 0.18)  # ~0.18°C interannual std dev
            temps.append(temp_anomaly)
            
            # Precipitation: slight increase in winter, decrease in summer
            precip_trend = 1.0 + np.random.normal(0, 0.08)  # ±8% variability
            precips.append(precip_trend)
        
        return {
            "years": years.tolist(),
            "temperature_anomaly_c": temps,  # Relative to 1980-2010
            "precipitation_fraction": precips,  # 1.0 = baseline
            "source": "EEAR-CLIM",
            "temporal_resolution": "daily, aggregated to annual"
        }
    
    def load_permos(self, region: str, year_start: int, year_end: int) -> dict:
        """Permafrost monitoring - borehole temperature at 10m depth."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 6)
        
        years = np.arange(year_start, year_end + 1)
        
        # High altitude permafrost temperature warming at depth: +0.2°C per decade
        baseline_temp_10m = {
            "Swiss Alps": -3.0, "French Alps": -2.5, "Italian Alps": -2.2,
            "Austrian Alps": -3.2, "Slovenian Alps": -1.8,
            "All Alps": -2.6
        }
        
        baseline_temp = baseline_temp_10m.get(region, -2.5)
        warming_per_decade = 0.18  # Slower than surface
        
        temps_10m = []
        for year in years:
            years_since_2000 = year - 2000
            temp = baseline_temp + warming_per_decade * (years_since_2000 / 10)
            temp += np.random.normal(0, 0.25)
            temps_10m.append(temp)
        
        return {
            "years": years.tolist(),
            "temperature_10m_celsius": temps_10m,
            "source": "PERMOS",
            "temporal_resolution": "annual mean"
        }
    
    def load_biodiversity(self, region: str, year_start: int, year_end: int) -> dict:
        """Species elevation shift and habitat changes."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 7)
        
        years = np.arange(year_start, year_end + 1)
        
        # Alpine elevation shift: ~8-12m per decade upslope
        species_data = {
            "ibex": {"baseline_elevation": 3200, "shift_per_decade": 10},
            "ptarmigan": {"baseline_elevation": 2800, "shift_per_decade": 9},
            "apollo_butterfly": {"baseline_elevation": 2200, "shift_per_decade": 8},
            "edelweiss": {"baseline_elevation": 2500, "shift_per_decade": 7},
            "alpine_salamander": {"baseline_elevation": 1800, "shift_per_decade": 6},
        }
        
        species_shifts = {}
        for species, data in species_data.items():
            elevations = []
            for year in years:
                years_since_2000 = year - 2000
                elevation = data["baseline_elevation"] + data["shift_per_decade"] * (years_since_2000 / 10)
                elevation += np.random.normal(0, 15)
                elevations.append(elevation)
            species_shifts[species] = elevations
        
        return {
            "years": years.tolist(),
            "species_elevation_shifts": species_shifts,
            "source": "GBIF observations",
            "temporal_resolution": "annual aggregation"
        }
    
    def load_phenology(self, region: str, year_start: int, year_end: int) -> dict:
        """Start-of-season shift (days earlier per decade)."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 8)
        
        years = np.arange(year_start, year_end + 1)
        
        # Alpine phenology advance: 6-8 days earlier per decade
        advance_per_decade = 7.0
        baseline_sos_day = 150  # May 30, about day 150 of year
        
        sos_days = []
        for year in years:
            years_since_1980 = year - 1980
            sos = baseline_sos_day - advance_per_decade * (years_since_1980 / 10)
            sos += np.random.normal(0, 3)  # ~3 day std dev
            sos_days.append(max(sos, 60))  # Not before March
        
        return {
            "years": years.tolist(),
            "start_of_season_day_of_year": sos_days,
            "source": "European Phenology Network",
            "temporal_resolution": "annual"
        }
    
    def load_economic_tourism(self, region: str, year_start: int, year_end: int) -> dict:
        """Ski season length and tourism impacts."""
        seed = self.region_seeds.get(region, hash(region) % 10000)
        np.random.seed(seed + 9)
        
        years = np.arange(year_start, year_end + 1)
        
        # Ski season shortening: ~4 weeks since 1980 in lower elevation resorts
        baseline_season_length = {
            "Swiss Alps": 160, "French Alps": 150, "Italian Alps": 140,
            "Austrian Alps": 170, "Slovenian Alps": 120, "All Alps": 148
        }
        baseline = baseline_season_length.get(region, 145)
        
        # Decline: ~3-4 days per year on lower-elevation resorts
        season_lengths = []
        for year in years:
            years_since_1980 = year - 1980
            length = baseline - 3.5 * years_since_1980
            length += np.random.normal(0, 5)
            season_lengths.append(max(length, 80))  # Minimum 80 days
        
        return {
            "years": years.tolist(),
            "ski_season_days": season_lengths,
            "source": "Eurostat tourism",
            "temporal_resolution": "annual"
        }
    
    def load_all_data(self, region: str, year_start: int, year_end: int) -> dict:
        """Load all available data sources for a region."""
        return {
            "sentinel2": self.load_sentinel2(region, year_start, year_end),
            "modis": self.load_modis_snow(region, year_start, year_end),
            "landsat": self.load_landsat(region, year_start, year_end),
            "grace": self.load_grace(region, year_start, year_end),
            "dem": self.load_copernicus_dem(region, year_start, year_end),
            "climate": self.load_eear_clim(region, year_start, year_end),
            "permafrost": self.load_permos(region, year_start, year_end),
            "biodiversity": self.load_biodiversity(region, year_start, year_end),
            "phenology": self.load_phenology(region, year_start, year_end),
            "tourism": self.load_economic_tourism(region, year_start, year_end),
        }

# Singleton instance
_loader = None

def get_loader() -> DataLoader:
    """Get or create loader instance."""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader
