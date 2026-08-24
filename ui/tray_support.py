"""System tray — optional (Pillow + pystray)."""
from __future__ import annotations

import threading


class TrayHelper:
    def __init__(self, app) -> None:
        self.app = app
        self.available = False
        self._icon = None
        self._thread = None
        try:
            import pystray  # noqa: F401
            from PIL import Image, ImageDraw  # noqa: F401

            self._pystray = __import__("pystray")
            self._Image = __import__("PIL.Image", fromlist=["Image"]).Image
            self._ImageDraw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
            self.available = True
            self.start()
        except Exception:
            self.available = False

    def _image(self):
        img = self._Image.new("RGB", (64, 64), "#0d1117")
        d = self._ImageDraw.Draw(img)
        d.ellipse((10, 10, 54, 54), fill="#3fb950")
        return img

    def start(self) -> None:
        if not self.available or self._icon:
            return
        Menu = self._pystray.Menu
        Item = self._pystray.MenuItem

        def show(icon, item):
            self.app.root.after(0, self.app.root.deiconify)

        def start_asf(icon, item):
            self.app.root.after(0, lambda: self.app.process_mgr.start())

        def stop_asf(icon, item):
            def _():
                try:
                    self.app.ipc.exit_asf()
                except Exception:
                    pass
                self.app.process_mgr.stop()

            self.app.root.after(0, _)

        def quit_app(icon, item):
            icon.stop()
            self.app.root.after(0, self.app.exit_app)

        menu = Menu(
            Item("Abrir ASF Desktop", show, default=True),
            Item("Executar ASF", start_asf),
            Item("Parar ASF", stop_asf),
            Item("Encerrar ASF Desktop", quit_app),
        )
        self._icon = self._pystray.Icon("asf_desktop", self._image(), "ASF Desktop", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
