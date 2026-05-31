import threading
from typing import Callable
import pystray
from PIL import Image, ImageDraw

_COLORS = {
    "idle":      "#6b7280",
    "recording": "#e94560",
    "typing":    "#0a84ff",
}


def _make_icon_image(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([8, 8, 56, 56], fill=color)
    return img


class TrayIcon:
    def __init__(
        self,
        on_open: Callable,
        on_quit: Callable,
    ) -> None:
        self._icon = pystray.Icon(
            "MurmurAI",
            _make_icon_image(_COLORS["idle"]),
            "MurmurAI",
            menu=pystray.Menu(
                pystray.MenuItem("Open", lambda icon, item: on_open(), default=True),
                pystray.MenuItem("Quit", lambda icon, item: on_quit()),
            ),
        )

    def start(self) -> None:
        threading.Thread(target=self._icon.run, daemon=True).start()

    def set_state(self, state_name: str) -> None:
        self._icon.icon = _make_icon_image(_COLORS.get(state_name, _COLORS["idle"]))

    def stop(self) -> None:
        self._icon.stop()
