# Kaki - Advanced application library for Kivy

This library enhance Kivy frameworks with opiniated features such as:

- Auto reloading kv or py (`watchdog` required, limited to some uses cases)
- Idle detection support
- Foreground lock (windows only)

## Installation
```shell
pip install https://github.com/kengoon/kaki/releases/download/v1.0.1/kaki_cli-1.0.1-py3-none-any.whl
```

## Example

This is a bootstrap that will:
- automatically declare the module `live.ui` (`live/ui.py`) as a provider for the widget `UI`
- build the application widget, and show it to a window

If the bootstrap is started with the environment variable `DEBUG=1`, it will start a watchdog, and listen for changes, according to `AUTORELOADER_PATHS`.
When something changes, the current application widget will be cleared out, and a new one will be instanciated, after reloading.

```shell
kaki run # deploy app and run hotreload
kaki run --build # build, deploy and run hotreload
```

## Idle Management

The idle detection feature is designed to trigger an action if the user has not touched the screen for a certain period of time. This can be used to display an attractor screen, screensaver, or other content.

To enable idle detection, set the `IDLE_DETECTION` configuration to `True`.
Kaki will then listen for touch down/move events. If no such events occur within the `IDLE_TIMEOUT` interval, or if the `rearm_idle` function has not been called, the `on_idle` event will be triggered on the application class. If a touch event occurs or `rearm_idle` is called while the system is in idle mode, the `on_wakeup` event will be triggered on the application class.

If you are playing a video and do not want idle detection to be triggered, you can use the `rearm_idle` function on the application class to reset the idle timer to 0 seconds.