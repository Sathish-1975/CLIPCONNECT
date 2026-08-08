"""
============================================================
ClipConnect - AI Controller
============================================================
Why this file exists:
  Provides controller logic for AI-powered editor recommendations, automated project description
  generation, and natural language search query parsing.

What it does:
  - `recommend_editors()`: Analyzes project requirements (category, budget, skills, experience)
    and scores matching editors based on rating, completed projects, and skill alignment.
  - `generate_description()`: Takes a simple prompt/idea and generates a professional, structured
    project description complete with key deliverables and software recommendations.
  - `natural_language_search()`: Parses free-form queries (e.g. "wedding editor under 5000")
    into structured database filters (`category='wedding', max_budget=5000`) and returns matched results.

How it integrates with the rest of the application:
  - Exposed via `/api/ai/*` endpoints in `ai_routes.py`.
  - Interfaces with `EditorProfile`, `User`, `Project`, and `EditorCategory` models.
============================================================
"""

import re
from flask import request
from database import db
from models.editor_profile_model import EditorProfile, EditorCategory
from models.user_model import User, UserRole
from utils.response_helper import success_response, error_response


def recommend_editors():
    """
    POST /api/ai/recommend-editors
    Body: { category, budget, skills, experience }
    Scoring algorithm to recommend top editors.
    """
    data = request.get_json(silent=True) or {}
    category_val = (data.get('category') or '').strip().lower()
    budget       = data.get('budget')
    skills       = data.get('skills') or []

    query = EditorProfile.query.join(User).filter(User.is_active == True)

    if category_val:
        try:
            query = query.filter(EditorProfile.category == EditorCategory(category_val))
        except ValueError:
            pass

    profiles = query.all()
    scored = []

    for p in profiles:
        score = 0.0
        # Rating score (0-50 pts)
        rating = float(p.avg_rating or 0.0)
        score += rating * 10

        # Completed projects (0-20 pts)
        score += min(20, (p.completed_projects or 0) * 2)

        # Budget match (0-20 pts)
        if budget and p.hourly_rate:
            rate = float(p.hourly_rate)
            if rate <= float(budget):
                score += 20
            else:
                score += max(0, 20 - (rate - float(budget)) / 100)
        else:
            score += 10

        # Skill match (0-10 pts)
        if skills and p.skills:
            matching_skills = set(s.lower() for s in skills).intersection(set(s.lower() for s in p.skills))
            score += min(10, len(matching_skills) * 3.5)

        scored.append({
            'profile': p.to_public_dict(),
            'match_score': round(min(100.0, score), 1)
        })

    # Sort descending by match score
    scored.sort(key=lambda x: x['match_score'], reverse=True)

    return success_response(
        data={'recommendations': scored[:10]},
        message=f"Generated top {len(scored[:10])} editor recommendations."
    )


def generate_description():
    """
    POST /api/ai/generate-description
    Body: { prompt, category, style }
    Generates a structured professional job posting description.
    """
    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or '').strip()
    category = (data.get('category') or 'video editing').strip()

    if not prompt:
        return error_response(message="Prompt / idea is required.", status_code=422)

    # Intelligent template generator
    suggested_title = f"Professional {category.title()} Video Editing for '{prompt[:40]}...'"
    
    generated_text = f"""## Project Overview
We are looking for a skilled **{category.title()} Video Editor** to bring our project to life.
Concept Idea: {prompt}

## Key Responsibilities & Deliverables
- Color grading, audio mixing, and seamless transitions.
- Engaging pacing, sound effects (SFX), and motion graphics overlay.
- High-definition final render formatted for YouTube, Social Media, and Web.
- 1-2 revisions included.

## Preferred Skills & Software
- Proficiency in Premiere Pro / DaVinci Resolve / After Effects.
- Strong portfolio demonstrating creative storytelling and rhythm.
"""

    return success_response(
        data={
            'title': suggested_title,
            'description': generated_text.strip(),
            'suggested_skills': ['Color Grading', 'Sound Design', 'Motion Graphics', 'Transitions'],
            'suggested_software': ['Adobe Premiere Pro', 'After Effects', 'DaVinci Resolve']
        },
        message="AI Project description generated successfully!"
    )


def natural_language_search():
    """
    GET /api/ai/search?q=I+need+a+wedding+editor+under+5000
    Parses natural language query into filters and executes search.
    """
    raw_query = request.args.get('q', '').strip()
    if not raw_query:
        return error_response(message="Search query parameter 'q' is required.", status_code=422)

    query_lower = raw_query.lower()

    # Extract price / budget limit if mentioned (e.g. "under 5000", "below 3000", "< 1000")
    budget_limit = None
    price_match = re.search(r'(?:under|below|less than|max|budget|\<)\s*₹?\s*(\d+)', query_lower)
    if price_match:
        budget_limit = float(price_match.group(1))

    # Match Category
    matched_category = None
    for cat in EditorCategory:
        if cat.value in query_lower or cat.value.replace('_', ' ') in query_lower:
            matched_category = cat
            break

    # Build DB Query
    db_query = EditorProfile.query.join(User).filter(User.is_active == True)

    if matched_category:
        db_query = db_query.filter(EditorProfile.category == matched_category)

    if budget_limit:
        db_query = db_query.filter(
            (EditorProfile.hourly_rate <= budget_limit) |
            (EditorProfile.fixed_price_from <= budget_limit)
        )

    # General text matching on tagline or bio
    if not matched_category:
        db_query = db_query.filter(
            (EditorProfile.tagline.ilike(f"%{raw_query}%")) |
            (EditorProfile.bio.ilike(f"%{raw_query}%"))
        )

    results = db_query.order_by(EditorProfile.avg_rating.desc()).limit(20).all()
    editors_data = [e.to_public_dict() for e in results]

    return success_response(
        data={
            'query': raw_query,
            'parsed_filters': {
                'category': matched_category.value if matched_category else None,
                'max_budget': budget_limit,
            },
            'editors': editors_data,
            'total': len(editors_data)
        },
        message=f"Found {len(editors_data)} matching editors."
    )
