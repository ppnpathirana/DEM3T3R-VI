import pytest
import time
from backend.position_estimator import PositionEstimator, haversine_distance, calculate_bearing


def test_rover_gps_update():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    ekf.update_rover_gps(6.9272, 79.8613, hdop=1.2, satellites=9, fix_type=1)
    pose = ekf.get_pose()
    assert pose["gps_fixes"] == 1
    assert pose["last_rover_gps"]["satellites"] == 9
    assert abs(pose["latitude"] - 6.9272) < 0.001
    assert abs(pose["longitude"] - 79.8613) < 0.001


def test_laptop_gps_update():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    ekf.update_laptop_gps(6.92715, 79.86125, accuracy_m=3.5, altitude=16.0)
    pose = ekf.get_pose()
    assert pose["laptop_updates"] == 1
    assert pose["last_laptop_gps"]["accuracy_m"] == 3.5
    assert abs(pose["latitude"] - 6.92715) < 0.001


def test_dual_source_fusion_reduces_uncertainty():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    initial_unc = ekf.get_pose()["uncertainty_m"]
    
    ekf.update_rover_gps(6.92718, 79.86122, hdop=1.0, satellites=10, fix_type=1)
    rover_only_unc = ekf.get_pose()["uncertainty_m"]
    assert rover_only_unc < initial_unc
    
    ekf.update_laptop_gps(6.92719, 79.86121, accuracy_m=2.0)
    fused_unc = ekf.get_pose()["uncertainty_m"]
    assert fused_unc <= rover_only_unc + 0.1
    pose = ekf.get_pose()
    assert pose["fusion_mode"] == "FUSED_DUAL"


def test_baseline_vector_between_laptop_and_rover():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    laptop_lat, laptop_lon = 6.92710, 79.86120
    rover_lat, rover_lon = 6.92720, 79.86120
    
    ekf.update_laptop_gps(laptop_lat, laptop_lon, accuracy_m=3.0)
    ekf.update_rover_gps(rover_lat, rover_lon, hdop=0.9, satellites=10, fix_type=1)
    
    baseline = ekf.get_baseline_vector()
    assert baseline is not None
    assert "distance_m" in baseline
    assert "bearing_deg" in baseline
    assert 9.0 <= baseline["distance_m"] <= 13.0
    assert baseline["bearing_deg"] < 5.0 or baseline["bearing_deg"] > 355.0


def test_fusion_mode_selection():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    assert ekf.set_fusion_mode("ROVER_GPS_ONLY") == "ROVER_GPS_ONLY"
    assert ekf.set_fusion_mode("LAPTOP_GCS_ONLY") == "LAPTOP_GCS_ONLY"
    assert ekf.set_fusion_mode("FUSED_DUAL") == "FUSED_DUAL"
    assert ekf.set_fusion_mode("INVALID_MODE") == "FUSED_DUAL"
