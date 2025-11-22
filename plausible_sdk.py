"""
Plausible Analytics API SDK
A lightweight SDK for interacting with Plausible Analytics Stats API
"""

import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json


class PlausibleAPIError(Exception):
    """Custom exception for Plausible API errors"""
    pass


class PlausibleClient:
    """Client for interacting with Plausible Analytics API"""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Plausible API client

        Args:
            base_url: Base URL of your Plausible instance (e.g., 'https://plausible.io')
            api_key: Your Plausible API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def list_sites(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        List all sites accessible to your account

        Args:
            limit: Maximum number of sites to return (default: 100)

        Returns:
            List of site dictionaries with 'domain' and 'timezone' keys
        """
        url = f'{self.base_url}/api/v1/sites'
        params = {'limit': limit}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('sites', [])
        except requests.exceptions.RequestException as e:
            raise PlausibleAPIError(f"Failed to list sites: {str(e)}")

    def query_stats(
        self,
        site_id: str,
        metrics: List[str],
        date_range: Union[str, List[str]],
        dimensions: Optional[List[str]] = None,
        filters: Optional[List[List[Any]]] = None,
        order_by: Optional[List[Union[str, List[str]]]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query stats for a specific site

        Args:
            site_id: Domain of the site (e.g., 'example.com')
            metrics: List of metrics to query (e.g., ['visitors', 'pageviews', 'bounce_rate'])
            date_range: Date range as string (e.g., '7d', 'day', 'month') or list ['YYYY-MM-DD', 'YYYY-MM-DD']
            dimensions: Optional list of dimensions to group by
            filters: Optional list of filters
            order_by: Optional ordering specification
            limit: Optional limit on number of results

        Returns:
            Dictionary containing query results, metadata, and query info
        """
        url = f'{self.base_url}/api/v2/query'

        query = {
            'site_id': site_id,
            'metrics': metrics,
            'date_range': date_range
        }

        if dimensions:
            query['dimensions'] = dimensions
        if filters:
            query['filters'] = filters
        if order_by:
            query['order_by'] = order_by
        if limit:
            query['limit'] = limit

        try:
            response = requests.post(url, headers=self.headers, json=query)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PlausibleAPIError(f"Failed to query stats for {site_id}: {str(e)}")

    def get_last_24h_stats(
        self,
        site_id: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get stats for the last 24 hours for a specific site

        Args:
            site_id: Domain of the site
            metrics: List of metrics (defaults to common metrics)

        Returns:
            Dictionary with stats for the last 24 hours
        """
        if metrics is None:
            metrics = [
                'visitors',
                'visits',
                'pageviews',
                'views_per_visit',
                'bounce_rate',
                'visit_duration'
            ]

        return self.query_stats(site_id, metrics, 'day')

    def get_period_stats(
        self,
        site_id: str,
        period: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get stats for a specific period for a site

        Args:
            site_id: Domain of the site
            period: Period string ('day', '7d', '30d', 'month', '6mo', '12mo')
            metrics: List of metrics (defaults to common metrics)

        Returns:
            Dictionary with stats for the specified period
        """
        if metrics is None:
            metrics = [
                'visitors',
                'visits',
                'pageviews',
                'views_per_visit',
                'bounce_rate',
                'visit_duration'
            ]

        return self.query_stats(site_id, metrics, period)

    def get_all_sites_stats(
        self,
        date_range: Union[str, List[str]] = 'day',
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get stats for all sites

        Args:
            date_range: Date range as string or list (defaults to 'day' for last 24h)
            metrics: List of metrics (defaults to common metrics)

        Returns:
            Dictionary mapping site domains to their stats
        """
        if metrics is None:
            metrics = [
                'visitors',
                'visits',
                'pageviews',
                'views_per_visit',
                'bounce_rate',
                'visit_duration'
            ]

        sites = self.list_sites()
        results = {}

        for site in sites:
            domain = site['domain']
            try:
                stats = self.query_stats(domain, metrics, date_range)
                results[domain] = {
                    'success': True,
                    'timezone': site.get('timezone'),
                    'stats': stats
                }
            except PlausibleAPIError as e:
                results[domain] = {
                    'success': False,
                    'error': str(e)
                }

        return results

    def format_stats_summary(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format stats data into a clean summary

        Args:
            stats_data: Raw stats data from query

        Returns:
            Formatted summary dictionary
        """
        if 'results' not in stats_data or not stats_data['results']:
            return {'metrics': {}}

        # For aggregate queries (no dimensions), there's typically one result row
        result = stats_data['results'][0] if stats_data['results'] else {}

        # Remove dimensions if present, keep only metrics
        metrics = {k: v for k, v in result.items() if k not in ['dimensions']}

        return {
            'metrics': metrics,
            'query_info': stats_data.get('meta', {})
        }
