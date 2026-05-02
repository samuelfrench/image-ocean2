"""Random prompt bank for image-ocean2.

Organized by category. Mostly fun, some serious, all PG.
Each prompt is a raw subject — style and quality modifiers are appended by generate.py.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    category: str
    subject: str


# -------------------------- WHIMSICAL / FUN --------------------------
# Heaviest bucket — "mostly fun".
WHIMSICAL = [
    "a raccoon in a three-piece pinstripe suit reading a newspaper on a park bench",
    "an octopus working as a barista pulling espresso shots with all eight arms",
    "a grumpy cat wearing a tiny crown and royal robes on a velvet throne",
    "a corgi astronaut floating inside the International Space Station eating a treat",
    "a flock of origami birds flying out of an open book at sunset",
    "a hedgehog in a raincoat holding a tiny red umbrella in a puddle",
    "a polar bear DJ wearing headphones behind turntables made of ice",
    "a tiny mouse chef plating a microscopic gourmet meal on a thimble",
    "a capybara in a hot spring reading a philosophy book with steam rising",
    "a golden retriever lifeguard in sunglasses on a wooden tower at the beach",
    "a pair of otters holding hands floating on their backs in a crystal lake",
    "a panda bear construction worker in a hard hat reviewing blueprints",
    "a dignified owl professor in tweed jacket lecturing to a class of mice",
    "a family of ducks crossing a cobblestone street holding umbrellas in the rain",
    "a chubby hamster riding a skateboard down a marble staircase",
    "a sloth in a chef's hat slowly making a pancake at sunrise",
    "a pug in a tuxedo playing chess against a crow in a bowler hat",
    "a bear ranger drinking coffee from a massive thermos at a mountain lookout",
    "a frog wizard stirring a bubbling green potion in a mushroom-shaped hut",
    "a kitten detective in a trench coat examining paw prints with a magnifying glass",
    "a raccoon librarian shushing patrons from behind a tall oak desk",
    "a fox in a knitted sweater sipping cocoa by a fireplace with snow outside",
    "a herd of tiny elephants parading across a kitchen table past a sugar bowl",
    "a dachshund in a hot dog bun costume confidently walking down a red carpet",
    "a giant rabbit serving tea to miniature human guests in a garden",
    "an alpaca wearing round glasses and a bowtie giving a TED talk",
    "a penguin mail carrier delivering letters across an iceberg neighborhood",
    "a squirrel stockbroker shouting into a phone at a nut-themed trading floor",
    "a whale floating above the clouds with city lights far below",
    "a mouse family picnicking on a giant mushroom under fairy lights",
    "a walrus in a Hawaiian shirt lounging on a beach chair with sunglasses",
    "a golden retriever pizza chef twirling dough in a New York style pizzeria",
    "a cat wearing a beret painting a self-portrait in a sunlit Parisian studio",
    "a bear in a flannel shirt playing acoustic guitar by a campfire under stars",
    "a platypus wearing a snorkel and flippers giving a tour of a coral reef",
    "a tiny dragon curled up asleep on a stack of warm toast",
    "a rabbit in running shoes winning a marathon ahead of a confused turtle",
    "a chameleon painter with color-stained brushes standing in front of a mural",
    "a bunch of hedgehogs having a book club meeting with tiny teacups",
    "a robot vacuum leading a parade of cats around a living room",
    "a gentleman crab in a top hat offering a pearl on an ocean floor",
    "a kitten being knighted by a mouse king with a toothpick sword",
    "a sleepy koala typing at a laptop in a tiny eucalyptus-themed office",
    "a rubber duck in a sea captain's uniform commanding a bathtub fleet",
    "a french bulldog bodybuilder flexing in front of a mirror in a gym",
    "a cheerful snowman sipping hot chocolate by a cozy fireplace",
    "a wizard cat at a floating desk studying a glowing spellbook",
]

# -------------------------- NATURE / LANDSCAPE --------------------------
NATURE = [
    "a misty pine forest at dawn with golden sunbeams slicing through fog",
    "an alpine lake reflecting jagged snow-capped peaks under a clear sky",
    "a field of purple lupines sweeping toward a distant red barn",
    "a desert canyon at sunset with deep orange and violet striations",
    "a coastal lighthouse on a rocky cliff during a dramatic storm",
    "a waterfall cascading through a lush tropical rainforest",
    "a frozen waterfall in deep winter backlit by afternoon sun",
    "a tide pool teeming with anemones, starfish, and tiny crabs",
    "a field of sunflowers stretching to the horizon under a summer sky",
    "a quiet birch forest in autumn with yellow leaves carpeting the ground",
    "a bioluminescent bay at night with glowing waves on a sandy shore",
    "an aurora borealis dancing over a snow-covered valley with log cabin",
    "a sequoia grove with sun filtering through massive tree trunks",
    "a foggy Scottish moor with heather blooming in shades of purple",
    "a tranquil Japanese garden in spring with cherry blossoms raining down",
    "a flock of flamingos wading in shallow pink-tinted waters at dawn",
    "a humpback whale breaching off a rugged coastline at golden hour",
    "ocean waves crashing against black volcanic rocks under moody skies",
    "a herd of wild horses running across a Patagonian plain",
    "a mountain stream tumbling over moss-covered boulders in summer",
    "an old-growth redwood forest with ferns glowing in dappled light",
    "a rice terrace in Vietnam reflecting the afternoon sun in layers",
    "a clear night sky with the Milky Way over a desert arch formation",
    "a polar landscape with icebergs drifting under a soft pink sky",
]

# -------------------------- ARCHITECTURE --------------------------
ARCHITECTURE = [
    "a cozy Scandinavian cabin on stilts above a glacial lake at sunset",
    "a bustling night market in Tokyo with neon signs reflecting in puddles",
    "a Moroccan riad courtyard with intricate blue tilework and a citrus tree",
    "a medieval European clocktower overlooking a snow-dusted village square",
    "a modernist glass house perched on a seaside cliff at sunrise",
    "a winding cobblestone alley in Lisbon with pastel houses and laundry lines",
    "a Venice canal at dawn with gondolas moored against weathered facades",
    "an abandoned art deco theater being reclaimed by flowering vines",
    "a colorful favela hillside in Rio de Janeiro glowing at blue hour",
    "a high desert pueblo village at dusk with warm yellow window light",
    "a cozy English village pub with a thatched roof and hanging flower baskets",
    "a Parisian boulangerie storefront at dawn with fresh bread in the window",
    "a sweeping art nouveau staircase in a restored European mansion",
    "a floating fish market on wooden boats in a Thai river",
    "a futuristic eco-city with vertical forests on every skyscraper",
    "a quiet Kyoto alley lined with lanterns and wooden machiya houses",
    "an ivy-covered Oxford college quadrangle in late afternoon light",
    "a brutalist concrete library with dramatic geometric shadows",
    "a tiny bookshop with a spiral staircase and shelves reaching the ceiling",
    "a Moorish-influenced courtyard with a reflecting pool and columns",
]

# -------------------------- PORTRAITS --------------------------
# PG portraits — character studies, no celebrities, no kids in sensitive ways.
PORTRAITS = [
    "weathered face of an elderly fisherman in a yellow raincoat at a harbor",
    "a jazz trumpet player in a dim smoky club under a single amber spotlight",
    "a cheerful Italian grandmother rolling pasta on a flour-dusted wooden table",
    "a beekeeper in a veil surrounded by soft morning light in a lavender field",
    "a potter's hands shaping wet clay on a spinning wheel with deep focus",
    "a bookshop owner in a cardigan reading in a leather armchair",
    "a lighthouse keeper with a thick beard peering into the fog with a lantern",
    "a ballerina lacing pointe shoes in a sunlit practice studio",
    "a silver-haired botanist cataloging dried plants in a book-lined study",
    "a street musician playing violin on a rainy European cobblestone street",
    "a chef with flour on his apron laughing in a copper-pot-lined kitchen",
    "a farmer standing in a wheat field at golden hour holding his straw hat",
    "a watchmaker working on tiny gears under a jeweler's loupe",
    "a choir singer mid-note in stained-glass light streaming through a cathedral",
    "a cartographer surrounded by antique maps drawing by lamplight",
    "an astronaut looking out a spacecraft window at earthrise with quiet awe",
]

# -------------------------- SCI-FI --------------------------
SCI_FI = [
    "a friendly humanoid robot tending a rooftop vegetable garden in a future city",
    "a lone spacewalker tethered to a station with Jupiter filling the background",
    "a cat-eared astronaut discovering a glowing crystal on an alien moon",
    "a retro 1960s-style rocket launching from a jungle pad at dusk",
    "a dome colony on a Martian plain under a pale pink sky",
    "a crowded spaceport bazaar with aliens bartering strange goods",
    "a derelict ocean liner repurposed as a deep-space research vessel",
    "a cozy space diner orbiting a ringed gas giant with a neon OPEN sign",
    "a biopunk greenhouse habitat with luminous flowers and floating seeds",
    "a city built inside a hollowed-out asteroid with lights glittering in the rock",
    "a submarine exploring an alien ocean with bioluminescent jellyfish",
    "a traveler in a retro-futuristic suit walking a causeway between floating islands",
    "a cluster of observatories on a ridge under a double-sun sunset",
    "a food-delivery drone buzzing down a rainy cyberpunk alley with neon reflections",
    "a Dyson swarm sunrise viewed from a habitable moon's surface",
]

# -------------------------- FANTASY --------------------------
FANTASY = [
    "a miniature dragon curled protectively around a glowing lantern in a library",
    "a floating island city with waterfalls spilling off its edges into clouds",
    "a cozy hobbit-style burrow with a round door and a smoking chimney at dusk",
    "a forest path lit by hundreds of floating paper lanterns at twilight",
    "a friendly stone giant gently holding a village in the palm of his hand",
    "a wise turtle with a city on its back swimming through a starry sea",
    "a fairy ring of glowing mushrooms in a mossy forest at night",
    "a knight's helmet abandoned on a hill while deer graze nearby",
    "an ancient tree with doorways, windows, and tiny glowing lamps in its bark",
    "a phoenix rising from sun-warmed autumn leaves in an empty courtyard",
    "a cartographer mermaid spreading nautical charts across a coral table",
    "a cozy witch's cottage deep in a snowy pine wood with warm orange windows",
    "a crystal cave with shafts of colored light illuminating a sleeping baby dragon",
    "an enchanted marketplace in a forest with lanterns, spice stalls, and elves",
]

# -------------------------- FOOD / STILL LIFE --------------------------
FOOD = [
    "a rustic wooden table of warm sourdough, aged cheeses, grapes, and dark wine",
    "a slice of New York pizza with mozzarella pulling dramatically toward the camera",
    "an overhead flat lay of a colorful Buddha bowl with vivid vegetables",
    "a steaming bowl of ramen with a perfect egg, green onions, and chili oil",
    "a rustic apple pie cooling on a windowsill with cinnamon steam rising",
    "a croissant tower arranged in a sunny French patisserie window",
    "a matcha latte with latte art in a ceramic cup on a linen-covered table",
    "a bowl of fresh raspberries sparkling in morning sunlight on a blue cloth",
    "a plate of hand-rolled sushi at a minimalist wooden counter",
    "a cast iron skillet of shakshuka garnished with herbs and crumbled feta",
    "a still life of hand-thrown pottery, figs, pomegranates, and dried lavender",
    "a row of colorful macarons stacked in a pastel pyramid",
    "a steaming cup of black coffee next to a leather journal and fountain pen",
    "a smoky barbecue grill with glistening corn, skewers, and lemon wedges",
]

# -------------------------- ANIMALS (naturalistic) --------------------------
ANIMALS = [
    "a red fox peering through tall ferns in a misty morning forest",
    "a bald eagle soaring above a river canyon with wings fully extended",
    "a pod of dolphins racing alongside a wave at sunset",
    "a tabby kitten batting at dandelion seeds in a sunny meadow",
    "a horse galloping through shallow tide at an empty beach",
    "a tiny colorful tree frog clinging to a raindrop-beaded leaf",
    "a mother elephant and calf walking together on an African savanna",
    "a snow leopard hidden in rocky Himalayan terrain at golden hour",
    "a great white owl in mid-flight through a snow-covered forest",
    "a koi fish pond with lily pads and dappled sunlight on the water",
    "a macro close-up of a bumblebee dusted with pollen on a dahlia",
    "a herd of bison grazing at dawn in Yellowstone with steam rising",
    "a seahorse drifting past swaying sea grass in turquoise water",
    "a lion cub yawning while leaning against its mother's warm flank",
]

# -------------------------- VEHICLES / MACHINES --------------------------
VEHICLES = [
    "a vintage 1960s convertible driving along a cliffside coastal highway",
    "a polished steam locomotive emerging from a tunnel with a plume of smoke",
    "a hot air balloon festival at dawn with dozens of balloons rising",
    "a classic wooden sailboat cutting through blue water under full sails",
    "a custom vintage motorcycle parked in front of a neon-lit American diner",
    "a retro-futuristic camper van on a desert road with mountains behind",
    "a Zeppelin airship gliding above Art Deco skyscrapers in golden hour",
    "a weathered fishing trawler returning to harbor with seagulls overhead",
    "a restored 1950s pickup truck parked by a farmhouse with hay bales",
]

# -------------------------- ABSTRACT / ART --------------------------
ABSTRACT = [
    "a surreal clock melting over a tree branch in a desert at twilight",
    "an impossible staircase in the style of Escher with geometric harmony",
    "a cross-section cutaway of a cozy multi-level treehouse in watercolor",
    "a kaleidoscope of autumn leaves swirling in a gentle wind tunnel",
    "oil paint swirls in vivid blues and golds forming an abstract galaxy",
    "a library where the books are tiny houses with glowing windows",
    "a cello made of frozen water melting in a sunlit concert hall",
    "paper-craft diorama of a tiny mountain village in a matchbox",
    "an M.C. Escher-style garden with pathways folding into themselves",
]


ALL_CATEGORIES: dict[str, list[str]] = {
    "whimsical": WHIMSICAL,
    "nature": NATURE,
    "architecture": ARCHITECTURE,
    "portraits": PORTRAITS,
    "sci_fi": SCI_FI,
    "fantasy": FANTASY,
    "food": FOOD,
    "animals": ANIMALS,
    "vehicles": VEHICLES,
    "abstract": ABSTRACT,
}


# SDXL was trained on multiple aspect-ratio buckets (Podell et al., 2023). Picking the
# bucket size that matches the subject reliably produces stronger composition than always
# rendering at 1024×1024 — wide subjects get wide canvases, etc. All values below are
# real SDXL bucket sizes.
CATEGORY_RESOLUTIONS: dict[str, tuple[int, int]] = {
    "nature": (1344, 768),
    "architecture": (1344, 768),
    "vehicles": (1344, 768),
    "sci_fi": (1344, 768),
    "portraits": (832, 1216),
    "animals": (1152, 896),
    "whimsical": (1024, 1024),
    "fantasy": (1024, 1024),
    "food": (1024, 1024),
    "abstract": (1024, 1024),
}


def get_default_resolution(category: str) -> tuple[int, int]:
    """Return the SDXL bucket resolution that suits a category. Falls back to square."""
    return CATEGORY_RESOLUTIONS.get(category, (1024, 1024))


# Weights favor fun. Tuned so roughly 55% of random draws are whimsical/fantasy/sci-fi/abstract.
DEFAULT_WEIGHTS: dict[str, float] = {
    "whimsical": 3.0,
    "fantasy": 1.3,
    "sci_fi": 1.0,
    "abstract": 0.7,
    "animals": 1.4,
    "nature": 1.2,
    "architecture": 0.9,
    "portraits": 0.8,
    "food": 0.7,
    "vehicles": 0.6,
}


# Quality / style modifiers appended to every prompt for "super high quality" output.
QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra detailed, intricate detail, "
    "sharp focus, professional photography, cinematic lighting, "
    "dramatic composition, 8k, crisp, high dynamic range"
)

# Negative prompt — broad quality filter plus extra PG guard rails.
# The generator always includes these even when the user supplies their own subject.
NEGATIVE_PROMPT = (
    "low quality, worst quality, blurry, out of focus, jpeg artifacts, "
    "noisy, oversaturated, low contrast, poorly lit, "
    "deformed, disfigured, malformed, extra limbs, extra fingers, missing fingers, "
    "bad anatomy, bad proportions, mutated hands, fused fingers, long neck, "
    "watermark, signature, text, logo, frame, border, cropped, "
    "nsfw, nude, suggestive, gore, blood, violence, weapon, scary, horror, dark themes"
)


def list_categories() -> list[str]:
    return sorted(ALL_CATEGORIES.keys())


def get_random_prompt(
    category: str | None = None,
    rng: random.Random | None = None,
) -> Prompt:
    """Return a random Prompt. If `category` is None, pick one weighted by DEFAULT_WEIGHTS."""
    rng = rng or random.Random()
    if category is None:
        names = list(DEFAULT_WEIGHTS.keys())
        weights = [DEFAULT_WEIGHTS[n] for n in names]
        category = rng.choices(names, weights=weights, k=1)[0]
    if category not in ALL_CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Known: {', '.join(list_categories())}"
        )
    subject = rng.choice(ALL_CATEGORIES[category])
    return Prompt(category=category, subject=subject)


def decorate(subject: str) -> str:
    """Attach the shared quality/style suffix so SDXL leans into a high-quality render."""
    return f"{subject}, {QUALITY_SUFFIX}"


if __name__ == "__main__":
    # Quick smoke test: print one random prompt per category plus three unrestricted draws.
    rng = random.Random(0)
    for cat in list_categories():
        p = get_random_prompt(cat, rng)
        print(f"[{p.category}] {p.subject}")
    print("--- unrestricted ---")
    for _ in range(3):
        p = get_random_prompt(rng=rng)
        print(f"[{p.category}] {p.subject}")
