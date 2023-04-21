#!/usr/bin/python3
import gi
import sys

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk

from application import Application
from metadata import RESOURCES_DIR


def main():
    cssProvider = Gtk.CssProvider()
    cssProvider.load_from_path(str(RESOURCES_DIR / 'styles.css'))
    screen = Gdk.Screen.get_default()
    styleContext = Gtk.StyleContext()
    styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    Application().run(sys.argv)

if __name__ == "__main__":
    main()

