# Usage

## Interface Overview

The interface is divided in 3 parts:

1.  At the top, the menu bar gives access to basic actions (see below)
2.  Right below the menu bar, a notebook with several tabs can be used to switch between the editor's various views
3.  The rest of the screen displays the currently selected view

Available menus:

*   `File` menu: create, load or save a savegame; exit the editor
*   `View` menu: switch between the views (same as clicking on the corresponding tab in the notebook)
*   `Help` menu: display this help file or display information about the editor

The following global keyboard shortcuts are also supported:

*   `Alt+F`: open/close the `File` menu
*   `Ctrl+N`: create a new savegame
*   `Ctrl+O`: load an existing savegame file
*   `Ctrl+S`: save the current savegame
*   `Ctrl+Shift+S`: save the current savegame under a new name
*   `Ctrl+Q` or `Alt+F4`: quit the editor
*   `Alt+V`: open/close the `View` menu
*   `Alt+H`: open/close the `Help` menu
*   `F1`: display the help (this file)
*   `Alt+G`: go to the `General Information` view
*   `Alt+C`: go to the `Cards` view
*   `Alt+D`: go to the `Duelists` view
*   `Ctrl+PageUp` / `Ctrl+PageDown`: go to the previous/next view (circular)
*   `Shift+Tab` / `Tab`: give the focus to the previous/next field in the view
*   `Up` / `Down`: while in a menu, move to the previous/next menu entry
*   `Space` or `Enter`: while in a menu, activate the selected menu entry
*   `Escape`: while in a menu, close the menu

In addition, when the `About...` dialog (from the `Help` menu) is shown, either the `Escape` key or `Alt+F4` can be used to close the dialog.

If you try to create/load a new savegame or exit the editor while there are unsaved changes, a confirmation dialog will be shown:

![Confirmation dialog for unsaved changes](unsaved_changes.png)

The `Left` / `Right` arrow keys can be used to move between the `Cancel` and `OK` buttons.
Pressing the `Enter` or `Space` key will activate the currently focused button.


## Views

### General Information

!["General Information" view](general_info.png)

This view allows the game's general settings to be customized:

*   Current in-game date. The calendar also shows what in-game events are set to occur on each date (such as delivery of the Yu-Gi-Oh! Magazine).
*   Round in the November National Championship the player has qualified for.

**Note:** the in-game date cannot be set to a value before January 1st, 2001, nor after June 6th, 2180.

The view also shows various statistics about the player's progress:

*   Statistics about the total number of cards obtained, how many unique cards have been collected, and so on.
*   Statistics about the total number of duels played, and how many duels have been won, drawn & lost.

The following keyboard shortcuts can also be used while on this view:

*   while focus is on the `Current date in the game` field:
    *   `Left` / `Right` arrow keys: move to the previous/next day
    *   `Ctrl+Left` / `Ctrl+Right`: move to the previous/next month
    *   `Up` / `Down` arrow keys: move to the previous/next week
    *   `Ctrl+Up` / `Ctrl+Down`: move to the previous/next year
    *   `Space`: if the currently focused day refers to a day in the previous/next month, move to that month. Otherwise, select the focused day

*   while focus is on the `National Championship qualification` field:
    *   `Space` or `Enter`: if the dropdown is closed, open it (display the list of values). Otherwise, select the currently focus value
    *   `Up` / `Down` arrow keys: move the focus to the previous/next value in the list


### Cards

!["Cards" view](cards.png)

This view can be used to:

*   View bits of information about a card present in the game.
*   Change the number of copies of a card inside the trunk, main deck/extra deck, or side deck.

**Note:** the editor applies the same limitations as the game. Therefore you may not have more than 3 copies of a card in your deck (including side deck).
In addition, some cards may be further limited. In some cases, a card may be completely forbidden and cannot be added to the main deck/extra deck or side deck at all.
This is the case for the following cards:

*   #814 - The Monarchy
*   #815 - Set Sail for the Kingdom
*   #816 - Glory of the King's Hand
*   #817 - Obelisk the Tormenter
*   #818 - Slifer the Sky Dragon
*   #819 - The Winged Dragon of Ra
*   #820 - Insect Monster Token

In addition, several buttons at the bottom of the view can be used to edit the deck "en masse":

*   `Move all to trunk` moves every card currently in any of the decks to the trunk.
*   `New Deck (Black)`, `New Deck (Red)` & `New Deck (Green)` clear the trunk and deck, then create a brand new deck.
    The content of the new deck will be similar to that of the Black, Red and Green decks the player can choose from at the very beginning of the game, respectively.

The following keyboard shortcuts can also be used while on this view:

*   while focus is on the cards list:
    *   `Up` / `Down` arrow keys: move to the previous/next row in the list
    *   `PageUp` / `PageDown`: move to the previous/next page (in 10-entries increments) in the list
    *   `Space` or `Enter`:
        *   while a cell in the `ID`, `Name` or `Deck usage` columns is focused: display the card's information dialog (see below)
        *   while a cell in the `Trunk`, `Main/Extra deck` or `Side deck` columns is focused: edit the value
            (enter the new value, then press `Enter` to validate or `Escape` to cancel) 
        *   while a cell in the `Password used?` column is focused: toggle the checkbox between the checked/unchecked states
        *   has no effect otherwise
    *   any other key will start a (case-insensitive) search for cards whose name starts with the given text

*   while focus is on the search bar:
    *   `Enter` or `Escape`: close the search bar

*   while focus is on one of the buttons are the button of the screen:
    *   `Space` or `Enter`: activate the button

#### Card Information

!["Card Information" dialog](card_info.png)

This dialog is shown when a card's ID, name or deck usage is double clicked.

It display various pieces of information about the selected card, such as its type (Monster, Trap or Magic) and the in-game password required to unlock the card.
For monsters, additional data is shown such as the monster's level, attribute, type, ATK/DEF points and so on.

The following keyboard shortcuts can also be used while this dialog is shown:

*   `Escape` or `Alt+F4`: close the dialog (return to the card list)

### Duelists

!["Duelists" view](duelists.png)

This view can be used to:

*   Edit how many duels have been won, drawn or lost to each of the game's duelist.

In addition, several buttons at the bottom of the view can be used to lock/unlock some features:

*   `Reset` sets the number of duels won, drawn & lost to 0 (zero) for every duelist.
*   `Unlock duelists` unlocks every duelist available in the game.
*   `Unlock packs` unlocks every pack available in the game.

**Note:** the `Reset` button also resets the list of duelists and packs available to the player (only those initially unlocked will be available).

The following keyboard shortcuts can also be used while on this view:

*   while focus is on the duelists list:
    *   `Up` / `Down`: move to the previous/next row in the list
    *   `PageUp` / `PageDown`: move to the previous/next page (in 10-entries increments) in the list
    *   `Space` or `Enter`:
        *   while a cell in the `Won`, `Drawn` or `Lost` columns is focused: edit the value
            (enter the new value, then press `Enter` to validate or `Escape` to cancel) 
        *   has no effect otherwise
    *   any other key will start a (case-insensitive) search for duelists whose name starts with the given text

*   while focus is on the search bar:
    *   `Enter` or `Escape`: close the search bar

*   while focus is on one of the buttons are the button of the screen:
    *   `Space` or `Enter`: activate the button

