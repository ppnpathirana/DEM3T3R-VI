"""
@file: rule_engine.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Treatment Rule Engine.
Loads rules from YAML and evaluates condition dicts against diagnosed diseases and sensor metrics.
Supported operators: >, <, >=, <=, ==, !=, contains, not_contains
"""
import os
import yaml
from typing import Dict, Any, Optional

class TreatmentRuleEngine:
    def __init__(self, yaml_path: str = "rules/treatment_rules.yaml"):
        self.yaml_path = yaml_path
        self.rules = []
        self.load_rules()

    def load_rules(self):
        if not os.path.exists(self.yaml_path):
            print(f"[RULE_ENGINE] Warning: {self.yaml_path} not found.")
            return
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.rules = data.get('rules', []) if data else []

    def evaluate(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate diagnosis dict against loaded YAML rules in priority order.
        diagnosis keys: 'disease' (str), 'severity' (float), 'confidence' (float), 'humidity' (float), etc.
        """
        for rule in self.rules:
            conditions = rule.get("if", {})
            if self._matches_all(conditions, diagnosis):
                result = dict(rule.get("then", {}))
                result["matched_rule"] = rule.get("id")
                result["rule_name"] = rule.get("name")
                return result

        # Default safe fallback
        return {
            "matched_rule": "default_safe_fallback",
            "rule_name": "Default Safe Fallback",
            "action": "alert_only",
            "duration_seconds": 0,
            "dose": "none",
            "alert": "Standard observation. No direct actuation triggered."
        }

    def _matches_all(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        for field, condition in conditions.items():
            val = context.get(field)
            if val is None:
                # If severity is passed as string, e.g. "severe", map to numeric
                if field == "severity" and isinstance(context.get("severity_str"), str):
                    s_map = {"mild": 30, "moderate": 55, "severe": 85}
                    val = s_map.get(context["severity_str"].lower(), 50)
                else:
                    return False

            if not self._check_condition(val, condition):
                return False
        return True

    def _check_condition(self, val: Any, condition: Any) -> bool:
        if isinstance(condition, dict):
            for op, target in condition.items():
                if op == ">" and not (float(val) > float(target)):
                    return False
                elif op == ">=" and not (float(val) >= float(target)):
                    return False
                elif op == "<" and not (float(val) < float(target)):
                    return False
                elif op == "<=" and not (float(val) <= float(target)):
                    return False
                elif op == "==" and not (str(val).lower() == str(target).lower()):
                    return False
                elif op == "!=" and not (str(val).lower() != str(target).lower()):
                    return False
                elif op == "contains" and not (str(target).lower() in str(val).lower()):
                    return False
                elif op == "not_contains" and (str(target).lower() in str(val).lower()):
                    return False
            return True
        else:
            return str(val).lower() == str(condition).lower()
