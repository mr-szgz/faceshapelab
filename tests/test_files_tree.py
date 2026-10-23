import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QPersistentModelIndex, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTreeView

from faceshapelab.files_tree import FilesTreeModel


class FilesTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, condition):
        for _ in range(200):
            self.app.processEvents()
            if condition():
                return
            QTest.qWait(10)
        self.fail("Tree did not finish updating")

    def test_folder_shortcuts_expand_independently_and_drag_target_files(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            tempfile.TemporaryDirectory(
                dir=Path(__file__).resolve().parents[1]
            ) as shortcuts,
        ):
            root = Path(folder)
            links = Path(shortcuts) / "links"
            target = root / "target"
            links.mkdir()
            (target / "nested").mkdir(parents=True)
            (target / "nested" / "photo.png").write_bytes(b"image")
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "$shell = New-Object -ComObject WScript.Shell; "
                        "foreach ($name in @('First', 'Second')) { "
                        "$link = $shell.CreateShortcut((Join-Path $env:SHORTCUT_TEST_LINKS ($name + '.lnk'))); "
                        "$link.TargetPath = Join-Path $env:SHORTCUT_TEST_ROOT 'target'; $link.Save() }"
                    ),
                ],
                env={
                    **os.environ,
                    "SHORTCUT_TEST_ROOT": folder,
                    "SHORTCUT_TEST_LINKS": str(links),
                },
                check=True,
                capture_output=True,
            )
            model = FilesTreeModel()
            tree = QTreeView()
            tree.setModel(model)
            tree.setRootIndex(model.setRootPath(str(links)))
            tree.show()
            self.wait_for(lambda: model.rowCount(tree.rootIndex()) == 2)
            first = model.index(0, 0, tree.rootIndex())
            second = model.index(1, 0, tree.rootIndex())
            self.assertEqual(first.data(), "First.lnk")
            self.assertTrue(model.hasChildren(first))
            tree.expand(first)
            tree.expand(second)
            self.wait_for(lambda: model.rowCount(first) == 1)
            nested = model.index(0, 0, first)
            other_nested = model.index(0, 0, second)
            self.assertEqual(nested.parent(), first)
            self.assertEqual(other_nested.parent(), second)
            self.assertNotEqual(nested, other_nested)
            tree.expand(nested)
            self.wait_for(lambda: model.rowCount(nested) == 1)
            photo = model.index(0, 0, nested)
            self.assertEqual(
                Path(model.mimeData([photo]).urls()[0].toLocalFile()),
                target / "nested" / "photo.png",
            )
            tree.collapse(first)
            self.assertFalse(tree.isExpanded(first))
            self.assertTrue(tree.isExpanded(second))
            tree.expand(first)
            selected = QPersistentModelIndex(nested)
            model.sort(0, Qt.SortOrder.DescendingOrder)
            self.wait_for(
                lambda: model.index(0, 0, tree.rootIndex()).data() == "Second.lnk"
            )
            self.assertEqual(selected.parent().data(), "First.lnk")
            (target / "new").mkdir()
            self.wait_for(
                lambda: model.rowCount(first) == 2 and model.rowCount(second) == 2
            )
            self.assertEqual(selected.data(), "nested")
            self.assertTrue(tree.isExpanded(selected.parent()))
            (target / "new").rmdir()
            self.wait_for(
                lambda: model.rowCount(first) == 1 and model.rowCount(second) == 1
            )
            (links / "First.lnk").unlink()
            self.wait_for(lambda: model.rowCount(tree.rootIndex()) == 1)
            self.assertFalse(selected.isValid())
            self.assertEqual(model.index(0, 0, tree.rootIndex()).data(), "Second.lnk")
            tree.close()
            tree.setModel(None)
