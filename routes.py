import logging
from datetime import datetime, timedelta
from flask import render_template, jsonify, request
from models import Tender, ScrapingLog
from scraper import run_scraper
from sqlalchemy import desc, func
from app import db

logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/')
    def index():
        """Home page route"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard page route"""
        return render_template('dashboard.html')
    
    @app.route('/tenders')
    def tenders():
        """Tenders page route"""
        return render_template('tenders.html')
    
    @app.route('/api/tenders')
    def api_tenders():
        """API endpoint to get tenders with pagination and filtering"""
        try:
            # Always return all tenders by default for better performance with client-side DataTables
            page = 1
            per_page = 300
            search = request.args.get('search', '')
            organization = request.args.get('organization', '')
            tender_type = request.args.get('tender_type', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Build the query
            query = Tender.query
            
            # Apply filters
            if search:
                query = query.filter(Tender.tender_title.ilike(f'%{search}%') | 
                                    Tender.reference_number.ilike(f'%{search}%') |
                                    Tender.organization.ilike(f'%{search}%'))
            
            if organization:
                query = query.filter(Tender.organization.ilike(f'%{organization}%'))
            
            if tender_type:
                query = query.filter(Tender.tender_type.ilike(f'%{tender_type}%'))
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(Tender.publication_date >= date_from_obj)
                except ValueError:
                    logger.warning(f"Invalid date_from format: {date_from}")
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                    # Add one day to include the end date
                    date_to_obj = date_to_obj + timedelta(days=1)
                    query = query.filter(Tender.publication_date <= date_to_obj)
                except ValueError:
                    logger.warning(f"Invalid date_to format: {date_to}")
            
            # Order by publication date (newest first)
            query = query.order_by(Tender.publication_date.desc())
            
            # Paginate the results
            paginated_tenders = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Format the response
            result = {
                'tenders': [tender.to_dict() for tender in paginated_tenders.items],
                'total': paginated_tenders.total,
                'pages': paginated_tenders.pages,
                'current_page': page
            }
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error fetching tenders: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tenders/<tender_id>')
    def api_tender_details(tender_id):
        """API endpoint to get details of a specific tender"""
        try:
            tender = Tender.query.filter_by(tender_id=tender_id).first()
            
            if not tender:
                return jsonify({'error': 'Tender not found'}), 404
            
            return jsonify(tender.to_dict())
        except Exception as e:
            logger.error(f"Error fetching tender details: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats')
    def api_stats():
        """API endpoint to get statistics for the dashboard"""
        try:
            # Get total number of tenders
            total_tenders = Tender.query.count()
            
            # Get tenders by type
            tenders_by_type = db.session.query(
                Tender.tender_type, 
                func.count(Tender.id).label('count')
            ).group_by(Tender.tender_type).all()
            
            # Get tenders by organization (top 10)
            tenders_by_org = db.session.query(
                Tender.organization, 
                func.count(Tender.id).label('count')
            ).group_by(Tender.organization).order_by(desc('count')).limit(10).all()
            
            # Get tenders by date (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            tenders_by_date = db.session.query(
                func.date(Tender.publication_date).label('date'),
                func.count(Tender.id).label('count')
            ).filter(Tender.publication_date >= thirty_days_ago).group_by('date').all()
            
            # Get latest scraping logs
            latest_logs = ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(5).all()
            
            result = {
                'total_tenders': total_tenders,
                'tenders_by_type': [{'type': t[0] or 'Unknown', 'count': t[1]} for t in tenders_by_type],
                'tenders_by_organization': [{'organization': o[0] or 'Unknown', 'count': o[1]} for o in tenders_by_org],
                'tenders_by_date': [{'date': d[0].strftime('%Y-%m-%d') if d[0] else 'Unknown', 'count': d[1]} for d in tenders_by_date],
                'latest_logs': [log.to_dict() for log in latest_logs]
            }
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/organizations')
    def api_organizations():
        """API endpoint to get list of organizations for filtering"""
        try:
            organizations = db.session.query(
                Tender.organization
            ).filter(Tender.organization.isnot(None)).distinct().order_by(Tender.organization).all()
            
            return jsonify([org[0] for org in organizations if org[0]])
        except Exception as e:
            logger.error(f"Error fetching organizations: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tender-types')
    def api_tender_types():
        """API endpoint to get list of tender types for filtering"""
        try:
            tender_types = db.session.query(
                Tender.tender_type
            ).filter(Tender.tender_type.isnot(None)).distinct().order_by(Tender.tender_type).all()
            
            return jsonify([t_type[0] for t_type in tender_types if t_type[0]])
        except Exception as e:
            logger.error(f"Error fetching tender types: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/trigger-scrape', methods=['POST'])
    def api_trigger_scrape():
        """API endpoint to manually trigger the scraper"""
        try:
            run_scraper()
            return jsonify({'message': 'Scraper triggered successfully'})
        except Exception as e:
            logger.error(f"Error triggering scraper: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs')
    def api_logs():
        """API endpoint to get scraping logs"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            paginated_logs = ScrapingLog.query.order_by(
                ScrapingLog.start_time.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            result = {
                'logs': [log.to_dict() for log in paginated_logs.items],
                'total': paginated_logs.total,
                'pages': paginated_logs.pages,
                'current_page': page
            }
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}")
            return jsonify({'error': str(e)}), 500
