import datetime
import os

from gi.repository import Gtk

from constants import CARDS, DUELISTS, MAX_WON, MAX_DRAWN, MAX_LOST, MAX_TRUNK_COPIES, MAX_TRUNK_CARDS
from deck import InitialDeck
from enums import NextNationalChampionshipRound, CardColumn, DuelistColumn, MonsterType, DeckColor
from metadata import RESOURCES_DIR, __game_id__
from save import Save


def compute_card_usage(used, limit):
    limit = int(limit)
    return used * 100 / max(1, limit) if limit else 100


def partialmethod(f, **keywords):
    def inner(*args, **kwargs):
        new_kwargs = keywords.copy()
        new_kwargs.update(kwargs)
        return f(*args, **new_kwargs)
    return inner


class ApplicationWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(1000, 700)

        self.save = None
        self.unsaved = False

        handlers = {
            "misc_date_changed": self.on_misc_date_changed,
            "misc_national_championship_changed": self.on_misc_national_championship_changed,

            "card_trunk_editing_started": partialmethod(self.on_card_spin_editing_started, column=CardColumn.TRUNK),
            "card_main_extra_editing_started": partialmethod(self.on_card_spin_editing_started, column=CardColumn.MAIN_EXTRA),
            "card_side_editing_started": partialmethod(self.on_card_spin_editing_started, column=CardColumn.SIDE),
            "card_trunk_edited": partialmethod(self.on_card_spin_edited, column=CardColumn.TRUNK),
            "card_main_extra_edited": partialmethod(self.on_card_spin_edited, column=CardColumn.MAIN_EXTRA),
            "card_side_edited": partialmethod(self.on_card_spin_edited, column=CardColumn.SIDE),
            "card_password_toggled": self.on_card_password_toggled,

            "deck_move_to_trunk": self.on_deck_move_to_trunk,
            "deck_new_black": partialmethod(self.on_deck_new, color=DeckColor.BLACK),
            "deck_new_red": partialmethod(self.on_deck_new, color=DeckColor.RED),
            "deck_new_green": partialmethod(self.on_deck_new, color=DeckColor.GREEN),

            "duelist_won_editing_started": partialmethod(self.on_duelist_spin_editing_started, column=DuelistColumn.WON),
            "duelist_drawn_editing_started": partialmethod(self.on_duelist_spin_editing_started, column=DuelistColumn.DRAWN),
            "duelist_lost_editing_started": partialmethod(self.on_duelist_spin_editing_started, column=DuelistColumn.LOST),
            "duelist_won_edited": partialmethod(self.on_duelist_spin_edited, column=DuelistColumn.WON),
            "duelist_drawn_edited": partialmethod(self.on_duelist_spin_edited, column=DuelistColumn.DRAWN),
            "duelist_lost_edited": partialmethod(self.on_duelist_spin_edited, column=DuelistColumn.LOST),

            "duels_reset": self.on_duels_reset,
            "duels_unlock_duelists": self.on_duels_unlock_duelists,
            "duels_unlock_packs": self.on_duels_unlock_packs,
        }

        self.builder = Gtk.Builder()
        self.builder.add_from_file(str(RESOURCES_DIR / "app.glade"))
        self.builder.connect_signals(handlers)
        self.add(self.builder.get_object("root"))

        # Global objects
        self.adjustment = self.builder.get_object("adjustment")
        self.searchbar = self.builder.get_object("searchbar")
        self.searchentry = self.builder.get_object("searchentry")

        # General page
        nationals = (
            ("1st round",   NextNationalChampionshipRound.ROUND_1),
            ("2nd round",   NextNationalChampionshipRound.ROUND_2),
            ("Semi-finals", NextNationalChampionshipRound.SEMIFINALS),
            ("Final",       NextNationalChampionshipRound.FINAL),
        )

        self.misc_nationals = self.builder.get_object("misc-nationals")
        for index, (label, value) in enumerate(nationals):
            self.misc_nationals.insert(index, str(value.value), label)
        self.misc_date = self.builder.get_object("misc-date")

        self.stats_cards_total = self.builder.get_object("stats-cards-total")
        self.stats_cards_unique = self.builder.get_object("stats-cards-unique")
        self.stats_cards_unique_pct = self.builder.get_object("stats-cards-unique-pct")
        self.stats_cards_trunk = self.builder.get_object("stats-cards-trunk")
        self.stats_cards_trunk_pct = self.builder.get_object("stats-cards-trunk-pct")
        self.stats_cards_main = self.builder.get_object("stats-cards-main")
        self.stats_cards_main_pct = self.builder.get_object("stats-cards-main-pct")
        self.stats_cards_extra = self.builder.get_object("stats-cards-extra")
        self.stats_cards_extra_pct = self.builder.get_object("stats-cards-extra-pct")
        self.stats_cards_side = self.builder.get_object("stats-cards-side")
        self.stats_cards_side_pct = self.builder.get_object("stats-cards-side-pct")

        self.stats_duels_total = self.builder.get_object("stats-duels-total")
        self.stats_duels_won = self.builder.get_object("stats-duels-won")
        self.stats_duels_won_pct = self.builder.get_object("stats-duels-won-pct")
        self.stats_duels_drawn = self.builder.get_object("stats-duels-drawn")
        self.stats_duels_drawn_pct = self.builder.get_object("stats-duels-drawn-pct")
        self.stats_duels_lost = self.builder.get_object("stats-duels-lost")
        self.stats_duels_lost_pct = self.builder.get_object("stats-duels-lost-pct")

        # Cards page
        self.data_cards = self.builder.get_object("data-cards")
        for card in CARDS.values():
            self.data_cards.append([card.ID, card.Name, 0, 0, 0, False, 0.0, "0/{}".format(card.Limit)])

        # Duelists page
        self.data_duelists = self.builder.get_object("data-duelists")
        for duelist in DUELISTS.values():
            self.data_duelists.append([duelist.ID, duelist.Name, duelist.Stage.value, 0, 0, 0])

        self.on_open(None)
        self.connect("delete-event", self.on_quit)
        self.show_all()

    def update_title(self):
        title = "Save Editor for {}".format(__game_id__)
        if self.save.filename is not None:
            title += " ({})".format(os.path.basename(self.save.filename))
        if self.unsaved:
            title += " - UNSAVED"
        self.set_title(title)

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

    def confirm_data_loss(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
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
        new_value = datetime.date(*widget.get_date())
        if old_value != new_value:
            self.save.set_ingame_date(new_value)
            self.update_unsaved(True)

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
            # currently in use in case they were transferred there.
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
        # Clamp the value to the adjustement's bounds
        self.adjustment.set_value(int(value))
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

    def on_card_password_toggled(self, widget, path: str):
        self.update_unsaved(True)
        row = self.data_cards[path]
        value = not row[CardColumn.PASSWORD]
        card = self.save.get_detailed_cards_stats()[row[CardColumn.ID]]
        card.password = value
        row[CardColumn.PASSWORD] = value

    def on_deck_move_to_trunk(self, widget):
        if self.save.get_detailed_cards_stats().move_to_trunk():
            self.update_ui()
            self.update_unsaved(True)

    def on_deck_new(self, widget, color: DeckColor):
        self.save.get_detailed_cards_stats().reset_deck(InitialDeck(color))
        self.update_ui()
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
        # Clamp the value to the adjustement's bounds
        self.adjustment.set_value(int(value))
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

    def on_duels_reset(self, widget):
        stats = self.save.get_detailed_duelists_stats()
        for duelist in stats:
            duelist.won = duelist.drawn = duelist.lost = 0
        self.update_ui()
        self.update_unsaved(True)

    def on_duels_unlock_duelists(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="This feature has not been implemented yet!",
        )
        dialog.run()
        dialog.destroy()

    def on_duels_unlock_packs(self, widget):
        self.on_duels_unlock_duelists(widget)

    def on_search(self):
        self.searchbar.set_search_mode(True)
        self.searchentry.grab_focus()

    def on_open(self, filename: str):
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

    def update_ui(self):
        # - General
        self.misc_nationals.set_active_id(str(self.save.get_next_national_championship_round().value))
        ingame_date = self.save.get_ingame_date()
        self.misc_date.select_month(ingame_date.month, ingame_date.year)
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

    def on_save(self, filename: str):
        with open(filename, 'wb') as fd:
            self.save.dump(fd)
        self.clear_unsaved()

    def on_quit(self, *args):
        return not self.on_open(None)
