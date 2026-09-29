# GIS & Geospatial Processing Architecture

The GIS subsystem manages vector layers, terrain analysis, and spatial constraints for candidate sites.

---

## 1. Multi-Factor Site Suitability Model

The platform uses a standardized, weighted scoring model:

| Dimension | Weight | Primary Factors Evaluated |
| :--- | :--- | :--- |
| **Renewable Resource Availability** | **35%** | Solar GHI ($\ge 5.5 \text{ kWh/m}^2/\text{day}$) and Wind Speed ($\ge 7.5 \text{ m/s}$) |
| **Geographic Suitability** | **25%** | Terrain slope ($< 2.5^\circ$ optimal, $> 15^\circ$ penalized) & elevation |
| **Infrastructure Accessibility** | **15%** | Distance to transmission grid, substations, and paved heavy-haul access roads |
| **Environmental Impact** | **15%** | Buffer distance from protected reserves, wildlife corridors, and water bodies |
| **Economic Feasibility** | **10%** | Land tenure (Public/Leased vs Restricted) and terrain civil grading expenditure |

### Category Thresholds
- **90 – 100**: Excellent
- **75 – 89**: Highly Suitable
- **60 – 74**: Moderately Suitable
- **40 – 59**: Low Suitability
- **0 – 39**: Unsuitable

---

## 2. Spatial Calculations & Geometry

- **Haversine Geodesic Distance**: Computes great-circle distance between coordinates and infrastructure hubs.
- **Site Boundary Polygon Generator**: Generates closed polygon footprints based on acreage and center coordinates.
- **Topographic Terrain Profiler**: Calculates slope incline, azimuth aspect orientation, and solar orientation factor.

---

## 3. Vector Layers Supported

- **Substations**: Points with operational voltage ratings (230kV, 345kV, 500kV).
- **Transmission Corridors**: LineStrings representing regional grid interties.
- **Heavy Haul Transport Roads**: Trunk and Interstate access routes for turbine/PV equipment.
- **Environmental Exclusion Buffers**: Strict Nature Reserves, National Parks, and Avian Sanctuaries.
- **Hydrological Features**: Lakes, reservoirs, and wetland floodplains.
- **Agricultural Land Cover**: Non-prime grazing vs agricultural classifications.
