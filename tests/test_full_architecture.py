import sys, os, time, pytest, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.plugins import CropModelRegistry
from backend.event_store import EventStore
from backend.position_estimator import PositionEstimator, haversine_distance
from backend.coverage_planner import CoveragePlanner, WaypointNavigator
from backend.rule_engine import TreatmentRuleEngine
from backend.mcp_server import CropGuardMCPServer
from backend.rag_knowledge import RAGKnowledgeBase
from backend.gradcam_analyzer import GradCAMVisualizer
from backend.precision_spray import ConfidenceRouter, TreatmentAdvisor, PrecisionSprayController
from backend.model_optimizer import PlantPreFilter, SensorAnomalyDetector

def test_plugin_registry_16_crops():
    registry = CropModelRegistry(models_dir="models")
    crops = registry.list_crops()
    assert len(crops) == 16
    assert "tomato" in crops
    assert "rice" in crops
    assert "tea" in crops
    meta = registry.get_metadata("tomato")
    assert meta["crop"] == "tomato"
    assert "tomato_early_blight" in meta["diseases"]

def test_event_store_append_and_replay():
    db_file = "test_events_temp.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    store = EventStore(db_path=db_file)
    id1 = store.append("state_transition", {"old_state": "IDLE", "new_state": "SCANNING"})
    id2 = store.append("detection", {"class": "tomato_early_blight", "confidence": 0.88})
    assert id1 > 0 and id2 > id1
    assert store.count() == 2
    events = store.replay()
    assert len(events) == 2
    assert events[0].event_type == "state_transition"
    assert store.get_last_state() == "SCANNING"
    store.close()
    if os.path.exists(db_file):
        os.remove(db_file)

def test_position_estimator_ekf():
    ekf = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)
    ekf.update_gps(6.9275, 79.8615, timestamp=time.time())
    ekf.update_heading_and_velocity(heading_deg=45.0, velocity_ms=0.5, timestamp=time.time()+0.1)
    pose = ekf.get_pose()
    assert "x_local_m" in pose
    assert "latitude" in pose
    assert "heading_deg" in pose
    assert pose["velocity_ms"] >= 0.0

def test_coverage_planner_and_navigator():
    planner = CoveragePlanner(row_spacing_m=1.0)
    # Field polygon in Colombo
    boundary = [
        (6.92710, 79.86120),
        (6.92730, 79.86120),
        (6.92730, 79.86140),
        (6.92710, 79.86140)
    ]
    waypoints = planner.plan_field(boundary)
    assert len(waypoints) >= 2
    nav = WaypointNavigator(waypoints=waypoints, arrival_radius_m=2.0)
    status = nav.update_position(6.92710, 79.86120)
    assert "esp32_cmd" in status
    assert status["coverage_pct"] >= 0.0

def test_yaml_rule_engine():
    engine = TreatmentRuleEngine("rules/treatment_rules.yaml")
    # Early blight severity 80 -> spray copper fungicide
    diag = {"disease": "tomato_early_blight", "severity": 80.0, "confidence": 0.90}
    res = engine.evaluate(diag)
    assert res["action"] == "spray"
    assert "copper" in res.get("agent", "").lower()
    
    # Healthy plant -> monitor
    res_healthy = engine.evaluate({"disease": "healthy"})
    assert res_healthy["action"] == "monitor"

def test_mcp_server_and_rag():
    rag = RAGKnowledgeBase()
    docs = rag.query("tomato", "early blight fungicide")
    assert len(docs) > 0
    assert "Alternaria" in docs[0]["pathogen"]
    
    mcp = CropGuardMCPServer(rag_store=rag)
    tools = mcp.list_tools()
    assert len(tools) >= 5
    res = mcp.call_tool("read_sensors", {})
    assert res["status"] == "success"

def test_gradcam_and_plant_filter():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[100:300, 100:300] = [35, 180, 50]  # Green plant tissue
    has_plant, ratio = PlantPreFilter.has_plant_tissue(frame)
    assert has_plant is True
    assert ratio > 0.05
    
    overlay = GradCAMVisualizer.generate_detection_heatmap(frame, bbox=[100, 100, 300, 300])
    assert overlay.shape == (480, 640, 3)

def test_confidence_router_and_precision_spray():
    router = ConfidenceRouter(auto_threshold=0.75)
    high_conf = router.route_diagnosis({"disease": "tomato_early_blight", "confidence": 0.85})
    assert high_conf["decision"] == "AUTO_TREAT"
    
    low_conf = router.route_diagnosis({"disease": "tomato_early_blight", "confidence": 0.60})
    assert low_conf["decision"] == "FARMER_REVIEW"
    assert len(router.farmer_review_queue) == 1
    
    duration = PrecisionSprayController.calculate_spray_duration(severity="moderate")
    assert 4.0 <= duration <= 6.0

def test_sensor_anomaly_detector():
    detector = SensorAnomalyDetector()
    # Feed 15 normal temperature readings around 28.0C
    for _ in range(15):
        detector.inspect_reading("temperature", 28.0)
    # Feed an anomalous spike of 58.0C
    res = detector.inspect_reading("temperature", 58.0)
    assert res["is_anomaly"] is True
