import argparse
import calendar
import datetime
import functools
import os
import subprocess
import sys
import textwrap

from functools import partial

from gi.repository import Gio, Gtk, Gdk

from .constants import CARDS, DUELISTS, MAX_WON, MAX_DRAWN, MAX_LOST, MAX_TRUNK_COPIES, MAX_TRUNK_CARDS
from .decks import InitialDeck
from .enums import CardColumn, CardType, DeckColor, DuelistColumn, Event
from .enums import Limit, MonsterType, NextNationalChampionshipRound, NotebookPage
from .metadata import RESOURCES_DIR, __game_title__, __game_name__, __game_id__, __version__
from .save import Save


def compute_card_usage(used, limit):
    limit = int(limit)
    return used * 100 / max(1, limit) if limit else 100

class Application(Gtk.Application):
    CALENDAR = calendar.Calendar(calendar.SUNDAY)

    # The in-game delivery of "Weekly Yu-Gi-Oh!" follows the rules of japanese holidays,
    # AS THEY WERE when "Yu-Gi-Oh! Duel Monsters 5: Expert 1" (the japanese game
    # "Yu-Gi-Oh! The Eternal Duelist Soul" is based on) was released (~ July 2001).
    # When a delivery falls on a holiday, it will happen on the previous working day instead.
    # Sundays are considered non-working days.
    HOLIDAYS = (
        (1, 1),     # New Year's Day
        # Ignore Coming of Age Day (2nd Monday of January) as no event ever takes place on Mondays.
        (2, 11),    # National Foundation Day
        # Not entirely sure why February 24th is marked as a holiday in the game.
        # This could be a reference to Emperor Hirohito's funeral day dating 1989.
        (2, 24),    # ???
        # Ignore Vernal Equinox Day (at it changes every year and cannot be computed).
        (4, 29),    # Showa Day
        (5, 3),     # Constitution Memorial Day
        (5, 4),     # Greenery Day
        (5, 5),     # Children's Day
        # Marine Day used to be celebrated on July 20th back when the game was released.
        # It was later changed to the 3rd Monday of July starting in 2003.
        (7, 20),    # Marine Day
        (8, 11),    # Mountain Day
        # Respect for the Aged Day used to be celebrated on September 15th,
        # until it was changed to the 3rd Monday of September starting in 2003.
        (9, 15),
        # Ignore Autumnal Equinox Day (at it changes every year and cannot be computed).
        # Ignore Health and Sports Day (2nd Monday of October). See also Coming of Age Day.
        (11, 3),    # Culture Day
        (11, 23),   # Labor Thanksgiving Day
        (12, 23),   # The Emperor's Birthday (Emperor Akihito)
    )

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="net.erebot.save-editors.{}".format(__game_id__),
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.window = None
        self.save = None
        self.unsaved = False

    def do_startup(self):
        Gtk.Application.do_startup(self)

        actions = (
            ("new",                 self.on_new),
            ("open",                self.on_open),
            ("save",                self.on_save),
            ("save-as",             self.on_save_as),
            ("help",                self.on_help),
            ("about",               self.on_about),
            ("quit",                self.on_quit),
            ("tab-set-general",     partial(self.on_tab_set, tab=NotebookPage.GENERAL)),
            ("tab-set-cards",       partial(self.on_tab_set, tab=NotebookPage.CARDS)),
            ("tab-set-duelists",    partial(self.on_tab_set, tab=NotebookPage.DUELISTS)),
        )
        for name, cb in actions:
            action = Gio.SimpleAction(name=name)
            action.connect("activate", cb)
            self.add_action(action)

        builder = Gtk.Builder.new_from_file(str(RESOURCES_DIR / 'menu.glade'))
        self.set_menubar(builder.get_object("menubar"))

    def get_builder(self):
        handlers = {
            "quit_request": self.on_quit_request,

            "misc_date_changed": self.on_misc_date_changed,
            "misc_national_championship_changed": self.on_misc_national_championship_changed,

            "card_trunk_editing_started": partial(self.on_card_spin_editing_started, column=CardColumn.TRUNK),
            "card_main_extra_editing_started": partial(self.on_card_spin_editing_started, column=CardColumn.MAIN_EXTRA),
            "card_side_editing_started": partial(self.on_card_spin_editing_started, column=CardColumn.SIDE),
            "card_trunk_edited": partial(self.on_card_spin_edited, column=CardColumn.TRUNK),
            "card_main_extra_edited": partial(self.on_card_spin_edited, column=CardColumn.MAIN_EXTRA),
            "card_side_edited": partial(self.on_card_spin_edited, column=CardColumn.SIDE),
            "card_password_toggled": self.on_card_password_toggled,
            "card_row_activated": self.on_card_row_activated,

            "deck_move_to_trunk": self.on_deck_move_to_trunk,
            "deck_new_black": partial(self.on_deck_new, color=DeckColor.BLACK),
            "deck_new_red": partial(self.on_deck_new, color=DeckColor.RED),
            "deck_new_green": partial(self.on_deck_new, color=DeckColor.GREEN),

            "duelist_won_editing_started": partial(self.on_duelist_spin_editing_started, column=DuelistColumn.WON),
            "duelist_drawn_editing_started": partial(self.on_duelist_spin_editing_started, column=DuelistColumn.DRAWN),
            "duelist_lost_editing_started": partial(self.on_duelist_spin_editing_started, column=DuelistColumn.LOST),
            "duelist_won_edited": partial(self.on_duelist_spin_edited, column=DuelistColumn.WON),
            "duelist_drawn_edited": partial(self.on_duelist_spin_edited, column=DuelistColumn.DRAWN),
            "duelist_lost_edited": partial(self.on_duelist_spin_edited, column=DuelistColumn.LOST),

            "duels_reset": self.on_duels_reset,
            "duels_unlock_duelists": self.on_duels_unlock_duelists,
            "duels_unlock_packs": self.on_duels_unlock_packs,
        }

        builder = Gtk.Builder.new_from_file(str(RESOURCES_DIR / "application.glade"))
        builder.connect_signals(handlers)
        return builder

    def load_ui_data(self):
        # General page
        nationals = (
            ("1st round",   NextNationalChampionshipRound.ROUND_1),
            ("2nd round",   NextNationalChampionshipRound.ROUND_2),
            ("Semi-final",  NextNationalChampionshipRound.SEMI_FINAL),
            ("Final",       NextNationalChampionshipRound.FINAL),
        )

        for index, (label, value) in enumerate(nationals):
            self.misc_nationals.insert(index, str(value.value), label)

        # Cards page
        for card in CARDS.values():
            self.data_cards.append([card.ID, card.Name, 0, 0, 0, False, 0.0, "0/{}".format(card.Limit)])

        # Duelists page
        for duelist in DUELISTS.values():
            self.data_duelists.append([duelist.ID, duelist.Name, duelist.Stage.value, 0, 0, 0])

    def prepare_window(self, window, builder):
            actions = (
                (
                    "tab-next",
                    partial(self.on_tab_change, step=1),
                    [
                        "<Primary>Page_Down",
#                        "<Primary>Tab",
                    ],
                ),
                (
                    "tab-prev",
                    partial(self.on_tab_change, step=-1),
                    [
                        "<Primary>Page_Up",
#                        "<Primary><Shift>Tab",
                    ]
                ),
            )
            for name, cb, accels in actions:
                action = Gio.SimpleAction(name=name)
                action.connect("activate", cb)
                self.window.add_action(action)
                self.set_accels_for_action("win.{}".format(name), accels)

            self.adjustment = builder.get_object("adjustment")
            self.notebook = builder.get_object("notebook")

            self.misc_nationals = builder.get_object("misc-nationals")
            self.misc_date = builder.get_object("misc-date")

            self.stats_cards_total = builder.get_object("stats-cards-total")
            self.stats_cards_unique = builder.get_object("stats-cards-unique")
            self.stats_cards_unique_pct = builder.get_object("stats-cards-unique-pct")
            self.stats_cards_trunk = builder.get_object("stats-cards-trunk")
            self.stats_cards_trunk_pct = builder.get_object("stats-cards-trunk-pct")
            self.stats_cards_main = builder.get_object("stats-cards-main")
            self.stats_cards_main_pct = builder.get_object("stats-cards-main-pct")
            self.stats_cards_extra = builder.get_object("stats-cards-extra")
            self.stats_cards_extra_pct = builder.get_object("stats-cards-extra-pct")
            self.stats_cards_side = builder.get_object("stats-cards-side")
            self.stats_cards_side_pct = builder.get_object("stats-cards-side-pct")

            self.stats_duels_total = builder.get_object("stats-duels-total")
            self.stats_duels_won = builder.get_object("stats-duels-won")
            self.stats_duels_won_pct = builder.get_object("stats-duels-won-pct")
            self.stats_duels_drawn = builder.get_object("stats-duels-drawn")
            self.stats_duels_drawn_pct = builder.get_object("stats-duels-drawn-pct")
            self.stats_duels_lost = builder.get_object("stats-duels-lost")
            self.stats_duels_lost_pct = builder.get_object("stats-duels-lost-pct")

            self.data_cards = builder.get_object("data-cards")
            self.list_cards = builder.get_object("list-cards")
            self.data_duelists = builder.get_object("data-duelists")
            self.list_duelists = builder.get_object("list-duelists")

            self.load_ui_data()
            self.misc_date.set_detail_func(self.get_details_for_date)

            # Make sure all widgets are fully realized when this function returns
            self.window.show_all()

    @functools.lru_cache(maxsize=64)
    def get_events_for_month(self, year, month):
        # Note: it is possible for multiple events to happen on the same day
        # (e.g. Yu-Gi-Oh! Magazine & Weekly Yu-Gi-Oh! when the 21st day is a Tuesday).
        # Therefore, we use a list of lists to represent the events.
        month_events = []
        for week_in_month, days in enumerate(self.CALENDAR.monthdayscalendar(year, month), 1):
            for day in days:
                # Skip padding at the beginning/end of the month
                if not day:
                    continue

                date = datetime.date(year, month, day)
                weekday = date.weekday()
                events = []
                month_events.append(events)
                day_occurrence = (day - 1) // 7 + 1

                # 1st Saturday of June: Grandpa's Cup Qualifiers
                if weekday == calendar.SATURDAY and month == 6 and day_occurrence == 1:
                    events.append(Event.GRANDPA_QUALIFIERS)

                # At the start of the 2nd week of June: Grandpa's Cup Final
                elif weekday == calendar.SUNDAY and month == 6 and week_in_month == 2:
                    events.append(Event.GRANDPA_FINAL)

                # 2nd & 4th Saturday of the month: Weekend Duel
                if weekday == calendar.SATURDAY and day_occurrence in (2, 4):
                    events.append(Event.WEEKEND_DUEL)

                # 1st, 2nd, 3rd & 4th Sunday of November: National Championship
                elif weekday == calendar.SUNDAY and month == 11:
                    rounds = [
                        Event.NATIONALS_ROUND_1,
                        Event.NATIONALS_ROUND_2,
                        Event.NATIONALS_SEMI_FINAL,
                        Event.NATIONALS_FINAL,
                    ]
                    events.append(rounds[day_occurrence-1])

                # every Tuesday (or on the previous working day if it falls on a Sunday/holiday): Weekly Yu-Gi-Oh!
                elif weekday == calendar.TUESDAY:
                    curr_date = datetime.date(date.year, date.month, date.day)
                    while curr_date.weekday() == calendar.SUNDAY or (curr_date.month, curr_date.day) in self.HOLIDAYS:
                        curr_date -= datetime.timedelta(days=1)
                    if curr_date.month == month: # Protect against month swapping
                        month_events[curr_date.day-1].append(Event.WEEKLY_YUGIOH)

                # on the 21st (or on the previous working day if it falls on a Sunday/holiday): Yu-Gi-Oh! Magazine
                if day == 21:
                    curr_date = datetime.date(date.year, date.month, date.day)
                    while curr_date.weekday() == calendar.SUNDAY or (curr_date.month, curr_date.day) in self.HOLIDAYS:
                        curr_date -= datetime.timedelta(days=1)
                    if curr_date.month == month: # Protect against month swapping
                        month_events[curr_date.day-1].append(Event.YUGIOH_MAGAZINE)
        return month_events


    def get_details_for_date(self, widget, year, month, day):
        # Due to the observance of japanese holidays, it is easier to recreate
        # and cache the calendar for the whole month, then pick up the information we need,
        # rather that trying to compute the details for any given day directly.
        # Also, are 0-based in GTKCalendar while days are 1-based.
        events = self.get_events_for_month(year, month+1)
        day_events = events[day-1]
        return "\n".join(e.value for e in day_events) if day_events else None

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            builder = self.get_builder()
            self.window = builder.get_object("root")
            self.window.set_application(self)
            self.prepare_window(self.window, builder)

            # We do command-line parsing here, because the UI must be fully initialized
            # before we can actually load a save file.
            parser = argparse.ArgumentParser(prog="save-editor")
            parser.add_argument('filename', metavar='FILE', nargs="?", help="save file to load on startup")
            parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))
            opts = parser.parse_args(sys.argv[1:])

            self.load_save(opts.filename)

            # @HACK: Move calendar focus to current in-game day
            ingame_date = self.save.get_ingame_date()
            first = ingame_date.replace(day=1)
            move = (first.isoweekday() % 7) + (ingame_date - first).days + 1
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            keyboard = seat.get_keyboard()
            while move > 0:
                event = Gdk.Event().new(Gdk.EventType.KEY_PRESS)
                event.window = self.misc_date.get_window()
                event.type = Gdk.EventType.KEY_PRESS
                event.send_event = True
                event.time = Gdk.CURRENT_TIME
                event.keyval = Gdk.KEY_Right
                event.set_device(keyboard)
                event.put()
                move -= 1

        self.window.present()

    def do_command_line(self, command_line):
        self.activate()
        return 0

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
            if self.save.filename:
                dialog.set_current_folder(os.path.dirname(self.save.filename))
                dialog.set_current_name(os.path.basename(self.save.filename))
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
        self.load_save(None)

    def on_open(self, action, param):
        filename = self.select_file(False)
        if filename:
            self.load_save(filename)

    def on_save(self, action, param):
        if self.save.filename is None:
            return self.on_save_as(action, param)
        self.save_save(self.save.filename)

    def on_save_as(self, action, param):
        filename = self.select_file(True)
        if filename is None:
            return
        self.save_save(filename)

    def on_help(self, action, param):
        help_page = "https://github.com/fpoirotte/save-editor-{}/tree/main/docs/Usage.md".format(__game_id__)

        # Try calling GIO/GVFS handlers first.
        try:
            Gtk.show_uri_on_window(self.window, help_page, Gdk.CURRENT_TIME)
            return
        except Exception as e:
            print(e)

        # Fall back to xdg-open
        try:
            subprocess.check_call(["xdg-open", help_page])
            return
        except Exception as e:
            print(e)

        # Last resort: display a message with the help's URL
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text="This program's help can be read online at:\n" + help_page)
        dialog.run()
        dialog.destroy()

    def on_about(self, action, param):
        dialog = Gtk.AboutDialog(
            transient_for=self.window,
            logo_icon_name="gtk-edit",
            program_name="save-editor-{}".format(__game_id__),
            copyright="© 2023 - F. Poirotte",
            website="https://github.com/fpoirotte/save-editor-{}/".format(__game_id__),
            license_type=Gtk.License.MIT_X11,
            version=__version__,
            comments=textwrap.dedent('''\
                Game title: {}
                Internal name: {} / Game ID: {}
            ''').format(__game_title__, __game_name__, __game_id__),
            modal=True,
        )
        dialog.present()

    def on_quit_request(self, *args):
        # We attempt to load a new empty save, which will display a confirmation dialog if necessary.
        # Also, the return value determines if the default exit handler should be called (False) or not (True).
        return not self.load_save(None)

    def on_quit(self, *args):
        prevent_exit = self.on_quit_request()
        if not prevent_exit:
            self.window.destroy()

    def on_tab_change(self, action, param, step):
        nb_pages = self.notebook.get_n_pages()
        # Implement circular tab navigation
        self.notebook.set_current_page((self.notebook.get_current_page() + nb_pages + step) % nb_pages)

    def on_tab_set(self, action, param, tab):
        self.notebook.set_current_page(tab.value)

    def update_title(self):
        title = "Save Editor for {}".format(__game_id__)
        if self.save.filename is not None:
            title += " ({})".format(os.path.basename(self.save.filename))
        if self.unsaved:
            title += " - UNSAVED"
        self.window.set_title(title)

    def update_unsaved(self, unsaved: bool):
        self.unsaved |= unsaved
        self.update_title()

    def clear_unsaved(self):
        self.unsaved = False
        self.update_title()

    def update_cards_stats(self):
        stats = self.save.get_cards_stats()
        stats["unique_pct"] = stats["unique"] * 100 / stats["unique_max"]
        stats["trunk_max"] = MAX_TRUNK_CARDS
        stats["trunk_pct"] = stats["trunk"] * 100 / MAX_TRUNK_CARDS
        stats["main_pct"] = stats["main"] * 100 / stats["main_max"]
        stats["extra_pct"] = stats["extra"] * 100 / stats["extra_max"]
        stats["side_pct"] = stats["side"] * 100 / stats["side_max"]
        self.stats_cards_total.set_text("{total}".format(**stats))
        self.stats_cards_unique.set_text("{unique}/{unique_max}".format(**stats))
        self.stats_cards_unique_pct.set_text("({unique_pct:.2f}%)".format(**stats))
        self.stats_cards_trunk.set_text("{trunk}/{trunk_max}".format(**stats))
        self.stats_cards_trunk_pct.set_text("({trunk_pct:.2f}%)".format(**stats))
        self.stats_cards_main.set_text("{main}/{main_max}".format(**stats))
        self.stats_cards_main_pct.set_text("({main_pct:.2f}%)".format(**stats))
        self.stats_cards_extra.set_text("{extra}/{extra_max}".format(**stats))
        self.stats_cards_extra_pct.set_text("({extra_pct:.2f}%)".format(**stats))
        self.stats_cards_side.set_text("{side}/{side_max}".format(**stats))
        self.stats_cards_side_pct.set_text("({side_pct:.2f}%)".format(**stats))

    def update_duels_stats(self):
        stats = self.save.get_duelists_stats()
        adj_total = max(1, stats["total"])
        stats["won_pct"] = stats["won"] * 100 / adj_total
        stats["drawn_pct"] = stats["drawn"] * 100 / adj_total
        stats["lost_pct"] = stats["lost"] * 100 / adj_total
        self.stats_duels_total.set_text("{total}".format(**stats))
        self.stats_duels_won.set_text("{won}/{total}".format(**stats))
        self.stats_duels_won_pct.set_text("({won_pct:.2f}%)".format(**stats))
        self.stats_duels_drawn.set_text("{drawn}/{total}".format(**stats))
        self.stats_duels_drawn_pct.set_text("({drawn_pct:.2f}%)".format(**stats))
        self.stats_duels_lost.set_text("{lost}/{total}".format(**stats))
        self.stats_duels_lost_pct.set_text("({lost_pct:.2f}%)".format(**stats))

    def update_ui(self):
        # - General
        self.misc_nationals.set_active_id(str(self.save.get_next_national_championship_round().value))
        ingame_date = self.save.get_ingame_date()
        self.misc_date.select_month(ingame_date.month-1, ingame_date.year)
        self.misc_date.select_day(ingame_date.day)
        self.update_cards_stats()
        self.update_duels_stats()

        # - Cards
        stats = self.save.get_detailed_cards_stats()
        for row in self.data_cards:
            card = stats[row[CardColumn.ID]]
            row[CardColumn.TRUNK] = card.copiesTrunk
            row[CardColumn.MAIN_EXTRA] = card.copiesMainExtra
            row[CardColumn.SIDE] = card.copiesSide
            row[CardColumn.PASSWORD] = card.password
            used = card.copiesMainExtra + card.copiesSide
            limit = card.card.Limit
            row[CardColumn.USED] = compute_card_usage(used, limit)
            row[CardColumn.LIMIT] = "{}/{}".format(used, limit)

        # - Duelists
        stats = self.save.get_detailed_duelists_stats()
        for row in self.data_duelists:
            duelist = stats[row[DuelistColumn.ID]]
            row[DuelistColumn.WON] = duelist.won
            row[DuelistColumn.DRAWN] = duelist.drawn
            row[DuelistColumn.LOST] = duelist.lost

    def confirm_data_loss(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Warning: there are unsaved changes!",
        )
        dialog.format_secondary_text(
            'Choose "OK" to drop the changes and close the file.\n'
            'Choose "Cancel" to return to the file.'
        )
        response = dialog.run()
        dialog.destroy()
        return response

    def on_misc_date_changed(self, widget):
        old_value = self.save.get_ingame_date()
        year, month, day = widget.get_date()
        new_value = datetime.date(year, month+1, day)
        try:
            if old_value != new_value:
                self.save.set_ingame_date(new_value)
                self.update_unsaved(True)
        except ValueError:
            self.misc_date.select_month(old_value.month-1, old_value.year)
            self.misc_date.select_day(old_value.day)

    def on_misc_national_championship_changed(self, widget):
        old_value = self.save.get_next_national_championship_round()
        new_value = NextNationalChampionshipRound(widget.get_active_id())
        if old_value != new_value:
            self.save.set_next_national_championship_round(new_value)
            self.update_unsaved(True)

    def on_card_spin_editing_started(self, widget, button, path: str, column: CardColumn):
        row = self.data_cards[path]
        card = self.save.get_detailed_cards_stats()[row[CardColumn.ID]]
        stats = self.save.get_cards_stats()
        value = row[column.value]
        used = card.copiesMainExtra + card.copiesSide
        limits = [
            # There must still be enough room in the trunk to accomodate for all the copies
            # currently in use, in case they were transferred there later on.
            MAX_TRUNK_COPIES - int(card),
        ]

        if column != CardColumn.TRUNK:
            # The number of copies in use must not exceed the restriction set by in-game limitations.
            limits.append(card.card.Limit - used)

        if column == CardColumn.TRUNK:
            target = "trunk"
        elif column == CardColumn.SIDE:
            target = "side"
        elif column != CardColumn.MAIN_EXTRA:
            raise RuntimeError()
        elif card.card.MonsterType == MonsterType.FUSION:
            target = "extra"
        else:
            target = "main"

        # There must still be room left in the selected storage (deck)
        limits.append(stats[target + "_max"] - stats[target])
        upper = value + min(limits)
        self.adjustment.configure(value=value, lower=0, upper=upper, step_increment=1, page_increment=10, page_size=0)

    def on_card_spin_edited(self, widget, path: str, value: str, column: CardColumn):
        try:
            # Clamp the value to the adjustement's bounds
            self.adjustment.set_value(int(value))
        except ValueError:
            pass
        value = int(self.adjustment.get_value())
        row = self.data_cards[path]
        card = self.save.get_detailed_cards_stats()[row[CardColumn.ID]]
        limit = card.card.Limit

        if column == CardColumn.TRUNK:
            self.update_unsaved(value != card.copiesTrunk)
            card.copiesTrunk = value
        elif column == CardColumn.MAIN_EXTRA:
            self.update_unsaved(value != card.copiesMainExtra)
            card.copiesMainExtra = value
        elif column == CardColumn.SIDE:
            self.update_unsaved(value != card.copiesSide)
            card.copiesSide = value
        else:
            raise RuntimeError()

        used = card.copiesMainExtra + card.copiesSide
        row[column.value] = value
        row[CardColumn.USED] = compute_card_usage(used, limit)
        row[CardColumn.LIMIT] = "{}/{}".format(used, limit)
        self.update_cards_stats()

    def on_card_password_toggled(self, widget, path: str):
        self.update_unsaved(True)
        row = self.data_cards[path]
        value = not row[CardColumn.PASSWORD]
        card = self.save.get_detailed_cards_stats()[row[CardColumn.ID]]
        card.password = value
        row[CardColumn.PASSWORD] = value

    def on_card_row_activated(self, widget, path: str, column):
        row = self.data_cards[path]
        card = self.save.get_detailed_cards_stats()[row[CardColumn.ID]].card
        builder = Gtk.Builder.new_from_file(str(RESOURCES_DIR / "card.glade"))
        dialog = builder.get_object("root")
        grid = builder.get_object("grid")
        data = [("Name", card.Name), ("Card Number", "{:03}".format(card.ID))]
        restrictions = {
            Limit.LIMIT_0: "Cannot be used in\nmain/extra/side deck",
            Limit.LIMIT_1: "only 1 copy allowed\n(main/extra + side deck)",
            Limit.LIMIT_2: "only 2 copies allowed\n(main/extra + side deck)",
            Limit.LIMIT_3: "only 3 copies allowed\n(main/extra + side deck)",
        }

        if card.MonsterType:
            data.append(("Card Type", "{} {}".format(card.MonsterType.value, card.CardType.value)))
        else:
            data.append(("Card Type", card.CardType.value))

        if card.Password:
            data.append(("Password", card.Password))

        if card.CardType == CardType.MONSTER:
            data.extend([
                ("Level", card.Level.value),
                ("Attribute", card.Attribute.value),
                ("Monster Type", card.Type.value),
                ("ATK", card.ATK),
                ("DEF", card.DEF)
            ])

        data.append(("Restrictions", restrictions[int(card.Limit)]))

        for index, (name, value) in enumerate(data):
            grid.insert_row(index)
            label = Gtk.Label(xalign=0, yalign=0)
            label.set_markup("<b>{}:</b>".format(name))
            grid.attach(label, left=0, top=index, width=1, height=1)
            grid.attach(Gtk.Label(xalign=0, yalign=0, label=str(value)), left=1, top=index, width=1, height=1)

        dialog.set_transient_for(self.window)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def on_deck_move_to_trunk(self, widget):
        if self.save.get_detailed_cards_stats().move_to_trunk():
            self.update_cards_stats()
            self.update_unsaved(True)

    def on_deck_new(self, widget, color: DeckColor):
        self.save.get_detailed_cards_stats().reset_deck(InitialDeck(color))
        self.update_cards_stats()
        self.update_unsaved(True)

    def on_duelist_spin_editing_started(self, widget, button, path: str, column: DuelistColumn):
        value = int(self.data_duelists[path][column.value])
        upper = {
            DuelistColumn.WON: MAX_WON,
            DuelistColumn.DRAWN: MAX_DRAWN,
            DuelistColumn.LOST: MAX_LOST,
        }[column]
        self.adjustment.configure(value=value, lower=0, upper=upper, step_increment=1, page_increment=10, page_size=0)

    def on_duelist_spin_edited(self, widget, path: str, value: str, column: DuelistColumn):
        try:
            # Clamp the value to the adjustement's bounds
            self.adjustment.set_value(int(value))
        except ValueError:
            pass
        value = int(self.adjustment.get_value())
        row = self.data_duelists[path]
        duelist = self.save.get_detailed_duelists_stats()[row[DuelistColumn.ID]]

        if column == DuelistColumn.WON:
            self.update_unsaved(value != duelist.won)
            duelist.won = value
        elif column == DuelistColumn.DRAWN:
            self.update_unsaved(value != duelist.drawn)
            duelist.drawn = value
        elif column == DuelistColumn.LOST:
            self.update_unsaved(value != duelist.lost)
            duelist.lost = value
        else:
            raise RuntimeError()

        row[column.value] = value
        self.update_duels_stats()

    def on_duels_reset(self, widget):
        stats = self.save.get_detailed_duelists_stats()
        for duelist in stats:
            duelist.won = duelist.drawn = duelist.lost = 0
        self.update_duels_stats()
        self.update_unsaved(True)

    def on_duels_unlock_duelists(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="This feature has not been implemented yet!",
        )
        dialog.run()
        dialog.destroy()

    def on_duels_unlock_packs(self, widget):
        self.on_duels_unlock_duelists(widget)

    def load_save(self, filename: str):
        if self.unsaved and self.confirm_data_loss() != Gtk.ResponseType.OK:
            return False

        if filename is None:
            self.save = Save()
        else:
            with open(filename, 'rb') as fd:
                self.save = Save.load(fd)

        self.update_ui()
        self.clear_unsaved()
        return True

    def save_save(self, filename: str):
        with open(filename, 'wb') as fd:
            self.save.dump(fd)
        self.clear_unsaved()
