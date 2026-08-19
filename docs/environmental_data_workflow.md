# Environmental Data & Machine Learning Workflow Design Specification
**Project**: AI-Powered Solar & Wind Deployment Intelligence Platform  
**Phase**: Milestone 2 (Environmental Intelligence & Resource Prediction)  

---

> [!NOTE]
> **Design Specification Disclaimer**  
> The environmental workflow described in this document is a **design specification** at this milestone. Actual API data ingestion, data cleaning scripts, model training, and large-scale parallel processing pipelines will be implemented in subsequent development stages after the uploaded Kaggle and API datasets are fully validated.

---

## 1. Objectives & Scope
The goal of the Environmental Intelligence module is to automate the collection, cleaning, harmonization, and modeling of diverse environmental parameters to evaluate site suitability for solar and wind power plants. 

The pipeline takes a candidate coordinate pair (Latitude and Longitude) and outputs:
1. Expected Solar & Wind energy generation yields (using Machine Learning models).
2. A multi-factor Site Suitability Score based on environmental, geographic, infrastructure, and economic constraints.

---

## 2. Environmental Variables: Direct vs. Derived

In order to establish a rigorous data model, we distinguish between variables directly retrieved from external APIs/datasets and variables mathematically derived by the platform:

```
                      CANDIDATE COORDINATE
                     (Latitude / Longitude)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     [ DIRECT DATA ]                      [ DERIVED DATA ]
  - GHI, DNI, Diffuse (NASA)           - Land Slope (from DEM)
  - Wind Speed/Dir (Wind Atlas)        - Peak Sun Hours (from GHI profile)
  - Elevation (NASA SRTM)              - Wind Power Density (from Speed/Temp)
  - Land Cover (Sentinel)              - Grid Distances (from OSM geometry)
  - Road/Substation Geometries (OSM)
```

### Variable Reference Table

| Category | Variable | Nature | Units | Purpose / Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Solar** | Global Horizontal Irradiance (GHI) | Direct | $kWh/m^2/day$ | Primary input for solar output prediction. |
| **Solar** | Direct Normal Irradiance (DNI) | Direct | $kWh/m^2/day$ | Track direct sun rays for concentrated solar cells. |
| **Solar** | Diffuse Horizontal Irradiance | Direct | $kWh/m^2/day$ | Track scattered sun rays in cloudy climates. |
| **Solar** | Peak Sun Hours | **Derived** | Hours/day | Computed from daily solar irradiance profile thresholds. |
| **Wind** | Wind Speed (at 10m, 50m, 100m) | Direct | $m/s$ | Wind velocity at standard turbine hub heights. |
| **Wind** | Wind Direction | Direct | Degrees | Used to calculate optimal orientation for wind arrays. |
| **Wind** | Wind Power Density (WPD) | **Derived** | $W/m^2$ | Computed mathematically using Wind Speed & Air Density. |
| **Wind** | Turbulence Intensity | **Derived** | % | Derived standard deviation of wind speed variations. |
| **Climate** | Temperature | Direct | °C | Modulates solar cell efficiency (high heat reduces output). |
| **Climate** | Humidity & Rainfall | Direct | % / mm | Assess weathering, potential rust, and cloud patterns. |
| **Terrain** | Elevation | Direct | Meters | Sourced from Digital Elevation Model (DEM) data. |
| **Terrain** | Land Slope | **Derived** | Degrees | Slope computed from surrounding elevation grid gradients. |
| **Land Cover**| Land Classification (LULC) | Direct | Class ID | Identify if candidate site falls in urban or water zones. |
| **Land Cover**| Vegetation Index (NDVI) | Direct | Index (-1 to 1)| Measure vegetation density to prevent deforestation. |
| **Infra** | Road Distance | **Derived** | Meters | Proximity derived from nearest OpenStreetMap road lines. |
| **Infra** | Substation / Grid Distance | **Derived** | Meters | Proximity derived from nearest OSM power substation nodes. |

---

## 3. Recommended API Data Sources

| Requirement | Source specified in Milestone | Reason / Justification | Data Usage |
| :--- | :--- | :--- | :--- |
| **Solar & Weather** | **NASA POWER API** | Globally coverage, standard meteorological reference dataset. | Retrieves solar irradiance, surface temperature, humidity, and cloud coverage. |
| **Wind Potential** | **Global Wind Atlas** | Provides pre-modeled wind statistics at multiple heights. | Retrieves average wind speeds, direction, and turbulence parameters. |
| **Terrain Elevation** | **NASA SRTM** | Worldwide 30-meter resolution Digital Elevation Model (DEM). | Retrieves raw elevation profiles used to calculate slope gradients. |
| **Land Cover** | **Copernicus Sentinel Hub** | High-resolution Sentinel-2 multispectral imagery. | Analyzes land classification, water bodies, and vegetation health indexes (NDVI). |
| **Infrastructure** | **OpenStreetMap (OSM)** | Up-to-date crowdsourced GIS geometry mappings. | Extracts road and electrical grid infrastructure networks to calculate distances. |

---

## 4. Preliminary Kaggle Dataset Assessment
*Note: This is a preliminary assessment of external Kaggle datasets to serve as training baselines or supplementary validation data. Final verdicts are subject to verifying actual column configurations, row counts, missing values, duplicates, geographical/temporal coverages, target variables, and unit compatibility.*

### 1. Solar Power Generation Data ([anikannal/solar-power-generation-data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data))
* **Columns**: `yield`, `module_temperature`, `ambient_temperature`, `irradiation`.
* **Provisional Verdict**: **Supplement / Baseline Only**. Helpful to validate inverter conversion performance, but lacks geographical metadata.

### 2. Sentinel Land Use Land Cover ([vinitdesai564/sen-lulc](https://www.kaggle.com/datasets/vinitdesai564/sen-lulc))
* **Columns**: Multispectral Sentinel images with corresponding land use classes (forest, agriculture, water, urban, etc.).
* **Provisional Verdict**: **Use**. Excellent dataset for training land classification networks to enforce geographic exclusion boundaries.

### 3. Time Series Forecasting of Solar Energy ([chaitanyakumar12/time-series-forecasting-of-solar-energy](https://www.kaggle.com/datasets/chaitanyakumar12/time-series-forecasting-of-solar-energy))
* **Columns**: Hourly values of `GHI`, `DNI`, `Wind Speed`, `Temperature` spanning several years.
* **Provisional Verdict**: **Use**. Directly usable as historical training sets for seasonal solar forecasting models.

### 4. Wind Power Generation Data Forecasting ([mubashirrahim/wind-power-generation-data-forecasting](https://www.kaggle.com/datasets/mubashirrahim/wind-power-generation-data-forecasting))
* **Columns**: `wind_speed`, `wind_direction`, `active_power`, `theoretical_power_curve`.
* **Provisional Verdict**: **Use**. Essential to model turbine power curves and predict wind farm energy generation capacity.

---

## 5. Ingestion, storage, & Data Harmonization

Because environmental data originates from multiple external APIs and file formats (JSON, GeoTIFF, CSV), the data pipeline must ingest, clean, and harmonize this data before sending it to the ML models.

### The Ingestion Pipeline

```text
NASA POWER ───────┐
Global Wind Atlas ┤
NASA SRTM ────────┤
Sentinel ─────────┤
OpenStreetMap ────┤
Kaggle ───────────┘
        │
        ▼
   DATA INGESTION
        │
        ▼
   RAW STORAGE
        │
        ▼
 VALIDATION/CLEANING
        │
        ▼
 DATA HARMONIZATION
        │
        ▼
 FEATURE ENGINEERING
        │
 ┌───────────────┐
 │ Unified Dataset│
 └───────┬───────┘
         │
 ┌───────┴────────┐
 │                │
 ▼                ▼
SOLAR MODEL    WIND MODEL
 │                │
 ▼                ▼
Solar output    Wind output
 └───────┬────────┘
         │
         ▼
 RESOURCE ASSESSMENT
         │
         ▼
 SITE SUITABILITY
         │
         ▼
 DEPLOYMENT OPTIMIZATION
```

### The Data Harmonization Problem & Solutions
Environmental and geographic datasets never match out of the box. The pipeline resolves these differences through a series of standardization steps:

1. **Coordinate Standardization**: Reprojects different GIS spatial projections (e.g., UTM, state-plane) to a unified coordinate system, such as the standard **WGS84** (Latitude/Longitude).
2. **Unit Standardization**: Converts disparate units (e.g., wind speed in knots or miles per hour to standard metric meters per second ($m/s$), and temperatures to Celsius).
3. **Timestamp Standardization**: Converts UTC offsets, regional solar times, and varying date formats to unified ISO 8601 UTC timestamps.
4. **Spatial Alignment**: Resamples satellite rasters (like Sentinel bands) and terrain grids (SRTM) to match identical grid boundaries.
5. **Temporal Alignment**: Resamples or interpolates hourly wind observations and daily weather summaries to a unified, standard time interval (e.g., hourly averages).
6. **Missing Data Handling**: Filters out corrupted values and uses forward-filling or interpolation for short gaps, or rejects rows with extensive missing records.

### Unified Environmental Dataset Schema
The output of the harmonization step is a unified dataset matching the following schema:

```sql
CREATE TABLE unified_environmental_features (
    site_id UUID,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- Solar & Climate
    ghi DOUBLE PRECISION,
    dni DOUBLE PRECISION,
    diffuse_irradiance DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    cloud_cover DOUBLE PRECISION,
    
    -- Wind
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    wind_power_density DOUBLE PRECISION,
    turbulence_intensity DOUBLE PRECISION,
    
    -- Terrain
    elevation DOUBLE PRECISION,
    slope DOUBLE PRECISION,
    
    -- Land cover
    land_cover_class INT,
    ndvi DOUBLE PRECISION,
    
    -- Infrastructure Proximities
    road_distance DOUBLE PRECISION,
    substation_distance DOUBLE PRECISION,
    transmission_line_distance DOUBLE PRECISION,
    urban_distance DOUBLE PRECISION,
    
    -- Environmental Constraints
    protected_area BOOLEAN,
    water_body BOOLEAN,
    agricultural_land BOOLEAN,
    
    timestamp TIMESTAMP,
    data_source VARCHAR(100)
);
```

### Database Storage Architecture
* **Primary Database**: **PostgreSQL + PostGIS**. Geographic coordinates (`geography` points) and grid shapes are stored in PostGIS. We utilize **GIST Spatial Indexing** to perform rapid spatial proximity checks.
* **Storage Optimization**: For large-scale historical time-series analytics, we propose saving historical records in **Apache Parquet format** with gzip compression. This reduces file storage footprint and speeds up analytics without bloating the primary relational database.

---

## 6. Machine Learning Strategy

We will utilize a defensive machine learning selection strategy to ensure robust predictions. Rather than immediately deploying complex neural networks, we will establish baseline models first and choose the simplest model that meets the required accuracy.

### Model Evaluation Flow
```text
Environmental data
        ↓
Define prediction target
        ↓
Create train/validation/test split
        ↓
Baseline model (e.g., Linear Regression / Random Forest)
        ↓
XGBoost / LightGBM comparison
        ↓
Evaluate performance (using MAE / RMSE / $R^2$)
        ↓
Select model
        ↓
Resource prediction (Solar / Wind yields)
```

### Target Prediction Tasks

1. **Solar Potential Prediction**:
   - *Inputs*: GHI, DNI, temperature, cloud cover, slope, latitude, longitude.
   - *Model Selection*: Compare **XGBoost** and **LightGBM** against a **Random Forest** baseline to predict annual expected energy yields ($kWh/m^2/year$).
2. **Wind Potential Prediction**:
   - *Inputs*: Wind speed (at 10m, 50m, 100m), wind direction, turbulence index, elevation, slope.
   - *Model Selection*: Use **XGBoost/LightGBM** to map wind measurements against non-linear turbine power curves to estimate active generator output ($MWh/year$).
3. **Forecasting**:
   - Evaluate deep learning frameworks (**TensorFlow/PyTorch** LSTMs or GRUs) for seasonal/temporal energy yield forecasting *only if* the baseline statistical models prove insufficient for capture.

---

## 7. Site Suitability Scoring Matrix
Once ML models predict the solar and wind resource potential, the **Decision-Making Suitability Engine** combines these predictions with geographical and environmental constraints. 

We separate prediction from decision scoring. The engine ranks candidate locations using the project-defined weighted scoring formula:

$$\text{Suitability Score} = \text{Resource Availability } (35\%) + \text{Geographic Suitability } (25\%) + \text{Infrastructure Access } (15\%) + \text{Environmental Impact } (15\%) + \text{Economic Feasibility } (10\%)$$

* **Resource Availability (35%)**: Evaluates GHI/DNI and Wind Power Density outputs.
* **Geographic Suitability (25%)**: Elevational thresholds and land slope (steeper slopes reduce suitability due to high construction costs).
* **Infrastructure Access (15%)**: Proximity to roads and high-voltage transmission lines (reduces connection construction costs).
* **Environmental Impact (15%)**: Evaluates NDVI levels and land classification (completely excludes protected reserves, dense forests, and water bodies).
* **Economic Feasibility (10%)**: Estimations based on land ownership, proximity to urban consumption centers, and local grid connection costs.
