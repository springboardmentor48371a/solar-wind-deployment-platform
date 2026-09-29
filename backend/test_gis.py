import pytest
from app.gis.spatial_engine import spatial_engine, haversine_distance_km, generate_site_boundary_polygon
from app.gis.terrain import analyze_terrain
from app.gis.layers import get_gis_vector_layers, get_heatmap_grid


def test_haversine_distance():
    # Distance between ~35.0, -115.0 and 35.0, -114.0 (~91 km)
    d = haversine_distance_km(35.0, -115.0, 35.0, -114.0)
    assert 85.0 <= d <= 95.0


def test_spatial_distances():
    dist = spatial_engine.compute_distances(35.15, -115.50)
    assert "distance_to_substation_km" in dist
    assert "distance_to_grid_km" in dist
    assert "distance_to_road_km" in dist
    assert "protected_zone_distance_km" in dist
    assert dist["distance_to_grid_km"] > 0


def test_site_boundary_polygon():
    poly = generate_site_boundary_polygon(35.0, -115.0, area_sqkm=5.0)
    assert poly["type"] == "Polygon"
    assert len(poly["coordinates"][0]) == 5


def test_terrain_analysis():
    terrain = analyze_terrain(35.15, -115.50, base_elevation_m=650.0)
    assert "elevation_m" in terrain
    assert "slope_deg" in terrain
    assert "aspect_deg" in terrain
    assert "solar_orientation_factor" in terrain


def test_vector_layers():
    layers = get_gis_vector_layers()
    assert "substations" in layers
    assert "transmission_lines" in layers
    assert "roads" in layers
    assert "protected_zones" in layers
    assert "water_bodies" in layers
    assert "agricultural_land" in layers
