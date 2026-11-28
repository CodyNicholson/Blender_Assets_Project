"""Procedural alternate styles for every Hangar ship that had fewer than three styles.

Each style builds its parent ship from story_ships or fleet_ships, remaps its
palette swatches to a contrasting theme, optionally applies subtle proportional
reshaping (to both verts and sockets), and adds hull-anchored silhouette accents.
"""
from mathutils import Vector

import fleet_ships
import palette
import story_ships


def _q(hq, high, low):
    return high if hq else low


def _hull_extents(mb):
    """Derives solid hull anchor coordinates from built vertices and base sockets."""
    xs = [v.x for v in mb.verts]
    ys = [v.y for v in mb.verts]
    zs = [v.z for v in mb.verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    length = max(4.0, max_y - min_y)

    dc = mb.sockets.get("deck_centre")
    bl = mb.sockets.get("boarding_L")
    dc_z = dc.z if dc is not None else min_z + (max_z - min_z) * 0.45
    bl_x = abs(bl.x) if bl is not None else max(2.2, (max_x - min_x) * 0.35)

    # Find solid midship hull half-width near the deck/hull band.
    mid_band = [
        abs(v.x)
        for v in mb.verts
        if abs(v.y) <= length * 0.22 and (min_z + 0.2) <= v.z <= (dc_z + 0.6)
    ]
    mid_x = min(bl_x * 1.15, max(mid_band)) if mid_band else bl_x
    mid_x = max(1.6, mid_x)

    # Find solid bow Y/Z inside the central hull band (ignores thin forward antennas/sprits).
    bow_verts = [
        v
        for v in mb.verts
        if abs(v.x) <= mid_x * 0.75 and (min_z + 0.25) <= v.z <= (dc_z + 0.9)
    ]
    if bow_verts:
        bow_v = min(bow_verts, key=lambda v: v.y)
        bow_y = bow_v.y
        bow_z = max(min_z + 0.8, min(dc_z - 0.1, bow_v.z))
    else:
        bow_y = min_y + length * 0.08
        bow_z = min_z + (dc_z - min_z) * 0.65

    # Find solid stern Y inside the central hull band.
    stern_verts = [
        v
        for v in mb.verts
        if abs(v.x) <= mid_x * 0.75 and (min_z + 0.25) <= v.z <= (dc_z + 0.9)
    ]
    stern_y = max(v.y for v in stern_verts) if stern_verts else (max_y - length * 0.08)

    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "min_z": min_z,
        "max_z": max_z,
        "length": length,
        "dc_z": dc_z,
        "mid_x": mid_x,
        "bow_y": bow_y,
        "bow_z": bow_z,
        "stern_y": stern_y,
    }


def _accent_spiked_prow_fins(mb, ext, hq, c_main, c_trim):
    by, bz, dz = ext["bow_y"], ext["bow_z"], ext["dc_z"]
    ln, mx = ext["length"], ext["mid_x"]
    sy = ext["stern_y"]
    fwd = max(1.6, ln * 0.10)
    mb.plate(
        [
            (0.0, by + 1.5, bz - 0.3),
            (0.0, by - fwd, bz + 0.35),
            (0.0, by + 1.0, bz + 0.9),
            (0.0, by + 1.8, bz + 0.2),
        ],
        0.22,
        c_trim,
    )
    for sign in (1, -1):
        mb.plate(
            [
                (sign * mx * 0.25, by + 2.2, bz),
                (sign * mx * 0.75, by + 0.8, bz + 0.45),
                (sign * mx * 0.45, by - fwd * 0.55, bz + 0.15),
                (sign * mx * 0.20, by + 1.4, bz - 0.15),
            ],
            0.14,
            c_main,
        )
    mb.plate(
        [
            (0.0, sy - 2.6, dz - 0.45),
            (0.0, sy - 0.4, dz - 0.45),
            (0.0, sy + 0.3, dz + 1.8),
            (0.0, sy - 1.5, dz + 1.3),
        ],
        0.16,
        c_main,
    )


def _accent_swept_winglets(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    by, bz = ext["bow_y"], ext["bow_z"]
    wz = max(ext["min_z"] + 0.8, dz * 0.74)
    span = max(1.8, mx * 0.52)
    for sign in (1, -1):
        rx = sign * mx * 0.52
        tx = sign * (mx + span)
        mb.plate(
            [
                (rx, -ln * 0.08, wz),
                (tx, ln * 0.14, wz + 0.45),
                (tx, ln * 0.24, wz + 0.35),
                (rx, ln * 0.12, wz - 0.05),
            ],
            0.14,
            c_main,
        )
        mb.tube((rx, -ln * 0.06, wz), (tx, ln * 0.16, wz + 0.4), 0.11, 0.05, sides=_q(hq, 5, 3), color=c_trim)
    mb.plate(
        [
            (0.0, by + 1.2, bz - 0.15),
            (0.0, by - max(1.1, ln * 0.06), bz + 0.2),
            (0.0, by + 0.9, bz + 0.55),
        ],
        0.14,
        c_trim,
    )


def _accent_dorsal_crest_wings(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    sy = ext["stern_y"]
    wz = max(ext["min_z"] + 0.8, dz * 0.78)
    span = max(1.5, mx * 0.42)
    for sign in (1, -1):
        rx = sign * mx * 0.55
        tx = sign * (mx + span)
        mb.plate(
            [
                (rx, sy - ln * 0.20, wz),
                (tx, sy - ln * 0.02, wz + 0.65),
                (tx, sy + ln * 0.05, wz + 0.50),
                (rx, sy - ln * 0.04, wz - 0.08),
            ],
            0.14,
            c_main,
        )
    mb.plate(
        [
            (0.0, -ln * 0.30, dz - 0.35),
            (0.0, -ln * 0.10, dz - 0.35),
            (0.0, -ln * 0.12, dz + 1.35),
            (0.0, -ln * 0.26, dz + 0.85),
        ],
        0.16,
        c_trim,
    )


def _accent_armored_sponsons(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    by, bz = ext["bow_y"], ext["bow_z"]
    sz = max(ext["min_z"] + 0.9, dz * 0.64)
    sh = max(1.2, (dz - ext["min_z"]) * 0.48)
    sl = max(3.6, ln * 0.26)
    for sign in (1, -1):
        sx = sign * (mx * 0.82)
        mb.box((sx, 0.0, sz), (1.15, sl, sh), c_main, top_scale=0.86)
        mb.box((sx + sign * 0.48, 0.0, sz + sh * 0.15), (0.28, sl * 0.85, 0.32), c_trim)
    mb.box((0.0, by + 0.35, bz), (mx * 0.55, 1.35, max(0.9, sh * 0.65)), c_trim, top_scale=0.88)


def _accent_twin_bow_lances(mb, ext, hq, c_main, c_trim):
    by, bz, dz = ext["bow_y"], ext["bow_z"], ext["dc_z"]
    mx, ln, sy = ext["mid_x"], ext["length"], ext["stern_y"]
    lx = max(0.85, mx * 0.40)
    fwd = max(2.0, ln * 0.12)
    sides = _q(hq, 6, 4)
    for sign in (1, -1):
        mb.tube((sign * lx, by + 2.2, bz), (sign * lx * 0.88, by - fwd, bz + 0.15), 0.22, 0.04, sides=sides, color=c_main)
        mb.plate(
            [
                (sign * mx * 0.55, sy - 2.0, dz * 0.82),
                (sign * (mx + 1.35), sy + 0.2, dz * 0.98),
                (sign * mx * 0.55, sy - 0.1, dz * 0.78),
            ],
            0.12,
            c_trim,
        )
    mb.tube((-lx, by - fwd * 0.35, bz + 0.05), (lx, by - fwd * 0.35, bz + 0.05), 0.12, 0.12, sides=4, color=c_trim)


def _accent_outrigger_pods(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    pz = max(ext["min_z"] + 0.9, dz * 0.72)
    px = mx + 1.7
    sides = _q(hq, 6, 4)
    for sign in (1, -1):
        mb.tube((sign * mx * 0.48, -ln * 0.08, pz), (sign * px, -ln * 0.04, pz), 0.18, 0.16, sides=4, color=c_trim)
        mb.tube((sign * mx * 0.48, ln * 0.14, pz), (sign * px, ln * 0.14, pz), 0.18, 0.16, sides=4, color=c_trim)
        mb.path(
            [
                (sign * px, -ln * 0.24, pz),
                (sign * px, -ln * 0.16, pz),
                (sign * px, ln * 0.24, pz),
            ],
            [0.14, 0.55, 0.45],
            sides,
            c_main,
        )


def _accent_prow_tusks(mb, ext, hq, c_main, c_trim):
    by, bz = ext["bow_y"], ext["bow_z"]
    mx, ln = ext["mid_x"], ext["length"]
    tx = max(0.78, mx * 0.36)
    fwd = max(1.9, ln * 0.11)
    sides = _q(hq, 6, 4)
    for sign in (1, -1):
        mb.path(
            [
                (sign * tx, by + 1.8, bz - 0.15),
                (sign * tx * 1.15, by - fwd * 0.35, bz + 0.25),
                (sign * tx * 0.95, by - fwd, bz + 1.15),
            ],
            [0.32, 0.22, 0.05],
            sides,
            c_main,
        )
    mb.box((0.0, by + 0.7, bz + 0.2), (tx * 2.1, 0.9, 0.55), c_trim, top_scale=0.85)


def _accent_cathedral_crown(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    by, bz = ext["bow_y"], ext["bow_z"]
    px = max(1.25, mx * 0.55)
    py = -ln * 0.24
    for sign in (1, -1):
        mb.box((sign * px, py, dz + 0.8), (0.9, 0.9, 2.4), c_main, top_scale=0.82)
        mb.tube((sign * px, py, dz + 2.0), (sign * px, py, dz + 4.0), 0.46, 0.04, sides=4, color=c_trim)
    mb.plate(
        [
            (0.0, by + 1.4, bz - 0.2),
            (0.0, by - max(1.4, ln * 0.08), bz + 0.5),
            (0.0, by + 1.0, bz + 1.1),
        ],
        0.18,
        c_trim,
    )


def _accent_crown_obelisk(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    by, bz, sy = ext["bow_y"], ext["bow_z"], ext["stern_y"]
    px = max(1.2, mx * 0.52)
    py = sy - ln * 0.16
    for sign in (1, -1):
        mb.box((sign * px, py, dz + 0.65), (0.85, 0.85, 2.1), c_main, top_scale=0.8)
        mb.tube((sign * px, py, dz + 1.7), (sign * px, py, dz + 3.4), 0.42, 0.04, sides=4, color=c_trim)
    mb.tube((0.0, by + 1.2, bz + 0.1), (0.0, by - max(1.5, ln * 0.08), bz + 0.85), 0.28, 0.04, sides=4, color=c_trim)


def _accent_twin_exhaust_stacks(mb, ext, hq, c_main, c_trim):
    dz, mx, ln = ext["dc_z"], ext["mid_x"], ext["length"]
    by, bz, sy = ext["bow_y"], ext["bow_z"], ext["stern_y"]
    sx = max(1.05, mx * 0.44)
    sy_pos = sy - ln * 0.18
    sides = _q(hq, 6, 4)
    for sign in (1, -1):
        mb.tube((sign * sx, sy_pos, dz - 0.35), (sign * sx * 1.12, sy_pos + 0.8, dz + 2.7), 0.36, 0.28, sides=sides, color=c_main)
        mb.tube((sign * sx * 1.11, sy_pos + 0.72, dz + 2.4), (sign * sx * 1.14, sy_pos + 0.86, dz + 2.85), 0.38, 0.38, sides=sides, color=c_trim)
    mb.box((0.0, by + 0.4, bz), (mx * 0.65, 1.1, 0.75), c_trim, top_scale=0.88)


def _accent_minimal_prow_crest(mb, ext, hq, c_main, c_trim):
    by, bz, ln = ext["bow_y"], ext["bow_z"], ext["length"]
    mb.plate(
        [
            (0.0, by + 1.5, bz - 0.2),
            (0.0, by - ln * 0.09, bz + 0.55),
            (0.0, by + 1.0, bz + 1.1),
        ],
        0.24,
        c_trim,
    )


def _accent_minimal_dorsal_blade(mb, ext, hq, c_main, c_trim):
    dz, sy, ln = ext["dc_z"], ext["stern_y"], ext["length"]
    mb.plate(
        [
            (0.0, sy - ln * 0.18, dz - 0.3),
            (0.0, sy - 0.2, dz - 0.3),
            (0.0, sy + 0.4, dz + 2.4),
            (0.0, sy - ln * 0.12, dz + 1.7),
        ],
        0.22,
        c_main,
    )


ACCENTS = {
    "spiked_prow_fins": _accent_spiked_prow_fins,
    "swept_winglets": _accent_swept_winglets,
    "dorsal_crest_wings": _accent_dorsal_crest_wings,
    "armored_sponsons": _accent_armored_sponsons,
    "twin_bow_lances": _accent_twin_bow_lances,
    "outrigger_pods": _accent_outrigger_pods,
    "prow_tusks": _accent_prow_tusks,
    "cathedral_crown": _accent_cathedral_crown,
    "crown_obelisk": _accent_crown_obelisk,
    "twin_exhaust_stacks": _accent_twin_exhaust_stacks,
    "minimal_prow_crest": _accent_minimal_prow_crest,
    "minimal_dorsal_blade": _accent_minimal_dorsal_blade,
}


def _make_style(base_fn, remap, accent_name, accent_colors, scale=None):
    def builder(mb, hq):
        base_fn(mb, hq)
        if remap:
            mb.faces = [(idx, remap.get(sw, sw), sm) for idx, sw, sm in mb.faces]
        if scale is not None:
            sx, sy, sz = scale
            mb.verts = [Vector((v.x * sx, v.y * sy, v.z * sz)) for v in mb.verts]
            mb.sockets = {k: Vector((p.x * sx, p.y * sy, p.z * sz)) for k, p in mb.sockets.items()}
        ext = _hull_extents(mb)
        ACCENTS[accent_name](mb, ext, hq, accent_colors[0], accent_colors[1])

    return builder


# (model_name, base_builder, default_faction, swatch_remap, accent_name, (accent_main, accent_trim), scale)
STYLE_SPECS = [
    # 1-6: Ships that previously had 2 styles -> 1 new style each
    (
        "SM_Ship_ScrapRaiderToxic",
        story_ships.scrap_raider,
        "Emerald",
        {
            "rust": "toxic_dark",
            "rust_dark": "abyss",
            "canvas_dark": "cloth_black",
            "cloth_brown": "toxic_dark",
            "ember": "toxic",
            "wood_dark": "iron",
            "steel": "toxic_dark",
            "faction_a": "toxic",
            "faction_b": "cloth_black",
            "faction_c": "toxic_dark",
        },
        "spiked_prow_fins",
        ("abyss", "toxic"),
        None,
    ),
    (
        "SM_Ship_SmugglerRunnerIvory",
        story_ships.smuggler_runner,
        "Gilded",
        {
            "wood_dark": "navy",
            "wood_mid": "cloth_white",
            "wood_light": "enamel",
            "wood_deck": "enamel",
            "brass": "gold",
            "lamp": "liftstone",
            "faction_a": "gold",
            "faction_b": "cloth_white",
            "faction_c": "navy",
        },
        "swept_winglets",
        ("cloth_white", "gold"),
        (0.95, 1.05, 1.0),
    ),
    (
        "SM_Ship_MirageSolar",
        story_ships.mirage,
        "Gilded",
        {
            "iron": "cloth_white",
            "iron_light": "enamel",
            "wood_dark": "gold_dark",
            "silver": "gold",
            "plasma": "ember",
            "glass": "amber",
            "faction_a": "gold",
            "faction_b": "cloth_white",
            "faction_c": "gold_dark",
        },
        "dorsal_crest_wings",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_ArmadaFrigateObsidian",
        story_ships.armada_frigate,
        "Obsidian",
        {
            "enamel": "cloth_black",
            "gold": "gem_red",
            "gold_dark": "velvet",
            "lamp": "ember",
            "iron": "abyss",
            "faction_a": "abyss",
            "faction_c": "gem_red",
        },
        "armored_sponsons",
        ("cloth_black", "gem_red"),
        None,
    ),
    (
        "SM_Ship_AegisDestroyerCrimson",
        fleet_ships.aegis_destroyer,
        "Crimson",
        {
            "steel": "wood_red",
            "storm_dark": "velvet",
            "iron": "cloth_black",
            "iron_light": "cloth_white",
            "silver": "gold",
            "liftstone": "ember",
        },
        "twin_bow_lances",
        ("wood_red", "gold"),
        None,
    ),
    (
        "SM_Ship_FleetCarrierArctic",
        fleet_ships.fleet_carrier,
        "Azure",
        {
            "steel": "cloth_white",
            "iron": "navy",
            "iron_light": "cloud_shade",
            "rust_dark": "gem_blue",
            "gold": "liftstone",
            "silver": "cloud",
            "faction_a": "gem_blue",
        },
        "outrigger_pods",
        ("cloth_white", "gem_blue"),
        None,
    ),
    # 7-64: 29 ships that previously had 1 style -> 2 new styles each
    (
        "SM_Ship_IronMawCrimson",
        story_ships.iron_maw,
        "Crimson",
        {
            "iron": "cloth_black",
            "iron_light": "wood_red",
            "rust_dark": "velvet",
            "wood_mid": "gem_red",
            "canvas_dark": "cloth_black",
            "rope": "gold",
        },
        "prow_tusks",
        ("gold", "cloth_black"),
        None,
    ),
    (
        "SM_Ship_IronMawFrost",
        story_ships.iron_maw,
        "Azure",
        {
            "iron": "navy",
            "iron_light": "cloud_shade",
            "rust_dark": "gem_blue",
            "wood_mid": "silver",
            "canvas_dark": "cloth_white",
            "rope": "liftstone",
        },
        "armored_sponsons",
        ("cloud_shade", "gem_blue"),
        (1.06, 1.0, 1.0),
    ),
    (
        "SM_Ship_BastionGilded",
        story_ships.bastion,
        "Gilded",
        {
            "steel": "enamel",
            "iron": "gold_dark",
            "iron_light": "gold",
            "lamp": "liftstone",
            "faction_a": "navy",
            "faction_b": "gold",
        },
        "cathedral_crown",
        ("enamel", "gold"),
        None,
    ),
    (
        "SM_Ship_BastionEmber",
        story_ships.bastion,
        "Obsidian",
        {
            "steel": "abyss",
            "iron": "cloth_black",
            "iron_light": "rust",
            "lamp": "ember",
            "faction_a": "gem_red",
            "faction_b": "ember",
        },
        "spiked_prow_fins",
        ("cloth_black", "ember"),
        None,
    ),
    (
        "SM_Ship_TartarusAloftIvory",
        story_ships.tartarus_aloft,
        "Gilded",
        {
            "steel": "cloth_white",
            "iron": "enamel",
            "iron_light": "gold",
            "abyss": "navy",
            "velvet": "gem_blue",
            "lamp": "liftstone",
        },
        "minimal_prow_crest",
        ("cloth_white", "gold"),
        (1.0, 1.05, 1.0),
    ),
    (
        "SM_Ship_TartarusAloftCrimson",
        story_ships.tartarus_aloft,
        "Crimson",
        {
            "steel": "wood_red",
            "iron": "abyss",
            "iron_light": "velvet",
            "gold": "ember",
            "lamp": "ember",
            "faction_a": "gem_red",
        },
        "minimal_dorsal_blade",
        ("wood_red", "ember"),
        (1.05, 1.0, 1.0),
    ),
    (
        "SM_Ship_TidebreakerCoral",
        fleet_ships.tidebreaker,
        "Crimson",
        {
            "navy": "velvet",
            "gem_blue": "gem_red",
            "liftstone": "ember",
            "liftstone_dark": "wood_red",
            "enamel": "parchment",
            "brass": "gold",
        },
        "swept_winglets",
        ("gem_red", "gold"),
        None,
    ),
    (
        "SM_Ship_TidebreakerAbyss",
        fleet_ships.tidebreaker,
        "Sorcerer",
        {
            "navy": "abyss",
            "gem_blue": "storm_dark",
            "liftstone": "plasma",
            "liftstone_dark": "abyss",
            "enamel": "cloth_black",
            "brass": "silver",
        },
        "dorsal_crest_wings",
        ("abyss", "plasma"),
        None,
    ),
    (
        "SM_Ship_TempestSpireSolar",
        fleet_ships.tempest_spire,
        "Gilded",
        {
            "storm": "enamel",
            "storm_dark": "gold_dark",
            "lightning": "ember",
            "brass": "gold",
            "faction_a": "gold",
        },
        "crown_obelisk",
        ("enamel", "gold"),
        None,
    ),
    (
        "SM_Ship_TempestSpireJade",
        fleet_ships.tempest_spire,
        "Emerald",
        {
            "storm": "cloth_green",
            "storm_dark": "abyss",
            "lightning": "liftstone",
            "brass": "silver",
            "faction_a": "grass",
        },
        "twin_bow_lances",
        ("cloth_green", "liftstone"),
        None,
    ),
    (
        "SM_Ship_EarthshakerMagma",
        fleet_ships.earthshaker,
        "Obsidian",
        {
            "rock": "abyss",
            "rock_dark": "cloth_black",
            "grass_dark": "rust_dark",
            "liftstone": "ember",
            "liftstone_dark": "gem_red",
            "iron": "rust",
        },
        "spiked_prow_fins",
        ("abyss", "ember"),
        None,
    ),
    (
        "SM_Ship_EarthshakerMarble",
        fleet_ships.earthshaker,
        "Gilded",
        {
            "rock": "cloth_white",
            "rock_dark": "enamel",
            "grass_dark": "gold_dark",
            "liftstone": "lamp",
            "liftstone_dark": "gold",
            "iron": "brass",
        },
        "cathedral_crown",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_InfernoForgeFrost",
        fleet_ships.inferno_forge,
        "Azure",
        {
            "abyss": "navy",
            "rust": "cloud_shade",
            "rust_dark": "gem_blue",
            "iron": "silver",
            "brass": "cloud",
            "ember": "liftstone",
        },
        "twin_exhaust_stacks",
        ("silver", "liftstone"),
        None,
    ),
    (
        "SM_Ship_InfernoForgeToxic",
        fleet_ships.inferno_forge,
        "Emerald",
        {
            "rust": "toxic_dark",
            "rust_dark": "cloth_green",
            "brass": "toxic",
            "ember": "toxic",
            "iron": "cloth_black",
        },
        "armored_sponsons",
        ("cloth_black", "toxic"),
        None,
    ),
    (
        "SM_Ship_ZephyrLotusNight",
        fleet_ships.zephyr_lotus,
        "Sorcerer",
        {
            "enamel": "cloth_black",
            "gold": "plasma",
            "gold_dark": "velvet",
            "wind": "plasma",
            "faction_a": "abyss",
            "faction_b": "velvet",
        },
        "swept_winglets",
        ("cloth_black", "plasma"),
        None,
    ),
    (
        "SM_Ship_ZephyrLotusSakura",
        fleet_ships.zephyr_lotus,
        "Crimson",
        {
            "enamel": "gem_red",
            "gold": "cloth_white",
            "gold_dark": "wood_red",
            "wind": "lamp",
            "faction_a": "velvet",
            "faction_b": "cloth_white",
        },
        "dorsal_crest_wings",
        ("gem_red", "cloth_white"),
        (1.06, 1.0, 1.0),
    ),
    (
        "SM_Ship_GlacierFangObsidian",
        fleet_ships.glacier_fang,
        "Obsidian",
        {
            "cloud": "cloth_black",
            "cloud_shade": "abyss",
            "silver": "iron",
            "gem_blue": "gem_red",
            "liftstone": "ember",
        },
        "prow_tusks",
        ("cloth_black", "ember"),
        None,
    ),
    (
        "SM_Ship_GlacierFangEmerald",
        fleet_ships.glacier_fang,
        "Emerald",
        {
            "cloud": "grass",
            "cloud_shade": "cloth_green",
            "silver": "gold",
            "gem_blue": "toxic",
            "liftstone": "wind",
        },
        "dorsal_crest_wings",
        ("cloth_green", "gold"),
        None,
    ),
    (
        "SM_Ship_StarlightCruiserGold",
        fleet_ships.starlight_cruiser,
        "Gilded",
        {
            "steel": "enamel",
            "silver": "cloth_white",
            "iron_light": "gold",
            "plasma": "liftstone",
            "liftstone": "lamp",
            "faction_a": "gold",
        },
        "swept_winglets",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_StarlightCruiserShadow",
        fleet_ships.starlight_cruiser,
        "Obsidian",
        {
            "steel": "abyss",
            "silver": "cloth_black",
            "iron_light": "iron",
            "plasma": "ember",
            "liftstone": "gem_red",
            "faction_a": "gem_red",
        },
        "twin_bow_lances",
        ("cloth_black", "ember"),
        (1.0, 1.06, 1.0),
    ),
    (
        "SM_Ship_NebulaSaucerCrimson",
        fleet_ships.nebula_saucer,
        "Crimson",
        {
            "steel": "wood_red",
            "silver": "cloth_black",
            "gold": "ember",
            "plasma": "ember",
            "liftstone": "lamp",
            "faction_a": "gem_red",
            "faction_c": "abyss",
        },
        "crown_obelisk",
        ("wood_red", "ember"),
        None,
    ),
    (
        "SM_Ship_NebulaSaucerJade",
        fleet_ships.nebula_saucer,
        "Emerald",
        {
            "steel": "cloth_white",
            "silver": "enamel",
            "gold": "cloth_green",
            "plasma": "toxic",
            "liftstone": "wind",
            "faction_a": "grass",
            "faction_c": "cloth_green",
        },
        "outrigger_pods",
        ("cloth_white", "toxic"),
        None,
    ),
    (
        "SM_Ship_VoidInterceptorIvory",
        fleet_ships.void_interceptor,
        "Gilded",
        {
            "abyss": "cloth_white",
            "steel": "enamel",
            "silver": "gold",
            "plasma": "lamp",
            "liftstone": "wind",
            "faction_a": "gold",
            "faction_b": "cloth_white",
        },
        "swept_winglets",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_VoidInterceptorCrimson",
        fleet_ships.void_interceptor,
        "Crimson",
        {
            "abyss": "velvet",
            "steel": "cloth_black",
            "silver": "gem_red",
            "plasma": "ember",
            "liftstone": "ember",
            "faction_a": "gem_red",
            "faction_b": "gold",
        },
        "prow_tusks",
        ("gem_red", "gold"),
        (1.0, 1.06, 1.0),
    ),
    (
        "SM_Ship_PlasmaLancerAmber",
        fleet_ships.plasma_lancer,
        "Gilded",
        {
            "steel": "enamel",
            "silver": "gold",
            "iron": "gold_dark",
            "plasma": "ember",
            "faction_a": "brass",
            "faction_b": "lamp",
        },
        "twin_bow_lances",
        ("enamel", "ember"),
        None,
    ),
    (
        "SM_Ship_PlasmaLancerFrost",
        fleet_ships.plasma_lancer,
        "Azure",
        {
            "steel": "navy",
            "silver": "cloud",
            "iron": "abyss",
            "plasma": "lightning",
            "faction_a": "gem_blue",
            "faction_b": "liftstone",
        },
        "dorsal_crest_wings",
        ("navy", "lightning"),
        None,
    ),
    (
        "SM_Ship_SolarArkLunar",
        fleet_ships.solar_ark,
        "Azure",
        {
            "enamel": "navy",
            "gold": "silver",
            "gold_dark": "steel",
            "brass": "cloud_shade",
            "lamp": "lightning",
            "faction_a": "abyss",
        },
        "crown_obelisk",
        ("navy", "silver"),
        None,
    ),
    (
        "SM_Ship_SolarArkEclipse",
        fleet_ships.solar_ark,
        "Obsidian",
        {
            "enamel": "cloth_black",
            "gold": "gem_red",
            "gold_dark": "abyss",
            "brass": "velvet",
            "lamp": "ember",
            "faction_a": "abyss",
        },
        "swept_winglets",
        ("cloth_black", "gem_red"),
        None,
    ),
    (
        "SM_Ship_SkySubmarineGilded",
        fleet_ships.sky_submarine,
        "Gilded",
        {
            "storm_dark": "gold",
            "steel": "brass",
            "iron": "gold_dark",
            "rust_dark": "enamel",
            "silver": "cloth_white",
            "faction_a": "navy",
        },
        "dorsal_crest_wings",
        ("gold", "navy"),
        None,
    ),
    (
        "SM_Ship_SkySubmarineArctic",
        fleet_ships.sky_submarine,
        "Azure",
        {
            "storm_dark": "cloth_white",
            "steel": "cloud_shade",
            "iron": "navy",
            "rust_dark": "gem_blue",
            "brass": "liftstone",
            "silver": "cloud",
            "faction_a": "gem_blue",
        },
        "outrigger_pods",
        ("cloth_white", "gem_blue"),
        None,
    ),
    (
        "SM_Ship_HeavyCruiserCrimson",
        fleet_ships.heavy_cruiser,
        "Crimson",
        {
            "steel": "wood_red",
            "iron_light": "gem_red",
            "iron": "cloth_black",
            "navy": "abyss",
            "rust_dark": "gold",
            "faction_a": "gold",
        },
        "armored_sponsons",
        ("wood_red", "gold"),
        None,
    ),
    (
        "SM_Ship_HeavyCruiserIvory",
        fleet_ships.heavy_cruiser,
        "Gilded",
        {
            "steel": "cloth_white",
            "iron_light": "enamel",
            "iron": "navy",
            "navy": "gold_dark",
            "rust_dark": "gold",
            "faction_a": "gold",
        },
        "twin_exhaust_stacks",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_GunshipMonitorIvory",
        fleet_ships.gunship_monitor,
        "Gilded",
        {
            "steel": "cloth_white",
            "iron": "navy",
            "rust_dark": "gold_dark",
            "brass": "gold",
        },
        "armored_sponsons",
        ("cloth_white", "gold"),
        (1.06, 1.0, 1.0),
    ),
    (
        "SM_Ship_GunshipMonitorObsidian",
        fleet_ships.gunship_monitor,
        "Obsidian",
        {
            "steel": "abyss",
            "iron": "cloth_black",
            "rust_dark": "gem_red",
            "brass": "ember",
        },
        "spiked_prow_fins",
        ("cloth_black", "ember"),
        None,
    ),
    (
        "SM_Ship_ClockworkSovereignSilver",
        fleet_ships.clockwork_sovereign,
        "Azure",
        {
            "brass": "silver",
            "gold": "cloud",
            "wood_red": "navy",
            "wood_dark": "abyss",
            "iron": "steel",
            "lamp": "liftstone",
        },
        "crown_obelisk",
        ("navy", "silver"),
        None,
    ),
    (
        "SM_Ship_ClockworkSovereignObsidian",
        fleet_ships.clockwork_sovereign,
        "Obsidian",
        {
            "brass": "iron_light",
            "gold": "gem_red",
            "wood_red": "cloth_black",
            "wood_dark": "abyss",
            "lamp": "ember",
        },
        "spiked_prow_fins",
        ("cloth_black", "gem_red"),
        None,
    ),
    (
        "SM_Ship_SkyNautilusAbyssal",
        fleet_ships.sky_nautilus,
        "Sorcerer",
        {
            "parchment": "cloth_black",
            "amber": "plasma",
            "brass": "silver",
            "wood_dark": "abyss",
            "lamp": "liftstone",
        },
        "prow_tusks",
        ("cloth_black", "plasma"),
        None,
    ),
    (
        "SM_Ship_SkyNautilusPearl",
        fleet_ships.sky_nautilus,
        "Crimson",
        {
            "parchment": "cloth_white",
            "amber": "gem_red",
            "brass": "gold",
            "wood_dark": "velvet",
            "abyss": "wood_red",
            "lamp": "lamp",
        },
        "dorsal_crest_wings",
        ("cloth_white", "gem_red"),
        None,
    ),
    (
        "SM_Ship_BoneRevenantAshen",
        fleet_ships.bone_revenant,
        "Obsidian",
        {
            "parchment": "cloth_black",
            "wood_dark": "abyss",
            "iron": "rust_dark",
            "toxic": "ember",
            "toxic_dark": "gem_red",
            "abyss": "cloth_black",
        },
        "prow_tusks",
        ("cloth_black", "ember"),
        None,
    ),
    (
        "SM_Ship_BoneRevenantGilded",
        fleet_ships.bone_revenant,
        "Gilded",
        {
            "parchment": "gold",
            "wood_dark": "cloth_white",
            "iron": "brass",
            "toxic": "liftstone",
            "toxic_dark": "gem_blue",
            "abyss": "navy",
        },
        "crown_obelisk",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_CrystalSanctumNoir",
        fleet_ships.crystal_sanctum,
        "Shadow",
        {
            "cloth_white": "cloth_black",
            "enamel": "abyss",
            "gold": "cloth_white",
            "rock_dark": "silver",
            "lamp": "lightning",
            "liftstone": "cloud",
        },
        "cathedral_crown",
        ("cloth_black", "cloth_white"),
        None,
    ),
    (
        "SM_Ship_CrystalSanctumCrimson",
        fleet_ships.crystal_sanctum,
        "Crimson",
        {
            "cloth_white": "velvet",
            "enamel": "wood_red",
            "gold": "brass",
            "rock_dark": "abyss",
            "lamp": "ember",
            "liftstone": "ember",
        },
        "spiked_prow_fins",
        ("velvet", "brass"),
        (1.05, 1.0, 1.0),
    ),
    (
        "SM_Ship_DragonJunkerJade",
        fleet_ships.dragon_junker,
        "Emerald",
        {
            "wood_red": "cloth_green",
            "wood_dark": "abyss",
            "gold": "enamel",
            "ember": "liftstone",
            "faction_a": "grass",
        },
        "swept_winglets",
        ("cloth_green", "enamel"),
        None,
    ),
    (
        "SM_Ship_DragonJunkerShadow",
        fleet_ships.dragon_junker,
        "Obsidian",
        {
            "wood_red": "cloth_black",
            "wood_dark": "abyss",
            "gold": "silver",
            "ember": "plasma",
            "faction_a": "velvet",
        },
        "prow_tusks",
        ("cloth_black", "plasma"),
        (1.0, 1.05, 1.0),
    ),
    (
        "SM_Ship_BeetleScarabRuby",
        fleet_ships.beetle_scarab,
        "Crimson",
        {
            "cloth_green": "gem_red",
            "gold": "cloth_black",
            "gold_dark": "velvet",
            "abyss": "iron",
            "liftstone": "ember",
        },
        "prow_tusks",
        ("gem_red", "cloth_black"),
        None,
    ),
    (
        "SM_Ship_BeetleScarabSapphire",
        fleet_ships.beetle_scarab,
        "Azure",
        {
            "cloth_green": "gem_blue",
            "gold": "silver",
            "gold_dark": "navy",
            "abyss": "cloth_white",
            "liftstone": "lightning",
        },
        "dorsal_crest_wings",
        ("gem_blue", "silver"),
        None,
    ),
    (
        "SM_Ship_GyroCopterStealth",
        fleet_ships.gyro_copter,
        "Shadow",
        {
            "steel": "abyss",
            "iron": "cloth_black",
            "iron_light": "iron",
            "rust": "gem_red",
            "brass": "silver",
            "glass": "ember",
            "faction_a": "gem_red",
        },
        "swept_winglets",
        ("cloth_black", "gem_red"),
        None,
    ),
    (
        "SM_Ship_GyroCopterVanguard",
        fleet_ships.gyro_copter,
        "Gilded",
        {
            "steel": "cloth_white",
            "iron": "navy",
            "iron_light": "enamel",
            "rust": "gold",
            "brass": "gold",
            "glass": "liftstone",
            "faction_a": "gem_blue",
        },
        "twin_bow_lances",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_WhalerHarpoonerPolar",
        fleet_ships.whaler_harpooner,
        "Azure",
        {
            "wood_dark": "navy",
            "wood_mid": "cloth_white",
            "steel": "cloud_shade",
            "rust": "gem_red",
            "rust_dark": "wood_red",
            "canvas_dark": "cloud",
            "leather_dark": "navy",
            "brass": "silver",
        },
        "spiked_prow_fins",
        ("cloth_white", "gem_red"),
        None,
    ),
    (
        "SM_Ship_WhalerHarpoonerGilded",
        fleet_ships.whaler_harpooner,
        "Gilded",
        {
            "wood_dark": "abyss",
            "wood_mid": "cloth_black",
            "steel": "gold_dark",
            "iron": "cloth_black",
            "rust": "gold",
            "rust_dark": "brass",
            "canvas_dark": "enamel",
        },
        "twin_exhaust_stacks",
        ("cloth_black", "gold"),
        None,
    ),
    (
        "SM_Ship_LuxuryYachtNoir",
        fleet_ships.luxury_yacht,
        "Obsidian",
        {
            "cloth_white": "cloth_black",
            "enamel": "abyss",
            "gold": "silver",
            "gold_dark": "iron_light",
            "glass": "plasma",
            "lamp": "plasma",
            "liftstone": "lightning",
            "faction_a": "gem_red",
        },
        "dorsal_crest_wings",
        ("cloth_black", "plasma"),
        (1.0, 1.05, 1.0),
    ),
    (
        "SM_Ship_LuxuryYachtEmerald",
        fleet_ships.luxury_yacht,
        "Emerald",
        {
            "cloth_white": "cloth_green",
            "enamel": "grass_dark",
            "gold": "gold",
            "glass": "lamp",
            "liftstone": "lamp",
            "faction_a": "enamel",
        },
        "swept_winglets",
        ("cloth_green", "gold"),
        None,
    ),
    (
        "SM_Ship_ShadowStalkerIvory",
        fleet_ships.shadow_stalker,
        "Gilded",
        {
            "abyss": "cloth_white",
            "cloth_black": "enamel",
            "steel": "gold",
            "velvet": "navy",
            "ember": "liftstone",
            "faction_a": "gold",
        },
        "twin_bow_lances",
        ("cloth_white", "gold"),
        None,
    ),
    (
        "SM_Ship_ShadowStalkerVenom",
        fleet_ships.shadow_stalker,
        "Emerald",
        {
            "abyss": "cloth_green",
            "cloth_black": "abyss",
            "steel": "toxic_dark",
            "velvet": "grass_dark",
            "ember": "toxic",
            "faction_a": "toxic",
        },
        "swept_winglets",
        ("cloth_green", "toxic"),
        None,
    ),
    (
        "SM_Ship_PowderKegFrost",
        fleet_ships.powder_keg,
        "Azure",
        {
            "wood_red": "gem_blue",
            "rust": "cloth_white",
            "rust_dark": "navy",
            "iron": "steel",
            "abyss": "navy",
            "ember": "liftstone",
            "brass": "silver",
            "faction_a": "cloud",
        },
        "armored_sponsons",
        ("cloth_white", "liftstone"),
        None,
    ),
    (
        "SM_Ship_PowderKegToxic",
        fleet_ships.powder_keg,
        "Emerald",
        {
            "wood_red": "toxic_dark",
            "rust": "cloth_green",
            "rust_dark": "abyss",
            "iron": "cloth_black",
            "ember": "toxic",
            "brass": "gold",
            "faction_a": "toxic",
        },
        "twin_exhaust_stacks",
        ("cloth_black", "toxic"),
        None,
    ),
    (
        "SM_Ship_CloudTrainRoyal",
        fleet_ships.cloud_train,
        "Gilded",
        {
            "wood_red": "navy",
            "steel": "cloth_white",
            "iron": "gold_dark",
            "rust_dark": "gold",
            "brass": "gold",
            "lamp": "liftstone",
            "faction_a": "gold",
        },
        "dorsal_crest_wings",
        ("navy", "gold"),
        None,
    ),
    (
        "SM_Ship_CloudTrainPhantom",
        fleet_ships.cloud_train,
        "Sorcerer",
        {
            "wood_red": "abyss",
            "steel": "cloth_black",
            "iron": "abyss",
            "rust_dark": "velvet",
            "brass": "silver",
            "lamp": "plasma",
            "faction_a": "plasma",
        },
        "spiked_prow_fins",
        ("cloth_black", "plasma"),
        None,
    ),
    (
        "SM_Ship_DelphinusCrimson",
        fleet_ships.delphinus,
        "Crimson",
        {
            "navy": "abyss",
            "steel": "iron",
            "iron_light": "steel",
            "silver": "gold",
            "liftstone": "ember",
            "faction_b": "cloth_black",
        },
        "minimal_prow_crest",
        ("faction_a", "gold"),
        None,
    ),
    (
        "SM_Ship_DelphinusGilded",
        fleet_ships.delphinus,
        "Gilded",
        {
            "navy": "faction_a",
            "steel": "enamel",
            "iron_light": "cloth_white",
            "iron": "gold_dark",
            "silver": "gold",
            "faction_a": "enamel",
            "faction_b": "gold",
            "liftstone": "lamp",
        },
        "minimal_dorsal_blade",
        ("enamel", "gold"),
        None,
    ),
]


def _validate_specs():
    for name, _, faction, remap, accent_name, accent_colors, _ in STYLE_SPECS:
        assert faction in palette.FACTIONS, f"{name}: unknown faction {faction}"
        assert accent_name in ACCENTS, f"{name}: unknown accent {accent_name}"
        for k, v in remap.items():
            assert k in palette.SWATCH_INDEX, f"{name}: unknown source swatch {k}"
            assert v in palette.SWATCH_INDEX, f"{name}: unknown target swatch {v}"
        for c in accent_colors:
            assert c in palette.SWATCH_INDEX, f"{name}: unknown accent swatch {c}"


_validate_specs()

STYLE_SHIPS = {
    name: _make_style(base_fn, remap, accent_name, accent_colors, scale)
    for name, base_fn, _, remap, accent_name, accent_colors, scale in STYLE_SPECS
}
STYLE_FACTIONS = {name: faction for name, _, faction, _, _, _, _ in STYLE_SPECS}
STYLE_ICONS = {name.replace("SM_", ""): name for name, _, _, _, _, _, _ in STYLE_SPECS}
