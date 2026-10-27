# SpaceScope

A small space-themed Streamlit dashboard for exploring mission launches. MongoDB is
the app's only database. Launch records are imported from the trusted Hugging Face
dataset [`juliensimon/space-launch-log`](https://huggingface.co/datasets/juliensimon/space-launch-log).

## Run locally

1. Install the project dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Start MongoDB locally, or set `MONGO_URI` to your MongoDB Atlas connection string.
   Optionally set `MONGO_DB` (defaults to `spacescope`).

3. Download the launch dataset and import it into MongoDB:

   ```powershell
   python load_data.py
   ```

   The loader uses `load_dataset("juliensimon/space-launch-log", "launches")`.
   The initial run needs an internet connection. It can be run again safely to
   update existing records.

4. Start the dashboard:

   ```powershell
   streamlit run app.py
   ```

The dashboard includes organization, vehicle, mission, flight, site-code, category,
and available-year filters; eight dynamically calculated KPI cards; search; sorting;
and paginated mission records. Its tabs provide an overview, organization analytics
(bar, horizontal bar, pie, and donut chart selector), vehicle analytics (top 5/10/20
rankings, chart selector, and orbital-payload histogram), mission trends, data quality,
and the mission log. Organization/category comparisons use a treemap and stacked or
grouped bar chart. MongoDB reads are cached for five minutes; filtering and chart
calculations reuse that cached collection read.

The source has 76,015 launch-log rows and fields such as `agency`, `lv_type`,
`mission`, `flight`, `launch_site`, and `category`. Its `launch_date` values are
mostly labels, and its sparsely populated `launch_jd` values are inconsistent, so
neither is converted to a calendar date. There is no standardized mission outcome
or country field. The dashboard omits time-series and scatter plots when reliable
source values cannot support them, and explains those limitations rather than
inventing values. The importer preserves source launch labels, Julian-day values,
codes, and available numeric source fields without treating them as dates or
outcomes. Missing values appear as `N/A` in the mission log. Re-importing updates
the existing source records with newly mapped fields, removes stale records from
older importer versions, and preserves duplicate source rows.
