"""
@file: __init__.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Plugin System -- CropModelRegistry using pluggy + importlib auto-discovery.

Hook specification:
  cropguard_plugin: hook mark for all crop model plugins

CropModelRegistry auto-discovers all modules in backend/crops/ that
export a class matching the CropModel interface, and registers them.
"""
import pkgutil
import importlib
import os
import sys
from typing import Dict, Optional, Type
import pluggy
from backend.crops._base import CropModel

hookspec = pluggy.HookspecMarker('cropguard')
hookimpl = pluggy.HookimplMarker('cropguard')


class CropPluginSpec:
    @hookspec
    def get_crop_model(self) -> CropModel:
        """Return a CropModel instance for this crop plugin."""


class CropModelRegistry:
    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self._registry: Dict[str, CropModel] = {}
        self._pm = pluggy.PluginManager('cropguard')
        self._pm.add_hookspecs(CropPluginSpec)
        self._discover_and_register()

    def _discover_and_register(self):
        crops_package = 'backend.crops'
        try:
            pkg = importlib.import_module(crops_package)
        except ImportError:
            print('[CropRegistry] Could not import backend.crops package')
            return

        pkg_path = os.path.dirname(pkg.__file__)
        for finder, name, ispkg in pkgutil.iter_modules([pkg_path]):
            if name.startswith('_'):
                continue
            try:
                mod = importlib.import_module(f'{crops_package}.{name}')
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, CropModel)
                        and attr is not CropModel
                    ):
                        instance = attr()
                        meta = instance.get_metadata()
                        crop_name = meta.get('crop', name)
                        self._registry[crop_name] = instance
                        print(f'[CropRegistry] Registered plugin: {crop_name} ({attr_name})')
                        break
            except Exception as e:
                print(f'[CropRegistry] Failed to load crop plugin {name}: {e}')

    def load_model(self, crop_name: str) -> bool:
        model = self._registry.get(crop_name)
        if model is None:
            print(f'[CropRegistry] No plugin found for crop: {crop_name}')
            return False
        return model.load(self.models_dir)

    def predict(self, crop_name: str, frame) -> list:
        model = self._registry.get(crop_name)
        if model is None:
            return []
        return model.predict(frame)

    def get_metadata(self, crop_name: str) -> dict:
        model = self._registry.get(crop_name)
        if model is None:
            return {}
        return model.get_metadata()

    def list_crops(self):
        return list(self._registry.keys())
