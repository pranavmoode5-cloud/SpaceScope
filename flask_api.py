"""
SpaceScope: Big Data Analytics of Global Space Missions
Flask REST API Backend & Interactive Web Dashboard
Serves data to frontend dashboard and serverless clients
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
from flask import Flask, jsonify, request, render_template, render_template_string
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')


class SpaceScopeAPI:
    """Flask API & Dashboard service for SpaceScope"""
    
    def __init__(self, data_filepath=None):
        """Initialize Flask app, templates, and load data"""
        self.app = Flask(
            __name__,
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR
        )
        CORS(self.app)  # Enable CORS for frontend access
        
        self.data_filepath = data_filepath
        self.missions_df = None
        
        # Load data
        self.load_data()
        
        # Register routes
        self.register_routes()
        
        logger.info("✅ SpaceScope API initialized")
    
    def load_data(self):
        """Load processed data with automatic fallback"""
        try:
            from data_ingestion import SpaceMissionDataSource
            data_source = SpaceMissionDataSource()
            self.missions_df = data_source.load_data(self.data_filepath)
            
            # Defensive check: ensure all required columns are present and clean
            if self.missions_df is not None and not self.missions_df.empty:
                defaults = {
                    'year': 2020,
                    'company': 'Unknown',
                    'rocket': 'Unknown',
                    'launch_date': '2020-01-01',
                    'country': 'Unknown',
                    'launch_site': 'Unknown',
                    'mission_status': 'Success',
                    'mission_type': 'Commercial',
                    'detail': ''
                }
                for col, dval in defaults.items():
                    if col not in self.missions_df.columns:
                        self.missions_df[col] = dval
                    else:
                        self.missions_df[col] = self.missions_df[col].fillna(dval)
                self.missions_df['year'] = pd.to_numeric(self.missions_df['year'], errors='coerce').fillna(2020).astype(int)
                    
            logger.info(f"✅ Data loaded successfully: {len(self.missions_df) if self.missions_df is not None else 0} records")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            try:
                from data_ingestion import SpaceMissionDataSource
                data_source = SpaceMissionDataSource()
                self.missions_df = data_source.create_sample_dataset()
                logger.info("✅ Loaded fallback sample dataset")
            except Exception as e_fallback:
                logger.error(f"Fallback also failed: {e_fallback}")
                self.missions_df = None
    
    def register_routes(self):
        """Register API and dashboard routes"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            """Serve interactive web dashboard interface"""
            try:
                return render_template('index.html')
            except Exception as e:
                logger.warning(f"render_template failed ({e}), attempting direct file read fallback")
                html_path = os.path.join(TEMPLATE_DIR, 'index.html')
                if os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        return render_template_string(f.read())
                return "<h1>SpaceScope Dashboard</h1><p>Dashboard interface loading error.</p>", 500

        @self.app.route('/api/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'SpaceScope API',
                'timestamp': datetime.now().isoformat(),
                'records_loaded': len(self.missions_df) if self.missions_df is not None else 0
            })
        
        @self.app.route('/api/missions/summary', methods=['GET'])
        def missions_summary():
            """Get missions summary statistics"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            total = len(self.missions_df)
            success_count = int((self.missions_df['mission_status'] == 'Success').sum())
            success_rate = round((success_count / total * 100), 2) if total > 0 else 0.0

            valid_years = self.missions_df['year'].dropna()
            min_year = int(valid_years.min()) if not valid_years.empty else 0
            max_year = int(valid_years.max()) if not valid_years.empty else 0

            summary = {
                'total_missions': total,
                'success_rate': success_rate,
                'unique_organizations': int(self.missions_df['company'].nunique()),
                'unique_rockets': int(self.missions_df['rocket'].nunique()),
                'unique_countries': int(self.missions_df['country'].nunique()),
                'unique_launch_sites': int(self.missions_df['launch_site'].nunique()),
                'year_range': {
                    'min': min_year,
                    'max': max_year
                }
            }
            
            return jsonify(summary)
        
        @self.app.route('/api/missions/by-year', methods=['GET'])
        def missions_by_year():
            """Get missions grouped by year"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            yearly = self.missions_df.dropna(subset=['year']).groupby('year').size().to_dict()
            sorted_years = sorted(yearly.keys())
            
            return jsonify({
                'data': {
                    'years': [int(k) for k in sorted_years],
                    'counts': [int(yearly[k]) for k in sorted_years]
                }
            })
        
        @self.app.route('/api/missions/by-organization', methods=['GET'])
        def missions_by_org():
            """Get missions grouped by organization"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            limit = request.args.get('limit', 10, type=int)
            if limit is None or limit <= 0:
                limit = 10
            limit = min(limit, 500)
            org_data = self.missions_df.groupby('company').size().sort_values(ascending=False).head(limit)
            
            return jsonify({
                'data': {
                    'organizations': list(org_data.index.astype(str)),
                    'counts': [int(c) for c in org_data.values]
                }
            })
        
        @self.app.route('/api/missions/by-rocket', methods=['GET'])
        def missions_by_rocket():
            """Get missions grouped by rocket"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            limit = request.args.get('limit', 10, type=int)
            if limit is None or limit <= 0:
                limit = 10
            limit = min(limit, 500)
            rocket_data = self.missions_df.groupby('rocket').size().sort_values(ascending=False).head(limit)
            
            return jsonify({
                'data': {
                    'rockets': list(rocket_data.index.astype(str)),
                    'counts': [int(c) for c in rocket_data.values]
                }
            })
        
        @self.app.route('/api/missions/by-type', methods=['GET'])
        def missions_by_type():
            """Get missions grouped by type"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            type_data = self.missions_df.groupby('mission_type').size().sort_values(ascending=False)
            
            return jsonify({
                'data': {
                    'types': list(type_data.index.astype(str)),
                    'counts': [int(c) for c in type_data.values]
                }
            })
        
        @self.app.route('/api/missions/by-country', methods=['GET'])
        def missions_by_country():
            """Get missions grouped by country"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            limit = request.args.get('limit', 10, type=int)
            if limit is None or limit <= 0:
                limit = 10
            limit = min(limit, 500)
            country_data = self.missions_df.groupby('country').size().sort_values(ascending=False).head(limit)
            
            return jsonify({
                'data': {
                    'countries': list(country_data.index.astype(str)),
                    'counts': [int(c) for c in country_data.values]
                }
            })
        
        @self.app.route('/api/missions/outcome', methods=['GET'])
        def missions_outcome():
            """Get mission success/failure distribution"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            outcome = self.missions_df['mission_status'].value_counts()
            
            return jsonify({
                'data': {
                    'statuses': list(outcome.index.astype(str)),
                    'counts': [int(c) for c in outcome.values]
                }
            })
        
        @self.app.route('/api/missions/list', methods=['GET'])
        def missions_list():
            """Get list of missions with pagination and search filter"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            page = max(1, request.args.get('page', 1, type=int))
            limit = max(1, min(100, request.args.get('limit', 50, type=int)))
            search_query = (request.args.get('search') or request.args.get('q') or '').strip().lower()
            
            cols = [c for c in ['company', 'rocket', 'launch_date', 'year', 'country', 'launch_site', 'mission_status', 'mission_type', 'detail'] if c in self.missions_df.columns]
            base_df = self.missions_df[cols] if cols else self.missions_df

            if search_query:
                # Filter across company, rocket, country, launch_site, mission_type, detail, year
                search_mask = (
                    base_df['company'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['rocket'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['country'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['launch_site'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['mission_type'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['detail'].astype(str).str.lower().str.contains(search_query, regex=False) |
                    base_df['year'].astype(str).str.contains(search_query, regex=False)
                )
                filtered_df = base_df[search_mask]
            else:
                filtered_df = base_df

            total_records = len(filtered_df)
            total_pages = max(1, (total_records + limit - 1) // limit)
            
            start = (page - 1) * limit
            end = start + limit
            missions = filtered_df.iloc[start:end].to_dict('records')
            
            return jsonify({
                'data': missions,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_records,
                    'total_pages': total_pages
                }
            })
        
        @self.app.route('/api/organizations', methods=['GET'])
        def organizations():
            """Get organization statistics"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            limit = request.args.get('limit', None, type=int)
            org_stats = self.missions_df.groupby('company').agg(
                mission_count=('rocket', 'count'),
                success_rate=('mission_status', lambda x: round(float((x == 'Success').sum() / len(x) * 100), 2) if len(x) > 0 else 0.0)
            ).sort_values('mission_count', ascending=False)
            
            if limit is not None and limit > 0:
                org_stats = org_stats.head(limit)
            
            return jsonify({
                'data': org_stats.to_dict('index')
            })
        
        @self.app.route('/api/rockets', methods=['GET'])
        def rockets():
            """Get rocket statistics"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            limit = request.args.get('limit', None, type=int)
            rocket_stats = self.missions_df.groupby('rocket').agg(
                usage_count=('company', 'count'),
                success_rate=('mission_status', lambda x: round(float((x == 'Success').sum() / len(x) * 100), 2) if len(x) > 0 else 0.0)
            ).sort_values('usage_count', ascending=False)
            
            if limit is not None and limit > 0:
                rocket_stats = rocket_stats.head(limit)
            
            return jsonify({
                'data': rocket_stats.to_dict('index')
            })
        
        @self.app.route('/api/analytics/dashboard', methods=['GET'])
        def dashboard_data():
            """Get complete dashboard data"""
            if self.missions_df is None or self.missions_df.empty:
                return jsonify({'error': 'No data available'}), 404
            
            total = len(self.missions_df)
            success_count = (self.missions_df['mission_status'] == 'Success').sum()
            success_rate = round(float(success_count / total * 100), 1) if total > 0 else 0.0
            
            dashboard = {
                'kpis': {
                    'total_missions': total,
                    'success_rate': success_rate,
                    'organizations': int(self.missions_df['company'].nunique()),
                    'rockets': int(self.missions_df['rocket'].nunique()),
                    'countries': int(self.missions_df['country'].nunique())
                },
                'charts': {
                    'yearly_trend': self._get_yearly_trend(),
                    'org_distribution': self._get_org_distribution(),
                    'mission_types': self._get_mission_types(),
                    'success_rate': self._get_success_rate()
                }
            }
            
            return jsonify(dashboard)
        
        @self.app.errorhandler(400)
        def bad_request(error):
            """Handle 400 errors"""
            return jsonify({'error': 'Bad request'}), 400

        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors"""
            return jsonify({'error': 'Endpoint not found'}), 404

        @self.app.errorhandler(405)
        def method_not_allowed(error):
            """Handle 405 errors"""
            return jsonify({'error': 'Method not allowed'}), 405
        
        @self.app.errorhandler(500)
        def server_error(error):
            """Handle 500 errors"""
            return jsonify({'error': 'Server error'}), 500
    
    def _get_yearly_trend(self):
        """Get yearly trend data"""
        yearly = self.missions_df.dropna(subset=['year']).groupby('year').size()
        return {
            'labels': [int(y) for y in sorted(yearly.index)],
            'data': [int(yearly[y]) for y in sorted(yearly.index)]
        }
    
    def _get_org_distribution(self):
        """Get organization distribution"""
        orgs = self.missions_df['company'].value_counts().head(8)
        return {
            'labels': list(orgs.index.astype(str)),
            'data': [int(c) for c in orgs.values]
        }
    
    def _get_mission_types(self):
        """Get mission type distribution"""
        types = self.missions_df['mission_type'].value_counts()
        return {
            'labels': list(types.index.astype(str)),
            'data': [int(c) for c in types.values]
        }
    
    def _get_success_rate(self):
        """Get success rate by status"""
        status = self.missions_df['mission_status'].value_counts()
        return {
            'labels': list(status.index.astype(str)),
            'data': [int(c) for c in status.values]
        }
    
    def run(self, debug=False, port=5000, host='0.0.0.0'):
        """Run Flask application"""
        logger.info(f"🚀 Starting SpaceScope API on port {port}")
        print(f"\n🚀 SpaceScope API & Dashboard Server")
        print(f"   Running on: http://localhost:{port}")
        print(f"   Debug mode: {debug}")
        print(f"\n📚 API Endpoints:")
        print(f"   GET /                             - Interactive Web Dashboard")
        print(f"   GET /api/health                   - Health check")
        print(f"   GET /api/missions/summary         - Mission summary")
        print(f"   GET /api/missions/by-year         - Missions by year")
        print(f"   GET /api/missions/by-organization - Missions by org")
        print(f"   GET /api/missions/by-rocket       - Missions by rocket")
        print(f"   GET /api/missions/by-type         - Missions by type")
        print(f"   GET /api/missions/by-country      - Missions by country")
        print(f"   GET /api/missions/outcome         - Success/failure distribution")
        print(f"   GET /api/missions/list            - Mission list (paginated)")
        print(f"   GET /api/organizations            - Organization statistics")
        print(f"   GET /api/rockets                  - Rocket statistics")
        print(f"   GET /api/analytics/dashboard      - Complete dashboard data")
        print(f"\n")
        
        self.app.run(debug=debug, port=port, host=host)


# Expose module-level WSGI application
api = SpaceScopeAPI()
app = api.app


def main():
    """Test Flask API"""
    api.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
