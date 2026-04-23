from trame_client.widgets.core import Template
from trame_vuetify.widgets.vuetify3 import (
    VDivider,
    VList,
    VListItem,
    VMenu,
)

from .control_button import ControlButton

_EXPORT_FORMATS = [
    ("nrrd", "volume.nrrd", "画像 (.nrrd)"),
    ("nii.gz", "volume.nii.gz", "医用画像 (.nii.gz)"),
    None,
    ("seg.nrrd", "segmentation.seg.nrrd", "セグメンテーション (.seg.nrrd)"),
    None,
    ("stl", "segments_stl.zip", "3D メッシュ (.stl)"),
    ("obj", "segments_obj.zip", "3D テクスチャ (.obj)"),
]


class ExportButton(VMenu):
    def __init__(self, trigger_name: str, **kwargs):
        super().__init__(location="bottom start", close_on_content_click=True, **kwargs)

        with self:
            with Template(v_slot_activator="{ props }"):
                ControlButton(name="Export", icon="mdi-download", v_bind="props")

            with VList(density="compact"):
                for item in _EXPORT_FORMATS:
                    if item is None:
                        VDivider()
                    else:
                        fmt, filename, label = item
                        VListItem(
                            title=label,
                            click=(
                                f"utils.download('{filename}', "
                                f"trigger('{trigger_name}', ['{fmt}']), "
                                "'application/octet-stream')"
                            ),
                        )
