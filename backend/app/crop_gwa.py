import os
os.environ['GDAL_HTTP_UNSAFESSL'] = 'YES'
import rasterio
from rasterio.windows import from_bounds

def crop_gwa_rasters():
    """
    Opens the remote official GWA country-level GeoTIFFs (COGs) for India,
    crops them to the Rajasthan/Gujarat region bounds, and saves them locally.
    
    This preserves the original WGS84 Coordinate Reference System (CRS) 
    and Affine geotransform matrix.
    """
    # Target directory for local cropped rasters
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Gujarat/Rajasthan bounding box coordinates
    min_lon, min_lat, max_lon, max_lat = 68.0, 20.0, 78.0, 30.0

    # Remote GWA Cloud Optimized GeoTIFF (COG) URLs
    sources = {
        "wind_speed": "https://gwa.cdn.nazkamapps.com/country_tifs_v4/IND_wind-speed_100m.tif",
        "power_density": "https://gwa.cdn.nazkamapps.com/country_tifs_v4/IND_power-density_100m.tif"
    }

    # Local output filenames
    outputs = {
        "wind_speed": os.path.join(data_dir, "gujarat_rajasthan_wind_speed_100m.tif"),
        "power_density": os.path.join(data_dir, "gujarat_rajasthan_power_density_100m.tif")
    }

    for key, url in sources.items():
        out_path = outputs[key]
        print(f"==================================================")
        print(f"Opening remote GWA {key.upper()} dataset...")
        print(f"URL: {url}")
        
        try:
            # Query over HTTP. Rasterio handles Range Requests automatically via /vsicurl/
            with rasterio.open(url) as src:
                print(f"Original CRS: {src.crs}")
                print(f"Original Affine Transform:\n{src.transform}")
                print(f"Original Dimensions: {src.width} x {src.height} pixels")
                print(f"Original Bounding Box: {src.bounds}")
                
                # Map bounding coordinates to the raster window
                window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
                
                # Read band 1 (GWA values) for that window
                data = src.read(1, window=window)
                
                # Compute the geotransform affine matrix for the window crop
                win_transform = rasterio.windows.transform(window, src.transform)
                
                # Clone original metadata and update dimensions & transform bounds
                meta = src.meta.copy()
                meta.update({
                    "height": data.shape[0],
                    "width": data.shape[1],
                    "transform": win_transform
                })
                
                print(f"Writing cropped GWA {key.upper()} GeoTIFF locally...")
                print(f"Output: {out_path}")
                print(f"Cropped Dimensions: {data.shape[1]} x {data.shape[0]} pixels")
                print(f"Cropped Affine Transform:\n{win_transform}")
                
                with rasterio.open(out_path, "w", **meta) as dst:
                    dst.write(data, 1)
                    
            print(f"[OK] Successfully cropped and saved GWA {key}!")
        except Exception as e:
            print(f"[FAIL] Error querying or cropping {key}: {e}")
            raise e

if __name__ == "__main__":
    crop_gwa_rasters()
