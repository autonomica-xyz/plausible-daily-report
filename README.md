# Plausible Analytics Stats Fetcher

A lightweight Python SDK and CLI tool for fetching analytics data from Plausible Analytics (including self-hosted Community Edition).

## Features

- 🔌 Mini SDK for querying Plausible Stats API
- 📊 Fetch stats for all sites or individual sites
- ⏰ Support for various time periods (24h, 7d, 30d, etc.)
- 💾 Optional JSON file output
- 🔄 Cron-friendly (outputs to stdout, errors to stderr)
- ⚙️ Configurable via `.env` file

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd plausible-daily-report
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Plausible instance:
```bash
cp .env.example .env
# Edit .env with your Plausible URL and API key
```

## Configuration

Create a `.env` file with the following variables:

```env
# Your Plausible instance URL
PLAUSIBLE_BASE_URL=https://analytics.yourdomain.com

# Your API key (create in Plausible Settings → API Keys)
PLAUSIBLE_API_KEY=your_api_key_here

# Optional: Output directory for saved files
OUTPUT_DIR=./output
```

### Getting Your API Key

1. Log into your Plausible instance
2. Go to Settings → API Keys
3. Create a new API key
4. Copy the key to your `.env` file

## Usage

### Command Line Interface

#### Fetch stats for all sites (last 24 hours):
```bash
python fetch_stats.py --all
```

#### Fetch stats for all sites (last 7 days):
```bash
python fetch_stats.py --all --period 7d
```

#### Fetch stats for a specific site:
```bash
python fetch_stats.py --site example.com --period 30d
```

#### List all available sites:
```bash
python fetch_stats.py --list
```

#### Save output to JSON file:
```bash
python fetch_stats.py --all --save
```

#### Custom output directory:
```bash
python fetch_stats.py --all --save --output-dir /path/to/output
```

### Period Options

- `day` - Last 24 hours (default)
- `7d` - Last 7 days
- `30d` - Last 30 days
- `month` - Current month
- `6mo` - Last 6 months
- `12mo` - Last 12 months

### Using as a Python SDK

```python
from plausible_sdk import PlausibleClient

# Initialize client
client = PlausibleClient(
    base_url='https://analytics.yourdomain.com',
    api_key='your_api_key_here'
)

# List all sites
sites = client.list_sites()
print(sites)

# Get last 24h stats for all sites
stats = client.get_all_sites_stats(date_range='day')
print(stats)

# Get stats for a specific site
site_stats = client.get_period_stats('example.com', period='7d')
print(site_stats)

# Custom query with specific metrics
custom_stats = client.query_stats(
    site_id='example.com',
    metrics=['visitors', 'pageviews', 'bounce_rate'],
    date_range='30d'
)
print(custom_stats)
```

### Advanced SDK Usage

```python
from plausible_sdk import PlausibleClient

client = PlausibleClient(base_url='...', api_key='...')

# Query with dimensions (e.g., top pages)
top_pages = client.query_stats(
    site_id='example.com',
    metrics=['visitors', 'pageviews'],
    date_range='7d',
    dimensions=['event:page'],
    order_by=[['visitors', 'desc']],
    limit=10
)

# Query with filters
filtered_stats = client.query_stats(
    site_id='example.com',
    metrics=['visitors'],
    date_range='30d',
    filters=[['is', 'event:page', ['/blog/*']]]
)

# Get formatted summary
stats = client.get_last_24h_stats('example.com')
summary = client.format_stats_summary(stats)
print(summary['metrics'])
```

## Cron Setup

To run the script automatically via cron:

1. Make the script executable:
```bash
chmod +x fetch_stats.py
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add a cron job (example: daily at 8 AM):
```bash
# Fetch daily stats at 8 AM and save to file
0 8 * * * cd /path/to/plausible-daily-report && /usr/bin/python3 fetch_stats.py --all --save >> /var/log/plausible-stats.log 2>&1
```

4. Or use absolute paths in the cron job:
```bash
# Fetch stats every 6 hours
0 */6 * * * cd /home/user/plausible-daily-report && /usr/bin/python3 fetch_stats.py --all --period day --save
```

### Example Cron Schedules

```bash
# Every day at midnight
0 0 * * * cd /path/to/plausible-daily-report && python3 fetch_stats.py --all --save

# Every Monday at 9 AM (weekly report)
0 9 * * 1 cd /path/to/plausible-daily-report && python3 fetch_stats.py --all --period 7d --save

# Every 1st of the month at 10 AM (monthly report)
0 10 1 * * cd /path/to/plausible-daily-report && python3 fetch_stats.py --all --period month --save
```

## Output Format

### All Sites Stats
```json
{
  "timestamp": "2025-11-22T10:30:00",
  "period": "day",
  "total_sites": 3,
  "successful": 3,
  "failed": 0,
  "sites": {
    "example.com": {
      "timezone": "America/New_York",
      "metrics": {
        "visitors": 1234,
        "visits": 1456,
        "pageviews": 2345,
        "views_per_visit": 1.61,
        "bounce_rate": 45.2,
        "visit_duration": 123
      }
    },
    "another-site.com": {
      "timezone": "UTC",
      "metrics": {
        "visitors": 567,
        "visits": 678,
        "pageviews": 890,
        "views_per_visit": 1.31,
        "bounce_rate": 52.1,
        "visit_duration": 98
      }
    }
  }
}
```

### Single Site Stats
```json
{
  "timestamp": "2025-11-22T10:30:00",
  "site": "example.com",
  "period": "7d",
  "metrics": {
    "visitors": 8765,
    "visits": 9876,
    "pageviews": 15432,
    "views_per_visit": 1.56,
    "bounce_rate": 48.3,
    "visit_duration": 145
  }
}
```

## Available Metrics

The SDK supports all Plausible metrics:

- `visitors` - Unique visitors
- `visits` - Total visits
- `pageviews` - Total pageviews
- `views_per_visit` - Average pageviews per visit
- `bounce_rate` - Bounce rate percentage
- `visit_duration` - Average visit duration in seconds
- `events` - Custom events count
- `conversion_rate` - Conversion rate for goals

## Error Handling

The script outputs errors to stderr and exits with non-zero status codes:

```bash
# Check if script succeeded
if python fetch_stats.py --all; then
    echo "Success!"
else
    echo "Failed with exit code $?"
fi
```

## Troubleshooting

### Authentication Errors
- Verify your API key is correct in `.env`
- Check that the API key has the necessary permissions
- Ensure your Plausible instance URL is correct

### Connection Errors
- Verify your Plausible instance is accessible
- Check firewall rules if using self-hosted version
- Ensure the base URL doesn't have a trailing slash

### No Data Returned
- Verify the site domain is correctly configured in Plausible
- Check that the site has received traffic in the requested period
- Ensure your API key has access to the site

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Resources

- [Plausible Stats API Documentation](https://plausible.io/docs/stats-api)
- [Plausible Sites API Documentation](https://plausible.io/docs/sites-api)
- [Plausible Community Edition](https://plausible.io/self-hosted-web-analytics)
