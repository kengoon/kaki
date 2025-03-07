import inspect
from kivy.app import App
from kaki.hotreload import HotReload
import main


def find_kivy_app_class():
    for name, obj in inspect.getmembers(main):
        if inspect.isclass(obj) and issubclass(obj, App) and obj is not App:
            return obj
    return None


HotReload = type("HotReload", (HotReload, find_kivy_app_class()), {})
HotReload.CLASSES = {
        "UI": "live.ui"
    }
HotReload.AUTORELOADER_PATHS = [
        (".", {"recursive": True}),
    ]

if __name__ == "__main__":
    HotReload().run()
