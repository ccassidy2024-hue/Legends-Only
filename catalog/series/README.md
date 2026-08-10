# Series catalog

One YAML metadata file per series. Do not maintain a single giant catalog by hand.

- Start from `_template.yaml`
- Filename stem must equal `series_id`
- Populate only known values; use `null` / `unknown` / `TODO` otherwise
- **Do not invent** source IDs or publication delays
- `catalog/catalog.csv` is a generated artifact (gitignored)

Load via `python -m grainsys.catalog` or `grainsys.catalog.load_catalog()`.
