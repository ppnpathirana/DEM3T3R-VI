"""
@file: test_desktop_launcher.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import runpy
from pathlib import Path
from unittest.mock import patch, MagicMock


def launcher():
    return runpy.run_path(str(Path(__file__).resolve().parents[1] / 'CropGuard_App.pyw'))


def test_window_fits_small_and_large_screens():
    geometry = launcher()['window_geometry']
    for screen_width, screen_height in [(1280, 720), (1478, 814), (1920, 1080)]:
        width, height, minimum = geometry(screen_width, screen_height)
        assert width < screen_width
        assert height < screen_height
        assert minimum[0] <= width
        assert minimum[1] <= height


def test_health_check_bypasses_proxy_and_checks_service_identity():
    check = launcher()['check_http_live']
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"service":"cropguard"}'
    opener = MagicMock()
    opener.open.return_value.__enter__.return_value = response
    with patch('urllib.request.ProxyHandler') as proxy, patch('urllib.request.build_opener', return_value=opener):
        assert check()
        proxy.assert_called_once_with({})
        response.read.return_value = b'{"service":"unrelated"}'
        assert not check()


def test_relaunch_restores_existing_window_without_starting_backend():
    namespace = launcher()
    main = namespace['main']
    with patch.dict(main.__globals__, restore_existing_window=lambda: True,
                    ensure_servers=lambda: (_ for _ in ()).throw(AssertionError('Backend must not be started'))):
        main()
