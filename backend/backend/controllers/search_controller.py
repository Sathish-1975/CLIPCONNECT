"""
============================================================
ClipConnect - Search Controller
============================================================
  suggest_search()   GET /api/search/suggest?q=...
  Returns categorised autocomplete suggestions for the
  search bar: names, skills, software, cities, categories.
============================================================
"""

from flask import request
from sqlalchemy import or_, cast
from sqlalchemy import Text as SQLText

from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, EditorCategory
from utils.response_helper import success_response, error_response

# Category display labels
CATEGORY_LABELS = {
    'youtube':         'YouTube',
    'reels':           'Reels & Shorts',
    'wedding':         'Wedding',
    'corporate':       'Corporate',
    'motion_graphics': 'Motion Graphics',
    'podcast':         'Podcast',
    'ecommerce':       'E-Commerce',
    'documentary':     'Documentary',
    'other':           'Other',
}


def suggest_search():
    """
    GET /api/search/suggest?q=<query>&limit=5

    Returns autocomplete suggestions grouped by field type:
      names      — editor full names / usernames
      skills     — distinct skills that match
      software   — distinct software names that match
      cities     — distinct cities that match
      categories — matching categories

    Each entry has: { value, label, type, icon }
    """
    q = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 5)), 10)

    if not q or len(q) < 2:
        return success_response(data={'suggestions': [], 'groups': {}}, message='Query too short.')

    like = f'%{q}%'

    # Base: only active editors with profiles
    base = (
        db.session.query(EditorProfile, User)
        .join(User, EditorProfile.user_id == User.id)
        .filter(User.role == UserRole.EDITOR, User.is_active == True)
    )

    suggestions = []

    # ── 1. Names (full_name + username) ──
    name_rows = base.filter(or_(
        User.full_name.ilike(like),
        EditorProfile.username.ilike(like),
    )).limit(limit).all()

    seen_names = set()
    for p, u in name_rows:
        if u.full_name not in seen_names:
            seen_names.add(u.full_name)
            suggestions.append({
                'type':    'name',
                'icon':    '👤',
                'value':   u.full_name,
                'label':   u.full_name,
                'sub':     f'@{p.username}' if p.username else 'Editor',
                'user_id': u.id,
            })

    # ── 2. Skills (search JSON array as text, then extract individual matches) ──
    skill_rows = base.filter(
        cast(EditorProfile.skills, SQLText).ilike(like)
    ).limit(20).all()

    seen_skills = set()
    for p, u in skill_rows:
        for skill in (p.skills or []):
            if q.lower() in skill.lower() and skill not in seen_skills:
                seen_skills.add(skill)
                suggestions.append({
                    'type':  'skill',
                    'icon':  '🛠',
                    'value': skill,
                    'label': skill,
                    'sub':   'Skill',
                })
                if len(seen_skills) >= limit:
                    break

    # ── 3. Software ──
    sw_rows = base.filter(
        cast(EditorProfile.software_used, SQLText).ilike(like)
    ).limit(20).all()

    seen_sw = set()
    for p, u in sw_rows:
        for sw in (p.software_used or []):
            if q.lower() in sw.lower() and sw not in seen_sw:
                seen_sw.add(sw)
                suggestions.append({
                    'type':  'software',
                    'icon':  '💻',
                    'value': sw,
                    'label': sw,
                    'sub':   'Software',
                })
                if len(seen_sw) >= limit:
                    break

    # ── 4. Cities ──
    city_rows = base.filter(
        EditorProfile.city.ilike(like)
    ).with_entities(EditorProfile.city).distinct().limit(limit).all()

    seen_cities = set()
    for (city,) in city_rows:
        if city and city not in seen_cities:
            seen_cities.add(city)
            suggestions.append({
                'type':  'city',
                'icon':  '📍',
                'value': city,
                'label': city,
                'sub':   'City',
            })

    # ── 5. Categories ──
    matched_cats = []
    for cat in EditorCategory:
        label = CATEGORY_LABELS.get(cat.value, cat.value)
        if q.lower() in cat.value.lower() or q.lower() in label.lower():
            matched_cats.append({
                'type':  'category',
                'icon':  '🎬',
                'value': cat.value,
                'label': CATEGORY_LABELS.get(cat.value, cat.value),
                'sub':   'Category',
            })
    suggestions.extend(matched_cats[:limit])

    # ── Group by type for structured dropdown ──
    groups = {}
    for s in suggestions:
        t = s['type']
        if t not in groups:
            groups[t] = []
        groups[t].append(s)

    return success_response(
        data={
            'query':       q,
            'suggestions': suggestions[:20],
            'groups':      groups,
        },
        message=f'{len(suggestions)} suggestions found.'
    )
