import importlib.util
import shutil
import subprocess
import sys
from configparser import ConfigParser
from os import makedirs
from os.path import exists, dirname, join
from time import sleep

import psutil

from kaki import ArgumentParserWithHelp
from watchdog.observers import Observer

processes = []


def is_scrcpy_installed():
    try:
        subprocess.run(["scrcpy", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return True  # Command exists but failed, meaning scrcpy is installed


def run_server():
    from kaki.server import KivyFileListener

    handler = KivyFileListener()
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()

    def cleanup():
        handler.server.stop_server()
        observer.stop()
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        observer.join()
        shutil.move("app.py", "main.py")
        if exists("kaki"):
            shutil.rmtree("kaki")
        if exists("watchdog"):
            shutil.rmtree("watchdog")
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if "adb" in process.info["name"]:
                process.terminate()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        cleanup()
    except Exception:
        cleanup()
        raise


def main():
    parser = ArgumentParserWithHelp(
        prog="kaki",
        allow_abbrev=False,
        description="Kaki CLI Tool for Hot Reloading and APK Building"
    )
    parser.add_argument("run", help="Run Kaki hot reload")
    parser.add_argument("--build", action="store_true", help="Build APK before running Kaki")

    args = parser.parse_args()
    if "run" != args.run:
        parser.print_help()
        parser.exit(1)
    if not exists("main.py"):
        sys.exit("'main.py' not found")
    if not exists("buildozer.spec"):
        sys.exit("'buildozer.spec' not found")

    config = ConfigParser()
    config.read("buildozer.spec")
    if not config.getboolean("app", "android.no-byte-compile-python", fallback=False):
        sys.exit("uncomment or set 'android.no-byte-compile-python' to True in buildozer.spec")
    if "kaki" in config.get("app", "requirements", fallback=""):
        sys.exit("remove 'kaki' from buildozer.spec requirements. It's auto managed")

    subprocess.run("adb devices", shell=True)
    print("running: adb reverse tcp:5567 tcp:5567")
    subprocess.Popen(["adb", "reverse", "tcp:5567", "tcp:5567"])
    if not exists("app.py"):
        print("Moving: main.py to app.py")
        sleep(1)
        shutil.copy("main.py", "main.py.orig")
        shutil.move("main.py", "app.py")
        print("MOVED: main.py to app.py")
        sleep(1)
    shutil.copy(join(dirname(__file__), "main.py.tmp"), "main.py")

    kaki_dir = "kaki"
    if exists(kaki_dir):
        shutil.rmtree(kaki_dir)
    makedirs(kaki_dir)
    shutil.copy(join(dirname(__file__), "hotreload.py"), join(kaki_dir, "hotreload.py"))

    # copy watchdog to working dir for buildozer to bundle with app
    package_name = "watchdog"
    spec = importlib.util.find_spec(package_name)
    if spec and spec.origin:
        if exists("watchdog"):
            shutil.rmtree("watchdog")
        shutil.copytree(spec.submodule_search_locations[0], "watchdog")

    if args.build:
        print("\n🔧 Running Buildozer...")
        proc = subprocess.Popen(["buildozer", "android", "debug", "deploy", "run", "logcat"])
        processes.append(proc)
    else:
        proc = subprocess.Popen(["buildozer", "android", "deploy", "run", "logcat"])
        processes.append(proc)

    if is_scrcpy_installed():
        print("scrcpy is installed ✅")
        subprocess.run("alias adb=~/.buildozer/android/platform/android-sdk/platform-tools/adb", shell=True)
        proc = subprocess.Popen(["scrcpy", "--always-on-top"])
        processes.append(proc)
    else:
        print("scrcpy is NOT installed ❌")

    run_server()


if __name__ == "__main__":
    main()
