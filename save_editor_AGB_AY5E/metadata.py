import pathlib
from importlib.metadata import version

__game_title__ = "Yu-Gi-Oh! - The Eternal Duelist Soul"
__game_name__ = "YU-GI-OH!EDS"
__game_id__ = 'AGB-AY5E'
__version__ = version("save_editor_AGB_AY5E")

RESOURCES_DIR = pathlib.Path(__file__).parent / "resources"

