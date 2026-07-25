"""
============================================================
ClipConnect - Review Controller
============================================================
Handles:
  create_review()       POST /api/reviews
  get_editor_reviews()  GET  /api/reviews/<editor_id>
============================================================
"""

from flask import request, current_app
from database import db
from models.user_model import User, UserRole
from models.review_model import Review
from models.project_model import Project, ProjectStatus
from models.editor_profile_model import EditorProfile
from utils.response_helper import success_response, error_response


def create_review(current_user: dict):
    """
    POST /api/reviews
    Body: { editor_id, project_id (optional), rating (1-5), comment }
    Only clients can submit reviews.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can submit reviews.", status_code=403)

    data = request.get_json(silent=True) or {}
    editor_id  = data.get('editor_id')
    project_id = data.get('project_id')
    rating     = data.get('rating')
    comment    = (data.get('comment') or '').strip()

    # ── Validation ──
    if not editor_id:
        return error_response(message="editor_id is required.", status_code=422)

    if rating is None:
        return error_response(message="rating is required (1-5).", status_code=422)

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return error_response(message="rating must be an integer.", status_code=422)

    if rating < 1 or rating > 5:
        return error_response(message="rating must be between 1 and 5.", status_code=422)

    # Check editor exists
    editor = User.query.get(editor_id)
    if not editor or editor.role != UserRole.EDITOR:
        return error_response(message="Editor not found.", status_code=404)

    # Optional: verify the project exists and is completed
    if project_id:
        project = Project.query.get(project_id)
        if not project:
            return error_response(message="Project not found.", status_code=404)
        if project.client_id != current_user['user_id']:
            return error_response(message="You can only review editors on your own projects.", status_code=403)

        # Check for duplicate review on same project
        existing = Review.query.filter_by(
            reviewer_id=current_user['user_id'],
            project_id=project_id
        ).first()
        if existing:
            return error_response(message="You have already reviewed this editor for this project.", status_code=400)

    review = Review(
        reviewer_id=current_user['user_id'],
        editor_id=editor_id,
        project_id=project_id,
        rating=rating,
        comment=comment or None
    )

    try:
        db.session.add(review)
        db.session.flush()

        # Update editor profile stats
        _update_editor_rating(editor_id)

        db.session.commit()

        # Send notification to editor
        from utils.notification_helper import create_notification
        reviewer = User.query.get(current_user['user_id'])
        reviewer_name = reviewer.full_name if reviewer else 'A client'
        create_notification(
            user_id=editor_id,
            title="New Review ⭐",
            message=f"{reviewer_name} gave you a {rating}-star review!",
            type_str="review_received",
            related_project_id=project_id
        )

        return success_response(
            data={'review': review.to_dict()},
            message="Review submitted successfully!",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create review error: {e}")
        return error_response(message=f"Failed to submit review: {str(e)}", status_code=500)


def get_editor_reviews(editor_id: int):
    """
    GET /api/reviews/<editor_id>
    Public endpoint — returns all reviews for an editor.
    """
    editor = User.query.get(editor_id)
    if not editor or editor.role != UserRole.EDITOR:
        return error_response(message="Editor not found.", status_code=404)

    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', 20, type=int)))

    query = Review.query.filter_by(editor_id=editor_id).order_by(Review.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    reviews = [r.to_dict() for r in pagination.items]

    # Aggregate stats
    all_ratings = [r.rating for r in Review.query.filter_by(editor_id=editor_id).all()]
    avg_rating  = sum(all_ratings) / len(all_ratings) if all_ratings else 0.0
    total       = len(all_ratings)

    # Rating distribution
    distribution = {str(i): all_ratings.count(i) for i in range(1, 6)}

    return success_response(
        data={
            'reviews':      reviews,
            'avg_rating':   round(avg_rating, 2),
            'total_reviews': total,
            'distribution': distribution,
            'page':         page,
            'per_page':     per_page,
            'total_pages':  pagination.pages,
        },
        message=f"Found {total} reviews for this editor."
    )


def _update_editor_rating(editor_id: int):
    """Recalculate and store avg_rating + total_reviews on EditorProfile."""
    profile = EditorProfile.query.filter_by(user_id=editor_id).first()
    if not profile:
        return

    all_ratings = [r.rating for r in Review.query.filter_by(editor_id=editor_id).all()]
    profile.avg_rating    = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0.0
    profile.total_reviews = len(all_ratings)
