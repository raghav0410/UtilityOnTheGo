# UtilityOnTheGo

Utilities for acquiring and preprocessing solar and wind energy datasets.

## Data acquisition and preprocessing

The `src/data_pipeline.py` module downloads time-series data from the NREL
NSRDB and Wind Toolkit APIs. It merges both sources and adds basic temporal
features such as hour, day of week and month with cyclical encoding.

### Usage

```bash
export NREL_API_KEY=your_api_key
python src/data_pipeline.py <lat> <lon> <year> <start> <end> --out output.csv
```

- `lat`/`lon`: Site coordinates.
- `year`: Year for the NSRDB solar dataset.
- `start`/`end`: Start and end timestamps (YYYYMMDDHH) for wind data.
- `--out`: Path to save the merged CSV file.

The resulting dataset is sorted, interpolated and enriched with temporal
features to facilitate downstream forecasting experiments.
