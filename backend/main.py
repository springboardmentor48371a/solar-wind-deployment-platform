from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from pwdlib import PasswordHash

from database import engine

import urllib.request
import urllib.parse
import json
import math
import os

from datetime import date, timedelta


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform",
    description=(
        "Renewable energy site analysis using "
        "NASA POWER, Global Wind Atlas, SRTM, "
        "OpenStreetMap and Copernicus Sentinel data"
    ),
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


# ============================================================
# REQUEST MODELS
# ============================================================


class UserCreate(BaseModel):

    name: str

    email: EmailStr

    password: str


class UserLogin(BaseModel):

    email: EmailStr

    password: str


class SiteAnalysisRequest(BaseModel):

    user_id: int = Field(
        ...,
        gt=0
    )

    location: str = Field(
        ...,
        min_length=2
    )

    land_area: float = Field(
        ...,
        gt=0
    )


class SolarAnalysisRequest(BaseModel):

    user_id: int = Field(
        ...,
        gt=0
    )

    location: str

    land_area: float = Field(
        ...,
        gt=0
    )

    # OPTIONAL
    #
    # User does NOT need to enter these.
    # Backend obtains them automatically.

    irradiance: float | None = None

    temperature: float | None = None

    cloud_cover: float | None = None


class WindAnalysisRequest(BaseModel):

    user_id: int = Field(
        ...,
        gt=0
    )

    location: str

    land_area: float = Field(
        ...,
        gt=0
    )

    # OPTIONAL
    #
    # Backend obtains wind speed automatically.

    wind_speed: float | None = None

    temperature: float | None = None

    air_density: float = Field(
        default=1.225,
        gt=0
    )


# ============================================================
# COMMON HTTP HELPERS
# ============================================================


def http_get_json(
    url: str,
    timeout: int = 30
):

    request = urllib.request.Request(

        url,

        headers={
            "User-Agent":
                "SolarWindDeploymentPlatform/2.0"
        }

    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


def http_post_json(
    url: str,
    payload,
    headers=None,
    timeout: int = 60
):

    request_headers = {

        "User-Agent":
            "SolarWindDeploymentPlatform/2.0",

        "Content-Type":
            "application/json"

    }

    if headers:

        request_headers.update(
            headers
        )

    body = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(

        url,

        data=body,

        headers=request_headers,

        method="POST"

    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        return response.read()


# ============================================================
# HOME
# ============================================================


@app.get("/")
def home():

    return {

        "message":
            "Solar & Wind Deployment Intelligence Platform API is running",

        "version":
            "2.0.0",

        "datasets": [

            "NASA POWER",

            "Global Wind Atlas",

            "SRTM",

            "OpenStreetMap",

            "Copernicus Sentinel-2"

        ]

    }


# ============================================================
# DATABASE TEST
# ============================================================


@app.get("/db-test")
def database_test():

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            result.fetchone()

        return {

            "message":
                "Database connection successful!"

        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Database connection failed: {str(e)}"

        )


# ============================================================
# REGISTER
# ============================================================


@app.post("/register")
def register(user: UserCreate):

    try:

        # ----------------------------------------------------
        # CHECK EXISTING USER
        # ----------------------------------------------------

        with engine.connect() as connection:

            existing_user = connection.execute(

                text("""
                    SELECT id
                    FROM users
                    WHERE email = :email
                """),

                {
                    "email":
                        user.email
                }

            ).fetchone()

        if existing_user:

            raise HTTPException(

                status_code=400,

                detail=
                    "Email already registered"

            )

        # ----------------------------------------------------
        # PASSWORD HASH
        # ----------------------------------------------------

        hashed_password = password_hash.hash(
            user.password
        )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        with engine.begin() as connection:

            result = connection.execute(

                text("""
                    INSERT INTO users
                    (
                        full_name,
                        email,
                        password_hash,
                        created_at
                    )
                    VALUES
                    (
                        :full_name,
                        :email,
                        :password_hash,
                        CURRENT_TIMESTAMP
                    )
                    RETURNING id
                """),

                {

                    "full_name":
                        user.name,

                    "email":
                        user.email,

                    "password_hash":
                        hashed_password

                }

            )

            user_id = result.fetchone()[0]

        return {

            "message":
                "User registered successfully",

            "id":
                user_id,

            "name":
                user.name,

            "email":
                user.email

        }

    except HTTPException:

        raise

    except IntegrityError:

        raise HTTPException(

            status_code=400,

            detail=
                "Email already registered"

        )

    except Exception as e:

        print(
            "REGISTER ERROR:",
            e
        )

        raise HTTPException(

            status_code=500,

            detail=
                "Registration failed"

        )


# ============================================================
# LOGIN
# ============================================================


@app.post("/login")
def login(user: UserLogin):

    try:

        with engine.connect() as connection:

            result = connection.execute(

                text("""
                    SELECT
                        id,
                        full_name,
                        email,
                        password_hash
                    FROM users
                    WHERE email = :email
                """),

                {
                    "email":
                        user.email
                }

            ).fetchone()

        if not result:

            raise HTTPException(

                status_code=401,

                detail=
                    "Invalid email or password"

            )

        valid_password = password_hash.verify(

            user.password,

            result.password_hash

        )

        if not valid_password:

            raise HTTPException(

                status_code=401,

                detail=
                    "Invalid email or password"

            )

        return {

            "message":
                "Login successful",

            "user": {

                "id":
                    result.id,

                "name":
                    result.full_name,

                "email":
                    result.email

            }

        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "LOGIN ERROR:",
            e
        )

        raise HTTPException(

            status_code=500,

            detail=
                "Login failed"

        )


# ============================================================
# GEOCODING
#
# LOCATION TEXT
#       ↓
# LATITUDE + LONGITUDE
#
# OpenStreetMap Nominatim
# ============================================================


def get_coordinates(
    location: str
):

    try:

        encoded_location = urllib.parse.quote(
            location
        )

        url = (

            "https://nominatim.openstreetmap.org/search?"

            f"q={encoded_location}"

            "&format=json"

            "&limit=1"

        )

        data = http_get_json(
            url,
            timeout=20
        )

        if not data:

            raise HTTPException(

                status_code=404,

                detail=
                    f"Location not found: {location}"

            )

        latitude = float(
            data[0]["lat"]
        )

        longitude = float(
            data[0]["lon"]
        )

        display_name = data[0].get(
            "display_name",
            location
        )

        return (

            latitude,

            longitude,

            display_name

        )

    except HTTPException:

        raise

    except Exception as e:

        print(
            "GEOCODING ERROR:",
            e
        )

        raise HTTPException(

            status_code=502,

            detail=
                "Unable to convert location to coordinates"

        )


# ============================================================
# NASA POWER
#
# DATA:
#
# ALLSKY_SFC_SW_DWN
#     Solar irradiance
#
# T2M
#     Temperature
#
# WS10M
#     Wind speed
# ============================================================


def get_nasa_power_data(

    latitude: float,

    longitude: float

):

    try:

        end_date = (
            date.today()
            - timedelta(days=2)
        )

        start_date = (
            end_date
            - timedelta(days=365)
        )

        start_string = (
            start_date.strftime("%Y%m%d")
        )

        end_string = (
            end_date.strftime("%Y%m%d")
        )

        parameters = (

            "ALLSKY_SFC_SW_DWN,"

            "T2M,"

            "WS10M"

        )

        query = urllib.parse.urlencode({

            "parameters":
                parameters,

            "community":
                "RE",

            "longitude":
                longitude,

            "latitude":
                latitude,

            "start":
                start_string,

            "end":
                end_string,

            "format":
                "JSON"

        })

        url = (

            "https://power.larc.nasa.gov/"

            "api/temporal/daily/point?"

            + query

        )

        data = http_get_json(

            url,

            timeout=40

        )

        parameter_data = (

            data["properties"]["parameter"]

        )

        solar_values = []

        temperature_values = []

        wind_values = []


        # ----------------------------------------------------
        # SOLAR
        # ----------------------------------------------------

        for value in parameter_data[
            "ALLSKY_SFC_SW_DWN"
        ].values():

            if (

                value is not None

                and value >= 0

            ):

                solar_values.append(
                    float(value)
                )


        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        for value in parameter_data[
            "T2M"
        ].values():

            if value is not None:

                temperature_values.append(
                    float(value)
                )


        # ----------------------------------------------------
        # WIND
        # ----------------------------------------------------

        for value in parameter_data[
            "WS10M"
        ].values():

            if (

                value is not None

                and value >= 0

            ):

                wind_values.append(
                    float(value)
                )


        if not solar_values:

            raise Exception(
                "NASA returned no solar data"
            )


        if not wind_values:

            raise Exception(
                "NASA returned no wind data"
            )


        average_solar = (

            sum(solar_values)

            /

            len(solar_values)

        )


        average_temperature = (

            sum(temperature_values)

            /

            len(temperature_values)

            if temperature_values

            else 25.0

        )


        average_wind = (

            sum(wind_values)

            /

            len(wind_values)

        )


        return {

            "source":
                "NASA POWER",

            "start_date":
                start_string,

            "end_date":
                end_string,

            "days":
                len(solar_values),

            "average_solar_irradiance":
                average_solar,

            "average_temperature":
                average_temperature,

            "average_wind_speed":
                average_wind

        }

    except Exception as e:

        print(
            "NASA POWER ERROR:",
            e
        )

        raise HTTPException(

            status_code=502,

            detail=
                "NASA POWER data could not be retrieved: "
                + str(e)

        )


# ============================================================
# GLOBAL WIND ATLAS
#
# REAL GWA POINT API
#
# Uses:
#     Weibull A
#     Weibull k
#     Sector frequency
#
# Height:
#     100 meters
# ============================================================


def get_global_wind_atlas(

    latitude: float,

    longitude: float,

    requested_height: float = 100.0

):

    try:

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
                    "SolarWindDeploymentPlatform/2.0"

            }

        )

        with urllib.request.urlopen(

            request,

            timeout=40

        ) as response:

            raw = (

                response
                .read()
                .decode("utf-8")
            )

        lines = (

            raw
            .strip()
            .splitlines()
        )


        if len(lines) < 5:

            raise Exception(
                "Invalid Global Wind Atlas response"
            )


        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        nrough, nhgt, nsec = map(

            int,

            lines[1].split()

        )


        roughnesses = list(

            map(

                float,

                lines[2].split()

            )

        )


        heights = list(

            map(

                float,

                lines[3].split()

            )

        )


        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        raw_rows = []

        for line in lines[4:]:

            raw_rows.append(

                list(

                    map(

                        float,

                        line.split()

                    )

                )

            )


        data = [

            raw_rows

        ]


        # Flatten
        flat = []

        for row in raw_rows:

            flat.extend(row)


        expected = (

            nrough

            *

            (nhgt * 2 + 1)

            *

            nsec

        )


        if len(flat) != expected:

            raise Exception(

                "Unexpected Global Wind Atlas response size"

            )


        # ----------------------------------------------------
        # RESHAPE
        #
        # [roughness]
        # [height data]
        # [sector]
        # ----------------------------------------------------

        index = 0

        structured = []

        for r in range(nrough):

            roughness_data = []

            for h in range(
                nhgt * 2 + 1
            ):

                sector_values = []

                for s in range(nsec):

                    sector_values.append(
                        flat[index]
                    )

                    index += 1

                roughness_data.append(
                    sector_values
                )

            structured.append(
                roughness_data
            )


        # ----------------------------------------------------
        # CHOOSE 0.1M ROUGHNESS
        # ----------------------------------------------------

        roughness_index = min(

            range(
                len(roughnesses)
            ),

            key=lambda i:
                abs(
                    roughnesses[i]
                    - 0.1
                )

        )


        selected_roughness = (

            roughnesses[
                roughness_index
            ]

        )


        # ----------------------------------------------------
        # CHOOSE REQUESTED HEIGHT
        # ----------------------------------------------------

        height_index = min(

            range(
                len(heights)
            ),

            key=lambda i:
                abs(
                    heights[i]
                    - requested_height
                )

        )


        selected_height = (

            heights[
                height_index
            ]

        )


        rows = structured[
            roughness_index
        ]


        # ----------------------------------------------------
        # SECTOR FREQUENCY
        # ----------------------------------------------------

        frequency = rows[0]

        frequency_total = sum(
            frequency
        )


        if frequency_total <= 0:

            raise Exception(
                "Invalid GWA sector frequency"
            )


        frequency = [

            x / frequency_total

            for x in frequency

        ]


        # ----------------------------------------------------
        # WEIBULL A AND K
        # ----------------------------------------------------

        a_row_index = (
            1
            + (height_index * 2)
        )

        k_row_index = (
            2
            + (height_index * 2)
        )


        a_values = rows[
            a_row_index
        ]

        k_values = rows[
            k_row_index
        ]


        # ----------------------------------------------------
        # MEAN SPEED
        #
        # Mean = A * Gamma(1 + 1/k)
        # ----------------------------------------------------

        sector_means = []

        for A, k in zip(
            a_values,
            k_values
        ):

            if A <= 0 or k <= 0:

                sector_means.append(
                    0
                )

            else:

                mean_speed = (

                    A

                    *

                    math.gamma(
                        1 + (1 / k)
                    )

                )

                sector_means.append(
                    mean_speed
                )


        mean_wind_speed = sum(

            f * s

            for f, s in zip(

                frequency,

                sector_means

            )

        )


        # ----------------------------------------------------
        # WIND POWER DENSITY
        #
        # P = 1/2 * rho * V^3
        # ----------------------------------------------------

        air_density = 1.225

        wind_power_density = (

            0.5

            *

            air_density

            *

            mean_wind_speed ** 3

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
                requested_height,

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
# SRTM ELEVATION
#
# SRTM 90m
#
# OpenTopoData public API
# ============================================================


def get_srtm_elevation(

    latitude: float,

    longitude: float

):

    try:

        locations = (

            f"{latitude},{longitude}"

        )

        encoded = urllib.parse.quote(
            locations
        )

        url = (

            "https://api.opentopodata.org/"

            "v1/srtm90m?"

            f"locations={encoded}"

        )


        data = http_get_json(

            url,

            timeout=30

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
# OPENSTREETMAP
#
# Overpass API
#
# Finds:
#
# Roads
# Substations
# Power lines
# Buildings
# ============================================================


def get_osm_infrastructure(

    latitude: float,

    longitude: float,

    radius_m: int = 10000

):

    try:

        query = f"""

        [out:json][timeout:60];

        (

          way["highway"]

            (around:
                {radius_m},
                {latitude},
                {longitude}
            );

          node["power"="substation"]

            (around:
                {radius_m},
                {latitude},
                {longitude}
            );

          way["power"="substation"]

            (around:
                {radius_m},
                {latitude},
                {longitude}
            );

          way["power"="line"]

            (around:
                {radius_m},
                {latitude},
                {longitude}
            );

          way["building"]

            (around:
                {radius_m},
                {latitude},
                {longitude}
            );

        );

        out center;

        """


        body = (

            "data="

            +

            urllib.parse.quote(
                query
            )

        ).encode("utf-8")


        request = urllib.request.Request(

            "https://overpass-api.de/api/interpreter",

            data=body,

            headers={

                "User-Agent":
                    "SolarWindDeploymentPlatform/2.0",

                "Content-Type":
                    "application/x-www-form-urlencoded"

            },

            method="POST"

        )


        with urllib.request.urlopen(

            request,

            timeout=90

        ) as response:

            data = json.loads(

                response
                .read()
                .decode("utf-8")

            )


        elements = data.get(
            "elements",
            []
        )


        roads = 0

        substations = 0

        power_lines = 0

        buildings = 0


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
        # INFRASTRUCTURE SCORE
        # ----------------------------------------------------

        score = 0


        if roads > 0:

            score += 40


        if roads >= 10:

            score += 15


        if substations > 0:

            score += 25


        if power_lines > 0:

            score += 20


        score = min(
            score,
            100
        )


        return {

            "source":
                "OpenStreetMap",

            "radius_km":
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
                score,

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

            "radius_km":
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
                50,

            "status":
                "failed",

            "error":
                str(e)

        }


# ============================================================
# COPERNICUS SENTINEL-2
#
# OPTIONAL
#
# Required environment variables:
#
# COPERNICUS_CLIENT_ID
# COPERNICUS_CLIENT_SECRET
#
# If credentials are not configured,
# the endpoint returns "not_configured".
#
# Uses Sentinel-2 L2A + Statistical API
# to calculate mean NDVI.
# ============================================================


def get_sentinel_ndvi(

    latitude: float,

    longitude: float

):

    client_id = os.getenv(
        "COPERNICUS_CLIENT_ID"
    )

    client_secret = os.getenv(
        "COPERNICUS_CLIENT_SECRET"
    )


    if not client_id or not client_secret:

        return {

            "source":
                "Copernicus Sentinel-2",

            "status":
                "not_configured",

            "mean_ndvi":
                None

        }


    try:

        # ----------------------------------------------------
        # 1. GET OAUTH TOKEN
        # ----------------------------------------------------

        token_url = (

            "https://identity.dataspace.copernicus.eu"

            "/auth/realms/CDSE/protocol/openid-connect/token"

        )


        token_data = urllib.parse.urlencode({

            "grant_type":
                "client_credentials",

            "client_id":
                client_id,

            "client_secret":
                client_secret

        }).encode("utf-8")


        token_request = urllib.request.Request(

            token_url,

            data=token_data,

            headers={

                "Content-Type":
                    "application/x-www-form-urlencoded",

                "User-Agent":
                    "SolarWindDeploymentPlatform/2.0"

            },

            method="POST"

        )


        with urllib.request.urlopen(

            token_request,

            timeout=30

        ) as response:

            token_response = json.loads(

                response
                .read()
                .decode("utf-8")

            )


        access_token = token_response[
            "access_token"
        ]


        # ----------------------------------------------------
        # 2. CREATE SMALL BBOX
        #
        # Approximately 1 km around point
        # ----------------------------------------------------

        delta = 0.01


        bbox = [

            longitude - delta,

            latitude - delta,

            longitude + delta,

            latitude + delta

        ]


        # ----------------------------------------------------
        # 3. NDVI EVALSCRIPT
        # ----------------------------------------------------

        evalscript = """

        //VERSION=3

        function setup() {

            return {

                input: [{

                    bands: [
                        "B04",
                        "B08",
                        "SCL",
                        "dataMask"
                    ]

                }],

                output: [

                    {

                        id: "ndvi",

                        bands: 1,

                        sampleType: "FLOAT32"

                    },

                    {

                        id: "dataMask",

                        bands: 1

                    }

                ]

            }

        }


        function evaluatePixel(samples) {

            var denominator =
                samples.B08 +
                samples.B04;


            var valid = 1;


            if (denominator == 0) {

                valid = 0;

            }


            // SCL class 6 = water

            if (samples.SCL == 6) {

                valid = 0;

            }


            var ndvi = (

                samples.B08 -
                samples.B04

            ) / denominator;


            return {

                ndvi: [ndvi],

                dataMask: [

                    samples.dataMask * valid

                ]

            };

        }

        """


        # ----------------------------------------------------
        # 4. STATISTICS REQUEST
        # ----------------------------------------------------

        stats_request = {

            "input": {

                "bounds": {

                    "bbox":
                        bbox,

                    "properties": {

                        "crs":
                            "http://www.opengis.net/def/crs/OGC/1.3/CRS84"

                    }

                },

                "data": [

                    {

                        "type":
                            "sentinel-2-l2a",

                        "dataFilter": {

                            "mosaickingOrder":
                                "leastCC"

                        }

                    }

                ]

            },

            "aggregation": {

                "timeRange": {

                    "from":
                        (
                            date.today()
                            - timedelta(days=365)
                        ).isoformat()
                        + "T00:00:00Z",

                    "to":
                        date.today().isoformat()
                        + "T23:59:59Z"

                },

                "aggregationInterval": {

                    "of":
                        "P30D"

                },

                "evalscript":
                    evalscript,

                "resx":
                    20,

                "resy":
                    20

            }

        }


        stats_url = (

            "https://sh.dataspace.copernicus.eu"

            "/statistics/v1"

        )


        response_bytes = http_post_json(

            stats_url,

            stats_request,

            headers={

                "Authorization":
                    f"Bearer {access_token}",

                "Accept":
                    "application/json"

            },

            timeout=90

        )


        response = json.loads(
            response_bytes.decode("utf-8")
        )


        # ----------------------------------------------------
        # 5. EXTRACT MEAN NDVI
        # ----------------------------------------------------

        values = []


        for interval in response.get(
            "data",
            []
        ):

            stats = (

                interval
                .get("outputs", {})
                .get("ndvi", {})
                .get("bands", {})
                .get("B0", {})
                .get("stats", {})

            )


            mean = stats.get(
                "mean"
            )


            if mean is not None:

                values.append(
                    float(mean)
                )


        if not values:

            raise Exception(
                "No Sentinel NDVI statistics returned"
            )


        mean_ndvi = (

            sum(values)

            /

            len(values)

        )


        # ----------------------------------------------------
        # VEGETATION CONSTRAINT SCORE
        #
        # This is an application-level score,
        # not a Sentinel-provided score.
        # ----------------------------------------------------

        if mean_ndvi < 0.2:

            environmental_score = 90

        elif mean_ndvi < 0.4:

            environmental_score = 75

        elif mean_ndvi < 0.6:

            environmental_score = 60

        else:

            environmental_score = 40


        return {

            "source":
                "Copernicus Sentinel-2",

            "status":
                "success",

            "mean_ndvi":
                round(
                    mean_ndvi,
                    4
                ),

            "environmental_score":
                environmental_score

        }


    except Exception as e:

        print(
            "SENTINEL ERROR:",
            e
        )

        return {

            "source":
                "Copernicus Sentinel-2",

            "status":
                "failed",

            "mean_ndvi":
                None,

            "environmental_score":
                None,

            "error":
                str(e)

        }


# ============================================================
# SOLAR CALCULATION
# ============================================================


def calculate_solar(

    land_area: float,

    irradiance: float,

    temperature: float

):

    # --------------------------------------------------------
    # LAND
    # --------------------------------------------------------

    land_m2 = (

        land_area

        *

        4046.856

    )


    # --------------------------------------------------------
    # 70% USABLE LAND
    # --------------------------------------------------------

    usable_area = (

        land_m2

        *

        0.70

    )


    # --------------------------------------------------------
    # PANEL EFFICIENCY
    # --------------------------------------------------------

    efficiency = 0.20


    # --------------------------------------------------------
    # TEMPERATURE DERATING
    # --------------------------------------------------------

    temperature_factor = 1.0


    if temperature > 25:

        temperature_factor = (

            1

            -

            0.004
            *
            (temperature - 25)

        )


    temperature_factor = max(

        0.70,

        temperature_factor

    )


    # --------------------------------------------------------
    # ESTIMATED CAPACITY
    # --------------------------------------------------------

    capacity_kw = (

        usable_area

        *

        efficiency

        /

        1000

    )


    capacity_mw = (

        capacity_kw

        /

        1000

    )


    # --------------------------------------------------------
    # DAILY ENERGY
    #
    # Irradiance behaves approximately like
    # peak sun hours for this MVP estimate.
    # --------------------------------------------------------

    performance_ratio = (

        0.80

        *

        temperature_factor

    )


    daily_energy_mwh = (

        capacity_mw

        *

        irradiance

        *

        performance_ratio

    )


    annual_energy_mwh = (

        daily_energy_mwh

        *

        365

    )


    # --------------------------------------------------------
    # SOLAR SCORE
    # --------------------------------------------------------

    score = (

        irradiance

        /

        5.0

    ) * 100


    score = max(

        0,

        min(
            100,
            score
        )

    )


    if score >= 80:

        rating = "Excellent"

    elif score >= 60:

        rating = "Good"

    elif score >= 40:

        rating = "Moderate"

    else:

        rating = "Low"


    return {

        "score":
            round(
                score,
                1
            ),

        "rating":
            rating,

        "capacity_mw":
            round(
                capacity_mw,
                2
            ),

        "daily_energy_mwh":
            round(
                daily_energy_mwh,
                2
            ),

        "annual_energy_mwh":
            round(
                annual_energy_mwh,
                2
            ),

        "efficiency":
            20.0

    }


# ============================================================
# WIND CALCULATION
# ============================================================


def calculate_wind(

    land_area: float,

    wind_speed: float,

    wind_power_density: float | None = None

):

    # --------------------------------------------------------
    # WIND SCORE
    # --------------------------------------------------------

    score = (

        (wind_speed - 3)

        /

        5

    ) * 100


    score = max(

        0,

        min(
            100,
            score
        )

    )


    if score >= 80:

        rating = "Excellent"

    elif score >= 60:

        rating = "Good"

    elif score >= 40:

        rating = "Moderate"

    else:

        rating = "Low"


    # --------------------------------------------------------
    # APPROXIMATE CAPACITY
    #
    # MVP:
    # 0.0317 MW per acre
    # --------------------------------------------------------

    capacity_mw = (

        land_area

        *

        0.0317

    )


    # --------------------------------------------------------
    # CAPACITY FACTOR
    # --------------------------------------------------------

    capacity_factor = (

        wind_speed

        /

        8

    ) * 40


    capacity_factor = max(

        10,

        min(
            45,
            capacity_factor
        )

    )


    # --------------------------------------------------------
    # DAILY ENERGY
    # --------------------------------------------------------

    daily_energy_mwh = (

        capacity_mw

        *

        24

        *

        capacity_factor

        /

        100

    )


    annual_energy_mwh = (

        daily_energy_mwh

        *

        365

    )


    return {

        "score":
            round(
                score,
                1
            ),

        "rating":
            rating,

        "capacity_mw":
            round(
                capacity_mw,
                2
            ),

        "capacity_factor":
            round(
                capacity_factor,
                1
            ),

        "daily_energy_mwh":
            round(
                daily_energy_mwh,
                2
            ),

        "annual_energy_mwh":
            round(
                annual_energy_mwh,
                2
            ),

        "wind_power_density_w_m2":
            (
                round(
                    wind_power_density,
                    2
                )
                if wind_power_density is not None
                else None
            )

    }


# ============================================================
# ANALYSIS HISTORY - DATABASE HELPERS
# ============================================================


def save_analysis_history(
    user_id: int,
    analysis_type: str,
    entered_location: str,
    resolved_location: str | None,
    latitude: float | None,
    longitude: float | None,
    land_area_acres: float,
    result_payload: dict
):
    """Save a completed analysis for the logged-in user."""

    solar = result_payload.get("solar", {})
    wind = result_payload.get("wind", {})
    suitability = result_payload.get("suitability", {})

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO analysis_history (
                    user_id,
                    analysis_type,
                    entered_location,
                    resolved_location,
                    latitude,
                    longitude,
                    land_area_acres,
                    overall_score,
                    suitability_category,
                    recommended_technology,
                    solar_score,
                    solar_rating,
                    solar_capacity_mw,
                    solar_daily_energy_mwh,
                    solar_annual_energy_mwh,
                    wind_score,
                    wind_rating,
                    wind_capacity_mw,
                    wind_daily_energy_mwh,
                    wind_annual_energy_mwh,
                    result_json,
                    created_at
                )
                VALUES (
                    :user_id,
                    :analysis_type,
                    :entered_location,
                    :resolved_location,
                    :latitude,
                    :longitude,
                    :land_area_acres,
                    :overall_score,
                    :suitability_category,
                    :recommended_technology,
                    :solar_score,
                    :solar_rating,
                    :solar_capacity_mw,
                    :solar_daily_energy_mwh,
                    :solar_annual_energy_mwh,
                    :wind_score,
                    :wind_rating,
                    :wind_capacity_mw,
                    :wind_daily_energy_mwh,
                    :wind_annual_energy_mwh,
                    CAST(:result_json AS JSONB),
                    CURRENT_TIMESTAMP
                )
            """),
            {
                "user_id": user_id,
                "analysis_type": analysis_type,
                "entered_location": entered_location,
                "resolved_location": resolved_location,
                "latitude": latitude,
                "longitude": longitude,
                "land_area_acres": land_area_acres,
                "overall_score": suitability.get("overall_score"),
                "suitability_category": suitability.get("category"),
                "recommended_technology": suitability.get("recommended_technology"),
                "solar_score": solar.get("score"),
                "solar_rating": solar.get("rating"),
                "solar_capacity_mw": solar.get("capacity_mw"),
                "solar_daily_energy_mwh": solar.get("daily_energy_mwh"),
                "solar_annual_energy_mwh": solar.get("annual_energy_mwh"),
                "wind_score": wind.get("score"),
                "wind_rating": wind.get("rating"),
                "wind_capacity_mw": wind.get("capacity_mw"),
                "wind_daily_energy_mwh": wind.get("daily_energy_mwh"),
                "wind_annual_energy_mwh": wind.get("annual_energy_mwh"),
                "result_json": json.dumps(result_payload)
            }
        )


@app.get("/analysis-history/{user_id}")
def get_analysis_history(user_id: int):
    """Return saved analyses for one user, newest first."""

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT *
                    FROM analysis_history
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC, id DESC
                """),
                {"user_id": user_id}
            ).fetchall()

        history = []
        for row in rows:
            item = dict(row._mapping)
            if item.get("created_at") is not None:
                item["created_at"] = item["created_at"].isoformat()
            history.append(item)

        return {
            "user_id": user_id,
            "count": len(history),
            "history": history
        }

    except Exception as e:
        print("ANALYSIS HISTORY ERROR:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve analysis history"
        )


# ============================================================
# COMPLETE SITE ANALYSIS
#
# USER:
#
# Location
# Land Area
#
# BACKEND:
#
# NASA POWER
# Global Wind Atlas
# SRTM
# OSM
# Sentinel-2 (if credentials configured)
# ============================================================


@app.post("/site-analysis")
def site_analysis(
    data: SiteAnalysisRequest
):

    if data.land_area <= 0:

        raise HTTPException(

            status_code=400,

            detail=
                "Land area must be greater than zero"

        )


    # ========================================================
    # STEP 1
    # LOCATION → COORDINATES
    # ========================================================

    latitude, longitude, display_name = (

        get_coordinates(
            data.location
        )

    )


    # ========================================================
    # STEP 2
    # NASA POWER
    # ========================================================

    nasa = get_nasa_power_data(

        latitude,

        longitude

    )


    # ========================================================
    # STEP 3
    # GLOBAL WIND ATLAS
    # ========================================================

    gwa = get_global_wind_atlas(

        latitude,

        longitude

    )


    # ========================================================
    # STEP 4
    # SRTM
    # ========================================================

    srtm = get_srtm_elevation(

        latitude,

        longitude

    )


    # ========================================================
    # STEP 5
    # OPENSTREETMAP
    # ========================================================

    osm = get_osm_infrastructure(

        latitude,

        longitude

    )


    # ========================================================
    # STEP 6
    # SENTINEL
    # ========================================================

    sentinel = get_sentinel_ndvi(

        latitude,

        longitude

    )


    # ========================================================
    # SOLAR
    # ========================================================

    solar = calculate_solar(

        data.land_area,

        nasa[
            "average_solar_irradiance"
        ],

        nasa[
            "average_temperature"
        ]

    )


    # ========================================================
    # WIND
    #
    # GLOBAL WIND ATLAS FIRST
    #
    # NASA POWER FALLBACK
    # ========================================================

    if (

        gwa["status"] == "success"

        and

        gwa[
            "mean_wind_speed_mps"
        ] is not None

    ):

        wind_speed = gwa[
            "mean_wind_speed_mps"
        ]

        wind_source = (
            "Global Wind Atlas"
        )

        wind_power_density = gwa[
            "wind_power_density_w_m2"
        ]

    else:

        wind_speed = nasa[
            "average_wind_speed"
        ]

        wind_source = (
            "NASA POWER fallback"
        )

        wind_power_density = None


    wind = calculate_wind(

        data.land_area,

        wind_speed,

        wind_power_density

    )


    # ========================================================
    # TERRAIN SCORE
    # ========================================================

    elevation = srtm.get(
        "elevation_m"
    )


    if elevation is None:

        terrain_score = 50

    elif elevation < 500:

        terrain_score = 90

    elif elevation < 1000:

        terrain_score = 75

    elif elevation < 1500:

        terrain_score = 60

    else:

        terrain_score = 40


    # ========================================================
    # INFRASTRUCTURE SCORE
    # ========================================================

    infrastructure_score = (

        osm.get(
            "infrastructure_score",
            50
        )

    )


    if infrastructure_score is None:

        infrastructure_score = 50


    # ========================================================
    # ENVIRONMENTAL SCORE
    #
    # Sentinel if available.
    #
    # Otherwise a clearly marked MVP fallback.
    # ========================================================

    if (

        sentinel["status"] == "success"

        and

        sentinel[
            "environmental_score"
        ] is not None

    ):

        environmental_score = (

            sentinel[
                "environmental_score"
            ]

        )

    else:

        environmental_score = 75


    # ========================================================
    # ECONOMIC SCORE
    #
    # MVP PLACEHOLDER
    #
    # This should later use:
    #
    # CAPEX
    # OPEX
    # electricity price
    # land cost
    # ROI
    # ========================================================

    economic_score = 70


    # ========================================================
    # RENEWABLE RESOURCE SCORE
    # ========================================================

    renewable_resource_score = (

        solar["score"]

        *

        0.55

        +

        wind["score"]

        *

        0.45

    )


    # ========================================================
    # GEOGRAPHIC SUITABILITY
    # ========================================================

    geographic_suitability = (

        terrain_score

        *

        0.60

        +

        infrastructure_score

        *

        0.40

    )


    # ========================================================
    # FINAL WEIGHTED SCORE
    #
    # PROJECT SPECIFICATION:
    #
    # Renewable Resource = 35%
    # Geographic          = 25%
    # Infrastructure      = 15%
    # Environmental       = 15%
    # Economic            = 10%
    # ========================================================

    overall_score = (

        renewable_resource_score
        *
        0.35

        +

        geographic_suitability
        *
        0.25

        +

        infrastructure_score
        *
        0.15

        +

        environmental_score
        *
        0.15

        +

        economic_score
        *
        0.10

    )


    overall_score = max(

        0,

        min(
            100,
            overall_score
        )

    )


    # ========================================================
    # SUITABILITY CATEGORY
    # ========================================================

    if overall_score >= 85:

        category = "Excellent"

    elif overall_score >= 70:

        category = "Highly Suitable"

    elif overall_score >= 55:

        category = "Moderately Suitable"

    elif overall_score >= 40:

        category = "Low Suitability"

    else:

        category = "Unsuitable"


    # ========================================================
    # RECOMMENDATION
    # ========================================================

    if (

        solar["score"] >= 75

        and

        wind["score"] >= 60

    ):

        recommendation = (
            "Hybrid Solar + Wind"
        )

    elif solar["score"] >= wind["score"]:

        recommendation = "Solar"

    else:

        recommendation = "Wind"


    # ========================================================
    # RETURN COMPLETE RESULT
    # ========================================================

    response = {

        # ----------------------------------------------------
        # SITE
        # ----------------------------------------------------

        "site": {

            "entered_location":
                data.location,

            "resolved_location":
                display_name,

            "latitude":
                round(
                    latitude,
                    6
                ),

            "longitude":
                round(
                    longitude,
                    6
                ),

            "land_area_acres":
                data.land_area

        },


        # ----------------------------------------------------
        # BACKWARD COMPATIBILITY
        # ----------------------------------------------------

        "data_source": {

            "provider":
                "NASA POWER + Global Wind Atlas + SRTM + OSM + Sentinel-2",

            "start_date":
                nasa["start_date"],

            "end_date":
                nasa["end_date"],

            "days_analyzed":
                nasa["days"]

        },


        # ----------------------------------------------------
        # ALL DATA SOURCES
        # ----------------------------------------------------

        "data_sources": {

            "nasa_power":
                nasa,

            "global_wind_atlas":
                gwa,

            "srtm":
                srtm,

            "openstreetmap":
                osm,

            "sentinel":
                sentinel

        },


        # ----------------------------------------------------
        # ENVIRONMENT
        # ----------------------------------------------------

        "environment": {

            "solar_irradiance":
                round(
                    nasa[
                        "average_solar_irradiance"
                    ],
                    3
                ),

            "temperature":
                round(
                    nasa[
                        "average_temperature"
                    ],
                    2
                ),

            "wind_speed":
                round(
                    wind_speed,
                    2
                ),

            "wind_data_source":
                wind_source

        },


        # ----------------------------------------------------
        # GEOGRAPHIC
        # ----------------------------------------------------

        "geographic": {

            "elevation_m":
                elevation,

            "terrain_score":
                terrain_score,

            "infrastructure_score":
                infrastructure_score,

            "roads":
                osm.get(
                    "roads"
                ),

            "substations":
                osm.get(
                    "substations"
                ),

            "power_lines":
                osm.get(
                    "power_lines"
                ),

            "buildings":
                osm.get(
                    "buildings"
                )

        },


        # ----------------------------------------------------
        # SOLAR
        # ----------------------------------------------------

        "solar":
            solar,


        # ----------------------------------------------------
        # WIND
        # ----------------------------------------------------

        "wind":
            wind,


        # ----------------------------------------------------
        # SUITABILITY
        # ----------------------------------------------------

        "suitability": {

            "renewable_resource_score":
                round(
                    renewable_resource_score,
                    1
                ),

            "geographic_suitability_score":
                round(
                    geographic_suitability,
                    1
                ),

            "infrastructure_score":
                round(
                    infrastructure_score,
                    1
                ),

            "environmental_score":
                round(
                    environmental_score,
                    1
                ),

            "economic_score":
                round(
                    economic_score,
                    1
                ),

            "overall_score":
                round(
                    overall_score,
                    1
                ),

            "category":
                category,

            "recommended_technology":
                recommendation

        }

    }

    save_analysis_history(
        user_id=data.user_id,
        analysis_type="site",
        entered_location=data.location,
        resolved_location=display_name,
        latitude=latitude,
        longitude=longitude,
        land_area_acres=data.land_area,
        result_payload=response
    )

    return response


# ============================================================
# SOLAR ANALYSIS
#
# USER ENTERS:
#
# Location
# Land Area
#
# Backend fetches NASA automatically.
# ============================================================


@app.post("/solar-analysis")
def solar_analysis(
    data: SolarAnalysisRequest
):

    # --------------------------------------------------------
    # IF USER DID NOT PROVIDE ENVIRONMENTAL VALUES
    # FETCH NASA DATA
    # --------------------------------------------------------

    latitude = None
    longitude = None

    if (

        data.irradiance is None

        or

        data.temperature is None

    ):

        latitude, longitude, display_name = (

            get_coordinates(
                data.location
            )

        )


        nasa = get_nasa_power_data(

            latitude,

            longitude

        )


        irradiance = nasa[
            "average_solar_irradiance"
        ]

        temperature = nasa[
            "average_temperature"
        ]

        resolved_location = (
            display_name
        )

    else:

        irradiance = data.irradiance

        temperature = data.temperature

        resolved_location = (
            data.location
        )


    result = calculate_solar(

        data.land_area,

        irradiance,

        temperature

    )


    response = {

        "location":
            resolved_location,

        "latitude":
            round(latitude, 6) if latitude is not None else None,

        "longitude":
            round(longitude, 6) if longitude is not None else None,

        "score":
            result["score"],

        "rating":
            result["rating"],

        "capacity":
            result["capacity_mw"],

        "energy":
            result["daily_energy_mwh"],

        "annual_energy":
            result["annual_energy_mwh"],

        "efficiency":
            result["efficiency"],

        "land_area":
            data.land_area,

        "irradiance":
            round(
                irradiance,
                3
            ),

        "temperature":
            round(
                temperature,
                2
            ),

        "data_source":
            "NASA POWER"

    }

    # Coordinates are already available when NASA was fetched.
    # If the caller supplied environmental values, geocode once so
    # the saved history still contains coordinates.
    if latitude is None or longitude is None:
        latitude, longitude, resolved_location = get_coordinates(
            data.location
        )
        response["location"] = resolved_location

    save_analysis_history(
        user_id=data.user_id,
        analysis_type="solar",
        entered_location=data.location,
        resolved_location=response["location"],
        latitude=latitude,
        longitude=longitude,
        land_area_acres=data.land_area,
        result_payload={
            "site": {
                "entered_location": data.location,
                "resolved_location": response["location"],
                "latitude": latitude,
                "longitude": longitude,
                "land_area_acres": data.land_area
            },
            "solar": {
                "score": response["score"],
                "rating": response["rating"],
                "capacity_mw": response["capacity"],
                "daily_energy_mwh": response["energy"],
                "annual_energy_mwh": response["annual_energy"]
            },
            "input": response
        }
    )

    return response


# ============================================================
# WIND ANALYSIS
#
# USER ENTERS:
#
# Location
# Land Area
#
# Backend uses Global Wind Atlas first.
# NASA POWER is fallback.
# ============================================================


@app.post("/wind-analysis")
def wind_analysis(
    data: WindAnalysisRequest
):

    # --------------------------------------------------------
    # IF WIND SPEED NOT PROVIDED
    # FETCH EXTERNAL DATA
    # --------------------------------------------------------

    latitude = None
    longitude = None

    if data.wind_speed is None:

        latitude, longitude, display_name = (

            get_coordinates(
                data.location
            )

        )


        gwa = get_global_wind_atlas(

            latitude,

            longitude

        )


        if (

            gwa["status"] == "success"

            and

            gwa[
                "mean_wind_speed_mps"
            ] is not None

        ):

            wind_speed = gwa[
                "mean_wind_speed_mps"
            ]

            wind_source = (
                "Global Wind Atlas"
            )

            wind_power_density = gwa[
                "wind_power_density_w_m2"
            ]

        else:

            nasa = get_nasa_power_data(

                latitude,

                longitude

            )

            wind_speed = nasa[
                "average_wind_speed"
            ]

            wind_source = (
                "NASA POWER fallback"
            )

            wind_power_density = None

    else:

        wind_speed = data.wind_speed

        wind_source = (
            "User supplied"
        )

        wind_power_density = None

        display_name = (
            data.location
        )


    result = calculate_wind(

        data.land_area,

        wind_speed,

        wind_power_density

    )


    response = {

        "location":
            display_name,

        "latitude":
            round(latitude, 6) if latitude is not None else None,

        "longitude":
            round(longitude, 6) if longitude is not None else None,

        "score":
            result["score"],

        "rating":
            result["rating"],

        "capacity":
            result["capacity_mw"],

        "energy":
            result["daily_energy_mwh"],

        "annual_energy":
            result["annual_energy_mwh"],

        "capacity_factor":
            result["capacity_factor"],

        "wind_speed":
            round(
                wind_speed,
                2
            ),

        "wind_power_density":
            result[
                "wind_power_density_w_m2"
            ],

        "data_source":
            wind_source

    }

    if latitude is None or longitude is None:
        latitude, longitude, display_name = get_coordinates(
            data.location
        )
        response["location"] = display_name

    save_analysis_history(
        user_id=data.user_id,
        analysis_type="wind",
        entered_location=data.location,
        resolved_location=response["location"],
        latitude=latitude,
        longitude=longitude,
        land_area_acres=data.land_area,
        result_payload={
            "site": {
                "entered_location": data.location,
                "resolved_location": response["location"],
                "latitude": latitude,
                "longitude": longitude,
                "land_area_acres": data.land_area
            },
            "wind": {
                "score": response["score"],
                "rating": response["rating"],
                "capacity_mw": response["capacity"],
                "daily_energy_mwh": response["energy"],
                "annual_energy_mwh": response["annual_energy"]
            },
            "input": response
        }
    )

    return response