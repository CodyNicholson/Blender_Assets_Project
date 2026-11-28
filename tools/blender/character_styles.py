"""Two bespoke alternate styles for each of the 14 non-Vane playable crew members (28 models total).

Each style transforms BOTH hair/headgear AND clothing/gear silhouette (never just a palette swap),
retaining the character's proportions, facial traits, skeleton, and custom battle EXTRA_CLIPS.
"""
import math

from mathutils import Matrix, Vector

STYLE_FACTIONS = {
    "SK_RookArmada": "Gilded",
    "SK_RookFoundry": "Scrap",
    "SK_LyraTempest": "Azure",
    "SK_LyraStarweaver": "Syndicate",
    "SK_SableMasquerade": "Crimson",
    "SK_SableRonin": "Obsidian",
    "SK_ThorneAlchemist": "Emerald",
    "SK_ThorneArchmage": "Sorcerer",
    "SK_MorrowCorsair": "Crimson",
    "SK_MorrowAdmiral": "Gilded",
    "SK_BrillWhaler": "Azure",
    "SK_BrillDeckBoss": "Crimson",
    "SK_HaskIronclad": "Warden",
    "SK_HaskPrivateer": "Obsidian",
    "SK_WrenPlagueDoc": "Obsidian",
    "SK_WrenGentleman": "Emerald",
    "SK_IvoAetherMage": "Azure",
    "SK_IvoCoilRunner": "Scrap",
    "SK_Chad": "Crimson",
    "SK_RoxanneValkyrie": "Gilded",
    "SK_RoxanneSyndicate": "Syndicate",
    "SK_MayCenturion": "Gilded",
    "SK_MayRebel": "Crimson",
    "SK_MirrenBombardier": "Gilded",
    "SK_MirrenPyro": "Scrap",
    "SK_OdessaMachinist": "Scrap",
    "SK_OdessaMatron": "Azure",
    "SK_TobinNavigator": "Azure",
    "SK_TobinCastaway": "Scrap",
}


# ---- shared silhouette helpers ------------------------------------------------------------------

def _sc():
    import story_characters as sc
    return sc


def _at(ctx, x, y, z):
    return ctx.centre + Vector((x, y, z)) * ctx.s


def _ring(ctx, rx, ry, z, sides):
    s, w, g = ctx.s, ctx.w, ctx.g
    return [
        (
            rx * w * s * math.cos(2 * math.pi * (j + 0.5) / sides),
            ry * g * s * math.sin(2 * math.pi * (j + 0.5) / sides),
            z * s,
        )
        for j in range(sides)
    ]


def _shell(ctx, bone, rows, color):
    sides = ctx.q["torso"]
    with ctx.mb.bound_to(bone):
        ctx.mb.loft([_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=ctx.hq)


def _cuffs(ctx, color, start=0.72, flare=1.45):
    s, g, hq = ctx.s, ctx.g, ctx.hq
    r1 = 0.05 * s * g * ctx.hero.arm_bulk
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        with ctx.mb.bound_to(f"lower_arm.{side}"):
            ctx.mb.tube(elbow.lerp(wrist, start), elbow.lerp(wrist, 0.98), r1 * 1.15, r1 * flare, sides=8 if hq else 4, color=color)


def _greaves(ctx, color, trim=None):
    s, g, hq = ctx.s, ctx.g, ctx.hq
    r0 = 0.085 * s * g * ctx.hero.leg_bulk
    r1 = 0.07 * s * g * ctx.hero.leg_bulk
    for side in ("L", "R"):
        knee, ankle = (Vector(p) for p in ctx.joints[f"shin.{side}"][:2])
        with ctx.mb.bound_to(f"shin.{side}"):
            ctx.mb.tube(knee.lerp(ankle, 0.05), knee.lerp(ankle, 0.88), r0 * 1.16, r1 * 1.12, sides=8 if hq else 4, color=color)
            if trim and hq:
                ctx.mb.tube(knee.lerp(ankle, 0.03), knee.lerp(ankle, 0.14), r0 * 1.24, r0 * 1.22, sides=8, color=trim)


def _monocle(ctx, side=1, frame="gold", lens="glass"):
    s, hq = ctx.s, ctx.hq
    with ctx.mb.bound_to("head"):
        place = Matrix.Translation(_at(ctx, side * 0.078, -0.205, 0.03)) @ Matrix.Rotation(math.pi / 2, 4, "X")
        with ctx.mb.xf(place):
            ctx.mb.lathe([(0.048 * s, -0.008), (0.048 * s, 0.008)], 8 if hq else 4, frame, smooth=False)
            if hq:
                ctx.mb.lathe([(0.036 * s, -0.004), (0.036 * s, 0.004)], 6, lens, smooth=False)
        if hq:
            ctx.mb.path([_at(ctx, side * 0.12, -0.19, 0.01), _at(ctx, side * 0.14, -0.14, -0.08), _at(ctx, side * 0.11, -0.12, -0.18)], [0.004 * s] * 3, 3, frame)


def _goggles_eyes(ctx, frame="brass", lens="liftstone", strap="leather_dark"):
    s, hq = ctx.s, ctx.hq
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            place = Matrix.Translation(_at(ctx, sign * 0.076, -0.195, 0.035)) @ Matrix.Rotation(math.pi / 2, 4, "X")
            with ctx.mb.xf(place):
                ctx.mb.lathe([(0.054 * s, -0.018), (0.054 * s, 0.018)], 8 if hq else 4, frame, smooth=False)
                ctx.mb.lathe([(0.038 * s, -0.022), (0.038 * s, -0.014)], 6 if hq else 4, lens, smooth=False)
        ctx.mb.box(tuple(_at(ctx, 0, -0.205, 0.035)), (0.05 * s, 0.02 * s, 0.016 * s), frame)
        ctx.mb.tube(_at(ctx, -0.13, -0.15, 0.035), _at(ctx, -0.21, 0.06, 0.05), 0.012 * s, sides=4, color=strap)
        ctx.mb.tube(_at(ctx, 0.13, -0.15, 0.035), _at(ctx, 0.21, 0.06, 0.05), 0.012 * s, sides=4, color=strap)


def _dreads(ctx, count=5, length=0.34, beads="brass"):
    s, hq = ctx.s, ctx.hq
    xs = [(-0.14 + 0.28 * k / max(1, count - 1)) for k in range(count)] if hq else [-0.1, 0.0, 0.1]
    with ctx.mb.bound_to("head"):
        for k, x in enumerate(xs):
            drop = length + 0.04 * math.sin(k * 1.9)
            pts = [_at(ctx, x, 0.12, 0.12), _at(ctx, x * 1.2, 0.22, 0.02), _at(ctx, x * 1.25, 0.24, -drop)]
            ctx.mb.path(pts, [0.03 * s, 0.028 * s, 0.018 * s], 5 if hq else 3, ctx.hero.hair)
            if hq and k % 2 == 0:
                ctx.mb.tube(pts[1].lerp(pts[2], 0.45), pts[1].lerp(pts[2], 0.58), 0.03 * s, sides=5, color=beads)


def _twin_braids(ctx, color=None, band="gold", length=0.36):
    s, hq = ctx.s, ctx.hq
    hair = color or ctx.hero.hair
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            pts = [_at(ctx, sign * 0.16, -0.02, 0.12), _at(ctx, sign * 0.23, -0.05, -0.05), _at(ctx, sign * 0.22, -0.08, -length)]
            ctx.mb.path(pts, [0.04 * s, 0.034 * s, 0.014 * s], 5 if hq else 3, hair)
            if hq:
                for t in (0.35, 0.72):
                    ctx.mb.sphere(pts[1].lerp(pts[2], t), 0.04 * s, 5, 3, hair, smooth=False)
                ctx.mb.tube(pts[1].lerp(pts[2], 0.8), pts[1].lerp(pts[2], 0.9), 0.028 * s, sides=5, color=band)


def _topknot(ctx, pin_color="iron_light"):
    s, hq = ctx.s, ctx.hq
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.06, 0.28), (0.07 * s, 0.075 * s, 0.095 * s), 7 if hq else 4, 4 if hq else 2, ctx.hero.hair, smooth=hq)
        ctx.mb.tube(_at(ctx, 0, 0.06, 0.21), _at(ctx, 0, 0.06, 0.25), 0.05 * s, sides=6 if hq else 4, color=pin_color)
        if hq:
            ctx.mb.tube(_at(ctx, -0.14, 0.06, 0.29), _at(ctx, 0.14, 0.06, 0.26), 0.008 * s, sides=4, color=pin_color)


def _wide_hat(ctx, crown_c, band_c, brim_r=0.38, crown_h=0.22, sag=0.04):
    s, q, hq = ctx.s, ctx.q, ctx.hq
    sides = 14 if hq else 8
    with ctx.mb.bound_to("head"):
        with ctx.mb.xf(Matrix.Translation(_at(ctx, 0, 0.02, 0.13))):
            ctx.mb.lathe([(0.22 * s, 0.0), (0.205 * s, crown_h * 0.5 * s), (0.16 * s, crown_h * s), (0.04 * s, (crown_h + 0.02) * s)], q["head_s"], crown_c, smooth=hq)
            ctx.mb.lathe([(0.226 * s, 0.005 * s), (0.22 * s, 0.045 * s)], q["head_s"], band_c, smooth=False)
        rings = []
        for dz in (0.0, 0.018):
            ring = []
            for j in range(sides):
                a = 2 * math.pi * (j + 0.5) / sides
                drop = -sag * (math.cos(a) ** 2)
                ring.append(_at(ctx, brim_r * math.cos(a), 0.02 + brim_r * math.sin(a), 0.13 + dz + drop))
            rings.append(ring)
        inner = [_at(ctx, 0.2 * math.cos(2 * math.pi * (j + 0.5) / sides), 0.02 + 0.2 * math.sin(2 * math.pi * (j + 0.5) / sides), 0.13) for j in range(sides)]
        ctx.mb.loft([inner, rings[0], rings[1]], crown_c, smooth=False)


def _top_hat(ctx, color="cloth_black", band="faction_b"):
    s, q, hq = ctx.s, ctx.q, ctx.hq
    with ctx.mb.bound_to("head"):
        with ctx.mb.xf(Matrix.Translation(_at(ctx, 0, 0.02, 0.14))):
            ctx.mb.lathe([(0.3 * s, 0.0), (0.3 * s, 0.018 * s), (0.21 * s, 0.02 * s), (0.205 * s, 0.1 * s), (0.23 * s, 0.34 * s), (0.02 * s, 0.35 * s)], q["head_s"], color, smooth=False)
            ctx.mb.lathe([(0.214 * s, 0.022 * s), (0.218 * s, 0.07 * s)], q["head_s"], band, smooth=False)


def _pigtails(ctx, color=None, band="faction_b"):
    s, hq = ctx.s, ctx.hq
    c = color or ctx.hero.hair
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            pts = [_at(ctx, sign * 0.17, 0.02, 0.18), _at(ctx, sign * 0.29, 0.06, 0.22), _at(ctx, sign * 0.33, 0.08, -0.02), _at(ctx, sign * 0.29, 0.09, -0.2)]
            ctx.mb.path(pts, [0.05 * s, 0.068 * s, 0.052 * s, 0.014 * s], 6 if hq else 4, c)
            ctx.mb.sphere(_at(ctx, sign * 0.21, 0.03, 0.19), 0.034 * s, 5 if hq else 4, 3, band, smooth=False)


# ---- 1. Rook ------------------------------------------------------------------------------------

def rook_armada(ctx):
    """Rook: Gilded Armada heavy artillerist — braided crest under tall plumed shako, gilded cuirass, spiked steel pauldrons, navy braided coat sleeves & ammo drum belt."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    sc.moustache(ctx)
    sc.shako(ctx, "navy", "gold")
    sc.cuirass(ctx, "gold", "enamel")
    sc.pauldrons(ctx, "iron_light", True, "gold")
    sc.cross_belt(ctx, "enamel")
    _cuffs(ctx, "gold", start=0.66, flare=1.35)
    _greaves(ctx, "navy", "gold")
    with ctx.mb.bound_to("hips"):
        ctx.mb.lathe([(0.235 * w * s * g ** 0.3, 0.85 * s), (0.235 * w * s * g ** 0.3, 0.94 * s)], ctx.q["torso"], "leather_dark", smooth=False)
        if hq:
            for a in (-0.6, 0.0, 0.6):
                ctx.mb.tube((0.25 * w * s * math.sin(a), -0.22 * g * s * math.cos(a), 0.92 * s),
                            (0.25 * w * s * math.sin(a), -0.22 * g * s * math.cos(a), 0.82 * s), 0.034 * s, sides=6, color="brass")


def rook_foundry(ctx):
    """Rook: Scrap-Winds furnace-master — dreadlocked hair with copper rings, welder visor & goatee, riveted furnace apron, glowing shoulder exhaust & iron gauntlet."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    _dreads(ctx, count=5, length=0.3, beads="rust")
    sc.goatee(ctx)
    with ctx.mb.bound_to("head"):
        # Welder's flip-up iron visor across brow with glowing ember slit
        ctx.mb.box(tuple(_at(ctx, 0, -0.215, 0.095)), (0.28 * s, 0.05 * s, 0.08 * s), "iron")
        ctx.mb.box(tuple(_at(ctx, 0, -0.242, 0.095)), (0.22 * s, 0.015 * s, 0.022 * s), "ember")
    sc.apron(ctx, "leather_dark")
    sc.chain_wrap(ctx)
    with ctx.mb.bound_to("chest"):
        # Furnace shoulder stack on his left shoulder
        ctx.mb.sphere((0.32 * w * s, 0, 1.3 * s), (0.18 * s, 0.18 * s, 0.12 * s), 7 if hq else 4, 3, "rust_dark", smooth=False)
        ctx.mb.tube((0.36 * w * s, 0.04 * s, 1.38 * s), (0.4 * w * s, 0.08 * s, 1.62 * s), 0.055 * s, 0.048 * s, sides=6 if hq else 4, color="iron")
        ctx.mb.sphere((0.4 * w * s, 0.08 * s, 1.64 * s), 0.04 * s, 5 if hq else 4, 3, "ember", smooth=False)
    sc.iron_arm(ctx, "L")
    _greaves(ctx, "iron", "rust")


# ---- 2. Lyra ------------------------------------------------------------------------------------

def lyra_tempest(ctx):
    """Lyra: Tempest sky-aviator — high wind-swept ponytail under leather aviator cap & glowing wind goggles, cropped flight jacket, storm collar, split waist sash & laced boots."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_ponytail(ctx)
    with ctx.mb.bound_to("head"):
        # Aviator leather helmet ear-flaps and brow strap
        ctx.mb.sphere(_at(ctx, 0, 0.03, 0.08), (0.218 * s, 0.216 * s, 0.16 * s), ctx.q["head_s"], 4 if hq else 3, "leather_dark", smooth=ctx.hq)
        for sign in (1, -1):
            ctx.mb.plate([_at(ctx, sign * 0.19, -0.04, 0.04), _at(ctx, sign * 0.22, 0.08, 0.04), _at(ctx, sign * 0.2, 0.02, -0.15)], 0.022 * s, "leather_dark")
    sc.goggles_up(ctx, "wind")
    sc.short_jacket(ctx, "navy", "cloth_white")
    sc.high_collar(ctx, "faction_b")
    sc.scarf(ctx, "wind")
    sc.sash(ctx, "faction_a", tail=True)
    _boot_cuffs_wrap(ctx, "leather_dark", "wind")


def _boot_cuffs_wrap(ctx, color, cords):
    _sc()._boot_cuffs(ctx, color, flare=1.18, cords=cords)


def lyra_starweaver(ctx):
    """Lyra: Syndicate starweaver — twin braids with silver crescent circlet, tiered velvet-and-gold celestial cape, glowing liftstone brooches, laced midnight tunic & gold cuffs."""
    sc = _sc()
    s, w, hq = ctx.s, ctx.w, ctx.hq
    sc.hair_cap(ctx)
    _twin_braids(ctx, band="silver", length=0.38)
    with ctx.mb.bound_to("head"):
        # Crescent silver circlet on forehead
        ctx.mb.path([_at(ctx, -0.14, -0.13, 0.12), _at(ctx, 0, -0.205, 0.11), _at(ctx, 0.14, -0.13, 0.12)], [0.009 * s, 0.012 * s, 0.009 * s], 4, "silver")
        ctx.mb.plate([_at(ctx, -0.035, -0.205, 0.12), _at(ctx, 0.035, -0.205, 0.12), _at(ctx, 0, -0.215, 0.21)], 0.01 * s, "liftstone")
    sc.long_coat(ctx, "faction_a", "cloth_black", tail_len=0.34)
    sc.high_collar(ctx, "gold")
    sc.cape(ctx, "velvet", length=0.28, lining="plasma")
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.sphere((sign * 0.19 * w * s, -0.16 * s, 1.3 * s), 0.036 * s, 6 if hq else 4, 3, "liftstone", smooth=False)
    _cuffs(ctx, "gold", start=0.72, flare=1.42)
    sc.sash(ctx, "gold", tail=False)


# ---- 3. Sable -----------------------------------------------------------------------------------

def sable_masquerade(ctx):
    """Sable: Crimson masquerade infiltrator — hood off, sleek asymmetric bob with crimson ribbon, gilded half-face masquerade mask, velvet tailcoat, high collar & corset sash."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_side_shave(ctx, mirrored=False)
    with ctx.mb.bound_to("head"):
        # Ornate gold & ivory half-face masquerade mask over eyes
        ctx.mb.plate([_at(ctx, -0.15, -0.175, 0.08), _at(ctx, 0.15, -0.175, 0.08), _at(ctx, 0.12, -0.185, -0.01), _at(ctx, 0, -0.205, -0.04), _at(ctx, -0.12, -0.185, -0.01)], 0.012 * s, "gold")
        if hq:
            ctx.mb.plate([_at(ctx, 0.12, -0.18, 0.08), _at(ctx, 0.21, -0.16, 0.19), _at(ctx, 0.14, -0.17, 0.11)], 0.01 * s, "gem_red")
    sc.long_coat(ctx, "velvet", "cloth_black", tail_len=0.28)
    sc.high_collar(ctx, "velvet")
    sc.sash(ctx, "gold", tail=True)
    sc.dagger_sheaths(ctx)
    _cuffs(ctx, "gold", start=0.75, flare=1.3)


def sable_ronin(ctx):
    """Sable: Obsidian sky-ronin — high pinned topknot under wide conical kasa hat & black lower-face mask, layered lamellar pauldrons, split haori coat & shinobi leg wraps."""
    sc = _sc()
    s, w, hq = ctx.s, ctx.w, ctx.hq
    sc.hair_cap(ctx)
    _topknot(ctx, "silver")
    sc.face_mask(ctx, "cloth_black")
    with ctx.mb.bound_to("head"):
        # Wide conical kasa straw/lacquer hat
        with ctx.mb.xf(Matrix.Translation(_at(ctx, 0, 0.01, 0.12))):
            ctx.mb.lathe([(0.44 * s, 0.0), (0.3 * s, 0.11 * s), (0.14 * s, 0.21 * s), (0.02 * s, 0.26 * s)], 12 if hq else 6, "cloth_black", smooth=False)
            if hq:
                ctx.mb.lathe([(0.445 * s, -0.004 * s), (0.445 * s, 0.01 * s)], 12, "iron_light", smooth=False)
    sc.short_jacket(ctx, "cloth_black", "iron")
    sc.tabard(ctx, "cloth_black", "silver", length=0.4)
    sc.pauldrons(ctx, "iron", False, "silver")
    sc.cross_belt(ctx, "leather_dark")
    _greaves(ctx, "leather_dark", "iron_light")


def _side_tufts(ctx, color=None):
    """Low side-hair tufts tucked neatly below a hat brim."""
    s, hq = ctx.s, ctx.hq
    c = color or ctx.hero.hair
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            ctx.mb.sphere(_at(ctx, sign * 0.2, 0.04, 0.02), (0.065 * s, 0.09 * s, 0.08 * s), 6 if hq else 4, 3, c, smooth=False)


def _full_bandana(ctx, color="gem_red", tails=True):
    """Head-covering bandana that cleanly clears hair_cap underneath."""
    s, q, hq = ctx.s, ctx.q, ctx.hq
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.035, 0.095), (0.222 * s, 0.224 * s, 0.195 * s), q["head_s"], 5 if hq else 3, color, smooth=hq)
        if tails:
            y = 0.24
            ctx.mb.plate([_at(ctx, 0, y, 0.06), _at(ctx, 0.1, y + 0.2, -0.14), _at(ctx, -0.02, y + 0.13, -0.17)], 0.025 * s, color)


# ---- 4. Thorne ----------------------------------------------------------------------------------

def thorne_alchemist(ctx):
    """Dr. Thorne: Emerald plague-alchemist — hood off, wild grey side-tufts under tall buckled apothecary hat, brass spectacles & lower face respirator, buckled leather coat & glowing vial bandolier."""
    sc = _sc()
    s, g, w, hq = ctx.s, ctx.g, ctx.w, ctx.hq
    _side_tufts(ctx)
    _wide_hat(ctx, "leather_dark", "faction_b", brim_r=0.35, crown_h=0.26, sag=0.05)
    sc.spectacles(ctx)
    sc.face_mask(ctx, "leather_dark")
    sc.long_coat(ctx, "leather_dark", "cloth_black", tail_len=0.28)
    sc.bandolier(ctx, "liftstone")
    with ctx.mb.bound_to("hips"):
        # Glowing alchemical lantern flask at left hip
        ctx.mb.sphere((0.25 * w * s, -0.05 * s, 0.78 * s), 0.055 * s, 6 if hq else 4, 3, "faction_b", smooth=False)
        ctx.mb.tube((0.25 * w * s, -0.05 * s, 0.84 * s), (0.25 * w * s, -0.05 * s, 0.91 * s), 0.02 * s, sides=4, color="brass")
    _boot_cuffs_wrap(ctx, "leather", "brass")


def thorne_archmage(ctx):
    """Dr. Thorne: Sorcerer archmage — swept silver-black mane under jagged obsidian-and-plasma crown, wide standing wing-collar, sweeping plasma-lined cape, arcane breastplate & ritual tabard."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_long(ctx, 0.34)
    with ctx.mb.bound_to("head"):
        # Jagged obsidian & plasma crown
        spikes = 6 if hq else 4
        for k in range(spikes):
            a = 2 * math.pi * k / spikes
            base = _at(ctx, 0.19 * math.cos(a), 0.02 + 0.19 * math.sin(a), 0.14)
            tip = _at(ctx, 0.22 * math.cos(a), 0.02 + 0.22 * math.sin(a), 0.28 + (0.04 if k % 2 == 0 else 0.0))
            ctx.mb.tube(base, tip, 0.032 * s, 0.005 * s, sides=4, color="plasma" if k % 2 == 0 else "abyss")
    sc.cuirass(ctx, "abyss", "plasma")
    sc.pauldrons(ctx, "abyss", True, "plasma")
    sc.high_collar(ctx, "plasma")
    sc.cape(ctx, "abyss", length=0.3, lining="plasma")
    sc.tabard(ctx, "faction_a", "plasma", length=0.34)
    _cuffs(ctx, "plasma", start=0.72, flare=1.45)


# ---- 5. Morrow ----------------------------------------------------------------------------------

def morrow_corsair(ctx):
    """Morrow: Crimson sky-corsair — hat off, long rakish ponytail, crimson eyepatch & goatee, open laced shirt under embroidered bolero jacket, wide crimson sash, twin pistols & cavalier boots."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_ponytail(ctx)
    sc.eyepatch(ctx, side=1)
    sc.goatee(ctx)
    sc.short_jacket(ctx, "velvet", "cloth_white")
    sc._v_neck(ctx, sc._BASE_CHEST, ctx.hero.skin, depth=1.18)
    sc.sash(ctx, "gem_red", tail=True)
    with ctx.mb.bound_to("hips"):
        for sign in (1, -1):
            sc._pistol(ctx.mb, s, Vector((sign * 0.21 * w * s, -0.14 * g * s, 0.88 * s)), Vector((0, -0.05, -1)), Vector((0, -1, 0)), hq=hq)
    _cuffs(ctx, "cloth_white", start=0.72, flare=1.4)
    sc._boot_cuffs(ctx, "leather_dark", flare=1.28)


def morrow_admiral(ctx):
    """Morrow: Gilded grand admiral — plumed gilded bicorne & monocle, crisp white-and-navy naval dress greatcoat with gold braided epaulettes, medal cluster, scarlet sash & dress gloves."""
    sc = _sc()
    sc.hair_slick(ctx)
    _monocle(ctx, side=1, frame="gold", lens="glass")
    sc.bicorne(ctx, "navy", "gold")
    sc.long_coat(ctx, "enamel", "navy", tail_len=0.34)
    sc.epaulettes(ctx, "gold")
    sc.medals(ctx)
    sc.gold_buttons(ctx)
    sc.sash(ctx, "gem_red", tail=True)
    _cuffs(ctx, "gold", start=0.74, flare=1.36)
    sc._boot_cuffs(ctx, "navy", flare=1.15)


# ---- 6. Brill -----------------------------------------------------------------------------------

def brill_whaler(ctx):
    """Bosun Brill: Azure storm-whaler — ochre sou'wester storm hat, forked braided beard, heavy oilskin storm coat with high collar, coiled harpoon rope, hip lantern & tall wading boots."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    # Forked twin beard braids
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            pts = [_at(ctx, sign * 0.06, -0.16, -0.1), _at(ctx, sign * 0.09, -0.19, -0.22), _at(ctx, sign * 0.1, -0.18, -0.34)]
            ctx.mb.path(pts, [0.05 * s, 0.04 * s, 0.015 * s], 5 if hq else 3, ctx.hero.hair)
            if hq:
                ctx.mb.sphere(pts[2], 0.024 * s, 5, 3, "enamel", smooth=False)
    _wide_hat(ctx, "amber", "navy", brim_r=0.36, crown_h=0.16, sag=0.07)
    sc.long_coat(ctx, "navy", "amber", tail_len=0.45)
    sc.high_collar(ctx, "amber")
    # Heavy harpoon rope slung over chest
    with ctx.mb.bound_to("chest"):
        ctx.mb.tube((-0.26 * w * s, -0.14 * g * s, 1.32 * s), (0.24 * w * s, -0.19 * g * s, 1.06 * s), 0.042 * s, sides=6 if hq else 4, color="rope")
    with ctx.mb.bound_to("hips"):
        ctx.mb.sphere((-0.25 * w * s, -0.06 * s, 0.78 * s), 0.052 * s, 6 if hq else 4, 3, "lamp", smooth=False)
    sc._boot_cuffs(ctx, "amber", flare=1.24)


def brill_deck_boss(ctx):
    """Bosun Brill: Crimson deck-boss — cocked gold-trimmed pirate tricorn, waxed handlebar moustache & mutton chops (no long beard), open scarlet waistcoat with gold buttons & heavy chain sash."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    sc.moustache(ctx)
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            ctx.mb.sphere(_at(ctx, sign * 0.15, -0.1, -0.08), (0.045 * s, 0.06 * s, 0.08 * s), 5 if hq else 4, 3, ctx.hero.hair, smooth=False)
    sc.cocked_tricorn(ctx, "cloth_black", "gold")
    sc.short_jacket(ctx, "gem_red", "cloth_white")
    sc.gold_buttons(ctx)
    sc.chain_wrap(ctx)
    sc.sash(ctx, "gold_dark", tail=True)
    with ctx.mb.bound_to("hips"):
        sc._pistol(ctx.mb, s, Vector((-0.22 * w * s, -0.15 * g * s, 0.88 * s)), Vector((0, -0.05, -1)), Vector((0, -1, 0)), hq=hq)
    _cuffs(ctx, "cloth_white", start=0.68, flare=1.32)


# ---- 7. Hask ------------------------------------------------------------------------------------

def hask_ironclad(ctx):
    """Hask: Warden ironclad gunner — riveted steel half-helm with crest & braided back mohawk tail, full steel cuirass, spiked pauldrons, armored vambraces & steel tassets."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    with ctx.mb.bound_to("head"):
        # Steel half-helm bowl + noseguard + crest
        ctx.mb.sphere(_at(ctx, 0, 0.02, 0.1), (0.22 * s, 0.22 * s, 0.16 * s), ctx.q["head_s"], 4 if hq else 3, "iron_light", smooth=False)
        ctx.mb.box(tuple(_at(ctx, 0, -0.21, 0.04)), (0.04 * s, 0.025 * s, 0.11 * s), "iron")
        ctx.mb.plate([_at(ctx, 0, -0.18, 0.2), _at(ctx, 0, 0.18, 0.2), _at(ctx, 0, 0.08, 0.34), _at(ctx, 0, -0.12, 0.3)], 0.02 * s, "faction_b")
        # Braided mohawk tail out the back
        ctx.mb.path([_at(ctx, 0, 0.2, 0.08), _at(ctx, 0, 0.26, -0.06), _at(ctx, 0, 0.22, -0.22)], [0.045 * s, 0.036 * s, 0.015 * s], 5 if hq else 3, "hair_black")
    sc.scar(ctx, side=1)
    sc.cuirass(ctx, "iron", "faction_b")
    sc.pauldrons(ctx, "iron_light", True, "faction_b")
    sc.tabard(ctx, "faction_a", "faction_b", length=0.45)
    sc.chain_wrap(ctx)
    _cuffs(ctx, "iron_light", start=0.45, flare=1.22)
    _greaves(ctx, "iron", "iron_light")


def hask_privateer(ctx):
    """Hask: Obsidian deep-sky privateer — knotted crimson head-bandana with tails & braided chin-beard, sleeveless obsidian trenchcoat with upturned studded collar & dual brass bandoliers."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.bandana(ctx, "gem_red", tails=True)
    with ctx.mb.bound_to("head"):
        pts = [_at(ctx, 0, -0.17, -0.14), _at(ctx, 0, -0.19, -0.24), _at(ctx, 0, -0.17, -0.34)]
        ctx.mb.path(pts, [0.05 * s, 0.042 * s, 0.016 * s], 5 if hq else 3, "hair_black")
        if hq:
            ctx.mb.tube(pts[1], pts[1].lerp(pts[2], 0.4), 0.044 * s, sides=5, color="brass")
    sc.scar(ctx, side=1)
    sc.long_coat(ctx, "cloth_black", "leather_dark", tail_len=0.36)
    sc.high_collar(ctx, "cloth_black")
    sc.cross_belt(ctx, "brass")
    sc.sash(ctx, "gem_red", tail=True)
    _cuffs(ctx, "leather_dark", start=0.58, flare=1.18)


# ---- 8. Wren ------------------------------------------------------------------------------------

def wren_plague_doc(ctx):
    """Sawbones Wren: Obsidian plague doctor — wide dark slouch hat, long brass-and-leather plague beak mask with glowing green lenses, waxed shoulder capelet, buttoned trenchcoat & tonic flasks."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hood(ctx, "cloth_black")
    _wide_hat(ctx, "cloth_black", "iron_light", brim_r=0.36, crown_h=0.18, sag=0.05)
    with ctx.mb.bound_to("head"):
        # Plague beak projecting forward (-Y) + glowing emerald lenses
        ctx.mb.tube(_at(ctx, 0, -0.17, -0.02), _at(ctx, 0, -0.42, -0.1), 0.078 * s, 0.014 * s, sides=6 if hq else 4, color="leather_dark")
        if hq:
            ctx.mb.tube(_at(ctx, 0, -0.26, -0.045), _at(ctx, 0, -0.29, -0.055), 0.056 * s, sides=6, color="brass")
        for sign in (1, -1):
            ctx.mb.sphere(_at(ctx, sign * 0.075, -0.195, 0.03), 0.036 * s, 6 if hq else 4, 3, "glass", smooth=False)
    sc.long_coat(ctx, "leather_dark", "cloth_black", tail_len=0.28)
    sc.cape(ctx, "cloth_black", length=0.72)
    sc.bandolier(ctx, "glass")
    with ctx.mb.bound_to("hips"):
        for sign in (1, -1):
            ctx.mb.sphere((sign * 0.24 * w * s, -0.06 * s, 0.8 * s), 0.045 * s, 6 if hq else 4, 3, "toxic", smooth=False)


def wren_gentleman(ctx):
    """Sawbones Wren: Emerald Victorian gentleman-surgeon — tall silk stovepipe top hat with emerald band, swept silver side hair, brass monocle, emerald frock coat, cream cravat & watch chain."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    _side_tufts(ctx)
    _top_hat(ctx, "cloth_black", "faction_a")
    _monocle(ctx, side=-1, frame="gold", lens="glass")
    sc.long_coat(ctx, "faction_a", "cloth_white", tail_len=0.32)
    with ctx.mb.bound_to("chest"):
        # Cream cravat & gold lapel/watch trim
        ctx.mb.plate([(-0.06 * s, -0.19 * g * s, 1.36 * s), (0.06 * s, -0.19 * g * s, 1.36 * s), (0.04 * s, -0.205 * g * s, 1.15 * s), (-0.04 * s, -0.205 * g * s, 1.15 * s)], 0.02 * s, "cloth_white")
        if hq:
            ctx.mb.path([(-0.08 * s, -0.2 * g * s, 1.09 * s), (0.0, -0.215 * g * s, 1.03 * s), (0.12 * s, -0.195 * g * s, 1.08 * s)], [0.006 * s] * 3, 3, "gold")
    _cuffs(ctx, "cloth_white", start=0.74, flare=1.32)
    sc.tool_belt(ctx)


# ---- 9. Ivo -------------------------------------------------------------------------------------

def ivo_aether_mage(ctx):
    """Ivo: Azure academy aether-mage — tall crooked wizard hat wrapped in copper wire & glowing lightning crystal, neatly parted hair, cobalt-and-gold robe-coat & astrolabe shoulder rings."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_slick(ctx)
    with ctx.mb.bound_to("head"):
        # Tall crooked pointed wizard hat + wide brim + lightning crystal
        with ctx.mb.xf(Matrix.Translation(_at(ctx, 0, 0.02, 0.14))):
            ctx.mb.lathe([(0.36 * s, 0.0), (0.36 * s, 0.015 * s), (0.21 * s, 0.02 * s), (0.21 * s, 0.07 * s)], 12 if hq else 6, "navy", smooth=False)
        spire = [_at(ctx, 0, 0.02, 0.18), _at(ctx, 0.02, 0.04, 0.36), _at(ctx, -0.04, 0.09, 0.54), _at(ctx, -0.09, 0.15, 0.64)]
        ctx.mb.path(spire, [0.19 * s, 0.12 * s, 0.05 * s, 0.008 * s], 8 if hq else 4, "navy")
        ctx.mb.sphere(_at(ctx, 0, -0.21, 0.23), 0.036 * s, 6 if hq else 4, 3, "lightning", smooth=False)
    sc.long_coat(ctx, "faction_a", "cloth_white", tail_len=0.34)
    sc.cape(ctx, "navy", length=0.68, lining="lightning")
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            place = Matrix.Translation((sign * 0.28 * w * s, 0, 1.3 * s)) @ Matrix.Rotation(sign * 0.45, 4, "Y")
            with ctx.mb.xf(place):
                ctx.mb.lathe([(0.13 * s, -0.012), (0.13 * s, 0.012)], 8 if hq else 4, "gold", smooth=False)
    sc.sash(ctx, "gold", tail=True)
    _cuffs(ctx, "gold", start=0.7, flare=1.42)


def ivo_coil_runner(ctx):
    """Ivo: Scrap-Winds coil-runner — wild spiked shock hair, oversized brass/liftstone aviator goggles over eyes, billowing scarf, cropped flight jacket & twin Tesla coil spires on backpack."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_wild(ctx)
    _goggles_eyes(ctx, "brass", "liftstone", "leather_dark")
    sc.short_jacket(ctx, "leather", "canvas")
    sc.scarf(ctx, "amber")
    with ctx.mb.bound_to("chest"):
        # Twin Tesla coil backpack spires
        ctx.mb.box((0, 0.22 * g * s, 1.2 * s), (0.28 * s, 0.14 * s, 0.26 * s), "leather_dark")
        for sign in (1, -1):
            base = (sign * 0.1 * s, 0.25 * g * s, 1.32 * s)
            top = (sign * 0.14 * s, 0.27 * g * s, 1.62 * s)
            ctx.mb.tube(base, top, 0.03 * s, 0.02 * s, sides=6 if hq else 4, color="rust")
            ctx.mb.sphere(top, 0.042 * s, 6 if hq else 4, 3, "lightning", smooth=False)
    _greaves(ctx, "rust", "brass")


def chad_vampire(ctx):
    """Chad: Ivo's evil vampire sorcerer twin — swept brown waves with prominent front-left silver-white lock,
    tall crimson-lined vampire collar with silver filigree, white ruffled cravat, dark tailored coat with crimson
    lapels, sweeping crimson cape, silver cuffs & tall boots."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    with ctx.mb.bound_to("head"):
        # Swept brown wavy locks framing the forehead, temples, and nape
        waves = [
            (_at(ctx, -0.02, -0.15, 0.16), _at(ctx, -0.14, -0.12, 0.21), _at(ctx, -0.22, 0.02, 0.14), _at(ctx, -0.19, 0.14, -0.04)),
            (_at(ctx, 0.01, -0.16, 0.16), _at(ctx, 0.13, -0.13, 0.20), _at(ctx, 0.21, 0.02, 0.13), _at(ctx, 0.18, 0.14, -0.05)),
            (_at(ctx, -0.11, 0.04, 0.20), _at(ctx, 0.0, 0.14, 0.21), _at(ctx, 0.11, 0.04, 0.20), _at(ctx, 0.0, 0.21, 0.01)),
        ]
        for pts in (waves if hq else waves[:2]):
            ctx.mb.path(pts, [0.055 * s, 0.068 * s, 0.055 * s, 0.028 * s], 5 if hq else 3, ctx.hero.hair)
        # Signature swept white-silver lock (+X = character's left / viewer's right in portrait)
        ctx.mb.path(
            [_at(ctx, 0.0, -0.175, 0.145), _at(ctx, 0.09, -0.18, 0.165), _at(ctx, 0.165, -0.115, 0.13), _at(ctx, 0.18, 0.02, 0.07)],
            [0.032 * s, 0.044 * s, 0.036 * s, 0.015 * s],
            5 if hq else 3,
            "hair_white",
        )
        if hq:
            ctx.mb.path(
                [_at(ctx, 0.02, -0.18, 0.125), _at(ctx, 0.11, -0.165, 0.12), _at(ctx, 0.17, -0.07, 0.085)],
                [0.02 * s, 0.026 * s, 0.011 * s],
                4,
                "hair_white",
            )
    sc.long_coat(ctx, "cloth_black", "cloth_black", tail_len=0.36)
    sc.cape(ctx, "faction_a", length=0.68, lining="cloth_black")
    with ctx.mb.bound_to("chest"):
        # Tall flaring vampire collar (open at front -Y so face and cravat stay visible)
        cols = 8 if hq else 4
        outer_rings, inner_rings = [], []
        for r_idx, (rad_x, rad_y, z) in enumerate(((0.16, 0.16, 1.32), (0.24, 0.21, 1.54))):
            outer, inner = [], []
            for k in range(cols + 1):
                a = math.radians(-118 + 236 * k / cols)  # 0 rad is +Y (back), +/-118 deg leaves front open
                sx = math.sin(a)
                cy = math.cos(a)
                outer.append((rad_x * w * s * sx, rad_y * g * s * cy, z * s))
                inner.append(((rad_x - 0.018) * w * s * sx, (rad_y - 0.018) * g * s * cy, z * s))
            outer_rings.append(outer)
            inner_rings.append(inner)
        ctx.mb.loft([outer_rings[0] + list(reversed(inner_rings[0])), outer_rings[1] + list(reversed(inner_rings[1]))], "cloth_black", smooth=False)
        ctx.mb.loft(inner_rings, "gem_red", smooth=False)
        if hq:
            # Silver filigree trim along top rim of the vampire collar
            ctx.mb.path([(p[0] * 1.02, p[1] * 1.02, p[2] + 0.008 * s) for p in outer_rings[1]], [0.01 * s] * (cols + 1), 3, "silver")
        # White ruffled cravat & glowing crimson clasp at throat
        ctx.mb.plate([(-0.065 * s, -0.185 * g * s, 1.36 * s), (0.065 * s, -0.185 * g * s, 1.36 * s), (0.038 * s, -0.205 * g * s, 1.13 * s), (-0.038 * s, -0.205 * g * s, 1.13 * s)], 0.022 * s, "cloth_white")
        ctx.mb.sphere((0, -0.205 * g * s, 1.33 * s), (0.024 * s, 0.016 * s, 0.028 * s), 6 if hq else 4, 3, "ember", smooth=False)
        # Crimson & silver-trimmed vampire lapels
        for sign in (1, -1):
            ctx.mb.plate(
                [
                    (sign * 0.06 * s, -0.185 * g * s, 1.34 * s),
                    (sign * 0.18 * w * s, -0.175 * g * s, 1.32 * s),
                    (sign * 0.14 * w * s, -0.195 * g * s, 1.12 * s),
                    (sign * 0.04 * s, -0.20 * g * s, 1.14 * s),
                ],
                0.018 * s,
                "gem_red",
            )
            if hq:
                ctx.mb.tube((sign * 0.175 * w * s, -0.18 * g * s, 1.32 * s), (sign * 0.135 * w * s, -0.20 * g * s, 1.12 * s), 0.009 * s, sides=3, color="silver")
    _cuffs(ctx, "silver", start=0.72, flare=1.3)
    _greaves(ctx, "leather_dark", "silver")


# ---- 10. Roxanne --------------------------------------------------------------------------------

def roxanne_valkyrie(ctx):
    """Roxanne: Gilded sky-valkyrie — high braided war-ponytail, winged gilded circlet helm, sculpted ivory-and-gold cuirass with feathered wing-pauldrons, crimson cape & ornate greaves."""
    sc = _sc()
    s, w, hq = ctx.s, ctx.w, ctx.hq
    sc.hair_ponytail(ctx)
    with ctx.mb.bound_to("head"):
        # Winged Valkyrie circlet
        ctx.mb.path([_at(ctx, -0.17, -0.06, 0.12), _at(ctx, 0, -0.205, 0.14), _at(ctx, 0.17, -0.06, 0.12)], [0.015 * s, 0.02 * s, 0.015 * s], 4, "gold")
        for sign in (1, -1):
            ctx.mb.plate([_at(ctx, sign * 0.18, -0.04, 0.12), _at(ctx, sign * 0.22, 0.02, 0.12), _at(ctx, sign * 0.38, 0.16, 0.36), _at(ctx, sign * 0.26, 0.08, 0.26)], 0.016 * s, "enamel")
    sc.cuirass(ctx, "enamel", "gold")
    sc.pauldrons(ctx, "gold", False, "enamel")
    with ctx.mb.bound_to("chest"):
        # Sweeping wing-tips on shoulders
        for sign in (1, -1):
            ctx.mb.plate([(sign * 0.3 * w * s, 0.02 * s, 1.34 * s), (sign * 0.44 * w * s, 0.1 * s, 1.54 * s), (sign * 0.38 * w * s, 0.14 * s, 1.32 * s)], 0.018 * s, "enamel")
    sc.cape(ctx, "gem_red", length=0.4, lining="gold")
    sc.tabard(ctx, "faction_a", "gold", length=0.4)
    _greaves(ctx, "gold", "enamel")


def roxanne_syndicate(ctx):
    """Roxanne: Syndicate neon cyber-corsair — twin high punk pigtails, glowing cyan visor shades, cropped obsidian moto-corsair jacket with neon collar, asymmetric armored left shoulder & plasma hip rig."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    _pigtails(ctx, "faction_b", "faction_a")
    with ctx.mb.bound_to("head"):
        # Glowing cyan visor shades
        ctx.mb.box(tuple(_at(ctx, 0, -0.21, 0.035)), (0.26 * s, 0.026 * s, 0.055 * s), "liftstone")
        ctx.mb.box(tuple(_at(ctx, 0, -0.205, 0.068)), (0.27 * s, 0.03 * s, 0.014 * s), "cloth_black")
    sc.short_jacket(ctx, "cloth_black", "faction_a")
    sc.high_collar(ctx, "liftstone")
    with ctx.mb.bound_to("chest"):
        # Asymmetric heavy Syndicate pauldron on left shoulder only
        ctx.mb.sphere((0.3 * w * s, 0, 1.31 * s), (0.18 * s, 0.18 * s, 0.12 * s), 7 if hq else 4, 3, "faction_a", smooth=False)
        ctx.mb.box((0.32 * w * s, -0.14 * s, 1.3 * s), (0.16 * s, 0.02 * s, 0.03 * s), "liftstone")
    with ctx.mb.bound_to("hips"):
        for sign in (1, -1):
            ctx.mb.box((sign * 0.25 * w * s, -0.02 * s, 0.82 * s), (0.06 * s, 0.1 * s, 0.16 * s), "plasma")
    _cuffs(ctx, "plasma", start=0.68, flare=1.3)


# ---- 11. May ------------------------------------------------------------------------------------

def may_centurion(ctx):
    """May: Gilded royal centurion — crested silver-and-crimson plumed morion helm with loose locks below, gilded ceremonial cuirass, scarlet legionary cape, twin matching pauldrons & war tabard."""
    sc = _sc()
    sc.hair_long(ctx, 0.28)
    sc.morion(ctx, "silver", "gem_red")
    sc.cuirass(ctx, "gold", "enamel")
    sc.pauldrons(ctx, "gold", False, "gem_red")
    sc.tabard(ctx, "gem_red", "gold", length=0.38)
    sc.cape(ctx, "gem_red", length=0.36, lining="gold")
    _cuffs(ctx, "gold", start=0.62, flare=1.25)
    _greaves(ctx, "gold", "gem_red")


def may_rebel(ctx):
    """May: Crimson sky-rebel — hair let completely down in long flowing black waves, red-and-gold headband with flying tails, cropped crimson leather jacket, single iron shoulder guard & rogue half-cape."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_long(ctx, 0.44)
    _full_bandana(ctx, "gem_red", tails=True)
    sc.short_jacket(ctx, "gem_red", "cloth_white")
    sc.cross_belt(ctx, "leather_dark")
    with ctx.mb.bound_to("chest"):
        # Single salvaged iron shoulder guard on left shoulder + asymmetric half-cape
        ctx.mb.sphere((0.29 * w * s, 0, 1.3 * s), (0.16 * s, 0.16 * s, 0.1 * s), 7 if hq else 4, 3, "iron_light", smooth=False)
        ctx.mb.plate([(0.06 * w * s, 0.17 * g * s, 1.34 * s), (0.3 * w * s, 0.15 * g * s, 1.32 * s), (0.42 * w * s, 0.34 * g * s, 0.62 * s), (0.04 * w * s, 0.28 * g * s, 0.66 * s)], 0.02 * s, "cloth_black")
    sc.sash(ctx, "gold_dark", tail=True)
    _boot_cuffs_wrap(ctx, "leather_dark", "gold")


# ---- 12. Mirren ---------------------------------------------------------------------------------

def mirren_bombardier(ctx):
    """Mirren: Gilded parade bombardier — copper hair in twin thick braided pigtails under tall plumed artillery shako cap, navy-and-crimson artillery tunic, gold epaulettes & white cross-belts."""
    sc = _sc()
    sc.hair_cap(ctx)
    _twin_braids(ctx, band="gold", length=0.32)
    sc.shako(ctx, "navy", "gem_red")
    sc.long_coat(ctx, "navy", "gem_red", tail_len=0.42)
    sc.epaulettes(ctx, "gold")
    sc.cross_belt(ctx, "cloth_white")
    sc.gold_buttons(ctx)
    sc.sash(ctx, "gold", tail=True)
    _cuffs(ctx, "gem_red", start=0.72, flare=1.36)


def mirren_pyro(ctx):
    """Mirren: Scrap-Winds pyrotechnician — wild flame-swept copper pompadour, blast-goggles on forehead, heat-shielded leather blast-vest, glowing ember-furnace backpack, copper pauldrons & bomb bandolier."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_wild(ctx)
    sc.goggles_up(ctx, "ember")
    sc.short_jacket(ctx, "leather_dark", "rust")
    sc.pauldrons(ctx, "rust", False, "brass")
    sc.bandolier(ctx, "ember")
    with ctx.mb.bound_to("chest"):
        # Ember-furnace tank on back
        ctx.mb.tube((0, 0.23 * g * s, 1.06 * s), (0, 0.23 * g * s, 1.34 * s), 0.13 * s, 0.12 * s, sides=8 if hq else 4, color="iron")
        ctx.mb.sphere((0, 0.26 * g * s, 1.2 * s), 0.075 * s, 6 if hq else 4, 3, "ember", smooth=False)
    _cuffs(ctx, "leather_dark", start=0.58, flare=1.3)
    sc._boot_cuffs(ctx, "rust_dark", flare=1.2)


# ---- 13. Odessa ---------------------------------------------------------------------------------

def odessa_machinist(ctx):
    """Odessa: Scrap-Winds chief machinist — loose shoulder-length grey hair under knotted crimson mechanic's headband, magnifying brass visor-goggles, heavy sleeveless boiler overalls & liftstone core gauge."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_long(ctx, 0.3)
    _full_bandana(ctx, "gem_red", tails=True)
    sc.goggles_up(ctx, "liftstone")
    sc.apron(ctx, "cloth_blue")
    sc.tool_harness(ctx)
    sc.tool_belt(ctx)
    with ctx.mb.bound_to("chest"):
        # Brass pressure gauge cylinder on back
        ctx.mb.tube((0, 0.22 * g * s, 1.04 * s), (0, 0.22 * g * s, 1.32 * s), 0.11 * s, 0.11 * s, sides=8 if hq else 4, color="brass")
        ctx.mb.sphere((0, 0.22 * g * s, 1.33 * s), 0.06 * s, 6 if hq else 4, 3, "liftstone", smooth=False)
    _cuffs(ctx, "leather", start=0.62, flare=1.22)


def odessa_matron(ctx):
    """Odessa: Azure sanctuary matron — coiled braided crown-updo under crisp white apothecary wimple cap, deep-azure collared healer's cloak with gold trim, embroidered white apron & silver hip lantern."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    with ctx.mb.bound_to("head"):
        # Crisp white apothecary wimple / nurse veil framing head
        ctx.mb.sphere(_at(ctx, 0, 0.06, 0.06), (0.23 * s, 0.225 * s, 0.23 * s), ctx.q["head_s"], 4 if hq else 3, "cloth_white", smooth=ctx.hq)
        ctx.mb.plate([_at(ctx, -0.18, -0.05, 0.12), _at(ctx, 0.18, -0.05, 0.12), _at(ctx, 0.2, 0.15, -0.18), _at(ctx, -0.2, 0.15, -0.18)], 0.02 * s, "cloth_white")
    sc.long_coat(ctx, "faction_a", "cloth_white", tail_len=0.28)
    sc.cape(ctx, "faction_a", length=0.45, lining="cloth_white")
    sc.apron(ctx, "cloth_white")
    with ctx.mb.bound_to("hips"):
        ctx.mb.sphere((0.25 * w * s, -0.05 * s, 0.78 * s), 0.05 * s, 6 if hq else 4, 3, "silver", smooth=False)
        ctx.mb.sphere((0.25 * w * s, -0.07 * s, 0.78 * s), 0.03 * s, 5 if hq else 4, 3, "lamp", smooth=False)


# ---- 14. Tobin ----------------------------------------------------------------------------------

def tobin_navigator(ctx):
    """Tobin: Azure star-navigator — hat off, windswept silver hair & neat swept beard, brass folding monocle, midnight-blue astronomer's velvet coat, star-lined half-cape, astrolabe & chart quiver."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_wild(ctx)
    sc.beard_full(ctx, 0.26)
    _monocle(ctx, side=1, frame="gold", lens="liftstone")
    sc.long_coat(ctx, "navy", "cloth_white", tail_len=0.3)
    sc.cape(ctx, "navy", length=0.42, lining="gold")
    sc.navigator_case(ctx)
    with ctx.mb.bound_to("chest"):
        # Golden astrolabe medallion on chest
        ctx.mb.sphere((0, -0.195 * g * s, 1.2 * s), (0.048 * s, 0.02 * s, 0.048 * s), 6 if hq else 4, 3, "gold", smooth=False)
        # Rolled chart quiver on back
        ctx.mb.tube((-0.14 * s, 0.2 * g * s, 1.38 * s), (0.14 * s, 0.2 * g * s, 1.02 * s), 0.042 * s, 0.038 * s, sides=6 if hq else 4, color="leather")
        ctx.mb.sphere((-0.15 * s, 0.2 * g * s, 1.4 * s), 0.036 * s, 5 if hq else 4, 3, "parchment", smooth=False)
    _cuffs(ctx, "gold", start=0.74, flare=1.35)


def tobin_castaway(ctx):
    """Tobin: Scrap-Winds marooned castaway — knotted weathered bandana, massive wild sea-salt beard, tattered sleeveless canvas-and-rope deck vest over bare arms, thick anchor-rope bandolier & sash."""
    sc = _sc()
    s, w, g, hq = ctx.s, ctx.w, ctx.g, ctx.hq
    sc.hair_cap(ctx)
    _full_bandana(ctx, "rust", tails=True)
    sc.beard_full(ctx, 0.42)
    sc.moustache(ctx)
    # Sleeveless tattered vest over bare skin
    sc._v_neck(ctx, sc._BASE_CHEST, ctx.hero.skin, depth=1.18)
    with ctx.mb.bound_to("chest"):
        ctx.mb.loft(sc._open_shell(ctx, [(0.25, 0.18, 1.07), (0.31, 0.185, 1.28), (0.16, 0.115, 1.37)], 30), "canvas_dark", smooth=False)
        ctx.mb.tube((-0.24 * w * s, -0.14 * g * s, 1.32 * s), (0.22 * w * s, -0.19 * g * s, 1.06 * s), 0.044 * s, sides=6 if hq else 4, color="rope")
    sc.sash(ctx, "rust", tail=True)
    _boot_cuffs_wrap(ctx, "rope", "leather_dark")


# ---- registration -------------------------------------------------------------------------------

STYLE_FEATURES = {
    fn.__name__: fn
    for fn in (
        rook_armada, rook_foundry,
        lyra_tempest, lyra_starweaver,
        sable_masquerade, sable_ronin,
        thorne_alchemist, thorne_archmage,
        morrow_corsair, morrow_admiral,
        brill_whaler, brill_deck_boss,
        hask_ironclad, hask_privateer,
        wren_plague_doc, wren_gentleman,
        ivo_aether_mage, ivo_coil_runner, chad_vampire,
        roxanne_valkyrie, roxanne_syndicate,
        may_centurion, may_rebel,
        mirren_bombardier, mirren_pyro,
        odessa_machinist, odessa_matron,
        tobin_navigator, tobin_castaway,
    )
}


def register(features, cast, extra_clips, *, ROOK_CLIPS, LYRA_CLIPS, SABLE_CLIPS, IVO_CLIPS, MORROW_CLIPS, ROXANNE_CLIPS):
    sc = _sc()
    Hero = sc.Hero
    features.update(STYLE_FEATURES)

    cast.update({
        # 1. Rook
        "RookArmada": Hero(skin="skin_dark", hair="hair_black", top="navy", legs="enamel", boots="leather_dark", belt="leather_dark", sleeve="navy", forearm="navy", glove="enamel", scale=1.12, width=1.32, girth=1.28, arm_bulk=1.3, leg_bulk=1.2, iris="eye_dark", features=[("rook_armada",)]),
        "RookFoundry": Hero(skin="skin_dark", hair="hair_black", top="skin_dark", legs="cloth_brown", boots="iron", belt="iron", sleeve="skin_dark", forearm="skin_dark", scale=1.12, width=1.32, girth=1.28, arm_bulk=1.3, leg_bulk=1.2, iris="eye_dark", features=[("rook_foundry",)]),
        # 2. Lyra
        "LyraTempest": Hero(skin="skin_mid", hair="hair_brown", top="cloth_white", legs="navy", boots="leather_dark", belt="leather_dark", sleeve="navy", forearm="navy", glove="leather_dark", width=0.86, girth=0.82, iris="amber", brow=1, features=[("lyra_tempest",)]),
        "LyraStarweaver": Hero(skin="skin_mid", hair="hair_brown", top="cloth_black", legs="cloth_black", boots="cloth_black", belt="gold", sleeve="faction_a", forearm="faction_a", glove="cloth_black", width=0.86, girth=0.82, iris="amber", brow=1, features=[("lyra_starweaver",)]),
        # 3. Sable
        "SableMasquerade": Hero(skin="skin_light", hair="hair_black", top="velvet", legs="cloth_black", boots="leather_dark", belt="gold", sleeve="velvet", forearm="velvet", glove="cloth_black", scale=0.97, width=0.76, girth=0.8, arm_bulk=0.82, leg_bulk=0.88, brow=0, iris="silver", features=[("sable_masquerade",)]),
        "SableRonin": Hero(mouth=False, skin="skin_light", hair="hair_black", top="cloth_black", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="cloth_black", forearm="cloth_black", glove="cloth_black", scale=0.97, width=0.76, girth=0.8, arm_bulk=0.82, leg_bulk=0.88, brow=1, iris="silver", features=[("sable_ronin",)]),
        # 4. Thorne
        "ThorneAlchemist": Hero(mouth=False, skin="enamel", hair="hair_gray", brow_color="hair_black", top="leather_dark", legs="cloth_black", boots="leather", belt="leather_dark", sleeve="leather_dark", forearm="leather_dark", glove="leather_dark", scale=1.06, brow=2, iris="faction_b", sclera="abyss", features=[("thorne_alchemist",)]),
        "ThorneArchmage": Hero(skin="enamel", hair="hair_white", brow_color="hair_black", top="abyss", legs="abyss", boots="cloth_black", belt="plasma", sleeve="abyss", forearm="abyss", glove="cloth_black", scale=1.06, brow=2, iris="plasma", sclera="abyss", features=[("thorne_archmage",)]),
        # 5. Morrow
        "MorrowCorsair": Hero(skin="skin_mid", hair="hair_black", top="cloth_white", legs="cloth_black", boots="leather_dark", belt="gem_red", sleeve="cloth_white", forearm="cloth_white", glove="leather_dark", scale=1.05, width=0.88, girth=0.84, brow=0, iris="eye_dark", features=[("morrow_corsair",)]),
        "MorrowAdmiral": Hero(skin="skin_mid", hair="hair_black", top="navy", legs="enamel", boots="leather_dark", belt="gem_red", sleeve="enamel", forearm="enamel", glove="enamel", scale=1.05, width=0.88, girth=0.84, brow=1, iris="eye_dark", features=[("morrow_admiral",)]),
        # 6. Brill
        "BrillWhaler": Hero(skin="skin_light", hair="hair_gray", top="amber", legs="cloth_black", boots="amber", belt="leather_dark", sleeve="navy", forearm="navy", scale=0.95, width=1.3, girth=1.38, arm_bulk=1.25, leg_bulk=1.25, brow=1, iris="eye_dark", features=[("brill_whaler",)]),
        "BrillDeckBoss": Hero(skin="skin_light", hair="hair_gray", top="cloth_white", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="cloth_white", forearm="skin_light", scale=0.95, width=1.3, girth=1.38, arm_bulk=1.25, leg_bulk=1.25, brow=1, iris="eye_dark", features=[("brill_deck_boss",)]),
        # 7. Hask
        "HaskIronclad": Hero(skin="skin_mid", hair="rock_dark", top="iron", legs="cloth_black", boots="iron", belt="iron", sleeve="skin_mid", forearm="iron_light", scale=1.06, width=1.22, girth=1.12, arm_bulk=1.35, leg_bulk=1.12, brow=2, iris="steel", blind_eye=1, features=[("hask_ironclad",)]),
        "HaskPrivateer": Hero(skin="skin_mid", hair="rock_dark", top="leather_dark", legs="cloth_black", boots="leather_dark", belt="gem_red", sleeve="skin_mid", forearm="skin_mid", glove="leather_dark", scale=1.06, width=1.22, girth=1.12, arm_bulk=1.35, leg_bulk=1.12, brow=2, iris="steel", blind_eye=1, features=[("hask_privateer",)]),
        # 8. Wren
        "WrenPlagueDoc": Hero(mouth=False, skin="skin_light", hair="hair_black", top="cloth_black", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="leather_dark", forearm="leather_dark", glove="leather_dark", scale=1.1, width=0.86, girth=0.76, arm_bulk=0.72, leg_bulk=0.85, brow=0, iris="eye_dark", blind_eye=1, features=[("wren_plague_doc",)]),
        "WrenGentleman": Hero(skin="skin_light", hair="hair_gray", top="cloth_white", legs="cloth_black", boots="cloth_black", belt="gold", sleeve="faction_a", forearm="faction_a", glove="enamel", scale=1.1, width=0.86, girth=0.76, arm_bulk=0.72, leg_bulk=0.85, brow=0, iris="eye_dark", blind_eye=1, features=[("wren_gentleman",)]),
        # 9. Ivo
        "IvoAetherMage": Hero(skin="skin_light", hair="hair_black", top="cloth_white", legs="navy", boots="leather_dark", belt="gold", sleeve="faction_a", forearm="faction_a", glove="leather_dark", scale=0.92, width=0.82, girth=0.78, arm_bulk=0.85, leg_bulk=1.12, brow=-1, iris="wind", eye_scale=1.45, singed_brow=-1, features=[("ivo_aether_mage",)]),
        "IvoCoilRunner": Hero(skin="skin_light", hair="hair_black", top="canvas", legs="cloth_brown", boots="rust", belt="leather_dark", sleeve="leather", forearm="leather", glove="rust", scale=0.92, width=0.82, girth=0.78, arm_bulk=0.85, leg_bulk=1.12, brow=-1, iris="wind", eye_scale=1.45, singed_brow=-1, features=[("ivo_coil_runner",)]),
        "Chad": Hero(skin="skin_light", hair="hair_brown", brow_color="hair_black", top="cloth_black", legs="cloth_black", boots="leather_dark", belt="silver", sleeve="cloth_black", forearm="cloth_black", glove="leather_dark", scale=1.04, width=1.02, girth=0.96, arm_bulk=1.06, leg_bulk=1.04, brow=1, iris="ember", eye_scale=1.08, features=[("chad_vampire",)]),
        # 10. Roxanne
        "RoxanneValkyrie": Hero(skin="skin_light", hair="hair_blond", iris="amber", top="enamel", legs="cloth_white", boots="gold", belt="gold", sleeve="enamel", forearm="gold", glove="enamel", width=0.92, girth=0.88, brow=1, features=[("roxanne_valkyrie",)]),
        "RoxanneSyndicate": Hero(skin="skin_light", hair="faction_b", iris="liftstone", top="cloth_black", legs="cloth_black", boots="cloth_black", belt="plasma", sleeve="cloth_black", forearm="cloth_black", glove="cloth_black", width=0.92, girth=0.88, brow=1, features=[("roxanne_syndicate",)]),
        # 11. May
        "MayCenturion": Hero(skin="skin_light", hair="hair_black", iris="amber", top="gold", legs="cloth_white", boots="gold", belt="gem_red", sleeve="gold", forearm="gold", glove="enamel", width=0.92, girth=0.88, arm_bulk=0.95, brow=1, features=[("may_centurion",)]),
        "MayRebel": Hero(skin="skin_light", hair="hair_black", iris="amber", top="cloth_white", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="gem_red", forearm="gem_red", glove="leather_dark", width=0.92, girth=0.88, arm_bulk=0.95, brow=1, features=[("may_rebel",)]),
        # 12. Mirren
        "MirrenBombardier": Hero(skin="skin_light", hair="hair_red", iris="grass", top="gem_red", legs="enamel", boots="leather_dark", belt="gold", sleeve="navy", forearm="navy", glove="enamel", scale=0.98, width=1.1, girth=1.12, arm_bulk=1.2, leg_bulk=1.2, features=[("mirren_bombardier",)]),
        "MirrenPyro": Hero(skin="skin_light", hair="hair_red", iris="grass", top="rust", legs="cloth_black", boots="rust_dark", belt="leather_dark", sleeve="leather_dark", forearm="leather_dark", glove="leather_dark", scale=0.98, width=1.1, girth=1.12, arm_bulk=1.2, leg_bulk=1.2, features=[("mirren_pyro",)]),
        # 13. Odessa
        "OdessaMachinist": Hero(skin="skin_dark", hair="hair_gray", brow_color="hair_gray", iris="leather", top="canvas", legs="cloth_blue", boots="leather_dark", belt="leather_dark", sleeve="canvas", forearm="skin_dark", scale=1.0, width=1.12, girth=1.14, arm_bulk=1.05, leg_bulk=1.15, brow=-1, features=[("odessa_machinist",)]),
        "OdessaMatron": Hero(skin="skin_dark", hair="hair_gray", brow_color="hair_gray", iris="leather", top="cloth_white", legs="faction_a", boots="leather_dark", belt="silver", sleeve="faction_a", forearm="cloth_white", scale=1.0, width=1.12, girth=1.14, arm_bulk=1.05, leg_bulk=1.15, brow=-1, features=[("odessa_matron",)]),
        # 14. Tobin
        "TobinNavigator": Hero(skin="skin_mid", hair="hair_white", iris="steel", top="cloth_white", legs="navy", boots="leather_dark", belt="gold", sleeve="navy", forearm="navy", scale=1.08, width=0.95, girth=0.9, arm_bulk=0.9, leg_bulk=0.95, brow=-1, features=[("tobin_navigator",)]),
        "TobinCastaway": Hero(skin="skin_mid", hair="hair_gray", iris="steel", top="canvas_dark", legs="cloth_brown", boots="rope", belt="rope", sleeve="skin_mid", forearm="skin_mid", scale=1.08, width=0.95, girth=0.9, arm_bulk=0.9, leg_bulk=0.95, brow=-1, features=[("tobin_castaway",)]),
    })

    extra_clips["RookArmada"] = ROOK_CLIPS
    extra_clips["RookFoundry"] = ROOK_CLIPS
    extra_clips["LyraTempest"] = LYRA_CLIPS
    extra_clips["LyraStarweaver"] = LYRA_CLIPS
    extra_clips["SableMasquerade"] = SABLE_CLIPS
    extra_clips["SableRonin"] = SABLE_CLIPS
    extra_clips["IvoAetherMage"] = IVO_CLIPS
    extra_clips["IvoCoilRunner"] = IVO_CLIPS
    extra_clips["Chad"] = IVO_CLIPS
    extra_clips["MorrowCorsair"] = MORROW_CLIPS
    extra_clips["MorrowAdmiral"] = MORROW_CLIPS
    extra_clips["RoxanneValkyrie"] = ROXANNE_CLIPS
    extra_clips["RoxanneSyndicate"] = ROXANNE_CLIPS
    extra_clips["MayCenturion"] = ROXANNE_CLIPS
    extra_clips["MayRebel"] = ROXANNE_CLIPS
