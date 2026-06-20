"""
world_memory.py
Manages persistent story world state across story generations.
"""


def empty_memory() -> dict:
    return {
        "characters": [],
        "locations": [],
        "events": [],
        "world_notes": "",
    }


def update_memory(existing: dict, story_data: dict) -> dict:
    """
    Merge new story data into world memory.
    Keeps unique characters and locations, appends events.
    """
    mem = existing.copy()
    
    # Merge characters (by name)
    existing_names = {c["name"] for c in mem["characters"]}
    for char in story_data.get("characters", []):
        if char["name"] not in existing_names:
            mem["characters"].append(char)
            existing_names.add(char["name"])
    
    # Merge locations
    existing_locs = set(mem["locations"])
    for loc in story_data.get("locations", []):
        if loc not in existing_locs:
            mem["locations"].append(loc)
            existing_locs.add(loc)
    
    # Append world notes as an event
    notes = story_data.get("world_notes", "")
    if notes and notes not in mem["events"]:
        mem["events"].append(notes)
    
    # Update world notes
    mem["world_notes"] = notes or existing.get("world_notes", "")
    
    return mem


def get_analytics(story_data: dict, images: list) -> dict:
    """Compute story analytics for the dashboard."""
    chapters = story_data.get("chapters", [])
    
    total_words = sum(
        len(ch.get("text", "").split())
        for ch in chapters
    )
    reading_time_min = max(1, round(total_words / 200))  # avg 200 wpm
    
    return {
        "chapters": len(chapters),
        "characters": len(story_data.get("characters", [])),
        "locations": len(story_data.get("locations", [])),
        "words": total_words,
        "reading_time": reading_time_min,
        "images_generated": sum(1 for img in images if img is not None),
    }
