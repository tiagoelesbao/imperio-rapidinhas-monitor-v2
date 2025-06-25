from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/users')
@login_required
def users():
    return render_template('admin/users.html')