import requests
from sqlalchemy import text

from app.database import SessionLocal


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


def download_nasa_power(
    site_id,
    latitude,
    longitude,
    start_date="20220101",
    end_date="20261231"
):

    parameters = ",".join([
        "T2M",
        "WS10M",
        "ALLSKY_SFC_SW_DWN",
        "ALLSKY_SFC_SW_DNI",
        "ALLSKY_SFC_SW_DIFF"
    ])

    params = {
        "parameters": parameters,
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    print("\n===================================")
    print("DOWNLOADING NASA POWER DATA")
    print("===================================")

    print("Latitude :", latitude)
    print("Longitude:", longitude)
    print("Start    :", start_date)
    print("End      :", end_date)

    response = requests.get(
        NASA_POWER_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    parameters_data = data["properties"]["parameter"]

    temperature = parameters_data["T2M"]
    wind_speed = parameters_data["WS10M"]
    ghi = parameters_data["ALLSKY_SFC_SW_DWN"]
    dni = parameters_data["ALLSKY_SFC_SW_DNI"]
    dhi = parameters_data["ALLSKY_SFC_SW_DIFF"]

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:

        for recorded_date in temperature:

            temp_value = temperature.get(recorded_date)
            wind_value = wind_speed.get(recorded_date)
            ghi_value = ghi.get(recorded_date)
            dni_value = dni.get(recorded_date)
            dhi_value = dhi.get(recorded_date)

            # NASA POWER missing-value check
            if (
                temp_value == -999
                or wind_value == -999
                or ghi_value == -999
                or dni_value == -999
                or dhi_value == -999
            ):
                skipped += 1
                continue

            # Check duplicate
            existing = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM resource_data
                    WHERE site_id = :site_id
                    AND recorded_date = :recorded_date
                """),
                {
                    "site_id": site_id,
                    "recorded_date": recorded_date
                }
            ).scalar()

            if existing > 0:
                skipped += 1
                continue

            # Insert
            db.execute(
                text("""
                    INSERT INTO resource_data
                    (
                        site_id,
                        recorded_date,
                        temperature,
                        ghi,
                        dni,
                        dhi,
                        wind_speed
                    )
                    VALUES
                    (
                        :site_id,
                        :recorded_date,
                        :temperature,
                        :ghi,
                        :dni,
                        :dhi,
                        :wind_speed
                    )
                """),
                {
                    "site_id": site_id,
                    "recorded_date": recorded_date,
                    "temperature": temp_value,
                    "ghi": ghi_value,
                    "dni": dni_value,
                    "dhi": dhi_value,
                    "wind_speed": wind_value
                }
            )

            inserted += 1

            if inserted % 100 == 0:
                print(
                    "Inserted records:",
                    inserted
                )

        db.commit()

        print("\n===================================")
        print("NASA POWER DOWNLOAD COMPLETE")
        print("===================================")

        print("Inserted:", inserted)
        print("Skipped :", skipped)

    except Exception as error:

        db.rollback()

        print("\nERROR:")
        print(error)

        raise

    finally:

        db.close()


if __name__ == "__main__":

    SITE_ID = (
        "2c7a4bb4-1cb0-40b7-ba68-b49c468bb446"
    )

    LATITUDE = 13.0827

    LONGITUDE = 80.2707

    download_nasa_power(
        site_id=SITE_ID,
        latitude=LATITUDE,
        longitude=LONGITUDE,
        start_date="20220101",
        end_date="20261231"
    )