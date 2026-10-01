from pathlib import Path
import geopandas as gpd
import sys


def main():
    if len(sys.argv) < 2:
        raise ValueError("Usage: python convert_stations_to_geojson.py <basin_id>")

    basin_id = sys.argv[1]

    root = Path(__file__).resolve().parents[2]
    spatial_dir = root / "resources" / "txpwc" / "basins" / basin_id / "spatial"

    shp_path = spatial_dir / "stations.shp"
    geojson_path = spatial_dir / "stations.geojson"

    print(f"Converting stations for basin: {basin_id}")
    print(f"Looking for: {shp_path}")

    if not shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shp_path}")

    gdf = gpd.read_file(shp_path)

    # Ensure WGS84 (required for web maps)
    if gdf.crs is not None:
        gdf = gdf.to_crs(epsg=4326)

    gdf.to_file(geojson_path, driver="GeoJSON")

    print(f"Saved GeoJSON to: {geojson_path}")
    print("Columns:", list(gdf.columns))


if __name__ == "__main__":
    main()