#!/usr/bin/env python3
"""
Plausible Analytics Stats Fetcher
Fetches stats from Plausible Analytics and outputs formatted JSON
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from plausible_sdk import PlausibleClient, PlausibleAPIError


def load_config():
    """Load configuration from environment variables"""
    # Load .env file if it exists
    load_dotenv()

    base_url = os.getenv('PLAUSIBLE_BASE_URL')
    api_key = os.getenv('PLAUSIBLE_API_KEY')

    if not base_url:
        raise ValueError("PLAUSIBLE_BASE_URL environment variable is required")
    if not api_key:
        raise ValueError("PLAUSIBLE_API_KEY environment variable is required")

    return {
        'base_url': base_url,
        'api_key': api_key,
        'output_dir': os.getenv('OUTPUT_DIR', './output')
    }


def save_to_file(data: dict, output_dir: str, filename: str = None):
    """Save data to JSON file"""
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'plausible_stats_{timestamp}.json'

    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    return filepath


def fetch_all_sites_stats(client: PlausibleClient, period: str = 'day', save_output: bool = False, output_dir: str = './output'):
    """
    Fetch stats for all sites

    Args:
        client: PlausibleClient instance
        period: Time period for stats (default: 'day' for last 24h)
        save_output: Whether to save output to file
        output_dir: Directory to save output files
    """
    print(f"Fetching stats for all sites (period: {period})...", file=sys.stderr)

    try:
        stats = client.get_all_sites_stats(date_range=period)

        # Create summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'period': period,
            'total_sites': len(stats),
            'successful': sum(1 for s in stats.values() if s.get('success')),
            'failed': sum(1 for s in stats.values() if not s.get('success')),
            'sites': {}
        }

        # Format each site's stats
        for domain, site_data in stats.items():
            if site_data.get('success'):
                formatted = client.format_stats_summary(site_data['stats'])
                summary['sites'][domain] = {
                    'timezone': site_data.get('timezone'),
                    'metrics': formatted['metrics']
                }
            else:
                summary['sites'][domain] = {
                    'error': site_data.get('error')
                }

        # Output JSON
        print(json.dumps(summary, indent=2))

        # Save to file if requested
        if save_output:
            filepath = save_to_file(summary, output_dir)
            print(f"\nStats saved to: {filepath}", file=sys.stderr)

        return summary

    except PlausibleAPIError as e:
        print(f"Error fetching stats: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_site_stats(client: PlausibleClient, site_id: str, period: str = 'day', save_output: bool = False, output_dir: str = './output'):
    """
    Fetch stats for a specific site

    Args:
        client: PlausibleClient instance
        site_id: Domain of the site
        period: Time period for stats
        save_output: Whether to save output to file
        output_dir: Directory to save output files
    """
    print(f"Fetching stats for {site_id} (period: {period})...", file=sys.stderr)

    try:
        stats = client.get_period_stats(site_id, period)
        formatted = client.format_stats_summary(stats)

        result = {
            'timestamp': datetime.now().isoformat(),
            'site': site_id,
            'period': period,
            'metrics': formatted['metrics']
        }

        # Output JSON
        print(json.dumps(result, indent=2))

        # Save to file if requested
        if save_output:
            filename = f'plausible_stats_{site_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            filepath = save_to_file(result, output_dir, filename)
            print(f"\nStats saved to: {filepath}", file=sys.stderr)

        return result

    except PlausibleAPIError as e:
        print(f"Error fetching stats for {site_id}: {e}", file=sys.stderr)
        sys.exit(1)


def list_sites(client: PlausibleClient):
    """List all available sites"""
    print("Fetching list of sites...", file=sys.stderr)

    try:
        sites = client.list_sites()

        result = {
            'timestamp': datetime.now().isoformat(),
            'total_sites': len(sites),
            'sites': sites
        }

        print(json.dumps(result, indent=2))
        return result

    except PlausibleAPIError as e:
        print(f"Error listing sites: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch stats from Plausible Analytics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch last 24h stats for all sites
  python fetch_stats.py --all

  # Fetch last 7 days stats for all sites
  python fetch_stats.py --all --period 7d

  # Fetch stats for a specific site
  python fetch_stats.py --site example.com --period 30d

  # List all sites
  python fetch_stats.py --list

  # Save output to file
  python fetch_stats.py --all --save

Period options:
  day    - Last 24 hours (default)
  7d     - Last 7 days
  30d    - Last 30 days
  month  - Current month
  6mo    - Last 6 months
  12mo   - Last 12 months
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Fetch stats for all sites'
    )

    parser.add_argument(
        '--site',
        type=str,
        help='Fetch stats for a specific site (domain)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available sites'
    )

    parser.add_argument(
        '--period',
        type=str,
        default='day',
        help='Time period for stats (default: day). Options: day, 7d, 30d, month, 6mo, 12mo'
    )

    parser.add_argument(
        '--save',
        action='store_true',
        help='Save output to JSON file'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save output files (overrides OUTPUT_DIR env var)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not (args.all or args.site or args.list):
        parser.error("One of --all, --site, or --list is required")

    try:
        # Load configuration
        config = load_config()

        # Override output_dir if specified
        if args.output_dir:
            config['output_dir'] = args.output_dir

        # Initialize client
        client = PlausibleClient(config['base_url'], config['api_key'])

        # Execute requested action
        if args.list:
            list_sites(client)
        elif args.all:
            fetch_all_sites_stats(client, args.period, args.save, config['output_dir'])
        elif args.site:
            fetch_site_stats(client, args.site, args.period, args.save, config['output_dir'])

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
