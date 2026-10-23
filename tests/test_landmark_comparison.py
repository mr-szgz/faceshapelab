"""Shape distance and selected-face comparison state."""

from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtWidgets import QLabel, QVBoxLayout
from skimage import transform
from test_analysis_ui import load, window  # noqa: F401

from faceshapelab.face_analysis.comparison import landmark_distance
from faceshapelab.face_analysis.landmarks import POINT_COUNTS
from faceshapelab.face_analysis.regions import LANDMARK_REGIONS, REGION_LABELS
from faceshapelab.main import SimilarityDelegate


@pytest.mark.parametrize(
    ("value", "display"),
    [(1.0, "100.00%"), (0.5, "50.00%"), (0.0, "0.00%"), (0.875, "87.50%"), (-1, "-1")],
)
def test_similarity_percentage_display(value, display):
    assert SimilarityDelegate().displayText(value, QLocale()) == display


def test_distance_invariance_symmetry_and_shape_change():
    points = np.array([[-3, 0], [-1, -1], [1, -0.8], [3, 0], [1, 1.5], [-1, 1]])
    original = points.copy()
    moved = transform.SimilarityTransform(
        scale=2.5, rotation=0.7, translation=(10, 20)
    )(points)
    assert landmark_distance(points, moved) == pytest.approx(0, abs=1e-14)
    changed = points.copy()
    changed[4, 1] += 1.2
    distance = landmark_distance(points, changed)
    assert 0 < distance < 1
    assert landmark_distance(changed, points) == pytest.approx(distance)
    assert landmark_distance(points, points * [-1, 1]) > 0.5
    np.testing.assert_array_equal(points, original)


def install_results(window, side, model):  # noqa: F811 -- pytest fixture
    panel = getattr(window.ui, side + "Panel")
    load(window, panel)
    points = np.random.default_rng(42).normal(size=(POINT_COUNTS[model], 2)) * 10 + 30
    changed = points.copy()
    changed[LANDMARK_REGIONS[model]["mouth"][0], 1] += 15
    points5 = np.array([[10, 10], [30, 10], [20, 20], [12, 30], [28, 30]])
    results = [
        SimpleNamespace(points=value, points5=points5, model=model)
        for value in (points, changed)
    ]
    window.analysis_panel = panel
    window.analysis_key = window.image_pixmaps[
        getattr(window.ui, side + "Image")
    ].cacheKey()
    window.analysis_worker.action = "landmarks"
    window.analysis_completed(
        (
            SimpleNamespace(
                boxes=np.array([[0, 0, 60, 60]] * 2),
                points5=np.array([points5] * 2),
                scores=np.array([0.9, 0.8]),
            ),
            results,
            [np.full((64, 64, 3), 80, dtype=np.uint8)] * 2,
            [np.array([[1, 0, 0], [0, 1, 0]])] * 2,
        )
    )
    return results


def scores(table):
    return {
        table.item(row, 0).text(): table.item(row, 1).data(Qt.ItemDataRole.DisplayRole)
        for row in range(table.rowCount())
    }


@pytest.mark.parametrize("model", POINT_COUNTS)
def test_all_model_regions_and_face_selections(window, model):  # noqa: F811
    window.ui.landmarkDetectModelComboBox.setCurrentText(model)
    table = window.ui.landmarkComparisonTable
    regions = LANDMARK_REGIONS[model]
    assert table.rowCount() == len(regions)
    assert set(scores(table)) == {REGION_LABELS[region] for region in regions}
    install_results(window, "left", model)
    right = install_results(window, "right", model)
    for region, indices in regions.items():
        assert scores(table)[REGION_LABELS[region]] == (1 if len(indices) > 2 else -1)
    window.ui.rightSelectedFaceComboBox.setCurrentIndex(1)
    if model != "5":
        assert 0 < scores(table)["Mouth"] < 1
    before = scores(table)
    for column in (0, 1):
        for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            table.sortItems(column, order)
            window.update_analysis_controls()
            assert scores(table) == before
            values = [
                table.item(row, column).data(Qt.ItemDataRole.DisplayRole)
                for row in range(table.rowCount())
            ]
            assert values == sorted(
                values, reverse=order == Qt.SortOrder.DescendingOrder
            )
    window.ui.leftSelectedFaceComboBox.setCurrentIndex(1)
    if model != "5":
        assert scores(table)["Mouth"] == 1
    right[1] = None
    window.update_analysis_controls()
    assert set(scores(table).values()) == {-1}


def test_model_and_media_changes_clear_comparison(window):  # noqa: F811
    window.ui.landmarkDetectModelComboBox.setCurrentText("68")
    install_results(window, "left", "68")
    install_results(window, "right", "68")
    table = window.ui.landmarkComparisonTable
    assert scores(table)["Mouth"] == 1
    window.ui.landmarkDetectModelComboBox.setCurrentText("203")
    assert scores(table)["Mouth"] == -1
    install_results(window, "left", "203")
    assert scores(table)["Mouth"] == -1
    install_results(window, "right", "203")
    assert scores(table)["Mouth"] == 1
    frame = QImage(100, 100, QImage.Format.Format_RGB32)
    frame.fill(0)
    window.display_frame(window.ui.rightPanel, QVideoFrame(frame))
    assert set(scores(table).values()) == {-1}


def test_embedding_table_persists_and_clears_with_face_changes(window):  # noqa: F811
    assert isinstance(window.ui.compareFacesLayout, QVBoxLayout)
    assert window.findChild(QLabel, "landmarkComparisonLabel") is None
    for table in (
        window.ui.embeddingComparisonTable,
        window.ui.landmarkComparisonTable,
    ):
        assert table.horizontalHeaderItem(1).text() == "Similarity"
        assert isinstance(table.itemDelegateForColumn(1), SimilarityDelegate)
    install_results(window, "left", "203")
    install_results(window, "right", "203")
    window.analysis_panel = window.ui.leftPanel
    window.analysis_key = window.image_pixmaps[window.ui.leftImage].cacheKey()
    window.comparison_right_key = window.image_pixmaps[window.ui.rightImage].cacheKey()
    window.analysis_worker.action = "recognize"
    window.analysis_worker.recognizer = "Inswapper128ArcFace"
    window.analysis_completed(87.5)
    table = window.ui.embeddingComparisonTable
    assert scores(table) == {"Inswapper128ArcFace": 0.875}
    assert table.isSortingEnabled()
    window.statusBar().showMessage("Other activity")
    window.redraw_analysis()
    assert scores(table) == {"Inswapper128ArcFace": 0.875}
    window.ui.rightSelectedFaceComboBox.setCurrentIndex(1)
    assert table.rowCount() == 0
    window.analysis_completed(75)
    load(window, window.ui.leftPanel)
    assert table.rowCount() == 0
