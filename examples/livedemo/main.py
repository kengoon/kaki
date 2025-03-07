# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.factory import Factory


class Live(App):
    def build(self):
        return Factory.UI()


if __name__ == "__main__":
    Live().run()