import os
os.environ["DEBUG"] = "1"
import inspect
from kivy.app import App
from kaki.hotreload import HotReload
import main


def find_kivy_app_class():
    for name, obj in inspect.getmembers(main):
        if inspect.isclass(obj) and issubclass(obj, App) and obj is not App:
            return obj
    return None


def find_all_kv_files():
    """
    Recursively find KV files from the selected directory.
    """
    kv_files = []
    for path_to_dir, dirs, files in os.walk("."):
        if (
            "venv" in path_to_dir
            or ".buildozer" in path_to_dir
        ):
            continue
        for name_file in files:
            if (
                os.path.splitext(name_file)[1] == ".kv"
                and name_file != "style.kv"  # if use PyInstaller
                and "__MACOS" not in path_to_dir  # if use Mac OS
            ):
                path_to_kv_file = os.path.join(path_to_dir, name_file)
                kv_files.append(path_to_kv_file)
    return kv_files


HotReload = type("HotReload", (HotReload, find_kivy_app_class()), {})
HotReload.KV_FILES = find_all_kv_files()

if __name__ == "__main__":
    hotreload = HotReload()
    hotreload.run()
