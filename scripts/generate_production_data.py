"""
Generate production-ready sample datasets for Geospatial Measurement API.

Datasets created:
1. sample_data/production/drone_solar_farm_survey.kml
   - Heterogeneous KML containing Points (GCPs), LineStrings (flight paths, roads),
     and Polygons (solar array blocks, exclusion donut hole).
2. sample_data/production/infrastructure_transmission_lines_wgs84.zip
   - Homogeneous LineString Shapefile bundle (EPSG:4326 WGS84) with electric grid spans.
3. sample_data/production/cadastral_parcels_utm43n.zip
   - Homogeneous Polygon / MultiPolygon Shapefile bundle in metric UTM 43N (EPSG:32643).
4. sample_data/production/gas_pipeline_corridor_feet.zip
   - Homogeneous LineString Shapefile bundle in US survey feet (EPSG:2263 State Plane NY).
5. sample_data/production/ground_control_points_wgs84.zip
   - Homogeneous Point Shapefile bundle (EPSG:4326) with RTK surveying benchmarks.
"""

from pathlib import Path
import tempfile
import zipfile
import geopandas as gpd
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

OUTPUT_DIR = Path("sample_data/production")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_drone_solar_farm_kml(filepath: Path):
    """Create a realistic drone aerial survey KML file (heterogeneous geometries)."""
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Pavagada Solar Park Drone Aerial Inspection Survey</name>
    <description>Production aerial photogrammetry survey dataset collected via RTK-enabled UAV.</description>

    <!-- Ground Control Points (Points) -->
    <Placemark>
      <name>GCP-01-PRIMARY</name>
      <description>Survey-grade RTK base station receiver benchmark</description>
      <ExtendedData>
        <Data name="target_type"><value>Checkerboard Target</value></Data>
        <Data name="horizontal_accuracy_cm"><value>1.2</value></Data>
        <Data name="elevation_msl_m"><value>624.50</value></Data>
      </ExtendedData>
      <Point>
        <coordinates>77.275500,14.101200,624.5</coordinates>
      </Point>
    </Placemark>

    <Placemark>
      <name>GCP-02-PERIMETER</name>
      <description>Secondary perimeter verification target</description>
      <ExtendedData>
        <Data name="target_type"><value>Crosshair AeroPoint</value></Data>
        <Data name="horizontal_accuracy_cm"><value>1.5</value></Data>
        <Data name="elevation_msl_m"><value>626.10</value></Data>
      </ExtendedData>
      <Point>
        <coordinates>77.281000,14.106500,626.1</coordinates>
      </Point>
    </Placemark>

    <!-- Linear Features (LineStrings) -->
    <Placemark>
      <name>Heavy Haul Access Road</name>
      <description>Primary double-lane crushed gravel access corridor</description>
      <ExtendedData>
        <Data name="pavement_type"><value>Crushed Gravel</value></Data>
        <Data name="design_speed_kph"><value>30</value></Data>
      </ExtendedData>
      <LineString>
        <coordinates>
          77.275000,14.100000,623.0
          77.276200,14.102500,624.1
          77.278500,14.105200,625.4
          77.282000,14.107000,627.0
          77.285000,14.108500,628.2
        </coordinates>
      </LineString>
    </Placemark>

    <Placemark>
      <name>Drone Flight Mission - Strip 01</name>
      <description>Automated serpentine aerial photogrammetry corridor</description>
      <ExtendedData>
        <Data name="altitude_agl_m"><value>120.0</value></Data>
        <Data name="ground_sampling_dist_cm"><value>2.8</value></Data>
        <Data name="speed_m_s"><value>12.5</value></Data>
      </ExtendedData>
      <LineString>
        <coordinates>
          77.275200,14.101000,744.5
          77.275200,14.108000,744.5
          77.276500,14.108000,744.5
          77.276500,14.101000,744.5
          77.277800,14.101000,744.5
          77.277800,14.108000,744.5
          77.279100,14.108000,744.5
          77.279100,14.101000,744.5
        </coordinates>
      </LineString>
    </Placemark>

    <!-- Solar PV Array Block A (Standard Polygon) -->
    <Placemark>
      <name>Solar Array Block A - 50MW</name>
      <description>Main photovoltaic tracker array block</description>
      <ExtendedData>
        <Data name="capacity_mw"><value>50.0</value></Data>
        <Data name="module_count"><value>112000</value></Data>
        <Data name="tilt_system"><value>Single-Axis Tracker</value></Data>
      </ExtendedData>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.275500,14.101500,624.0
              77.282500,14.101500,625.5
              77.282500,14.107500,627.0
              77.275500,14.107500,625.0
              77.275500,14.101500,624.0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>

    <!-- Solar PV Array Block B with Substation Exclusion Donut Hole -->
    <Placemark>
      <name>Solar Array Block B with Substation Exclusion</name>
      <description>Array block containing an interior protected high-voltage step-up substation exclusion zone</description>
      <ExtendedData>
        <Data name="capacity_mw"><value>45.0</value></Data>
        <Data name="has_donut_exclusion"><value>true</value></Data>
      </ExtendedData>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.283500,14.101500,626.0
              77.290500,14.101500,628.0
              77.290500,14.107500,629.5
              77.283500,14.107500,627.5
              77.283500,14.101500,626.0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
        <innerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.286000,14.103500,627.0
              77.288000,14.103500,627.5
              77.288000,14.105500,628.0
              77.286000,14.105500,627.5
              77.286000,14.103500,627.0
            </coordinates>
          </LinearRing>
        </innerBoundaryIs>
      </Polygon>
    </Placemark>

  </Document>
</kml>
"""
    filepath.write_text(kml_content, encoding="utf-8")
    print(f"Created KML: {filepath}")


def create_transmission_lines_wgs84_shapefile(zip_filepath: Path):
    """
    Create a production LineString Shapefile archive for electrical transmission corridors.
    CRS: EPSG:4326 (WGS 84 geographic).
    """
    lines = [
        LineString([(77.5800, 13.0100), (77.5850, 13.0140), (77.5920, 13.0190), (77.5990, 13.0240)]),  # Main 400kV line
        LineString([(77.5850, 13.0140), (77.5870, 13.0210), (77.5910, 13.0250)]),                        # 220kV feeder
        LineString([(77.5790, 13.0090), (77.5840, 13.0130), (77.5980, 13.0230)]),                        # Maintenance road
        LineString([(77.5920, 13.0190), (77.5950, 13.0120), (77.5980, 13.0070)]),                        # Fiber optic tie
    ]
    data = {
        "LINE_ID": ["TL-400-01", "TL-220-04", "RD-MAINT-01", "FIBER-OP-02"],
        "VOLT_KV": [400, 220, 0, 0],
        "MATERIAL": ["ACSR Moose", "ACSR Zebra", "Gravel", "ADSS 48F"],
        "STATUS": ["ENERGIZED", "ENERGIZED", "OPERATIONAL", "ACTIVE"],
        "CIRCUITS": [2, 1, 0, 1],
    }
    gdf = gpd.GeoDataFrame(data, geometry=lines, crs="EPSG:4326")
    _bundle_shapefile_zip(gdf, zip_filepath, "transmission_lines")
    print(f"Created Shapefile ZIP (LineString EPSG:4326): {zip_filepath}")


def create_cadastral_parcels_utm43n_shapefile(zip_filepath: Path):
    """
    Create a production Polygon / MultiPolygon Shapefile archive for cadastral land parcels.
    CRS: EPSG:32643 (WGS 84 / UTM zone 43N - Metric).
    """
    x0, y0 = 780000.0, 1435000.0

    p1 = Polygon([(x0, y0), (x0 + 350, y0), (x0 + 350, y0 + 250), (x0, y0 + 250), (x0, y0)])
    p2 = Polygon([(x0 + 370, y0), (x0 + 750, y0), (x0 + 750, y0 + 250), (x0 + 370, y0 + 250), (x0 + 370, y0)])
    p3 = Polygon([(x0, y0 + 270), (x0 + 350, y0 + 270), (x0 + 350, y0 + 600), (x0, y0 + 600), (x0, y0 + 270)])

    # Disjoint sub-parcels represented as MultiPolygon
    sub1 = Polygon([(x0 + 370, y0 + 270), (x0 + 540, y0 + 270), (x0 + 540, y0 + 600), (x0 + 370, y0 + 600), (x0 + 370, y0 + 270)])
    sub2 = Polygon([(x0 + 560, y0 + 270), (x0 + 750, y0 + 270), (x0 + 750, y0 + 600), (x0 + 560, y0 + 600), (x0 + 560, y0 + 270)])
    mpoly = MultiPolygon([sub1, sub2])

    polys = [p1, p2, p3, mpoly]
    data = {
        "PARCEL_ID": ["PLOT-IND-101", "PLOT-IND-102", "PLOT-LOG-201", "ZONE-MFG-301"],
        "LAND_USE": ["Heavy Industry", "Warehouse", "Logistics Hub", "Special Mfg"],
        "MAX_FAR": [2.5, 1.8, 1.5, 3.0],
        "TENANT": ["Aerospace Corp", "Freight Hub", "Supply Logistics", "Precision Tech"],
        "ASSESSMENT": [14500000, 8900000, 7200000, 18500000],
    }
    gdf = gpd.GeoDataFrame(data, geometry=polys, crs="EPSG:32643")
    _bundle_shapefile_zip(gdf, zip_filepath, "cadastral_parcels")
    print(f"Created Shapefile ZIP (Polygon UTM 43N Metric): {zip_filepath}")


def create_pipeline_survey_us_feet_shapefile(zip_filepath: Path):
    """
    Create a production LineString Shapefile archive in US survey feet.
    CRS: EPSG:2263 (NAD83 / New York Long Island (ftUS)).
    Proves metric conversion on non-meter linear unit datasets.
    """
    x0, y0 = 985000.0, 195000.0

    # 1.0 US survey mile line = 5280 ftUS
    trunkline = LineString([(x0, y0), (x0 + 5280.0, y0), (x0 + 5280.0, y0 + 2640.0)])
    lateral1 = LineString([(x0 + 2640.0, y0), (x0 + 2640.0, y0 - 1500.0)])
    lateral2 = LineString([(x0 + 5280.0, y0 + 2640.0), (x0 + 7000.0, y0 + 2640.0)])

    lines = [trunkline, lateral1, lateral2]
    data = {
        "PIPE_ID": ["MAIN-12IN-X70", "LAT-04-6IN", "SPUR-02-8IN"],
        "MATERIAL": ["API-5L-X70", "CarbonSteel", "API-5L-X52"],
        "DIAM_IN": [12, 6, 8],
        "MAOP_PSI": [1200, 600, 800],
        "COATING": ["Fusion Bonded Epoxy", "FBE", "3-Layer Polyethylene"],
    }
    gdf = gpd.GeoDataFrame(data, geometry=lines, crs="EPSG:2263")
    _bundle_shapefile_zip(gdf, zip_filepath, "pipeline_corridors")
    print(f"Created Shapefile ZIP (LineString State Plane Feet EPSG:2263): {zip_filepath}")


def create_ground_control_points_wgs84_shapefile(zip_filepath: Path):
    """
    Create a production Point Shapefile archive for aerial surveying ground control points (GCPs).
    CRS: EPSG:4326 (WGS 84 geographic).
    """
    points = [
        Point(77.5800, 13.0100),
        Point(77.5850, 13.0140),
        Point(77.5920, 13.0190),
        Point(77.5990, 13.0240),
        Point(77.5870, 13.0210),
    ]
    data = {
        "POINT_ID": ["GCP-BASE-01", "GCP-CHK-02", "GCP-AERO-03", "GCP-AERO-04", "GCP-CHK-05"],
        "TYPE": ["Base Station", "Check Point", "Control Point", "Control Point", "Check Point"],
        "TARGET": ["Trimble R12", "Checkerboard", "AeroPoint V2", "AeroPoint V2", "X-Target"],
        "ELEV_M": [920.45, 918.30, 924.12, 927.80, 922.05],
        "HORIZ_PREC": [0.008, 0.015, 0.012, 0.012, 0.016],
    }
    gdf = gpd.GeoDataFrame(data, geometry=points, crs="EPSG:4326")
    _bundle_shapefile_zip(gdf, zip_filepath, "ground_control_points")
    print(f"Created Shapefile ZIP (Point WGS84 EPSG:4326): {zip_filepath}")


def _bundle_shapefile_zip(gdf: gpd.GeoDataFrame, zip_path: Path, base_name: str):
    """Write GeoDataFrame to shapefile and bundle into a clean zip archive."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        shp_file = tmp_path / f"{base_name}.shp"
        gdf.to_file(shp_file, driver="ESRI Shapefile")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                f = tmp_path / f"{base_name}{ext}"
                if f.exists():
                    zipf.write(f, arcname=f.name)


def main():
    print("=== Generating Production Geospatial Datasets ===")
    create_drone_solar_farm_kml(OUTPUT_DIR / "drone_solar_farm_survey.kml")
    create_transmission_lines_wgs84_shapefile(OUTPUT_DIR / "infrastructure_transmission_lines_wgs84.zip")
    create_cadastral_parcels_utm43n_shapefile(OUTPUT_DIR / "cadastral_parcels_utm43n.zip")
    create_pipeline_survey_us_feet_shapefile(OUTPUT_DIR / "gas_pipeline_corridor_feet.zip")
    create_ground_control_points_wgs84_shapefile(OUTPUT_DIR / "ground_control_points_wgs84.zip")
    print("=== All Production Datasets Generated Successfully ===")


if __name__ == "__main__":
    main()

