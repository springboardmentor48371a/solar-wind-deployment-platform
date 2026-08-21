import urllib.parse
import urllib.request
import json
import math


# ============================================================
# GENERIC HTTP GET
# ============================================================

def http_get_json(url, timeout=30):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SolarWindDeploymentPlatform/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


# ============================================================
# 1. GLOBAL WIND ATLAS
# ============================================================

def get_global_wind_atlas(
    latitude: float,
    longitude: float,
    height: float = 100.0
):

    """
    Get Global Wind Atlas wind-climate information
    for a geographic point.

    GWA returns Weibull parameters for multiple:
        - roughness classes
        - heights
        - wind-direction sectors

    We use the 100 m layer for preliminary wind assessment.
    """

    url = (
        "https://api.globalwindatlas.info/"
        "gwa3/v1/get-libfile-point?"
        f"latitude={latitude}"
        f"&longitude={longitude}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "SolarWindDeploymentPlatform/1.0"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            text = response.read().decode(
                "utf-8"
            )

        lines = (
            text
            .strip()
            .splitlines()
        )

        if len(lines) < 5:

            raise Exception(
                "Invalid Global Wind Atlas response"
            )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        dimensions = list(
            map(
                int,
                lines[1].split()
            )
        )

        nrough = dimensions[0]
        nhgt = dimensions[1]
        nsec = dimensions[2]

        # ----------------------------------------------------
        # Roughness classes
        # ----------------------------------------------------

        roughnesses = list(
            map(
                float,
                lines[2].split()
            )
        )

        # ----------------------------------------------------
        # Heights
        # ----------------------------------------------------

        heights = list(
            map(
                float,
                lines[3].split()
            )
        )

        # ----------------------------------------------------
        # Data
        # ----------------------------------------------------

        raw_rows = []

        for line in lines[4:]:

            values = list(
                map(
                    float,
                    line.split()
                )
            )

            raw_rows.extend(values)

        expected_size = (
            nrough
            * (nhgt * 2 + 1)
            * nsec
        )

        if len(raw_rows) != expected_size:

            raise Exception(
                "Unexpected Global Wind Atlas data size"
            )

        # ----------------------------------------------------
        # Find nearest requested height
        # ----------------------------------------------------

        height_index = min(
            range(len(heights)),
            key=lambda i:
                abs(heights[i] - height)
        )

        selected_height = heights[
            height_index
        ]

        # ----------------------------------------------------
        # Convert flattened data into:
        #
        # roughness
        # height
        # direction
        # ----------------------------------------------------

        index = 0

        all_data = []

        for r in range(nrough):

            roughness_data = []

            for h in range(nhgt * 2 + 1):

                sector_data = []

                for s in range(nsec):

                    sector_data.append(
                        raw_rows[index]
                    )

                    index += 1

                roughness_data.append(
                    sector_data
                )

            all_data.append(
                roughness_data
            )

        # ----------------------------------------------------
        # Select a representative low/moderate roughness
        #
        # For an MVP we use the nearest roughness to 0.1 m.
        # ----------------------------------------------------

        roughness_index = min(
            range(len(roughnesses)),
            key=lambda i:
                abs(roughnesses[i] - 0.1)
        )

        selected_roughness = roughnesses[
            roughness_index
        ]

        # ----------------------------------------------------
        # Extract sector data
        #
        # Layout:
        #
        # column 0 = sector frequency
        # column 1 = Weibull A
        # column 2 = Weibull k
        # column 3 = Weibull A
        # column 4 = Weibull k
        #
        # etc.
        # ----------------------------------------------------

        row_data = all_data[
            roughness_index
        ]

        frequency_row = row_data[0]

        frequency_total = sum(
            frequency_row
        )

        if frequency_total <= 0:

            raise Exception(
                "Invalid wind frequency data"
            )

        frequencies = [

            value / frequency_total

            for value in frequency_row

        ]

        a_values = []

        k_values = []

        for sector in range(nsec):

            a_column = (
                1
                + height_index * 2
            )

            k_column = (
                2
                + height_index * 2
            )

            A = row_data[
                a_column
            ][sector]

            k = row_data[
                k_column
            ][sector]

            a_values.append(A)

            k_values.append(k)

        # ----------------------------------------------------
        # Calculate mean wind speed from Weibull distribution
        #
        # Mean wind speed:
        #
        # A * Gamma(1 + 1/k)
        # ----------------------------------------------------

        sector_mean_speeds = []

        for A, k in zip(
            a_values,
            k_values
        ):

            if A <= 0 or k <= 0:

                sector_mean_speeds.append(
                    0.0
                )

                continue

            mean_speed = (
                A
                * math.gamma(
                    1.0 + (1.0 / k)
                )
            )

            sector_mean_speeds.append(
                mean_speed
            )

        # ----------------------------------------------------
        # Weighted mean wind speed
        # ----------------------------------------------------

        mean_wind_speed = sum(

            frequency
            * speed

            for frequency, speed
            in zip(
                frequencies,
                sector_mean_speeds
            )

        )

        # ----------------------------------------------------
        # Estimate wind power density
        #
        # P = 0.5 * rho * V³
        #
        # Using standard air density 1.225 kg/m³
        # for an MVP estimate.
        # ----------------------------------------------------

        air_density = 1.225

        wind_power_density = (

            0.5
            * air_density
            * (mean_wind_speed ** 3)

        )

        return {

            "source":
                "Global Wind Atlas",

            "height_m":
                selected_height,

            "roughness_m":
                selected_roughness,

            "mean_wind_speed_mps":
                round(
                    mean_wind_speed,
                    3
                ),

            "wind_power_density_w_m2":
                round(
                    wind_power_density,
                    2
                ),

            "status":
                "success"

        }

    except Exception as e:

        print(
            "GLOBAL WIND ATLAS ERROR:",
            e
        )

        return {

            "source":
                "Global Wind Atlas",

            "height_m":
                height,

            "mean_wind_speed_mps":
                None,

            "wind_power_density_w_m2":
                None,

            "status":
                "failed",

            "error":
                str(e)

        }


# ============================================================
# 2. SRTM ELEVATION
# ============================================================

def get_srtm_elevation(
    latitude: float,
    longitude: float
):

    """
    Retrieve elevation from SRTM 90m data.
    """

    try:

        locations = (
            f"{latitude},{longitude}"
        )

        encoded_locations = (
            urllib.parse.quote(
                locations
            )
        )

        url = (
            "https://api.opentopodata.org/"
            "v1/srtm90m?"
            f"locations={encoded_locations}"
        )

        data = http_get_json(
            url,
            timeout=20
        )

        results = data.get(
            "results",
            []
        )

        if not results:

            raise Exception(
                "No SRTM elevation returned"
            )

        elevation = results[0].get(
            "elevation"
        )

        return {

            "source":
                "SRTM 90m",

            "elevation_m":
                elevation,

            "status":
                "success"

        }

    except Exception as e:

        print(
            "SRTM ERROR:",
            e
        )

        return {

            "source":
                "SRTM 90m",

            "elevation_m":
                None,

            "status":
                "failed",

            "error":
                str(e)

        }


# ============================================================
# 3. OPENSTREETMAP / OVERPASS
# ============================================================

def get_osm_infrastructure(
    latitude: float,
    longitude: float,
    radius_m: int = 10000
):

    """
    Search OpenStreetMap around the selected location.

    We retrieve:
        - roads
        - substations
        - power lines
        - buildings

    within the specified radius.
    """

    try:

        query = f"""
        [out:json][timeout:25];

        (
          way["highway"](around:{radius_m},{latitude},{longitude});

          node["power"="substation"]
              (around:{radius_m},{latitude},{longitude});

          way["power"="substation"]
              (around:{radius_m},{latitude},{longitude});

          way["power"="line"]
              (around:{radius_m},{latitude},{longitude});

          way["building"]
              (around:{radius_m},{latitude},{longitude});
        );

        out center;
        """

        encoded_query = urllib.parse.urlencode({

            "data": query

        })

        url = (
            "https://overpass-api.de/api/interpreter?"
            + encoded_query
        )

        data = http_get_json(
            url,
            timeout=60
        )

        elements = data.get(
            "elements",
            []
        )

        roads = 0

        substations = 0

        power_lines = 0

        buildings = 0

        # ----------------------------------------------------
        # Count infrastructure
        # ----------------------------------------------------

        for element in elements:

            tags = element.get(
                "tags",
                {}
            )

            if "highway" in tags:

                roads += 1

            if tags.get(
                "power"
            ) == "substation":

                substations += 1

            if tags.get(
                "power"
            ) == "line":

                power_lines += 1

            if "building" in tags:

                buildings += 1

        # ----------------------------------------------------
        # Accessibility score
        # ----------------------------------------------------

        infrastructure_score = 0

        if roads > 0:

            infrastructure_score += 40

        if roads >= 10:

            infrastructure_score += 15

        if substations > 0:

            infrastructure_score += 25

        if power_lines > 0:

            infrastructure_score += 20

        infrastructure_score = min(
            infrastructure_score,
            100
        )

        return {

            "source":
                "OpenStreetMap",

            "search_radius_km":
                radius_m / 1000,

            "roads":
                roads,

            "substations":
                substations,

            "power_lines":
                power_lines,

            "buildings":
                buildings,

            "infrastructure_score":
                infrastructure_score,

            "status":
                "success"

        }

    except Exception as e:

        print(
            "OSM ERROR:",
            e
        )

        return {

            "source":
                "OpenStreetMap",

            "search_radius_km":
                radius_m / 1000,

            "roads":
                None,

            "substations":
                None,

            "power_lines":
                None,

            "buildings":
                None,

            "infrastructure_score":
                None,

            "status":
                "failed",

            "error":
                str(e)

        }


# ============================================================
# 4. COLLECT ALL GEOGRAPHIC DATA
# ============================================================

def collect_geographic_data(
    latitude: float,
    longitude: float
):

    """
    Collect:

        Global Wind Atlas
        SRTM
        OpenStreetMap

    for the same site coordinates.
    """

    wind_data = get_global_wind_atlas(
        latitude,
        longitude
    )

    elevation_data = get_srtm_elevation(
        latitude,
        longitude
    )

    osm_data = get_osm_infrastructure(
        latitude,
        longitude
    )

    return {

        "global_wind_atlas":
            wind_data,

        "srtm":
            elevation_data,

        "openstreetmap":
            osm_data

    }