from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services.analytics import AnalyticsService

bp = Blueprint('api', __name__, url_prefix='/api')
analytics = AnalyticsService()

@bp.route('/dashboard/metrics')
@login_required
def dashboard_metrics():
    period = request.args.get('period', 'today')
    metrics = analytics.get_dashboard_metrics(period)
    return jsonify(metrics)