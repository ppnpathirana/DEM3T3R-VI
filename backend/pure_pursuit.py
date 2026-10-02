"""
@file: pure_pursuit.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 MathWorks-Inspired Pure Pursuit & Velocity Profiler
Adapted from MathWorks Robotics System Toolbox:
https://github.com/mathworks-robotics/autonomous-navigation-ugv
(controllerPurePursuit and followWaypointsTrapVelTraj)

Implements differential drive pure pursuit path tracking with trapezoidal
velocity profiling for smooth acceleration, steady cruising, and gentle deceleration.
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class TrapezoidalVelocityProfile:
    def __init__(self, v_max: float = 0.6, a_max: float = 0.5, d_max: float = 0.8, v_min: float = 0.15):
        """
        :param v_max: Maximum cruising velocity (m/s).
        :param a_max: Maximum linear acceleration (m/s^2).
        :param d_max: Maximum linear deceleration (m/s^2).
        :param v_min: Minimum creep velocity when approaching waypoint (m/s).
        """
        self.v_max = v_max
        self.a_max = a_max
        self.d_max = d_max
        self.v_min = v_min
        self.current_v = 0.0

    def compute_velocity(self, distance_to_goal: float, dt: float = 0.1) -> float:
        """Computes current target velocity based on distance to goal and deceleration envelope."""
        if distance_to_goal <= 0.05:
            self.current_v = 0.0
            return 0.0

        # Maximum speed permitted by stopping distance
        v_decel_limit = math.sqrt(max(0.0, 2.0 * self.d_max * distance_to_goal))
        target_v = min(self.v_max, max(self.v_min, v_decel_limit))

        # Respect acceleration limit
        if target_v > self.current_v:
            self.current_v = min(target_v, self.current_v + self.a_max * dt)
        else:
            self.current_v = max(target_v, self.current_v - self.d_max * dt)

        return self.current_v


class PurePursuitController:
    def __init__(
        self,
        lookahead_distance: float = 1.2,
        max_angular_velocity: float = 2.0,
        wheel_base: float = 0.35,
        goal_radius: float = 0.5,
        max_pwm: int = 240
    ):
        """
        :param lookahead_distance: Lookahead distance L_d (meters).
        :param max_angular_velocity: Maximum allowable yaw rate omega (rad/s).
        :param wheel_base: Distance between left and right wheels W (meters).
        :param goal_radius: Radius to consider waypoint reached (meters).
        :param max_pwm: Maximum PWM duty cycle output (0-255).
        """
        self.lookahead_distance = lookahead_distance
        self.max_angular_velocity = max_angular_velocity
        self.wheel_base = wheel_base
        self.goal_radius = goal_radius
        self.max_pwm = max_pwm
        self.velocity_profiler = TrapezoidalVelocityProfile()

    def find_lookahead_point(
        self,
        current_pose: Tuple[float, float, float],
        waypoints: List[Tuple[float, float]]
    ) -> Tuple[Optional[Tuple[float, float]], float, int]:
        """
        Finds the lookahead point along the path at lookahead_distance ahead of robot.
        Returns: (target_point, distance_to_current_waypoint, current_target_idx)
        """
        x, y, _ = current_pose
        if not waypoints:
            return None, 0.0, 0

        # Find closest waypoint ahead
        closest_idx = 0
        min_dist = float('inf')
        for i, (wx, wy) in enumerate(waypoints):
            d = math.hypot(wx - x, wy - y)
            if d < min_dist:
                min_dist = d
                closest_idx = i

        # Look ahead along the path
        target_idx = closest_idx
        for i in range(closest_idx, len(waypoints)):
            wx, wy = waypoints[i]
            d = math.hypot(wx - x, wy - y)
            if d >= self.lookahead_distance:
                return (wx, wy), min_dist, i
            target_idx = i

        return waypoints[target_idx], min_dist, target_idx

    def compute_steering(
        self,
        current_pose: Tuple[float, float, float],
        waypoints: List[Tuple[float, float]],
        dt: float = 0.1
    ) -> Dict[str, Any]:
        """
        Computes curvature, linear velocity, angular velocity, and differential motor PWMs.
        
        :param current_pose: (x, y, heading_rad) in local meters and radians.
        :param waypoints: List of (x, y) coordinates in meters.
        :param dt: Time elapsed since last control step.
        """
        x, y, theta = current_pose

        if not waypoints:
            return {
                "motor_left": 0,
                "motor_right": 0,
                "linear_velocity": 0.0,
                "angular_velocity": 0.0,
                "curvature": 0.0,
                "goal_reached": True,
                "distance_to_goal": 0.0
            }

        target_point, dist_to_target, target_idx = self.find_lookahead_point(current_pose, waypoints)
        final_goal = waypoints[-1]
        dist_to_final = math.hypot(final_goal[0] - x, final_goal[1] - y)

        if dist_to_final <= self.goal_radius:
            return {
                "motor_left": 0,
                "motor_right": 0,
                "linear_velocity": 0.0,
                "angular_velocity": 0.0,
                "curvature": 0.0,
                "goal_reached": True,
                "distance_to_goal": dist_to_final
            }

        tx, ty = target_point if target_point else final_goal
        dx = tx - x
        dy = ty - y
        lookahead_dist = max(0.1, math.hypot(dx, dy))

        # Angle from robot heading to lookahead point
        target_angle = math.atan2(dy, dx)
        alpha = target_angle - theta

        # Normalize alpha to [-pi, pi]
        alpha = (alpha + math.pi) % (2 * math.pi) - math.pi

        # MathWorks Pure Pursuit curvature formula: kappa = 2 * sin(alpha) / L_d
        curvature = (2.0 * math.sin(alpha)) / lookahead_dist

        # Compute velocity with trapezoidal deceleration ramp
        v = self.velocity_profiler.compute_velocity(dist_to_final, dt=dt)
        omega = curvature * v
        omega = max(-self.max_angular_velocity, min(self.max_angular_velocity, omega))

        # Differential drive inverse kinematics:
        # v_left  = v - (omega * W / 2)
        # v_right = v + (omega * W / 2)
        v_left = v - (omega * self.wheel_base / 2.0)
        v_right = v + (omega * self.wheel_base / 2.0)

        # Scale to PWM values (-max_pwm to +max_pwm)
        v_max = self.velocity_profiler.v_max
        pwm_left = int(max(-self.max_pwm, min(self.max_pwm, (v_left / v_max) * self.max_pwm)))
        pwm_right = int(max(-self.max_pwm, min(self.max_pwm, (v_right / v_max) * self.max_pwm)))

        return {
            "motor_left": pwm_left,
            "motor_right": pwm_right,
            "linear_velocity": round(v, 3),
            "angular_velocity": round(omega, 3),
            "curvature": round(curvature, 4),
            "lookahead_point": (round(tx, 2), round(ty, 2)),
            "distance_to_goal": round(dist_to_final, 2),
            "goal_reached": False
        }
