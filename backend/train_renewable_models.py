import os
import glob
import joblib
import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "datasets"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


print("=" * 75)
print("🌞🌬️ SOLAR & WIND ML TRAINING PIPELINE")
print("=" * 75)


# ============================================================
# DATASET DISCOVERY
# ============================================================

all_files = []

for extension in ["*.csv", "*.xlsx", "*.xls"]:

    all_files.extend(
        glob.glob(
            os.path.join(
                DATA_DIR,
                extension
            )
        )
    )


if not all_files:

    raise FileNotFoundError(
        f"""
❌ No datasets found.

Put your datasets inside:

{DATA_DIR}
"""
    )


print()
print("📂 Datasets found:")

for file in all_files:

    print(
        "   ",
        os.path.basename(file)
    )


# ============================================================
# HELPERS
# ============================================================

def find_file(keyword):

    keyword = keyword.lower()

    for file in all_files:

        name = os.path.basename(
            file
        ).lower()

        if keyword in name:

            return file

    return None


def load_table(file):

    if file is None:

        return None

    extension = (
        os.path.splitext(file)[1]
        .lower()
    )

    try:

        if extension == ".csv":

            return pd.read_csv(
                file
            )

        if extension in [".xlsx", ".xls"]:

            excel = pd.ExcelFile(
                file
            )

            # First sheet by default
            return pd.read_excel(
                file,
                sheet_name=excel.sheet_names[0]
            )

    except Exception as e:

        print(
            f"⚠️ Could not read "
            f"{os.path.basename(file)}: {e}"
        )

        return None

    return None


def clean_columns(df):

    if df is None:

        return None

    df = df.copy()

    df.columns = [

        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")

        for column in df.columns

    ]

    return df


def numeric(df, column):

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


def model():

    return Pipeline(

        [

            (
                "imputer",

                SimpleImputer(
                    strategy="median"
                )

            ),

            (

                "model",

                ExtraTreesRegressor(

                    n_estimators=400,

                    max_depth=20,

                    min_samples_leaf=2,

                    random_state=42,

                    n_jobs=-1

                )

            )

        ]

    )


# ============================================================
# FIND NASA DATASET
# ============================================================

nasa_file = find_file(
    "nasa_power"
)

if nasa_file is None:

    raise FileNotFoundError(
        """
❌ NASA POWER dataset not found.

Expected a file containing:
nasa_power
"""
    )


print()
print(
    "🌍 NASA dataset:"
)

print(
    "   ",
    os.path.basename(
        nasa_file
    )
)


nasa = load_table(
    nasa_file
)

nasa = clean_columns(
    nasa
)


print(
    f"   Records: {len(nasa)}"
)


# ============================================================
# NASA REQUIRED COLUMNS
# ============================================================

required_nasa = [

    "latitude",
    "longitude",
    "year",

    "temp_mean_c",
    "temp_max_c",
    "temp_min_c",

    "precip_total_mm",

    "rh_mean_pct",

    "wind_mean_ms",

    "pressure_mean_kpa",

    "solar_annual_kwh_m2"

]


missing = [

    column
    for column in required_nasa
    if column not in nasa.columns

]


if missing:

    print()
    print(
        "❌ NASA dataset missing:"
    )

    for column in missing:

        print(
            "   ",
            column
        )

    raise SystemExit()


for column in required_nasa:

    numeric(
        nasa,
        column
    )


nasa = nasa.dropna(

    subset=[
        "latitude",
        "longitude",
        "year"
    ]

)


# ============================================================
# ADD DERIVED RESOURCE FEATURES
# ============================================================

if "wind_power_density" not in nasa.columns:

    # Approximate WPD from mean wind speed.
    #
    # This is only a baseline because real wind
    # turbine assessment should use hub-height data.

    nasa[
        "wind_power_density"
    ] = (

        0.5
        * 1.225
        * (
            nasa["wind_mean_ms"]
            ** 3
        )

    )


if "solar_mean_mj" not in nasa.columns:

    nasa[
        "solar_mean_mj"
    ] = (

        nasa[
            "solar_annual_kwh_m2"
        ]

        / 365

        * 3.6

    )


if "solar_clearness_idx" not in nasa.columns:

    if (
        "solar_clear_mean_mj"
        in nasa.columns
    ):

        nasa[
            "solar_clearness_idx"
        ] = (

            nasa[
                "solar_mean_mj"
            ]
            /
            nasa[
                "solar_clear_mean_mj"
            ]

        )

    else:

        nasa[
            "solar_clearness_idx"
        ] = 0.7


if "heat_stress_index" not in nasa.columns:

    nasa[
        "heat_stress_index"
    ] = (

        (
            nasa["temp_mean_c"]
            - 25
        )
        .clip(lower=0)

        * 5

    )


if "drought_stress_days" not in nasa.columns:

    nasa[
        "drought_stress_days"
    ] = (

        120
        -
        nasa[
            "precip_total_mm"
        ] / 10

    ).clip(
        lower=0
    )


if "humidity_stress_days" not in nasa.columns:

    nasa[
        "humidity_stress_days"
    ] = 20.0


if "climate_volatility" not in nasa.columns:

    nasa[
        "climate_volatility"
    ] = 10.0


if "gdp_per_capita_usd" not in nasa.columns:

    nasa[
        "gdp_per_capita_usd"
    ] = 5000.0


# ============================================================
# SOLAR MODEL
# ============================================================

print()
print("=" * 75)
print("☀️ SOLAR RESOURCE MODEL")
print("=" * 75)


SOLAR_FEATURES = [

    "latitude",
    "longitude",
    "year",

    "temp_mean_c",
    "temp_max_c",
    "temp_min_c",

    "precip_total_mm",

    "rh_mean_pct",

    "wind_mean_ms",

    "climate_volatility",

    "pressure_mean_kpa"

]


SOLAR_TARGET = (
    "solar_annual_kwh_m2"
)


solar_data = nasa.dropna(

    subset=[
        SOLAR_TARGET
    ]

)


solar_train = solar_data[
    solar_data["year"] < 2020
]


solar_test = solar_data[
    solar_data["year"] >= 2020
]


X_train = solar_train[
    SOLAR_FEATURES
]

y_train = solar_train[
    SOLAR_TARGET
]


X_test = solar_test[
    SOLAR_FEATURES
]

y_test = solar_test[
    SOLAR_TARGET
]


solar_model = model()


solar_model.fit(
    X_train,
    y_train
)


solar_pred = (
    solar_model.predict(
        X_test
    )
)


solar_mae = (
    mean_absolute_error(
        y_test,
        solar_pred
    )
)


solar_r2 = (
    r2_score(
        y_test,
        solar_pred
    )
)


print()
print(
    f"☀️ Solar training rows: "
    f"{len(X_train)}"
)

print(
    f"☀️ Solar testing rows : "
    f"{len(X_test)}"
)

print(
    f"☀️ Solar MAE: "
    f"{solar_mae:.2f} kWh/m²/year"
)

print(
    f"☀️ Solar R² : "
    f"{solar_r2:.4f}"
)


joblib.dump(

    solar_model,

    os.path.join(
        MODEL_DIR,
        "solar_model.pkl"
    )

)


joblib.dump(

    SOLAR_FEATURES,

    os.path.join(
        MODEL_DIR,
        "solar_features.pkl"
    )

)


print(
    "✅ solar_model.pkl saved"
)


# ============================================================
# WIND MODEL
# ============================================================

print()
print("=" * 75)
print("🌬️ WIND RESOURCE MODEL")
print("=" * 75)


WIND_FEATURES = [

    "latitude",
    "longitude",
    "year",

    "temp_mean_c",
    "temp_max_c",
    "temp_min_c",

    "precip_total_mm",

    "rh_mean_pct",

    "pressure_mean_kpa",

    "climate_volatility"

]


WIND_TARGET = (
    "wind_mean_ms"
)


wind_data = nasa.dropna(

    subset=[
        WIND_TARGET
    ]

)


wind_train = wind_data[
    wind_data["year"] < 2020
]


wind_test = wind_data[
    wind_data["year"] >= 2020
]


X_train = wind_train[
    WIND_FEATURES
]

y_train = wind_train[
    WIND_TARGET
]


X_test = wind_test[
    WIND_FEATURES
]

y_test = wind_test[
    WIND_TARGET
]


wind_model = model()


wind_model.fit(
    X_train,
    y_train
)


wind_pred = (
    wind_model.predict(
        X_test
    )
)


wind_mae = (
    mean_absolute_error(
        y_test,
        wind_pred
    )
)


wind_r2 = (
    r2_score(
        y_test,
        wind_pred
    )
)


print()
print(
    f"🌬️ Wind training rows: "
    f"{len(X_train)}"
)

print(
    f"🌬️ Wind testing rows : "
    f"{len(X_test)}"
)

print(
    f"🌬️ Wind MAE: "
    f"{wind_mae:.3f} m/s"
)

print(
    f"🌬️ Wind R² : "
    f"{wind_r2:.4f}"
)


joblib.dump(

    wind_model,

    os.path.join(
        MODEL_DIR,
        "wind_model.pkl"
    )

)


joblib.dump(

    WIND_FEATURES,

    os.path.join(
        MODEL_DIR,
        "wind_features.pkl"
    )

)


print(
    "✅ wind_model.pkl saved"
)


# ============================================================
# SOLAR PLANT DATA
# ============================================================

print()
print("=" * 75)
print("☀️ SOLAR PLANT DATA")
print("=" * 75)


plant_generation_files = [

    file

    for file in all_files

    if (
        "generation"
        in os.path.basename(
            file
        ).lower()
    )

]


plant_weather_files = [

    file

    for file in all_files

    if (
        "weather"
        in os.path.basename(
            file
        ).lower()
    )

]


print()
print(
    f"Generation files: "
    f"{len(plant_generation_files)}"
)

print(
    f"Weather files: "
    f"{len(plant_weather_files)}"
)


# ============================================================
# TRAIN PLANT GENERATION MODEL
#
# This is an additional model.
#
# It is NOT used to fake wind suitability.
# It learns actual solar-plant generation behaviour.
# ============================================================


plant_frames = []


for weather_file in plant_weather_files:

    weather = load_table(
        weather_file
    )

    weather = clean_columns(
        weather
    )

    if weather is None:

        continue


    generation_match = None

    weather_name = (
        os.path.basename(
            weather_file
        ).lower()
    )


    if "plant_1" in weather_name:

        generation_match = (

            find_file(
                "plant_1_generation"
            )

        )


    elif "plant_2" in weather_name:

        generation_match = (

            find_file(
                "plant_2_generation"
            )

        )


    if generation_match is None:

        continue


    generation = load_table(
        generation_match
    )

    generation = clean_columns(
        generation
    )


    if generation is None:

        continue


    print()
    print(
        "📊 Processing:"
    )

    print(
        "   Weather:",
        os.path.basename(
            weather_file
        )
    )

    print(
        "   Generation:",
        os.path.basename(
            generation_match
        )
    )


    # --------------------------------------------------------
    # Display columns for verification
    # --------------------------------------------------------

    print(
        "   Weather columns:",
        list(weather.columns)
    )

    print(
        "   Generation columns:",
        list(generation.columns)
    )


    # --------------------------------------------------------
    # Detect common date/time column
    # --------------------------------------------------------

    date_candidates = [

        "date_time",
        "datetime",
        "date",
        "timestamp"

    ]


    weather_date = None
    generation_date = None


    for column in date_candidates:

        if column in weather.columns:

            weather_date = column

            break


    for column in date_candidates:

        if column in generation.columns:

            generation_date = column

            break


    if (
        weather_date is None
        or
        generation_date is None
    ):

        print(
            "⚠️ Date column not detected."
        )

        continue


    weather[
        "merge_time"
    ] = pd.to_datetime(
        weather[
            weather_date
        ],
        errors="coerce"
    )


    generation[
        "merge_time"
    ] = pd.to_datetime(
        generation[
            generation_date
        ],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Find generation target
    # --------------------------------------------------------

    generation_candidates = [

        "daily_yield",
        "total_yield",
        "power",
        "generation",
        "energy",
        "ac_power",
        "dc_power"

    ]


    target_column = None


    for column in generation_candidates:

        if column in generation.columns:

            target_column = column

            break


    if target_column is None:

        print(
            "⚠️ Generation target not detected."
        )

        continue


    numeric(
        generation,
        target_column
    )


    # --------------------------------------------------------
    # Merge weather + generation
    # --------------------------------------------------------

    merged = pd.merge(

        weather,

        generation,

        on="merge_time",

        how="inner",

        suffixes=(
            "_weather",
            "_generation"
        )

    )


    if len(merged) < 100:

        print(
            "⚠️ Not enough merged records."
        )

        continue


    # --------------------------------------------------------
    # Detect weather features
    # --------------------------------------------------------

    feature_candidates = [

        "irradiation",
        "irradiance",
        "ghi",
        "poa",
        "ambient_temperature",
        "module_temperature",
        "temperature",
        "wind_speed",
        "humidity",
        "pressure"

    ]


    features = [

        column

        for column in feature_candidates

        if column in merged.columns

    ]


    if len(features) < 2:

        print(
            "⚠️ Not enough weather features."
        )

        continue


    for feature in features:

        numeric(
            merged,
            feature
        )


    merged = merged.dropna(

        subset=features

    )


    plant_frames.append(

        merged[
            features + [
                target_column
            ]
        ]

    )


# ============================================================
# TRAIN PLANT MODEL IF DATA AVAILABLE
# ============================================================

if plant_frames:

    plant_data = pd.concat(
        plant_frames,
        ignore_index=True
    )


    print()
    print(
        f"✅ Combined plant records: "
        f"{len(plant_data)}"
    )


    plant_features = [

        column

        for column
        in plant_data.columns

        if column != target_column

    ]


    X = plant_data[
        plant_features
    ]

    y = plant_data[
        target_column
    ]


    X_train, X_test, y_train, y_test = (

        train_test_split(

            X,

            y,

            test_size=0.20,

            random_state=42

        )

    )


    plant_model = model()


    plant_model.fit(
        X_train,
        y_train
    )


    plant_pred = (
        plant_model.predict(
            X_test
        )
    )


    plant_mae = (
        mean_absolute_error(
            y_test,
            plant_pred
        )
    )


    plant_r2 = (
        r2_score(
            y_test,
            plant_pred
        )
    )


    print()
    print(
        "☀️ Plant generation model:"
    )

    print(
        f"   MAE: {plant_mae:.3f}"
    )

    print(
        f"   R² : {plant_r2:.4f}"
    )


    joblib.dump(

        plant_model,

        os.path.join(
            MODEL_DIR,
            "solar_generation_model.pkl"
        )

    )


    joblib.dump(

        plant_features,

        os.path.join(
            MODEL_DIR,
            "solar_generation_features.pkl"
        )

    )


    print(
        "✅ solar_generation_model.pkl saved"
    )

else:

    print()
    print(
        "⚠️ Plant generation model not created."
    )

    print(
        "   NASA solar model is still valid."
    )


# ============================================================
# SUITABILITY MODEL
# ============================================================

print()
print("=" * 75)
print("🏆 SITE RESOURCE SUITABILITY MODEL")
print("=" * 75)


SUITABILITY_FEATURES = [

    "latitude",
    "longitude",

    "temp_mean_c",
    "precip_total_mm",

    "rh_mean_pct",

    "wind_mean_ms",

    "wind_power_density",

    "solar_total_mj",

    "solar_mean_mj",

    "solar_clearness_idx",

    "heat_stress_index",

    "drought_stress_days",

    "humidity_stress_days",

    "climate_volatility"

]


s = nasa.copy()


s["solar_total_mj"] = (

    s[
        "solar_annual_kwh_m2"
    ]

    * 3.6

)


def percentile(
    series
):

    return (

        series.rank(
            pct=True
        )

        .clip(
            0,
            1
        )

    )


solar_strength = percentile(

    s[
        "solar_annual_kwh_m2"
    ]

)


wind_strength = percentile(

    s[
        "wind_power_density"
    ]

)


heat_ok = (

    1

    -

    percentile(
        s[
            "heat_stress_index"
        ]
    )

)


drought_ok = (

    1

    -

    percentile(
        s[
            "drought_stress_days"
        ]
    )

)


humidity_ok = (

    1

    -

    percentile(
        s[
            "humidity_stress_days"
        ]
    )

)


climate_ok = (

    1

    -

    percentile(
        s[
            "climate_volatility"
        ]
    )

)


# Transparent resource-based target

s[
    "suitability_target"
] = (

    solar_strength * 40

    +

    wind_strength * 30

    +

    heat_ok * 10

    +

    drought_ok * 10

    +

    humidity_ok * 5

    +

    climate_ok * 5

)


s_train = s[
    s["year"] < 2020
]


s_test = s[
    s["year"] >= 2020
]


X_train = s_train[
    SUITABILITY_FEATURES
]

y_train = s_train[
    "suitability_target"
]


X_test = s_test[
    SUITABILITY_FEATURES
]

y_test = s_test[
    "suitability_target"
]


suitability_model = model()


suitability_model.fit(

    X_train,

    y_train

)


suitability_pred = (

    suitability_model.predict(
        X_test
    )

)


suitability_pred = np.clip(

    suitability_pred,

    0,

    100

)


suitability_mae = (

    mean_absolute_error(

        y_test,

        suitability_pred

    )

)


suitability_r2 = (

    r2_score(

        y_test,

        suitability_pred

    )

)


print()
print(
    f"🏆 Suitability MAE: "
    f"{suitability_mae:.3f}"
)

print(
    f"🏆 Suitability R² : "
    f"{suitability_r2:.4f}"
)


joblib.dump(

    suitability_model,

    os.path.join(
        MODEL_DIR,
        "suitability_model.pkl"
    )

)


joblib.dump(

    SUITABILITY_FEATURES,

    os.path.join(
        MODEL_DIR,
        "suitability_features.pkl"
    )

)


print(
    "✅ suitability_model.pkl saved"
)


# ============================================================
# METADATA
# ============================================================

metadata = {

    "solar_model":
        "NASA POWER climate/resource model",

    "wind_model":
        "NASA POWER baseline wind model",

    "plant_model":
        "Actual Indian solar plant weather/generation model",

    "solar_target":
        SOLAR_TARGET,

    "wind_target":
        WIND_TARGET,

    "solar_features":
        SOLAR_FEATURES,

    "wind_features":
        WIND_FEATURES,

    "suitability_features":
        SUITABILITY_FEATURES,

    "solar_r2":
        float(
            solar_r2
        ),

    "solar_mae":
        float(
            solar_mae
        ),

    "wind_r2":
        float(
            wind_r2
        ),

    "wind_mae":
        float(
            wind_mae
        ),

    "suitability_r2":
        float(
            suitability_r2
        ),

    "suitability_mae":
        float(
            suitability_mae
        )

}


joblib.dump(

    metadata,

    os.path.join(
        MODEL_DIR,
        "model_metadata.pkl"
    )

)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 75)
print("🎉 TRAINING COMPLETE")
print("=" * 75)

print()
print(
    "☀️ Solar R²:",
    round(
        solar_r2,
        4
    )
)

print(
    "🌬️ Wind R²:",
    round(
        wind_r2,
        4
    )
)

print(
    "🏆 Suitability R²:",
    round(
        suitability_r2,
        4
    )
)

print()
print(
    "📁 Models:"
)

print(
    "   solar_model.pkl"
)

print(
    "   solar_features.pkl"
)

print(
    "   wind_model.pkl"
)

print(
    "   wind_features.pkl"
)

print(
    "   suitability_model.pkl"
)

print(
    "   suitability_features.pkl"
)

print(
    "   model_metadata.pkl"
)

if plant_frames:

    print(
        "   solar_generation_model.pkl"
    )

    print(
        "   solar_generation_features.pkl"
    )

print()
print("=" * 75)