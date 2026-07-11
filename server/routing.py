from .models import RawItem


SOURCE_MODE = {
    "BBC Sport": "short",
    "Transfermarkt": "short",
    "World History Encyclopedia": "story",
    "The Football History Podcast": "story",
    "Holding Midfield": "story",
    "Spielverlagerung.com": "story",
    "American Songwriter": "story",

    "Far Out Magazine": "story",
    "Greek Reporter": "story",
    "Coaches' Voice": "story",
    "These Football Times": "story",
    "Achtung Radio": "story",
    "11v11": "story",

    "FabrizioRomanoTG": "short",
    "FootballHistor": "story",
    "ClassicRockNews": "story",
    "OasisProtocolFoundation": "short",
    "OasisProtocolCommunity": "short",
}


def get_mode_for_cluster(group: list[RawItem]) -> str:
    modes = {SOURCE_MODE.get(item.source_name, "story") for item in group}
    if len(modes) > 1:
        raise ValueError(
            f"Cluster has mixed modes: {modes} — sources: "
            f"{[item.source_name for item in group]}"
        )
    return modes.pop()
