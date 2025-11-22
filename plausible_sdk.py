"""
Plausible Analytics API SDK
A lightweight SDK for interacting with Plausible Analytics Stats API
"""

import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import time


class PlausibleAPIError(Exception):
    """Custom exception for Plausible API errors"""
    pass


class PlausibleRateLimitError(PlausibleAPIError):
    """Exception raised when API rate limit is exceeded"""
    pass


class PlausibleClient:
    """Client for interacting with Plausible Analytics API"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30, max_retries: int = 3):
        """
        Initialize Plausible API client

        Args:
            base_url: Base URL of your Plausible instance (e.g., 'https://plausible.io')
            api_key: Your Plausible API key
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)

        Raises:
            ValueError: If base_url or api_key is empty or invalid
        """
        if not base_url or not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty string")
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("api_key must be a non-empty string")

        self.base_url = base_url.strip().rstrip('/')
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            params: Query parameters
            json_data: JSON body data
            retry_count: Current retry attempt

        Returns:
            Parsed JSON response

        Raises:
            PlausibleAPIError: On API errors
            PlausibleRateLimitError: On rate limit errors
        """
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=self.timeout
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise PlausibleRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )

            # Handle authentication errors
            if response.status_code == 401:
                raise PlausibleAPIError("Authentication failed. Check your API key")

            # Handle forbidden
            if response.status_code == 403:
                raise PlausibleAPIError("Access forbidden. Check API key permissions")

            # Handle not found
            if response.status_code == 404:
                raise PlausibleAPIError(f"Resource not found: {url}")

            # Raise for other HTTP errors
            response.raise_for_status()

            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise PlausibleAPIError(f"Invalid JSON response from API: {str(e)}")

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                time.sleep(wait_time)
                return self._make_request(method, url, params, json_data, retry_count + 1)
            raise PlausibleAPIError(f"Request timeout after {self.timeout} seconds")

        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                time.sleep(wait_time)
                return self._make_request(method, url, params, json_data, retry_count + 1)
            raise PlausibleAPIError(f"Connection error: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise PlausibleAPIError(f"Request failed: {str(e)}")
        except PlausibleRateLimitError:
            raise  # Re-raise rate limit errors without wrapping
        except PlausibleAPIError:
            raise  # Re-raise our custom errors without wrapping

    def list_sites(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        List all sites accessible to your account

        Args:
            limit: Maximum number of sites to return (default: 100)

        Returns:
            List of site dictionaries with 'domain' and 'timezone' keys

        Raises:
            ValueError: If limit is invalid
            PlausibleAPIError: On API errors
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")

        url = f'{self.base_url}/api/v1/sites'
        params = {'limit': limit}

        try:
            data = self._make_request('GET', url, params=params)
            sites = data.get('sites', [])

            # Validate response structure
            if not isinstance(sites, list):
                raise PlausibleAPIError("Invalid response format: 'sites' is not a list")

            return sites
        except PlausibleAPIError:
            raise
        except Exception as e:
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

        Raises:
            ValueError: If parameters are invalid
            PlausibleAPIError: On API errors
        """
        # Validate inputs
        if not site_id or not isinstance(site_id, str) or not site_id.strip():
            raise ValueError("site_id must be a non-empty string")

        if not metrics or not isinstance(metrics, list) or len(metrics) == 0:
            raise ValueError("metrics must be a non-empty list")

        if not date_range:
            raise ValueError("date_range is required")

        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer")

        url = f'{self.base_url}/api/v2/query'

        query = {
            'site_id': site_id.strip(),
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
            data = self._make_request('POST', url, json_data=query)

            # Validate response structure
            if not isinstance(data, dict):
                raise PlausibleAPIError("Invalid response format: expected dictionary")

            if 'results' not in data:
                raise PlausibleAPIError("Invalid response format: missing 'results' field")

            return data
        except PlausibleAPIError:
            raise
        except Exception as e:
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

        Raises:
            PlausibleAPIError: If unable to list sites
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

        try:
            sites = self.list_sites()
        except PlausibleAPIError as e:
            raise PlausibleAPIError(f"Failed to list sites for stats collection: {str(e)}")

        if not sites:
            return {}

        results = {}

        for site in sites:
            # Safely get domain with validation
            domain = site.get('domain')
            if not domain:
                continue

            try:
                stats = self.query_stats(domain, metrics, date_range)
                results[domain] = {
                    'success': True,
                    'timezone': site.get('timezone'),
                    'stats': stats
                }
            except (PlausibleAPIError, ValueError) as e:
                results[domain] = {
                    'success': False,
                    'error': str(e)
                }
            except Exception as e:
                results[domain] = {
                    'success': False,
                    'error': f"Unexpected error: {str(e)}"
                }

        return results

    def format_stats_summary(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format stats data into a clean summary

        Args:
            stats_data: Raw stats data from query

        Returns:
            Formatted summary dictionary

        Raises:
            ValueError: If stats_data is invalid
        """
        if not isinstance(stats_data, dict):
            raise ValueError("stats_data must be a dictionary")

        if 'results' not in stats_data or not stats_data['results']:
            return {'metrics': {}, 'query_info': stats_data.get('meta', {})}

        results = stats_data['results']
        if not isinstance(results, list):
            raise ValueError("stats_data['results'] must be a list")

        # For aggregate queries (no dimensions), there's typically one result row
        result = results[0] if results else {}

        if not isinstance(result, dict):
            return {'metrics': {}, 'query_info': stats_data.get('meta', {})}

        # Remove dimensions if present, keep only metrics
        metrics = {k: v for k, v in result.items() if k not in ['dimensions']}

        return {
            'metrics': metrics,
            'query_info': stats_data.get('meta', {})
        }
