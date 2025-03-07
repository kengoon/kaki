# -*- coding: utf-8 -*-

from kivy.factory import Factory as F
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

Builder.load_string("""
<UI>:
    cols: 1
    Label:
        text: str(slider.value)
    Slider:
        id: slider
""")

class UI(GridLayout):
    pass
