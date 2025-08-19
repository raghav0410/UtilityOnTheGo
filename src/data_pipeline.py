"""Data acquisition and preprocessing utilities for solar and wind datasets."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import requests


@dataclass
class Location:
    """Simple representation of a geographic location."""

    latitude: float
    longitude: float


NREL_SOLAR_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"
NREL_WIND_URL = "https://developer.nrel.gov/api/wind-toolkit/v2/wind/wind-toolkit-download.csv"


def _get_api_key(provided: Optional[str]) -> str:
    """Return an API key either from argument or environment variable."""

    api_key = provided or os.getenv("NREL_API_KEY")
    if not api_key:
        raise ValueError("NREL API key must be supplied via argument or NREL_API_KEY env var")
    return api_key


def fetch_nsrdb(
    location: Location,
    year: int,
    api_key: Optional[str] = None,
    interval: int = 60,
) -> pd.DataFrame:
    """Download solar time-series data from the NSRDB API.

    Parameters
    ----------
    location:
        Location object with latitude and longitude.
    year:
        Year of data to download.
    api_key:
        Optional API key. Uses the ``NREL_API_KEY`` environment variable if omitted.
    interval:
        Data interval in minutes (e.g., 30 or 60).
    """

    params = {
        "api_key": _get_api_key(api_key),
        "wkt": f"POINT({location.longitude} {location.latitude})",
        "names": year,
        "interval": interval,
        "full_name": "Data Pipeline",
        "email": "example@example.com",
        "affiliation": "None",
        "reason": "academic",
        "mailing_list": "false",
        "utc": "true",
    }
    response = requests.get(NREL_SOLAR_URL, params=params, timeout=60)
    response.raise_for_status()

    # The CSV returned by NSRDB has metadata in the first two rows.
    data = pd.read_csv(io.StringIO(response.text), skiprows=2)
    data.rename(columns={"Year": "year", "Month": "month", "Day": "day", "Hour": "hour"}, inplace=True)
    data["timestamp"] = pd.to_datetime(
        data[["year", "month", "day", "hour"]]
    )
    return data.set_index("timestamp").drop(columns=["year", "month", "day", "hour"])


def fetch_wind_toolkit(
    location: Location,
    start: str,
    end: str,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Download wind data from the WIND Toolkit API."""

    params = {
        "api_key": _get_api_key(api_key),
        "wkt": f"POINT({location.longitude} {location.latitude})",
        "start": start,
        "end": end,
        "utc": "true",
    }
    response = requests.get(NREL_WIND_URL, params=params, timeout=60)
    response.raise_for_status()

    data = pd.read_csv(io.StringIO(response.text), skiprows=2)
    data.rename(columns={"Year": "year", "Month": "month", "Day": "day", "Hour": "hour"}, inplace=True)
    data["timestamp"] = pd.to_datetime(
        data[["year", "month", "day", "hour"]]
    )
    return data.set_index("timestamp").drop(columns=["year", "month", "day", "hour"])


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Basic preprocessing: sort, interpolate, and add time features."""

    df = df.sort_index().interpolate(limit_direction="both")
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month

    # Cyclical encoding for hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    return df


def merge_and_preprocess(solar: pd.DataFrame, wind: pd.DataFrame) -> pd.DataFrame:
    """Merge solar and wind data on timestamp and preprocess."""

    combined = solar.join(wind, how="outer", lsuffix="_solar", rsuffix="_wind")
    return preprocess(combined)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Download and preprocess solar and wind data")
    parser.add_argument("lat", type=float, help="Latitude")
    parser.add_argument("lon", type=float, help="Longitude")
    parser.add_argument("year", type=int, help="Year to download")
    parser.add_argument("start", help="Start date for wind data (YYYYMMDDHH)")
    parser.add_argument("end", help="End date for wind data (YYYYMMDDHH)")
    parser.add_argument("--out", default="data.csv", help="Output CSV file")
    args = parser.parse_args()

    location = Location(args.lat, args.lon)
    solar = fetch_nsrdb(location, args.year)
    wind = fetch_wind_toolkit(location, args.start, args.end)
    combined = merge_and_preprocess(solar, wind)
    combined.to_csv(args.out)


if __name__ == "__main__":  # pragma: no cover
    main()
