# save-editor-AGB-AY5E

## Introduction

This program is a savegame editor for the US version of the GameBoy Advance title "Yu-Gi-Oh! - The Eternal Duelist Soul".
The program's name refers to the game's unique identifier inside the GBA cartridge's header.


## Available features

The editor can be used to:

*   Load and edit an existing savegame.
*   Create a new savegame from scratch.

Using this tool, you can:

*   Change the in-game date.
*   Change your qualification status for the in-game National Championship.
*   Edit the number of copies of any card present in the game in your trunk, main deck/fusion deck or side deck.
*   Display various pieces of information about the cards present in the game.
*   Edit the number of duels won/drawn/lost against each duelist you can face in the game.


## Installation

### Prerequisites

This program requires the following dependencies:

*   [Python 3.6 or later](https://www.python.org/downloads/)
*   [GTK version 3.24 or later](https://www.gtk.org/) -- Please note that GTK 4.x **IS NOT SUPPORTED**
*   [GObject Introspection (GI) framework](https://gi.readthedocs.io/en/latest/)
*   GObject Introspection Repository (GIR) for [GTK version 3](https://www.gtk.org/)
*   [Poetry](https://python-poetry.org/docs/#installation)

On Linux, the following commands can be used to install all of the dependencies listed above:

*   Debian/Ubuntu:

        sudo apt install \
            libgirepository1.0-dev \
            gir1.2-gtk-3.0 \
            python3-pip`

*   Fedora:

        sudo dnf install \
            gobject-introspection-devel \
            gtk3 \
            python3-pip

**Note:** support for Microsoft Windows has not been tested.

### Installation steps

1.  Grab and uncompress the [latest archive](https://github.com/fpoirotte/save-editor-AGB-AY5E/archive/refs/heads/main.tar.gz) for this program.
2.  Inside a shell, go to the folder where you extracted the files and run `pip install --user ./`


## Usage

To start the editor, run `~/.local/bin/save-editor-AGB-AY5E` inside a shell.

Information about how to use the editor can be found in the dedicated [documentation](./docs/Usage.md).

More information about the savegame's contents and layout can be found in the page dedicated to [technical details](./docs/TechnicalDetails.md).

## Transferring savegames from/to the game's cartridge

There are several methods and tools that can be used to transfer savegames between an actual GameBoy Advance cartridge and a computer.

If you've never done that before, the following post may be a good starting point:
https://projectpokemon.org/home/tutorials/save-editing/managing-gba-saves/using-gba-backup-tool-r55/


## Disclaimer

This program should only be used by people who legally own a copy of the original game.
I do not condone nor encourage software/video game piracy.

If you do not own a legitimate copy of the game, please uninstall this program from your computer immediately.


## License

This program is released under the MIT license.
See https://github.com/fpoirotte/save-editor-AGB-AY5E/blob/main/LICENSE for more information.
