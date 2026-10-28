"""
SpaceScope Deployment & API Verification Test Suite
Tests serverless entrypoint, API endpoints, schema validity, dataset parsing, and fallback.
"""

import os
import json
import pytest
from flask import Flask

# Root path configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def client():
    """Create test client using the serverless WSGI entrypoint"""
    from api.index import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestDeploymentConfiguration:
    """Validate serverless configuration files and dependency limits"""

    def test_vercel_json_configuration(self):
        """vercel.json exists, is valid JSON, and configures @vercel/python"""
        vercel_path = os.path.join(ROOT_DIR, 'vercel.json')
        assert os.path.exists(vercel_path), "vercel.json must exist in project root"
        
        with open(vercel_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        assert config.get('version') == 2
        builds = config.get('builds', [])
        assert any(b.get('use') == '@vercel/python' for b in builds), "Must configure @vercel/python"
        assert any(b.get('src') == 'api/index.py' for b in builds), "Must point to api/index.py"
        assert 'routes' in config or 'rewrites' in config, "Must configure routes/rewrites"

    def test_requirements_serverless_compliance(self):
        """requirements.txt must exclude heavy PySpark/JVM/MongoDB to satisfy Vercel limits"""
        req_path = os.path.join(ROOT_DIR, 'requirements.txt')
        assert os.path.exists(req_path), "requirements.txt must exist"
        
        with open(req_path, 'r', encoding='utf-8') as f:
            lines = [line.strip().lower() for line in f if line.strip() and not line.strip().startswith('#')]
            
        assert not any('pyspark' in line for line in lines), "pyspark must NOT be in serverless requirements.txt"
        assert not any('pymongo' in line for line in lines), "pymongo must NOT be in serverless requirements.txt"
        assert any('flask' in line for line in lines), "flask must be in requirements.txt"
        assert any('pandas' in line for line in lines), "pandas must be in requirements.txt"

    def test_serverless_entrypoint_wsgi_initialization(self):
        """api/index.py exposes WSGI application instance 'app' and 'handler'"""
        from api.index import app, handler
        assert isinstance(app, Flask), "app must be a Flask instance"
        assert handler is app, "handler alias must point to WSGI application"


class TestDataIngestionAndReliability:
    """Validate data loading, date parsing, year extraction, and fallback mechanisms"""

    def test_csv_ingestion_and_year_extraction(self):
        """Space_Corrected.csv loads, parses dates, extracts year with zero KeyError"""
        from data_ingestion import SpaceMissionDataSource
        
        ds = SpaceMissionDataSource()
        csv_path = os.path.join(ROOT_DIR, 'Space_Corrected.csv')
        df = ds.load_from_csv(csv_path)
        
        assert df is not None, "Failed to load Space_Corrected.csv"
        assert len(df) >= 4000, f"Expected 4000+ rows, got {len(df)}"
        
        # Verify required fields are present
        required_cols = ['year', 'country', 'company', 'rocket', 'mission_status', 'launch_site', 'mission_type']
        for col in required_cols:
            assert col in df.columns, f"Required column '{col}' missing from processed dataset"
            
        # Verify year is integer and non-null
        assert df['year'].isnull().sum() == 0, "Year column contains null values"
        assert df['year'].min() == 1957, f"Expected min year 1957, got {df['year'].min()}"
        assert df['year'].max() >= 2020, f"Expected max year >= 2020, got {df['year'].max()}"

    def test_automatic_fallback_on_missing_file(self):
        """load_data gracefully falls back to sample dataset when CSV path is non-existent"""
        from data_ingestion import SpaceMissionDataSource
        
        ds = SpaceMissionDataSource()
        fallback_df = ds.load_data(filepath="non_existent_file_xyz_123.csv")
        
        assert fallback_df is not None
        assert len(fallback_df) == 68, f"Expected 68 sample records on genuine fallback, got {len(fallback_df)}"
        assert 'year' in fallback_df.columns
        assert 'company' in fallback_df.columns
        assert 'mission_status' in fallback_df.columns

    def test_date_extraction_variations(self):
        """_extract_year_and_date handles Kaggle date strings, ISO dates, slashes, and missing values"""
        from data_ingestion import _extract_year_and_date
        import numpy as np

        # Kaggle standard format
        yr, dt = _extract_year_and_date("Fri Aug 07, 2020 05:12 UTC")
        assert yr == 2020 and dt == "2020-08-07"

        # ISO format
        yr, dt = _extract_year_and_date("1969-07-20")
        assert yr == 1969 and dt == "1969-07-20"

        # Slash format
        yr, dt = _extract_year_and_date("1981/04/12")
        assert yr == 1981 and dt == "1981-04-12"

        # Year only
        yr, dt = _extract_year_and_date("Mission in 1995")
        assert yr == 1995 and dt == "1995-01-01"

        # None / NaN / Empty
        yr, dt = _extract_year_and_date(None)
        assert yr == 2020 and dt == "2020-01-01"
        yr, dt = _extract_year_and_date(np.nan)
        assert yr == 2020 and dt == "2020-01-01"
        yr, dt = _extract_year_and_date("")
        assert yr == 2020 and dt == "2020-01-01"


class TestWebAPIEndpoints:
    """Validate all API endpoints return HTTP 200 with schema-valid JSON"""

    def test_root_dashboard_html(self, client):
        """GET / returns HTTP 200 and renders the HTML dashboard"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.content_type
        html = response.get_data(as_text=True)
        assert 'SpaceScope' in html
        assert 'yearlyChart' in html
        assert 'Flight Log Explorer' in html

    def test_health_endpoint(self, client):
        """GET /api/health returns HTTP 200 with status 'healthy'"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('status') == 'healthy'
        assert 'timestamp' in data

    def test_missions_summary_endpoint(self, client):
        """GET /api/missions/summary returns non-null year_range, count, and success rate"""
        response = client.get('/api/missions/summary')
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data.get('total_missions'), int)
        assert data['total_missions'] > 0
        assert isinstance(data.get('success_rate'), (int, float))
        assert 0 <= data['success_rate'] <= 100
        
        year_range = data.get('year_range')
        assert isinstance(year_range, dict)
        assert year_range.get('min') is not None
        assert year_range.get('max') is not None
        assert year_range['min'] <= year_range['max']

    def test_missions_by_year_endpoint(self, client):
        """GET /api/missions/by-year returns sorted years and corresponding counts"""
        response = client.get('/api/missions/by-year')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        years = data['data'].get('years', [])
        counts = data['data'].get('counts', [])
        
        assert len(years) > 0
        assert len(years) == len(counts)
        assert years == sorted(years), "Years array must be sorted chronologically"
        assert all(isinstance(y, int) for y in years)
        assert all(isinstance(c, int) for c in counts)

    def test_missions_by_organization_endpoint(self, client):
        """GET /api/missions/by-organization returns HTTP 200 with valid data arrays"""
        response = client.get('/api/missions/by-organization')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        orgs = data['data'].get('organizations', [])
        counts = data['data'].get('counts', [])
        
        assert len(orgs) > 0
        assert len(orgs) == len(counts)
        assert all(isinstance(o, str) for o in orgs)
        assert all(isinstance(c, int) for c in counts)

    def test_missions_by_rocket_endpoint(self, client):
        """GET /api/missions/by-rocket returns HTTP 200 with valid data arrays"""
        response = client.get('/api/missions/by-rocket')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        rockets = data['data'].get('rockets', [])
        counts = data['data'].get('counts', [])
        
        assert len(rockets) > 0
        assert len(rockets) == len(counts)

    def test_missions_by_type_endpoint(self, client):
        """GET /api/missions/by-type returns HTTP 200 with valid data arrays"""
        response = client.get('/api/missions/by-type')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        types = data['data'].get('types', [])
        counts = data['data'].get('counts', [])
        
        assert len(types) > 0
        assert len(types) == len(counts)

    def test_missions_by_country_endpoint(self, client):
        """GET /api/missions/by-country returns HTTP 200 with valid data arrays"""
        response = client.get('/api/missions/by-country')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        countries = data['data'].get('countries', [])
        counts = data['data'].get('counts', [])
        
        assert len(countries) > 0
        assert len(countries) == len(counts)

    def test_missions_outcome_endpoint(self, client):
        """GET /api/missions/outcome returns HTTP 200 with valid data arrays"""
        response = client.get('/api/missions/outcome')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        statuses = data['data'].get('statuses', [])
        counts = data['data'].get('counts', [])
        
        assert len(statuses) > 0
        assert len(statuses) == len(counts)
        assert any('Success' in s for s in statuses)

    def test_missions_list_paginated_endpoint(self, client):
        """GET /api/missions/list returns HTTP 200 with pagination metadata"""
        response = client.get('/api/missions/list?page=1&limit=20')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) == 20
        
        pagination = data.get('pagination', {})
        assert pagination.get('page') == 1
        assert pagination.get('limit') == 20
        assert pagination.get('total') >= 4000

    def test_additional_analytics_endpoints(self, client):
        """GET /api/organizations, /api/rockets, /api/analytics/dashboard return 200"""
        r_org = client.get('/api/organizations')
        assert r_org.status_code == 200
        assert 'data' in r_org.get_json()

        r_rock = client.get('/api/rockets')
        assert r_rock.status_code == 200
        assert 'data' in r_rock.get_json()

        r_dash = client.get('/api/analytics/dashboard')
        assert r_dash.status_code == 200
        dash_data = r_dash.get_json()
        assert 'kpis' in dash_data
        assert 'charts' in dash_data

    def test_not_found_endpoint(self, client):
        """Calling non-existent endpoint returns HTTP 404 JSON response"""
        response = client.get('/api/non_existent_route')
        assert response.status_code == 404
        assert response.get_json() == {'error': 'Endpoint not found'}


class TestEdgeCasesAndBoundaries:
    """Validate boundary values, pagination limits, and sample dataset behavior"""

    def test_pagination_boundary_cases(self, client):
        """Page beyond total returns empty list, page=0 clamps to page=1, limit is capped"""
        # Page far beyond total
        r_beyond = client.get('/api/missions/list?page=99999&limit=10')
        assert r_beyond.status_code == 200
        data_beyond = r_beyond.get_json()
        assert data_beyond['data'] == []
        assert data_beyond['pagination']['page'] == 99999

        # Page 0 should clamp to 1
        r_zero = client.get('/api/missions/list?page=0&limit=5')
        assert r_zero.status_code == 200
        data_zero = r_zero.get_json()
        assert data_zero['pagination']['page'] == 1
        assert len(data_zero['data']) == 5

        # Limit beyond 100 should cap at 100
        r_cap = client.get('/api/missions/list?page=1&limit=500')
        assert r_cap.status_code == 200
        data_cap = r_cap.get_json()
        assert len(data_cap['data']) == 100
        assert data_cap['pagination']['limit'] == 100

    def test_api_behavior_with_fallback_sample_data(self):
        """When forced to use fallback sample data, all endpoints return valid HTTP 200 with 68 sample records"""
        from flask_api import SpaceScopeAPI
        
        # Initialize API instance with an intentionally missing CSV path to force fallback
        fallback_api = SpaceScopeAPI(data_filepath="forced_missing_path_abc.csv")
        test_client = fallback_api.app.test_client()

        # Health check
        r_health = test_client.get('/api/health')
        assert r_health.status_code == 200
        health_data = r_health.get_json()
        assert health_data.get('status') == 'healthy'
        assert health_data.get('records_loaded') == 68

        # Summary check
        r_sum = test_client.get('/api/missions/summary')
        assert r_sum.status_code == 200
        sum_data = r_sum.get_json()
        assert sum_data['total_missions'] == 68
        assert sum_data['year_range']['min'] is not None
        assert sum_data['year_range']['max'] is not None

        # By-year check (no KeyError: 'year')
        r_yr = test_client.get('/api/missions/by-year')
        assert r_yr.status_code == 200
        yr_data = r_yr.get_json()
        assert len(yr_data['data']['years']) > 0

        # Outcome check
        r_out = test_client.get('/api/missions/outcome')
        assert r_out.status_code == 200
        out_data = r_out.get_json()
        assert len(out_data['data']['statuses']) > 0

        # All other endpoints with fallback data
        for endpoint in ['/api/missions/by-organization', '/api/missions/by-rocket', 
                         '/api/missions/by-type', '/api/missions/by-country',
                         '/api/missions/list', '/api/organizations', 
                         '/api/rockets', '/api/analytics/dashboard']:
            res = test_client.get(endpoint)
            assert res.status_code == 200, f"Endpoint {endpoint} failed with fallback data: {res.status_code}"
            assert 'data' in res.get_json() or 'kpis' in res.get_json()

        # Root dashboard check
        r_dash = test_client.get('/')
        assert r_dash.status_code == 200
        assert 'SpaceScope' in r_dash.get_data(as_text=True)

    def test_missions_list_search_filtering(self, client):
        """GET /api/missions/list?search=... performs case-insensitive search across records"""
        # Search for known rockets
        r_search = client.get('/api/missions/list?search=Falcon&limit=10')
        assert r_search.status_code == 200
        data_search = r_search.get_json()
        assert len(data_search['data']) > 0
        assert any('Falcon' in m.get('rocket', '') or 'Falcon' in m.get('detail', '') for m in data_search['data'])

        # Search for non-existent keyword returns empty list cleanly without 500 error
        r_empty = client.get('/api/missions/list?search=NonExistentKeywordXYZ999')
        assert r_empty.status_code == 200
        data_empty = r_empty.get_json()
        assert data_empty['data'] == []
        assert data_empty['pagination']['total'] == 0
        assert data_empty['pagination']['total_pages'] == 1

    def test_negative_and_zero_query_limits(self, client):
        """Endpoints safely clamp non-positive limits to default 10 instead of slicing inversely"""
        for ep in ['/api/missions/by-organization', '/api/missions/by-rocket', '/api/missions/by-country']:
            r_neg = client.get(f"{ep}?limit=-5")
            assert r_neg.status_code == 200
            json_neg = r_neg.get_json()
            assert len(list(json_neg['data'].values())[0]) == 10

            r_zero = client.get(f"{ep}?limit=0")
            assert r_zero.status_code == 200
            json_zero = r_zero.get_json()
            assert len(list(json_zero['data'].values())[0]) == 10

    def test_static_asset_serving(self, client):
        """Local static assets exist and are served cleanly for air-gapped environments"""
        r_static = client.get('/static/js/chart.umd.min.js')
        assert r_static.status_code == 200
        assert len(r_static.data) > 100000

    def test_method_not_allowed_handler(self, client):
        """POST on GET-only routes returns HTTP 405 Method Not Allowed JSON"""
        r_post = client.post('/api/health')
        assert r_post.status_code == 405
        assert r_post.get_json() == {'error': 'Method not allowed'}

