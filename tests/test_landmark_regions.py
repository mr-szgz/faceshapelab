"""Topology coverage, persistent controls, and actual annotation colors."""

from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from test_analysis_ui import load, wait_idle, window  # noqa: F401

from faceshapelab.analysis_worker import image_array
from faceshapelab.face_analysis.landmarks import MODELS, POINT_COUNTS
from faceshapelab.face_analysis.regions import LANDMARK_REGIONS, REGION_LABELS
from faceshapelab.main import LANDMARK_COLORS, MainWindow


@pytest.mark.parametrize("model", MODELS)
def test_regions_partition_model_points(model):
    indices = [i for group in LANDMARK_REGIONS[model].values() for i in group]
    assert sorted(indices) == list(range(POINT_COUNTS[model]))
    assert set(LANDMARK_REGIONS[model]) <= REGION_LABELS.keys()


def test_color_controls_switch_and_persist(window, tmp_path):  # noqa: F811 -- pytest fixture
    selector = window.ui.landmarkDetectModelComboBox
    for model in MODELS:
        selector.setCurrentText(model)
        assert set(window.landmark_color_controls) == set(LANDMARK_REGIONS[model])
        for control in window.landmark_color_controls.values():
            assert control.currentText() == "yellow"
            assert control.accessibleName()
        window.landmark_color_controls["mouth"].setCurrentText("orange")
    selector.setCurrentText("203")
    window.landmark_color_controls["eyes"].setCurrentText("red")
    window.landmark_color_controls["nose"].setCurrentText("pink")
    selector.setCurrentText("68")
    assert window.landmark_color_controls["eyes"].currentText() == "yellow"
    selector.setCurrentText("203")
    assert window.landmark_color_controls["eyes"].currentText() == "red"
    window.settings.sync()
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    with patch("faceshapelab.main.QSettings", return_value=settings):
        reopened = MainWindow()
        assert reopened.ui.landmarkDetectModelComboBox.currentText() == "203"
        assert reopened.landmark_color_controls["nose"].currentText() == "pink"
        for model in MODELS:
            reopened.ui.landmarkDetectModelComboBox.setCurrentText(model)
            assert reopened.landmark_color_controls["mouth"].currentText() == "orange"
        reopened.close()
    assert all(QColor(name).isValid() for name in LANDMARK_COLORS)


@pytest.mark.models
def test_region_colors_use_result_model_in_both_views(window):  # noqa: F811 -- pytest fixture
    panel = window.ui.leftPanel
    load(window, panel)
    window.ui.landmarkDetectModelComboBox.setCurrentText("203")
    window.start_analysis(panel, "landmarks")
    wait_idle(window)
    result = window.face_results[panel][2][0]
    assert result.model == "203"
    window.ui.showLandmarksCheckBox.setChecked(True)
    window.landmark_color_controls["mouth"].setCurrentText("orange")
    for mode in ("Original", "Face"):
        window.ui.leftPreviewModeComboBox.setCurrentText(mode)
        orange = image_array(window.ui.leftImage.pixmap().toImage())
        window.landmark_color_controls["mouth"].setCurrentText("cyan")
        cyan = image_array(window.ui.leftImage.pixmap().toImage())
        changed = np.any(orange != cyan, axis=2)
        assert changed.any()
        assert cyan[changed, 2].mean() > orange[changed, 2].mean()
        window.ui.landmarkDetectModelComboBox.setCurrentText("68")
        window.landmark_color_controls["mouth"].setCurrentText("red")
        np.testing.assert_array_equal(
            image_array(window.ui.leftImage.pixmap().toImage()), cyan
        )
        window.ui.landmarkDetectModelComboBox.setCurrentText("203")
        window.landmark_color_controls["mouth"].setCurrentText("orange")
    QApplication.processEvents()
