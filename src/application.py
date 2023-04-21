import argparse
import os
import textwrap

from gi.repository import Gio, Gtk

from metadata import RESOURCES_DIR, __game_title__, __game_name__, __game_id__, __version__
from save import Save
from window import ApplicationWindow


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="net.erebot.save-editors.AGB-AYSE",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.filename = None

        actions = (
            ("new",     self.on_new),
            ("open",    self.on_open),
            ("search",  self.on_search),
            ("save",    self.on_save),
            ("save-as", self.on_save_as),
            ("about",   self.on_about),
            ("quit",    self.on_quit),
        )
        for name, cb in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", cb)
            self.add_action(action)

        with (RESOURCES_DIR / 'menu.glade').open() as fd:
            menu = fd.read()
        builder = Gtk.Builder.new_from_string(menu, -1)
        self.set_menubar(builder.get_object("menubar"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = ApplicationWindow(application=self)

        self.window.present()

    def do_command_line(self, command_line):
        parser = argparse.ArgumentParser(prog="save-editor")
        parser.add_argument('filename', metavar='FILE', nargs="?", help="Path to a save file")
        parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))
        opts = parser.parse_args(command_line.get_arguments()[1:])

        self.activate()
        self.open_save(opts.filename)
        return 0

    def open_save(self, filename):
        if self.window.on_open(filename):
            self.filename = filename

    def select_file(self, save):
        dialog = Gtk.FileChooserDialog(
            title="Please select a file",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE if save else Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE if save else Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        if save:
            if self.filename:
                dialog.set_current_folder(os.path.dirname(self.filename))
                dialog.set_current_name(os.path.basename(self.filename))
            dialog.set_do_overwrite_confirmation(True)

        allowed_types = (
            ("GBA save (*.sav)", "*.sav"),
            ("All files", "*"),
        )
        for name, ext in allowed_types:
            f = Gtk.FileFilter()
            f.set_name(name)
            f.add_pattern(ext)
            dialog.add_filter(f)

        response = dialog.run()
        filename = None
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        return filename

    def on_new(self, action, param):
        self.open_save(None)

    def on_open(self, action, param):
        filename = self.select_file(False)
        if filename:
            self.open_save(filename)

    def on_save(self, action, param):
        if self.filename is None:
            return self.on_save_as(action, param)
        self.window.on_save(self.filename)

    def on_save_as(self, action, param):
        filename = self.select_file(True)
        if filename is None:
            return
        self.filename = filename
        self.window.on_save(self.filename)

    def on_search(self, action, param):
        self.window.on_search()

    def on_about(self, action, param):
        dialog = Gtk.AboutDialog(
            logo_icon_name="gtk-edit",
            program_name=__game_title__,
            copyright="© 2023 - F. Poirotte",
            website="https://github.com/fpoirotte/save-editor-{}/".format(__game_id__),
            license_type=Gtk.License.MIT_X11,
            version=__version__,
            comments=textwrap.dedent('''\
                Game ID: {}
                Internal name: {}
            ''').format(__game_id__, __game_name__),
            transient_for=self.window,
            modal=True,
        )
        dialog.present()

    def on_quit(self, action, param):
        if not self.window.on_quit():
            self.window.destroy()

