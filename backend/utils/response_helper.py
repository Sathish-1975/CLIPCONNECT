"""
============================================================
ClipConnect - Response Helper Utilities
============================================================
Purpose:
    Provides standardized JSON response functions for ALL API endpoints.
    Ensures every response has the same structure, making it predictable
    for frontend developers consuming the API.

Standard Response Format:
    {
        "success": true/false,
        "message": "Human-readable message",
        "data": { ... },       # Only on success
        "errors": { ... },     # Only on failure
        "status_code": 200
    }

Usage:
    from utils.response_helper import success_response, error_response
    
    # Success
    return success_response(data=user.to_dict(), message="User created", status_code=201)
    
    # Error
    return error_response(message="Email already exists", status_code=409)
============================================================
"""

from flask import jsonify


def success_response(data=None, message="Success", status_code=200, meta=None):
    """
    Build a standardized success JSON response.
    
    Args:
        data (dict|list|None): The main payload to return (e.g., user object, list)
        message (str): Human-readable success message
        status_code (int): HTTP status code (200, 201, etc.)
        meta (dict|None): Optional metadata (pagination info, counts, etc.)
    
    Returns:
        tuple: (Flask Response object, HTTP status code)
    
    Example:
        return success_response(
            data={"user": user.to_dict()},
            message="Registration successful",
            status_code=201
        )
    """
    response_body = {
        "success": True,
        "message": message,
        "status_code": status_code,
    }

    # Only include 'data' key if data is provided
    if data is not None:
        response_body["data"] = data

    # Include pagination/meta info if provided
    if meta is not None:
        response_body["meta"] = meta

    return jsonify(response_body), status_code


def error_response(message="An error occurred", status_code=400, errors=None):
    """
    Build a standardized error JSON response.
    
    Args:
        message (str): Human-readable error description
        status_code (int): HTTP error code (400, 401, 404, 409, 500, etc.)
        errors (dict|list|None): Detailed field-level errors (e.g., validation errors)
    
    Returns:
        tuple: (Flask Response object, HTTP status code)
    
    Example:
        return error_response(
            message="Validation failed",
            status_code=422,
            errors={"email": "Invalid email format", "password": "Too short"}
        )
    """
    response_body = {
        "success": False,
        "message": message,
        "status_code": status_code,
    }

    # Include field-level errors if provided (great for form validation feedback)
    if errors is not None:
        response_body["errors"] = errors

    return jsonify(response_body), status_code


def paginated_response(items, total, page, per_page, message="Data fetched successfully"):
    """
    Build a standardized paginated list response.
    Used for listing editors, orders, gigs etc.
    
    Args:
        items (list): List of serialized items for the current page
        total (int): Total number of items in the database
        page (int): Current page number
        per_page (int): Items per page
        message (str): Success message
    
    Returns:
        tuple: (Flask Response object, 200 status)
    """
    total_pages = (total + per_page - 1) // per_page  # Ceiling division

    return success_response(
        data=items,
        message=message,
        meta={
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    )
