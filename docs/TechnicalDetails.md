# Technical details

## Overview

The gamepak uses a flash 128K memory chip to back the game up, but the actual savegame is only 8560 (0x2170) bytes long.
Moreover, when the game starts, it will copy the savegame's data to the on-board work RAM at 0x02011C20.
The following events cause the savegame to be written back to the gamepak's flash memory:

*   A duel/match ends (in case of a victory, this happens after the player has received a booster pack and left the screen where the pack's content is displayed)
*   The player leaves the deck editor
*   A card has been successfully traded with another player using the cable link
*   A password has been successfully used to receive a card

## Savegame layout

For convenience, the following table lists offsets relative to the start of the savegame (first column) and the absolute address to their counterpart in the on-board work RAM (second column).
Similarly, a type with an equavalent size in the [C language](https://en.wikipedia.org/wiki/C_(programming_language)) is provided for convenience (fourth column).

**Notes:**

*   Offsets and addresses are expressed in [hexadecimal notation](https://en.wikipedia.org/wiki/Hexadecimal), indicated by the `0x` prefix
*   Sizes are expressed in bytes
*   Integer values are stored in [Little-Endian](https://en.wikipedia.org/wiki/Endianness) byte order
*   All values are represented in [Most Significant Bit first](https://en.wikipedia.org/wiki/Bit_numbering) order

<table>
<thead>
<tr>
<td>Offset</td>
<td>Address</td>
<td>Size</td>
<td>Type</td>
<td>Name</td>
<td>Description</td>
</tr>
</thead>

<tbody>
<tr>
<td>0x0000</td>
<td>0x02011C20</td>
<td>4</td>
<td>u32</td>
<td></td>
<td>Unused (always equal to 0)</td>
</tr>

<tr>
<td>0x0004</td>
<td>0x02011C24</td>
<td>1</td>
<td>u8</td>
<td><tt>language</tt></td>
<td>
Language and alphabet selection

-- bits 0-3: language
    0=English   (en_US)
    1=Japanese  (jp_JP)
    2=German    (de_DE)
    3=French    (fr_FR)
    4=Italian   (it_IT)
    In practice, this field is not used (the translation effort was scraped
    before the final game release) and is always equal to 1 (Japanese).
-- bits 4-6: unused
-- bit 7: 0=use latin alphabet / 1=use japanese alphabet
</td>
</tr>

<tr>
<td>0x0005</td>
<td>0x02011C25</td>
<td>3</td>
<td>u8[3]</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x0008</td>
<td>0x02011C28</td>
<td>3284</td>
<td>u32[821]</td>
<td><tt>stats_cards</tt></td>
<td>
Statistics about each card.
See the section about <a href="#card-statistics">card statistics</a> for more information on what each entry contains.
The cards are stored in the order of their ID, starting with card #000 (a dummy card) and ending with card #820 (Insect Monster Token).
See <tt>cards.csv</tt> in the editor's resource files for the full list of cards.
</td>
</tr>

<tr>
<td>0x0CDC</td>
<td>0x020128FC</td>
<td>4908</td>
<td>u8[4908]</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x2008</td>
<td>0x02013C28</td>
<td>120</td>
<td>u16[60]</td>
<td><tt>deck_main</tt></td>
<td>
List of cards in the player's Main Deck.
Unused
</td>
</tr>

<tr>
<td>0x2080</td>
<td>0x02013CA0</td>
<td>30</td>
<td>u16[15]</td>
<td><tt>deck_side</tt></td>
<td>List of cards in the player's Side Deck.</td>
</tr>

<tr>
<td>0x209E</td>
<td>0x02013CBE</td>
<td>40</td>
<td>u16[20]</td>
<td><tt>deck_extra</tt></td>
<td>List of cards in the player's Extra Deck.</td>
</tr>

<tr>
<td>0x20C6</td>
<td>0x02013CE6</td>
<td>2</td>
<td>u16</td>
<td><tt>nb_trunk</tt></td>
<td>Number of cards in the player's Trunk.</td>
</tr>

<tr>
<td>0x20C8</td>
<td>0x02013CE8</td>
<td>2</td>
<td>u16</td>
<td><tt>nb_main</tt></td>
<td>Number of cards in the player's Main Deck.</td>
</tr>

<tr>
<td>0x20CA</td>
<td>0x02013CEA</td>
<td>2</td>
<td>u16</td>
<td><tt>nb_side</tt></td>
<td>Number of cards in the player's Side Deck.</td>
</tr>

<tr>
<td>0x20CC</td>
<td>0x02013CEC</td>
<td>2</td>
<td>u16</td>
<td><tt>nb_extra</tt></td>
<td>Number of cards in the player's Extra Deck.</td>
</tr>

<tr>
<td>0x20CE</td>
<td>0x02013CEE</td>
<td>2</td>
<td>u8[2]</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x20D0</td>
<td>0x02013CF0</td>
<td>200</td>
<td>u32[25]</td>
<td><tt>stats_duelists</tt></td>
<td>
Statistics about each duelist.
See the section about <a href="#duelist-statistics">duelist statistics</a> for more information on what each entry contains.
The duelists are stored in the order of their ID, starting with duelist #00 (a dummy dummy) and ending with duelist #24 (Trusdale).
See <tt>duelists.csv</tt> in the editor's resource files for the full list of duelists.
</td>
</tr>


<tr>
<td>0x2134</td>
<td>0x02013D54</td>
<td>28</td>
<td>u8[28]</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x2150</td>
<td>0x02013D70</td>
<td>2</td>
<td>u16</td>
<td><tt>days_elapsed</tt></td>
<td>
How many in-game days have passed since the beginning of the game (2001-01-01).
Time inside the game when 2100-12-32 is reached.
</td>
</tr>

<tr>
<td>0x2152</td>
<td>0x02013D72</td>
<td>2</td>
<td>u16</td>
<td><tt>static_value</tt></td>
<td>
This value is a bitfield with the following flags:

*   bit 0: unknown
*   bit 1: unknown
*   bits 2-7: unused

Both bit 0 and bit 1 are set to 1 at the start of new game.
These flags are never used by the game.
</td>
</tr>

<tr>
<td>0x2154</td>
<td>0x02013D74</td>
<td>2</td>
<td>u16</td>
<td><tt>last_pack</tt></td>
<td>
ID of the last booster pack received by the player.
See <tt>packs.csv</tt> in the editor's resource files for the full list of booster packs.
See also <tt>publication_victories</tt> below for reasons why this value may be significant.
</td>
</tr>

<tr>
<td>0x2156</td>
<td>0x02013D76</td>
<td>2</td>
<td>u16</td>
<td><tt<publication_victories</tt></td>
<td>
How many duels have been won since the last Weekly Yu-Gi-Oh! or Yu-Gi-Oh! Magazine was received.
The booster pack in the next Weekly Yu-Gi-Oh! or Yu-Gi-Oh! Magazine issue will always container a Normal Rare, Secret Rare or Ultra Rare card if either of the following conditions is met:

*   The player has won more than 6 duels and the next booster pack to be received is different from the last booster pack received
*   The player has won more than 10 duels and the next booster pack to be received is the same as the last booster pack received

The last booster pack received in indicated by the <tt>last_pack</tt> field above.
</td>
</tr>

<tr>
<td>0x2158</td>
<td>0x02013D78</td>
<td>2</td>
<td>u16</td>
<td><tt>last_duelist</tt></td>
<td>
ID of the last duelist the player has defeated.
See <tt>duelists.csv</tt> in the editor's resource files for the full list of duelists.

This field has no real significance in the game.
If the player challenges the same duelist they just defeated, the game will change the dialogs to make it look like the opponent wants a rematch.
</td>
</tr>

<tr>
<td>0x215A</td>
<td>0x02013D7A</td>
<td>4</td>
<td>u8[4]</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x215E</td>
<td>0x02013D7E</td>
<td>2</td>
<td>u16</td>
<td><tt>qualification_nationals</tt></td>
<td>
The National Championship is held every year in November.
This field indicates what round the the player has qualified for in this tournament:

* 0 = first qualifying round
* 1 = second qualifying round
* 2 = semi final
* 3 = final
</td>
</tr>

<tr>
<td>0x2160</td>
<td>0x02013D80</td>
<td>2</td>
<td>u16</td>
<td><tt>qualification_grandpa_cup</tt></td>
<td>
The Grandpa Cup is held every year in June.
This field indicates what round the the player has qualified for in this tournament:

* 0 = first qualifying round
* 1 = final
</td>
</tr>

<tr>
<td>0x2162</td>
<td>0x02013D82</td>
<td>1</td>
<td>s8</td>
<td><tt>nationals_victories</tt></td>
<td>
How many times the player won the National Championship.
Because times stops in the game once 2100-12-31 is reached, the maximum possible value here is 100.
</td>
</tr>

<tr>
<td>0x2163</td>
<td>0x02013D83</td>
<td>1</td>
<td>u8</td>
<td></td>
<td>Unused (padding) = 0x00</td>
</tr>

<tr>
<td>0x2164</td>
<td>0x02013D84</td>
<td>2</td>
<td>u16</td>
<td><tt>announcements</tt></td>
<td>
This bitfield controls some in-game announcements:

* bit 0: when this bit is set, an announcement will be made about the availability of new duelists the next time the player goes to the game's "Campaign" menu.
* bit 1: when this bit is set, an announcement will be made about the availability of a new Booster Pack the next time the player wins a duel.
* bit 2-15: unused
</td>
</tr>

<tr>
<td>0x2166</td>
<td>0x02013D86</td>
<td>8</td>
<td>u8[8]</td>
<td><tt>game_id</tt></td>
<td>
This field contains the static string <tt>DMEX1INT</tt>.
It is used when loading a savegame to make sure it is meant for this video game.
</td>
</tr>

<tr>
<td>0x216E</td>
<td>0x02013D8E</td>
<td>2</td>
<td>u16</td>
<td><tt>checksum</tt></td>
<td>
A checksum over the whole savegame to make sure it is valid.
This is used to protect the game against data corruption.
See the section entitled [checksum](#checksum) for more information on how to compute this checksum.
</td>
</tr>

<tr>
<td>0x2170</td>
<td>0x02013D90</td>
<td></td>
<td></td>
<td></td>
<td>End of the savegame.</td>
</tr>
</tbody>
</table>

## Card statistics

Statistics about each card are stored as a series of 32-bit values where the bits for each value are used as follows:

s* bits 0-9: number of copies of the card in the Trunk
* bits 10-11: number of copies of the card in the Main Deck
* bits 12-13: number of copies of the card in the Side Deck
* bits 14-15: number of copies of the card in the Extra Deck
* bit 16: unused
* bit 17: set if a password was used to receiving this card
* bits 18-31: unused

## Duelist statistics

Statistics about each duelist are stored as a series of 32-bit values where the bits for each value are used as follows:

* bits 0-10: number of duels won against that duelist
* bits 11-21: number of duels drawn against that duelist
* bits 22-31: number of duels lost against that duelist

## Checksum

The game uses a simple [sum complement checksum](https://en.wikipedia.org/wiki/Checksum#Sum_complement) to detect data corruption.
To compute the checksum:

*   Divide the savegame into 16-bits words
*   Sum all words together (discarding any overflow bits)
*   Flip all the bits in the resulting value (i.e. apply a XOR operation between this value and 0xFFFF)
*   Add 1 to this result and discard any overflow bit to get the final value

