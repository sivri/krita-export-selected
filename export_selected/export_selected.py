import os
import re

from krita import DockWidget, Krita
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QSpinBox, QCheckBox, QMessageBox, QComboBox
)


class ExportSelectedDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Export Selected")

        self.settings = QSettings("MoonBurnTools", "ExportSelected")

        root = QWidget()
        layout = QVBoxLayout()

        # Export folder
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Export Folder"))

        self.folder_edit = QLineEdit()
        self.folder_edit.setText(self.settings.value("folder", ""))
        folder_row.addWidget(self.folder_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)
        folder_row.addWidget(browse_btn)

        layout.addLayout(folder_row)

        # Scale
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Export Scale %"))

        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(1, 400)
        self.scale_spin.setValue(int(self.settings.value("scale", 100)))
        scale_row.addWidget(self.scale_spin)

        layout.addLayout(scale_row)

        # Resize quality
        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Resize Quality"))

        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Crisp / Pixel Sharp", "crisp")
        self.quality_combo.addItem("Smooth / Painted", "smooth")

        saved_quality = self.settings.value("quality", "crisp")
        index = self.quality_combo.findData(saved_quality)
        if index >= 0:
            self.quality_combo.setCurrentIndex(index)

        quality_row.addWidget(self.quality_combo)
        layout.addLayout(quality_row)

        # Padding
        pad_row = QHBoxLayout()
        pad_row.addWidget(QLabel("Padding"))

        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 512)
        self.padding_spin.setValue(int(self.settings.value("padding", 16)))
        pad_row.addWidget(self.padding_spin)

        layout.addLayout(pad_row)

        # Options
        self.trim_check = QCheckBox("Auto trim transparent space")
        self.trim_check.setChecked(self.settings.value("trim", "true") == "true")
        layout.addWidget(self.trim_check)

        self.merge_check = QCheckBox("Merge groups when exporting")
        self.merge_check.setChecked(self.settings.value("merge", "true") == "true")
        layout.addWidget(self.merge_check)

        # Export button
        export_btn = QPushButton("Export Selected")
        export_btn.clicked.connect(self.export_selected)
        layout.addWidget(export_btn)

        # Status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        root.setLayout(layout)
        self.setWidget(root)

    def canvasChanged(self, canvas):
        pass

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Export Folder",
            self.folder_edit.text() or ""
        )

        if folder:
            self.folder_edit.setText(folder)

    def export_selected(self):
        app = Krita.instance()
        doc = app.activeDocument()

        if not doc:
            QMessageBox.warning(self, "No Document", "Open a document first.")
            return

        if doc.colorModel() != "RGBA" or doc.colorDepth() != "U8":
            QMessageBox.warning(
                self,
                "Unsupported Document",
                "This exporter expects an RGBA / U8 document."
            )
            return

        folder = self.folder_edit.text().strip()

        if not folder:
            QMessageBox.warning(self, "No Folder", "Choose an export folder.")
            return

        # Do not create folders automatically.
        # You said you want control over folders.
        if not os.path.exists(folder):
            QMessageBox.warning(
                self,
                "Folder Does Not Exist",
                "Choose an existing folder. This exporter will not create folders automatically."
            )
            return

        scale = self.scale_spin.value()
        padding = self.padding_spin.value()
        trim = self.trim_check.isChecked()
        merge_groups = self.merge_check.isChecked()
        quality = self.quality_combo.currentData()

        self.settings.setValue("folder", folder)
        self.settings.setValue("scale", scale)
        self.settings.setValue("padding", padding)
        self.settings.setValue("trim", "true" if trim else "false")
        self.settings.setValue("merge", "true" if merge_groups else "false")
        self.settings.setValue("quality", quality)

        nodes = []

        if hasattr(doc, "activeNodes"):
            nodes = doc.activeNodes()

        if not nodes:
            node = doc.activeNode()
            if node:
                nodes = [node]

        if not nodes:
            QMessageBox.warning(self, "No Selection", "Select one or more layers or groups.")
            return

        exported = 0
        skipped = []

        for node in nodes:
            ok, reason = self.export_node(
                doc,
                node,
                folder,
                scale,
                padding,
                trim,
                merge_groups,
                quality
            )

            if ok:
                exported += 1
            else:
                skipped.append(f"{node.name()}: {reason}")

        msg = f"Exported {exported} item(s)."

        if skipped:
            msg += "\n\nSkipped:\n" + "\n".join(skipped)

        self.status_label.setText(msg)

    def export_node(self, doc, node, folder, scale, padding, trim, merge_groups, quality):
        name = self.clean_file_name(node.name())

        if not name:
            return False, "Invalid name"

        if trim:
            b = node.bounds()

            if b.width() <= 0 or b.height() <= 0:
                return False, "Empty bounds"

            left = max(0, b.x() - padding)
            top = max(0, b.y() - padding)
            right = min(doc.width(), b.x() + b.width() + padding)
            bottom = min(doc.height(), b.y() + b.height() + padding)

            width = right - left
            height = bottom - top
        else:
            left = 0
            top = 0
            width = doc.width()
            height = doc.height()

        if width <= 0 or height <= 0:
            return False, "Invalid export size"

        use_projection = merge_groups or node.type() == "grouplayer"

        try:
            if use_projection:
                raw = node.projectionPixelData(left, top, width, height)
            else:
                raw = node.pixelData(left, top, width, height)
        except Exception as e:
            return False, str(e)

        if raw is None:
            return False, "No pixel data"

        img = QImage(raw, width, height, width * 4, QImage.Format_RGBA8888).copy()

        if img.isNull():
            return False, "Failed to build image"

        if scale != 100:
            new_w = max(1, round(width * scale / 100.0))
            new_h = max(1, round(height * scale / 100.0))

            if quality == "crisp":
                transform_mode = Qt.FastTransformation
            else:
                transform_mode = Qt.SmoothTransformation

            img = img.scaled(
                new_w,
                new_h,
                Qt.IgnoreAspectRatio,
                transform_mode
            )

        out_path = os.path.join(folder, name + ".png")
        ok = img.save(out_path, "PNG")

        if not ok:
            return False, "Failed to save PNG"

        return True, ""

    def clean_file_name(self, name):
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        name = name.rstrip(". ")
        return name