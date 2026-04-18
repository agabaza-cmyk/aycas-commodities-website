#!/usr/bin/env python3
"""
Generate site imagery via kie.ai nano-banana (Gemini 2.5 Flash Image).

Reads KIE_API_KEY from .env (or environment). Creates tasks in parallel,
polls each until done, downloads JPEGs into assets/img/.

Re-run any time to regenerate. Existing files are overwritten.
Pass --only <slot> to regenerate a single image.

AYCAS Commodities — African earth palette (terracotta / ochre / sand /
charcoal), institutional-register commodities trading firm based in Harare.
"""
import os, sys, json, time, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "img"
ENV_FILE = ROOT / ".env"

# Shared brand / composition guidance appended to every prompt.
AYCAS = (
    " Photographic editorial quality. Warm African earth palette — terracotta reds, "
    "ochre golds, sand beige, charcoal shadows naturally present in the scene. "
    "Grounded institutional register, not lifestyle marketing, not stock photo. "
    "No people with prominent faces (three-quarter from behind is acceptable when a "
    "person is shown). No visible text, no logos, no watermarks, no signage, no labels "
    "with legible writing. Natural composition, documentary precision, generous negative "
    "space suited for website hero typography overlay. Warm Highveld golden-hour light "
    "or soft overhead daylight unless otherwise specified. Zimbabwean / Southern African "
    "context where appropriate. Shallow depth of field for macro shots; wide cinematic "
    "framing for landscapes."
)

# Heroes are 16:9 (wide cinematic for page-hero backgrounds with dark overlay).
# Supporting/detail images are 3:2 (more compact, sit well next to specs panels).
JOBS = [
    # =========================================================================
    # HERO IMAGES — one per page (12)
    # =========================================================================

    {"slot": "hero-home", "size": "16:9", "prompt":
        "Wide cinematic panoramic view at golden hour: a long dusty tarmac road runs "
        "dead-ahead through the Zimbabwean Highveld savanna toward distant blue-grey "
        "mountains on the horizon. Scattered msasa and acacia trees in the mid-ground. "
        "Tall ochre grasses catch the low warm afternoon light. A single articulated "
        "road-train truck with canvas-covered trailer moves along the road, seen from "
        "far behind with a trailing dust plume rising. Terracotta-red earth verges. "
        "Calm, epic, unpeopled — the quiet movement of commodities across Southern "
        "Africa." + AYCAS},

    {"slot": "hero-commodities", "size": "16:9", "prompt":
        "Wide cinematic industrial still-life on a raw polished concrete warehouse "
        "floor at dawn: three neatly arranged jute sacks of amber grain (slightly "
        "open showing kernels), two rough charcoal-metallic chunks of chrome ore, a "
        "sealed terracotta-red 200 kg industrial drum, a small sealed 25 kg kraft "
        "multi-wall bag of pale cream milk powder, a glass jar of deep red tomato "
        "paste. Items spaced with generous negative space, museum-like documentary "
        "composition. Soft overhead warehouse window light, deep shadows. Calm and "
        "precise, warm earth palette dominates." + AYCAS},

    {"slot": "hero-grains", "size": "16:9", "prompt":
        "Wide cinematic view of a vast golden maize field at harvest time in the "
        "Zimbabwean Highveld. Ripe dry-standing maize stretches to the horizon under "
        "a warm late-afternoon sun. A distant silhouette of a cluster of concrete "
        "grain silos breaks the tree-line. Ochre-yellow crop dominates, long warm "
        "shadows, fine dust haze catches golden light. No people. Epic agricultural "
        "scale, quiet and institutional." + AYCAS},

    {"slot": "hero-dairy", "size": "16:9", "prompt":
        "Wide cinematic interior: rows of neatly-stacked 25 kg kraft-paper multi-wall "
        "bags of milk powder on industrial wooden pallets in a clean commercial "
        "warehouse, stretching into soft focus depth. Stainless-steel processing "
        "equipment partially visible in the background. Warm diffused overhead light "
        "from high windows casting soft pools on the polished concrete floor. Pale "
        "cream bags, charcoal floor, warm beige walls. Institutional, quiet, orderly." + AYCAS},

    {"slot": "hero-specialty-agri", "size": "16:9", "prompt":
        "Wide cinematic overhead still-life on a weathered wooden farm market table: "
        "a neat row of natural baobab fruit pods (dry beige fibrous husks, some split "
        "open showing pale chalky interior pulp), a small wooden crate of ripe "
        "tomatoes and fresh oranges, an open cloth sack of cane sugar crystals, a "
        "stoneware jar with a wooden lid. Soft diffused overhead daylight. Warm "
        "earth palette, clean documentary still-life composition, generous negative "
        "space around the subjects." + AYCAS},

    {"slot": "hero-tungsten", "size": "16:9", "prompt":
        "Wide cinematic macro texture shot of heavy scheelite and wolframite tungsten "
        "concentrate — pale cool grey-brown crystalline chunks alongside darker "
        "metallic adamantine-lustred wolframite pieces, spilled on dark textured "
        "industrial paper on a warehouse workbench. Shallow depth of field, one end "
        "in crisp focus. Soft overhead warehouse light catches the metallic crystal "
        "facets and mineral edges. Terracotta dust and charcoal shadows. Documentary "
        "mineral-specimen precision, quiet industrial register." + AYCAS},

    {"slot": "hero-chrome", "size": "16:9", "prompt":
        "Wide cinematic panoramic view of the Great Dyke ridge line in Zimbabwe at "
        "golden hour. A long north-south-running stratified ultramafic escarpment "
        "of dark dolerite and chromite-bearing rock outcrops rises above green-brown "
        "Highveld savanna grassland. Low scrub and scattered acacia trees in the "
        "foreground catching warm Highveld afternoon light. Deep blue sky with "
        "dust haze at the horizon, long raking shadows across the ridge flanks. "
        "Epic geological scale, unpeopled. Authentic Southern African highveld "
        "geology, not fantasy landscape." + AYCAS},

    {"slot": "hero-enquiry", "size": "16:9", "prompt":
        "Cinematic overhead flat-lay on a raw concrete warehouse floor: a row of "
        "small clear glass specimen jars containing diverse commodity samples — "
        "golden grain kernels, crystalline refined sugar, small chrome ore fragments, "
        "dried baobab pulp, a scoop of pale milk powder, dark tungsten concentrate, "
        "dried tobacco leaf fragments, green-brown lithium spodumene chunks. Each jar "
        "with a small cream paper tag (no legible text). Soft overhead daylight, "
        "shallow shadows, institutional museum-like documentary register." + AYCAS},

    {"slot": "hero-services", "size": "16:9", "prompt":
        "Wide cinematic shot of a large articulated truck being loaded at a grain "
        "silo complex at dawn. A bulk grain chute pours ochre-golden grain into the "
        "open trailer. A technician in three-quarter view from behind (no face) stands "
        "to the side checking paperwork on a clipboard. Terracotta-dusty ground, "
        "weathered ochre-concrete silos rising on the left, warm early-morning sun "
        "catching fine grain dust in the air. Calm, organised industrial operation. "
        "Documentary editorial quality, no visible signage or branding." + AYCAS},

    {"slot": "hero-about", "size": "16:9", "prompt":
        "Wide cinematic elevated view across the Harare skyline at golden hour. "
        "Mid-rise commercial buildings in warm cream and terracotta-brick tones "
        "against the Zimbabwean Highveld backdrop. Distant blue-grey hills on the "
        "horizon. Mature jacaranda canopy breaking up the cityscape in the mid-ground. "
        "Calm, institutional, warm afternoon Highveld light. Urban but grounded. "
        "No visible signage or text, no prominent faces." + AYCAS},

    {"slot": "hero-compliance", "size": "16:9", "prompt":
        "Cinematic overhead shot of an organised dark walnut desk in a quiet Harare "
        "office at soft morning light: a neatly-ordered stack of document folders, "
        "an open ledger-style hard-cover notebook (blank pages, no legible text), "
        "a fountain pen resting diagonally, a small stack of cream A4 signed certificates "
        "visible at one edge (no legible text), a brass-and-ink pot with a leather "
        "blotter corner. Warm natural light from a side window, deep rich shadows. "
        "Institutional, precise, understated. Quiet professional register." + AYCAS},

    {"slot": "hero-contact", "size": "16:9", "prompt":
        "Wide cinematic view of a quiet Harare commercial street at golden hour: "
        "warm cream and terracotta-brick facades of mid-rise buildings on Sam Nujoma "
        "Street or similar. Mature jacaranda trees dropping purple petals on the "
        "pavement, soft warm late-afternoon light raking across the street. A few "
        "distant figures in soft focus (no faces visible). Calm professional urban "
        "register, unforced, uncluttered." + AYCAS},

    # =========================================================================
    # SUPPORTING IMAGES — commodity detail panels (10)
    # =========================================================================

    {"slot": "grains-maize", "size": "3:2", "prompt":
        "Extreme close-up macro shot of golden-yellow maize kernels freshly harvested, "
        "spilled generously on rough hessian sack fabric. Each kernel crisply defined "
        "with natural colour variation from pale amber to deep gold. Warm natural "
        "daylight from the side. Shallow depth of field, documentary precision. "
        "Commodity-grade agricultural product photography, no props." + AYCAS},

    {"slot": "grains-silo", "size": "3:2", "prompt":
        "Three-quarter view of a tall cluster of weathered cylindrical concrete grain "
        "silos at a Zimbabwean agricultural depot, rising above terracotta-red earth "
        "at the base. Rusted steel walkways and external stairs visible, ochre "
        "weathered concrete surfaces. Deep blue early-morning sky behind. No people. "
        "Industrial agricultural infrastructure, calm and epic, documentary quality." + AYCAS},

    {"slot": "dairy-powder", "size": "3:2", "prompt":
        "Macro close-up editorial product shot: a stainless-steel scoop pouring fine "
        "pale cream Full Cream Milk Powder into a small sample dish on a clean "
        "industrial white workbench. Fine airborne powder particles catch the soft "
        "overhead daylight. Crisp micro-texture of the powder visible. Shallow depth "
        "of field, clean minimalist food-ingredient documentary register." + AYCAS},

    {"slot": "dairy-processing", "size": "3:2", "prompt":
        "Interior wide-angle shot of a clean South African commercial dairy plant: "
        "gleaming stainless steel processing vats, pipes and valves, immaculately "
        "maintained. Warm diffused light from high industrial windows casts soft "
        "reflections on the stainless surfaces. Pools of condensation on the polished "
        "concrete floor. No people visible. Documentary industrial quality, quiet "
        "institutional register." + AYCAS},

    {"slot": "specialty-paste", "size": "3:2", "prompt":
        "Macro editorial shot of deep scarlet-red industrial-grade tomato paste "
        "pouring thick and glossy from the nozzle of a stainless aseptic drum into "
        "a stainless steel receiving vessel below. Rich red against cool steel-grey. "
        "Overhead warehouse lighting catches the paste's glossy surface. Documentary "
        "food-processing editorial, no visible labels or text." + AYCAS},

    {"slot": "specialty-baobab", "size": "3:2", "prompt":
        "A mature lone baobab tree at golden hour on a Zimbabwean savanna. Massive "
        "smooth terracotta-grey swollen trunk, bare gnarled branches reaching up "
        "like roots in the sky. Low ochre scrub grass and scattered termite mound at "
        "its base. Warm late-afternoon Highveld sun catching the characteristic bark "
        "texture, long shadow stretching across the grass. Ancient, unpeopled, "
        "iconic Southern African landscape." + AYCAS},

    {"slot": "tungsten-scheelite", "size": "3:2", "prompt":
        "Macro close-up mineral specimen photography: heavy scheelite concentrate "
        "chunks — pale grey-brown crystalline lumps with amber inclusions — arranged "
        "on a raw charcoal slate surface beside a small white porcelain evaporating "
        "dish containing a finer crushed sample. Soft directional daylight catches "
        "the fluorescent-adjacent mineral colour and crystal facets. Museum-grade "
        "mineral specimen register, documentary precision." + AYCAS},

    {"slot": "tungsten-wolframite", "size": "3:2", "prompt":
        "Museum-style mineral specimen photograph: several small dark chunks of "
        "natural mineral rock on a raw grey slate tile. Each chunk roughly 3 cm "
        "across, deep brown-black colour with a subtle metallic sheen on weathered "
        "crystal facets. Soft directional daylight from one side creates gentle "
        "highlights. Clean simple composition, shallow depth of field, plain dark "
        "slate background. Calm documentary geology-study aesthetic." + AYCAS},

    {"slot": "chrome-greatdyke", "size": "3:2", "prompt":
        "Aerial three-quarter panoramic view of a section of the Great Dyke in "
        "Zimbabwe: a stratified ultramafic ridge of dark dolerite rock and chromite "
        "bands running through green-brown Highveld savanna grassland. A small "
        "terracotta-earth exposed mining pit visible in mid-ground as a minor detail. "
        "Deep blue sky with fine dust haze, warm late-afternoon light raking across "
        "the landscape. Epic geological scale, documentary register." + AYCAS},

    {"slot": "chrome-ore", "size": "3:2", "prompt":
        "Macro close-up: rough freshly-mined chunks of chrome ore spilled on coarse "
        "hessian sack fabric — heavy lustrous charcoal-metallic chromite crystals "
        "embedded in terracotta-reddish serpentine gangue rock. Individual chunks "
        "5–15 cm across, natural undressed surfaces. Soft overhead warehouse light "
        "catches the metallic chromite facets. Textured industrial material, "
        "documentary mineral photography." + AYCAS},
]


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("KIE_API_KEY")
    if not key:
        sys.exit("KIE_API_KEY missing. Put it in .env or export it.")
    return key


def http(method, url, headers=None, body=None, timeout=90):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-X", method, url]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", json.dumps(body)]
    out = subprocess.check_output(cmd)
    return json.loads(out.decode())


def download_binary(url, dest, timeout=120):
    subprocess.check_call(["curl", "-sS", "--max-time", str(timeout), "-o", str(dest), url])


def create_task(key, prompt, size):
    return http(
        "POST",
        "https://api.kie.ai/api/v1/jobs/createTask",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        body={
            "model": "google/nano-banana",
            "input": {
                "prompt": prompt,
                "image_size": size,
                "output_format": "jpeg",
            },
        },
    )


def poll_task(key, task_id, max_wait=240):
    start = time.time()
    while time.time() - start < max_wait:
        r = http(
            "GET",
            f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}",
            headers={"Authorization": f"Bearer {key}"},
        )
        state = r.get("data", {}).get("state")
        if state == "success":
            result = json.loads(r["data"]["resultJson"])
            return result["resultUrls"][0]
        if state in ("fail", "failed", "error"):
            raise RuntimeError(f"task {task_id} failed: {r}")
        time.sleep(2)
    raise TimeoutError(f"task {task_id} did not complete within {max_wait}s")


def main():
    key = load_env()
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    jobs = [j for j in JOBS if only is None or j["slot"] == only]
    if not jobs:
        sys.exit(f"no job matched slot '{only}'")

    # Create tasks (small stagger to avoid rate limits)
    print(f"Creating {len(jobs)} tasks...")
    for job in jobs:
        r = create_task(key, job["prompt"], job["size"])
        job["task_id"] = r["data"]["taskId"]
        print(f"  {job['slot']:32s} → {job['task_id']}")
        time.sleep(0.3)

    # Poll + download each
    print("\nPolling + downloading...")
    ok = fail = 0
    for job in jobs:
        try:
            url = poll_task(key, job["task_id"])
            dest = IMG_DIR / f"{job['slot']}.jpg"
            download_binary(url, dest)
            kb = dest.stat().st_size // 1024
            print(f"  {job['slot']:32s} ✓ {kb}KB")
            ok += 1
        except Exception as e:
            print(f"  {job['slot']:32s} ✗ {e}")
            fail += 1

    # Manifest for future regeneration
    manifest = {j["slot"]: {"prompt": j["prompt"], "size": j["size"]} for j in JOBS}
    (IMG_DIR / "prompts.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {ok} succeeded, {fail} failed. Images in {IMG_DIR}")


if __name__ == "__main__":
    main()
