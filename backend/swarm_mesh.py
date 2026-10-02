"""
DEM3T3R V1 Multi-Robot Swarm Mesh Coordinator.
Manages decentralized multi-agent farm missions across a fleet:
- Node-01: Active Treatment Rover (Equipped with precision spray & soil probe)
- Node-02: Secondary Patrol Rover (Equipped with high-resolution canopy camera)
- Node-03: Scout UAV Drone (Aerial multispectral scout)
Allocates field sectors and synchronizes global disease map & telemetry across the swarm.
"""
import time
from typing import Dict, Any, List

class SwarmMeshCoordinator:
    def __init__(self):
        self.nodes = {
            "node-01": {
                "id": "node-01",
                "name": "CropGuard-Alpha (Active Rover)",
                "role": "Precision Treatment & Ground Telemetry",
                "battery_pct": 88,
                "status": "PATROL_ACTIVE",
                "assigned_sector": "Sector-A (Tomato Greenhouse)",
                "current_pose": {"latitude": 6.92715, "longitude": 79.86125},
                "last_heartbeat": time.time()
            },
            "node-02": {
                "id": "node-02",
                "name": "CropGuard-Beta (Standby Rover)",
                "role": "Soil Probing & Backup Sprayer",
                "battery_pct": 95,
                "status": "DOCKED_CHARGING",
                "assigned_sector": "Sector-B (Potato Field)",
                "current_pose": {"latitude": 6.92700, "longitude": 79.86100},
                "last_heartbeat": time.time()
            },
            "node-03": {
                "id": "node-03",
                "name": "CropGuard-AirScout (UAV Drone)",
                "role": "Aerial Thermal & Multispectral Mapping",
                "battery_pct": 72,
                "status": "AERIAL_STAGED",
                "assigned_sector": "Sector-C (Tea Plantation)",
                "current_pose": {"latitude": 6.92750, "longitude": 79.86150},
                "last_heartbeat": time.time()
            }
        }
        self.shared_disease_registry: List[Dict[str, Any]] = []

    def update_node_heartbeat(self, node_id: str, battery: int, status: str, pose: Dict[str, float]):
        if node_id in self.nodes:
            self.nodes[node_id].update({
                "battery_pct": battery,
                "status": status,
                "current_pose": pose,
                "last_heartbeat": time.time()
            })

    def broadcast_disease_hotspot(self, reporting_node: str, pathogen: str, lat: float, lon: float, severity: str):
        """Adds a discovered disease hotspot to the swarm mesh for collective action."""
        hotspot = {
            "id": f"spot_{int(time.time()*1000)}",
            "reporting_node": reporting_node,
            "pathogen": pathogen,
            "severity": severity,
            "latitude": lat,
            "longitude": lon,
            "timestamp": time.time(),
            "status": "ASSIGNED_FOR_TREATMENT" if severity in ["moderate", "severe"] else "MONITORING"
        }
        self.shared_disease_registry.append(hotspot)
        return hotspot

    def get_swarm_status(self) -> Dict[str, Any]:
        return {
            "active_nodes_count": len(self.nodes),
            "swarm_health": "OPTIMAL",
            "nodes": list(self.nodes.values()),
            "shared_hotspots_count": len(self.shared_disease_registry),
            "recent_hotspots": self.shared_disease_registry[-5:]
        }
