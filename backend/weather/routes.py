"""
@file: routes.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
==============================================================================
DEMETER Weather Intelligence System - REST API Routes
==============================================================================
Flask Blueprint exposing weather, GPS, disease risk, and agricultural insights.
==============================================================================
"""

from flask import Blueprint, jsonify, request

weather_bp = Blueprint("weather", __name__, url_prefix="/api")

_weather_service = None

def init_weather_routes(weather_service):
    """Binds weather service instance to blueprint routes."""
    global _weather_service
    _weather_service = weather_service
    return weather_bp

@weather_bp.route("/weather/current", methods=["GET"])
def get_current_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    force = request.args.get("force", default=False, type=lambda v: v.lower() == 'true')
    
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    data = _weather_service.get_weather(lat, lon, force_refresh=force)
    return jsonify({
        "status": "success",
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "location_name": data.get("location_name"),
        "provider": data.get("provider"),
        "is_cached": data.get("is_cached", False),
        "is_offline_fallback": data.get("is_offline_fallback", False),
        "current": data.get("current"),
        "fetched_at": data.get("fetched_at")
    })

@weather_bp.route("/weather/hourly", methods=["GET"])
def get_hourly_forecast():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    data = _weather_service.get_weather(lat, lon)
    return jsonify({
        "status": "success",
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "hourly": data.get("hourly", [])
    })

@weather_bp.route("/weather/forecast", methods=["GET"])
def get_daily_forecast():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    data = _weather_service.get_weather(lat, lon)
    return jsonify({
        "status": "success",
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "daily_7day": data.get("daily", [])
    })

@weather_bp.route("/weather/history", methods=["GET"])
def get_weather_history():
    limit = request.args.get("limit", default=50, type=int)
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    history = _weather_service.db.get_history(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history),
        "history": history
    })

@weather_bp.route("/weather/alerts", methods=["GET"])
def get_weather_alerts():
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    alerts = _weather_service.get_alerts()
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "alerts": alerts
    })

@weather_bp.route("/weather/disease-risk", methods=["GET"])
def get_disease_risk():
    crop = request.args.get("crop", default="Tomato", type=str)
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    risk_data = _weather_service.get_disease_risk(crop=crop)
    return jsonify({
        "status": "success",
        **risk_data
    })

@weather_bp.route("/weather/agriculture-insights", methods=["GET"])
def get_agriculture_insights():
    crop = request.args.get("crop", default="Tomato", type=str)
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    risk_data = _weather_service.get_disease_risk(crop=crop)
    weather = _weather_service.get_weather()
    return jsonify({
        "status": "success",
        "crop": crop,
        "location": weather.get("location_name"),
        "smart_irrigation": risk_data.get("smart_irrigation"),
        "disease_risks": risk_data.get("specific_pathogen_risks"),
        "overall_risk": risk_data.get("overall_environmental_risk"),
        "disclaimer": risk_data.get("disclaimer")
    })

@weather_bp.route("/gps/current", methods=["GET"])
def get_current_gps():
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    gps_data = _weather_service.get_current_gps()
    return jsonify({
        "status": "success",
        "gps": gps_data
    })

@weather_bp.route("/weather/status", methods=["GET"])
def get_weather_status():
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    gps = _weather_service.get_current_gps()
    weather = _weather_service.get_weather()
    return jsonify({
        "status": "success",
        "network": "CONNECTED" if not weather.get("is_offline_fallback") else "OFFLINE_FALLBACK",
        "gps_status": "FIXED" if gps.get("is_fixed") else "NO_FIX",
        "gps_accuracy_m": gps.get("accuracy"),
        "active_provider": weather.get("provider"),
        "is_cached": weather.get("is_cached", False),
        "last_weather_fetch": weather.get("fetched_at")
    })

@weather_bp.route("/weather/ai-summary", methods=["GET"])
def get_ai_weather_summary():
    crop = request.args.get("crop", default="Tomato", type=str)
    force = request.args.get("force", default=False, type=lambda v: v.lower() == 'true')
    if not _weather_service:
        return jsonify({"error": "Weather service not initialized"}), 503

    summary = _weather_service.get_ai_summary(crop=crop, force_refresh=force)
    return jsonify({
        "status": "success",
        **summary
    })
