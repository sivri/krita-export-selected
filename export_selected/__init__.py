from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase
from .export_selected import ExportSelectedDocker

Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "export_selected",
        DockWidgetFactoryBase.DockRight,
        ExportSelectedDocker
    )
)