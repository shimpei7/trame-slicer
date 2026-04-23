from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from slicer import vtkMRMLSegmentationNode, vtkMRMLSegmentationStorageNode, vtkMRMLVolumeNode
from trame_server import Server

from trame_slicer.core import SlicerApp

from .base_logic import BaseLogic


class ExportButtonLogic(BaseLogic):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, None)
        self._trigger_name = server.controller.trigger_name(self._export_file)

    @property
    def trigger_name(self) -> str:
        return self._trigger_name

    async def _export_file(self, fmt: str):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            if fmt in ("nrrd", "nii.gz"):
                data = self._export_volume(tmp_path, fmt)
            elif fmt == "seg.nrrd":
                data = self._export_segmentation(tmp_path)
            elif fmt == "stl":
                data = self._export_surface_files(tmp_path, "stl")
            elif fmt == "obj":
                data = self._export_surface_files(tmp_path, "obj")
            else:
                return None

            if data is None:
                return None

            return self._server.protocol.addAttachment(data)

    def _get_first_volume(self) -> vtkMRMLVolumeNode | None:
        nodes = self._slicer_app.scene.GetNodesByClass("vtkMRMLVolumeNode")
        nodes.InitTraversal()
        return nodes.GetNextItemAsObject()

    def _get_first_segmentation(self) -> vtkMRMLSegmentationNode | None:
        nodes = self._slicer_app.scene.GetNodesByClass("vtkMRMLSegmentationNode")
        nodes.InitTraversal()
        return nodes.GetNextItemAsObject()

    def _export_volume(self, tmp_path: Path, ext: str) -> bytes | None:
        volume = self._get_first_volume()
        if not volume:
            return None
        out_file = tmp_path / f"volume.{ext}"
        self._slicer_app.io_manager.write_volume(volume, out_file)
        return out_file.read_bytes() if out_file.exists() else None

    def _export_segmentation(self, tmp_path: Path) -> bytes | None:
        seg = self._get_first_segmentation()
        if not seg:
            return None
        out_file = tmp_path / "segmentation.seg.nrrd"
        storage = vtkMRMLSegmentationStorageNode()
        storage.SetFileName(out_file.as_posix())
        storage.WriteData(seg)
        return out_file.read_bytes() if out_file.exists() else None

    def _export_surface_files(self, tmp_path: Path, ext: str) -> bytes | None:
        seg = self._get_first_segmentation()
        if not seg:
            return None
        out_dir = tmp_path / ext
        out_dir.mkdir()

        if ext == "stl":
            self._slicer_app.segmentation_editor.export_segmentation_to_stl(
                seg, out_dir.as_posix()
            )
        else:
            self._slicer_app.segmentation_editor.export_segmentation_to_obj(
                seg, out_dir.as_posix()
            )

        files = sorted(out_dir.glob(f"*.{ext}"))
        if not files:
            return None

        zip_path = tmp_path / f"segments_{ext}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, f.name)
        return zip_path.read_bytes()
