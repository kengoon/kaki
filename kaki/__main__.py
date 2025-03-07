import shutil
import subprocess
import sys
from os.path import exists, dirname, join
from time import sleep

import psutil

from kaki import ArgumentParserWithHelp
from watchdog.observers import Observer
from kaki.server import KivyFileListener

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
    handler = KivyFileListener()
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        handler.server.stop_server()
        observer.stop()
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
    observer.join()
    shutil.move("app.py", "main.py")
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "adb" in process.info["name"]:\
            process.terminate()  # or process.kill()


def main():
    parser = ArgumentParserWithHelp(
        prog="kaki",
        allow_abbrev=False,
        description="Kaki CLI Tool for Hot Reloading and APK Building"
    )
    parser.add_argument("run", help="Run Kaki hot reload", nargs="?")
    parser.add_argument("--build", action="store_true", help="Build APK before running Kaki")

    args = parser.parse_args()
    if not exists("main.py"):
        sys.exit("'main.py' not found")
    if not exists("buildozer.spec"):
        sys.exit("'buildozer.spec' not found")
    subprocess.run("adb devices", shell=True)
    print("running: adb reverse tcp:5567 tcp:5567")
    subprocess.Popen(["adb", "reverse", "tcp:5567", "tcp:5567"])
    shutil.copy("main.py", "main.py.orig")
    shutil.move("main.py", "app.py")
    shutil.copy(join(dirname(__file__), "main.py.tmp"), "main.py")

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
