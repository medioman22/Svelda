import os
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from google import genai
from google.genai import types

# Load .env from _python/ (one level up from libs/)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ---------------------------------------------------------------------------
# Prompt constants
# All prompt dicts share the same schema:  { 'CATEGORY_NAME': [prompt, ...] }
# The first item in each list is the mosaic header instruction (where relevant).
# ---------------------------------------------------------------------------

NEUTRAL_WHITE_PROMPT = {
    'NEUTRAL_WHITE': [
        """Professional studio product photography. High-end e-commerce style.
MANDATE: Maintain the exact shape, dimensions, texture, and color of the product. Be true to the product. Make it look at its best. Center it in the image.
ENVIRONMENT: Place the product in a neutral environment, with a flat white background typical of product photography. Make the subject pop against the background, in a natural light.
LIGHTING: Apply professional 'three-point' diffused lighting to eliminate harsh shadows and make the background disappear in white, only leaving a soft shadow to the right of the object.
OUTPUT: Clean, sharp, 4K resolution, commercial-grade aesthetic."""
    ],
    'NEUTRAL_WHITE_FRAMING': [
        """Professional studio product photography. High-end e-commerce style.
MANDATE: Preserve the product's exact framing, scale, and position — do not move, crop, or resize the subject in any way. Maintain its precise shape, dimensions, texture, and color with zero distortion.
ENVIRONMENT: Replace only the background with a seamless, flat white studio backdrop. The subject must remain at its exact spatial coordinates within the frame. Preserve any foreground depth or surface the product rests on.
LIGHTING: Apply professional 'three-point' diffused lighting that wraps naturally around the object's existing silhouette. High-key aesthetic that dissolves the background into pure white, with a subtle soft contact shadow at the base to ground the product. No new shadows or highlights that would alter the perceived geometry.
OUTPUT: Clean, sharp, 4K resolution, commercial-grade aesthetic. The final image should look like the original was shot in a white studio from the same angle and distance."""
    ],
    'DARK_STUDIO': [
        """Professional studio product photography. Dark luxury aesthetic.
MANDATE: Preserve the product's exact framing, scale, and position — do not move, crop, or resize the subject in any way. Maintain its precise shape, dimensions, texture, and color with zero distortion.
ENVIRONMENT: Replace the background with a seamless, deep charcoal studio backdrop (near-black, not pure black). Preserve the surface the product rests on; let it fade naturally into the dark background.
LIGHTING: Dramatic single-source side lighting from the left, creating a bold shadow that recedes into the dark background on the right. A precise specular highlight catches the product's rim or polished edges. The result should feel editorial, high-fashion, and unmistakably premium.
OUTPUT: Clean, sharp, 4K resolution, luxury commercial aesthetic."""
    ],
    'WARM_LIFESTYLE': [
        """High-end lifestyle product photography. Warm, organic luxury aesthetic.
MANDATE: Preserve the product's exact framing and scale — do not move, crop, or resize the subject. Maintain its precise shape, dimensions, texture, and color.
ENVIRONMENT: Replace the background with a warm, natural surface — aged oak, honed sandstone, or raw linen — within a minimal, softly out-of-focus warm interior. The immediate surroundings should feel organic, tactile, and intentional. No clutter.
LIGHTING: Warm, directional late-afternoon light from one side, creating soft golden highlights on the product's rim and a gentle contact shadow that grounds it on the surface. The atmosphere should feel like natural light through a linen curtain — luminous but never harsh.
OUTPUT: Clean, sharp, 4K resolution, premium editorial aesthetic."""
    ]
}

CATS_PROMPTS_STUDIO = {
    'CATS_STUDIO_MOSAIC': [
        "MAKE A MOSAIC WITH THESE 9 SCENES",
        """Professional studio photography of the provided bowl.
MANDATE: Maintain the exact shape, dimensions, texture, and material of the bowl. Be true to the product.
ENVIRONMENT: Place the bowl on a dark, wire-brushed oak surface. A sleek, short-haired black cat is captured in a statuesque pose behind the bowl.
LIGHTING: Dramatic side-lighting to emphasize the polished stone's grain and the bowl's heavy, sculptural silhouette. Deep, clean shadows.
OUTPUT: Sharp 4K, high-end commercial aesthetic.""",
        """High-end e-commerce lifestyle photography of the provided bowl.
MANDATE: Preserve the authentic texture, color, and polished finish of the material.
ENVIRONMENT: The bowl is placed on a raw, honed stone floor within a minimalist architectural space. A serene, grey cat is captured mid-drink from the bowl.
LIGHTING: Soft, natural morning light flooding the scene, creating high-contrast highlights on the rim and a soft, realistic contact shadow beneath the bowl.
OUTPUT: Clean, sharp, 4K resolution.""",
        """Professional studio product photography.
MANDATE: Maintain the exact silhouette and material weight of the bowl. Center the subject.
ENVIRONMENT: Place the bowl in a neutral, gallery-like environment with a matte concrete background. An elegant Abyssinian cat is gracefully approaching the bowl.
LIGHTING: 'Three-point' professional lighting to make the subject pop, leaving only a subtle, soft shadow to the right. No harsh reflections.
OUTPUT: Clean, sharp, 4K resolution.""",
        """High-end lifestyle photography of the provided bowl.
MANDATE: Reflect the true color and complex texture of the provided material.
ENVIRONMENT: The bowl sits on a massive, reclaimed dark timber beam. A tabby cat is captured in a soft-focus background, looking toward the bowl.
LIGHTING: Warm, directional light that catches the polished edges of the stone, emphasizing its voluptuous form and heavy presence.
OUTPUT: 4K, sophisticated and grounded.""",
        """Professional e-commerce photography of the provided bowl.
MANDATE: Maintain the exact shape and material finish.
ENVIRONMENT: A minimalist kitchen setting with a dark slate countertop. A Siamese cat is elegantly eating from the bowl.
LIGHTING: Crisp, clean studio lighting with a focus on the specular highlights of the bowl's rim against the dark surface.
OUTPUT: 4K resolution, commercial-grade aesthetic.""",
        """High-end product photography of the provided bowl.
MANDATE: Be true to the product's dimensions and texture.
ENVIRONMENT: Place the bowl on a thick slab of polished white marble. A fluffy white Persian cat is captured in profile next to the bowl.
LIGHTING: Bright, airy "high-key" lighting that minimizes shadows and emphasizes the clean lines of the design.
OUTPUT: Sharp 4K, luxurious and serene.""",
        """Professional lifestyle photography of the provided bowl.
MANDATE: Retain the exact veining and color of the material.
ENVIRONMENT: An industrial-chic loft with a polished concrete floor. A Russian Blue cat is captured mid-stride passing the bowl.
LIGHTING: Harsh, cinematic sunlight streaming through a large window, creating long, dramatic shadows and bright highlights on the stone.
OUTPUT: 4K, evocative and architectural.""",
        """Close-up product photography of the provided bowl.
MANDATE: Exact representation of the bowl's curvature and weight.
ENVIRONMENT: The bowl is set on a matte black wooden surface. A Bengal cat is leaning in to eat, showing the contrast between the stone and the animal's coat.
LIGHTING: Softbox lighting to eliminate glare and show the depth of the material's texture.
OUTPUT: Sharp, 4K, professional e-commerce style.""",
        """Professional studio photography of the provided bowl.
MANDATE: Maintain the exact shape, dimensions, and texture of the product.
ENVIRONMENT: A neutral, warm-toned plaster background. A tortoiseshell cat is sitting patiently beside the bowl.
LIGHTING: Balanced 'three-point' lighting with a warm fill to enhance the organic feel of the stone.
OUTPUT: Clean, sharp, 4K resolution, commercial-grade aesthetic.""",
    ]
}

CATS_PROMPTS_HOME = {
    'CATS_HOME_MOSAIC_GALLERY': [
        "MAKE A MOSAIC WITH THESE 9 SCENES",
        """Professional lifestyle photography of the provided bowl.
MANDATE: Maintain the exact shape, texture, and material finish of the bowl.
ENVIRONMENT: A sun-drenched, minimalist courtyard with terracotta tiles. A sleek cat is lounging in the shade next to the bowl.
LIGHTING: Bright, natural overhead sunlight with soft dappled shadows from an unseen olive tree.
OUTPUT: Sharp 4K, organic and serene aesthetic.""",
        """High-end e-commerce photography of the provided bowl.
MANDATE: Preserve the authentic weight and polished surface of the stone.
ENVIRONMENT: A modern, "glass-house" living room with floor-to-ceiling windows. The bowl sits on a low-profile basalt stone ledge. A Savannah cat is captured in a graceful, predatory stretch toward the bowl.
LIGHTING: Soft, ambient blue-hour light with warm interior spotlighting on the bowl.
OUTPUT: 4K resolution, architectural and premium.""",
        """Professional product photography of the provided bowl.
MANDATE: Absolute fidelity to the bowl's geometry and color.
ENVIRONMENT: An outdoor wooden deck made of weathered silver teak. A fluffy Maine Coon is drinking from the bowl.
LIGHTING: Late afternoon "Golden Hour" light hitting the rim of the bowl, creating a warm, glowing rim-light effect.
OUTPUT: Clean, sharp, 4K resolution.""",
        """High-end lifestyle photography of the provided bowl.
MANDATE: Reflect the true material grain and sculptural form.
ENVIRONMENT: A minimalist Zen garden with raked gravel. The bowl is placed on a large, flat river rock. A charcoal-colored cat is sitting in a meditative pose behind the bowl.
LIGHTING: Diffused, overcast daylight that flattens shadows and emphasizes the raw texture of the stone.
OUTPUT: 4K, tranquil and sophisticated.""",
        """Professional studio-style photography in a home setting.
MANDATE: Maintain the exact silhouette and dimensions of the bowl.
ENVIRONMENT: A sunken conversation pit with dark stone surfaces. An Abyssinian cat is gracefully perched on the edge of the pit next to the bowl.
LIGHTING: Hidden cove lighting creating a soft, ethereal glow around the base of the bowl.
OUTPUT: Sharp 4K, moody and luxurious.""",
        """High-end e-commerce photography of the provided bowl.
MANDATE: Be true to the product's polished finish and veining.
ENVIRONMENT: A brutalist-style concrete patio. The bowl is centered on a pedestal of raw concrete. A sleek black cat is captured mid-leap over the bowl.
LIGHTING: High-contrast midday sun, creating sharp, architectural shadows.
OUTPUT: 4K, bold and sculptural.""",
        """Professional lifestyle photography of the provided bowl.
MANDATE: Retain the exact material weight and color.
ENVIRONMENT: A cozy, minimalist fireplace hearth made of dark slate. A ginger cat is curled up near the bowl.
LIGHTING: The warm, flickering orange glow from the fire hitting one side of the bowl, with soft shadows on the other.
OUTPUT: Sharp 4K, tactile and evocative.""",
        """High-end outdoor photography of the provided bowl.
MANDATE: Maintain the exact texture and material of the bowl.
ENVIRONMENT: A lush, walled secret garden with ivy-covered stone. The bowl sits on a pedestal of aged limestone. A British Shorthair cat is investigating the bowl.
LIGHTING: Soft, filtered sunlight through a canopy of leaves, creating a bright, airy garden atmosphere.
OUTPUT: 4K resolution, commercial-grade.""",
        """Professional product photography of the provided bowl.
MANDATE: Absolute fidelity to the bowl's dimensions and material.
ENVIRONMENT: An ultra-modern kitchen with a dark, honed granite waterfall island. A Siamese cat is captured in a high-fashion, statuesque pose next to the bowl.
LIGHTING: Sophisticated pendant lighting from above, creating a perfect circular highlight on the interior of the bowl.
OUTPUT: Clean, sharp, 4K resolution.""",
    ],
    'CATS_HOME_MOSAIC_EVERYDAY': [
        "MAKE A MOSAIC WITH THESE 9 SCENES",
        """Professional lifestyle photography of the provided bowl.
MANDATE: Maintain the exact shape, texture, and material of the bowl.
ENVIRONMENT: A real, sun-lit kitchen corner on a slightly worn white oak floor. A calico cat is caught in a candid moment, stretching next to the bowl. A few stray kibbles lie on the floor nearby for a natural look.
LIGHTING: Bright, indirect light coming from a nearby kitchen window. No studio lights; just natural, soft daylight and realistic shadows.
OUTPUT: Sharp 4K, authentic and lived-in.""",
        """High-end e-commerce photography of the provided bowl.
MANDATE: Preserve the authentic weight and material finish.
ENVIRONMENT: A transition space between a living room and a garden terrace. The bowl sits on a concrete step. A tabby cat is casually walking past the bowl toward the door.
LIGHTING: Natural afternoon sun with a slight glare on the stone's polished edge, looking like a quick, high-quality snapshot.
OUTPUT: 4K resolution, realistic and grounded.""",
        """Professional photography of the provided bowl.
MANDATE: Absolute fidelity to the bowl's geometry.
ENVIRONMENT: The bowl is placed on a simple, dark slate tile in a hallway. A black cat is captured mid-lick, leaning over the bowl. The background is a slightly out-of-focus, neutral-colored wall.
LIGHTING: Dim, ambient indoor lighting supplemented by a soft light from a side room, creating a cozy, everyday evening vibe.
OUTPUT: Clean, sharp, 4K resolution.""",
        """High-end lifestyle photography of the provided bowl.
MANDATE: Reflect the true material grain and form.
ENVIRONMENT: An outdoor patio with simple stone pavers. A grey cat is sitting near the bowl, looking at something off-camera. A potted plant is partially visible in the corner of the frame to ground the scene.
LIGHTING: Overcast, flat natural light that reveals the true, raw color of the stone without dramatic studio effects.
OUTPUT: 4K, honest and serene.""",
        """Professional photography of the provided bowl in a home setting.
MANDATE: Maintain the exact silhouette of the bowl.
ENVIRONMENT: A minimalist breakfast nook. The bowl sits on a wooden bench. A Siamese cat is sitting patiently by the bowl, waiting for food. The scene feels like a quiet morning at home.
LIGHTING: Soft, hazy morning light filtering through a thin curtain, creating a gentle, realistic atmosphere.
OUTPUT: Sharp 4K, warm and authentic.""",
        """High-end photography of the provided bowl.
MANDATE: Be true to the product's finish.
ENVIRONMENT: A gravel courtyard path next to a back door. The bowl is placed directly on the pebbles. A ginger cat is sniffing the edge of the bowl.
LIGHTING: Sharp, direct sunlight with high-contrast shadows, mimicking a bright summer day outdoors.
OUTPUT: 4K, raw and unpolished but high-quality.""",
        """Professional lifestyle photography of the provided bowl.
MANDATE: Retain the exact material weight and color.
ENVIRONMENT: A wooden kitchen island with a few everyday items (like a bowl of fruit) blurred in the far background. A Russian Blue cat is eating peacefully.
LIGHTING: Overhead kitchen lights mixed with a bit of natural light from a window, creating a realistic "home" color balance.
OUTPUT: Sharp 4K, approachable and premium.""",
        """High-end outdoor photography of the provided bowl.
MANDATE: Maintain the exact texture of the material.
ENVIRONMENT: A simple brick-lined porch. The bowl is tucked into a corner by a doorframe. A black-and-white tuxedo cat is lounging near it.
LIGHTING: Late-day shade, very soft and even, highlighting the bowl's form without artificial highlights.
OUTPUT: 4K resolution, believable and high-end.""",
        """Professional product photography of the provided bowl.
MANDATE: Absolute fidelity to the bowl's dimensions.
ENVIRONMENT: A bathroom or utility room with large-format grey floor tiles. A cat is captured drinking water from the bowl. The reflection of the cat is visible on the floor tile.
LIGHTING: Neutral, clean indoor lighting that feels like a standard high-end residence.
OUTPUT: Clean, sharp, 4K resolution.""",
    ],
    'CATS_HOME_MOSAIC_LUXURY': [
        "MAKE A MOSAIC WITH THESE 9 SCENES",
        """The Sunken Lounge: Professional lifestyle photography of the provided bowl.
MANDATE: Maintain the exact material texture and sculptural weight.
ENVIRONMENT: A brutalist-inspired sunken living room with micro-cement floors and a low-slung modular sofa. The bowl is placed on a wide concrete step. A sleek charcoal-grey cat is walking toward the bowl.
LIGHTING: Natural light from a high clerestory window, creating long, clean diagonal shadows across the room.
OUTPUT: Sharp 4K, architectural and serene.""",
        """The White Oak Sanctuary: High-end e-commerce photography of the provided bowl.
MANDATE: Preserve the authentic stone veining and polished finish.
ENVIRONMENT: A minimalist kitchen featuring floor-to-ceiling white oak cabinetry and a seamless stone island. The bowl sits on the floor near a large olive tree in a terracotta pot. A ginger tabby cat is captured mid-sip.
LIGHTING: Soft, diffused morning light filtering through linen drapes.
OUTPUT: 4K resolution, warm and organic luxury.""",
        """The Gallery Hallway: Professional product photography of the provided bowl.
MANDATE: Absolute fidelity to the bowl's geometry.
ENVIRONMENT: A minimalist gallery-style hallway with lime-wash plaster walls and a single piece of abstract textured art. The bowl is placed directly on a dark basalt floor. A Siamese cat is sitting in a statuesque pose next to it.
LIGHTING: Discreet recessed ceiling spotlights creating a soft halo around the bowl.
OUTPUT: Sharp 4K, sophisticated and high-fashion.""",
        """The Courtyard Reflection: High-end outdoor photography of the provided bowl.
MANDATE: Reflect the true color and complex texture of the material.
ENVIRONMENT: A private Mediterranean-style courtyard with limestone pavers and a small reflecting pool. The bowl is placed on the edge of the water. A black cat is drinking from the bowl, with its reflection visible in the pool.
LIGHTING: Indirect, late-afternoon sky-light, providing a cool, even glow.
OUTPUT: 4K, tranquil and grounded.""",
        """The Penthouse View: Professional lifestyle photography of the provided bowl.
MANDATE: Maintain the exact silhouette and polished sheen.
ENVIRONMENT: A high-end penthouse with floor-to-ceiling windows overlooking a soft-focus city skyline at dusk. The bowl sits on a polished dark wood floor. A Russian Blue cat is lounging gracefully nearby.
LIGHTING: The warm glow of the setting sun hitting the side of the bowl, contrasted with the cool blue tones of the room.
OUTPUT: Sharp 4K, evocative and premium.""",
        """The Zen Atrium: High-end e-commerce photography of the provided bowl.
MANDATE: Stay true to the product's dimensions and material weight.
ENVIRONMENT: An indoor-outdoor transition space with a pebble floor and a single floating wooden step. The bowl is placed on the wooden surface. A fluffy white cat is investigating the bowl.
LIGHTING: Bright, natural light from an overhead skylight, creating sharp, realistic shadows on the pebbles.
OUTPUT: 4K resolution, raw and architectural.""",
        """The Monolithic Kitchen: Professional product photography of the provided bowl.
MANDATE: Exact representation of the bowl's curvature and stone grain.
ENVIRONMENT: A dark, moody kitchen with a Nero Marquina marble backsplash and matte black fixtures. The bowl is centered on a matching marble floor. A tuxedo cat is captured mid-stride passing the bowl.
LIGHTING: Moody, directional spotlighting that emphasizes the "sculptural intervention" of the piece.
OUTPUT: Sharp 4K, dramatic and tactile.""",
        """The Library Corner: High-end lifestyle photography of the provided bowl.
MANDATE: Retain the exact color and material density.
ENVIRONMENT: A quiet corner of a home library with dark walnut shelving and a textured wool rug. The bowl sits on a small, low travertine plinth. A calico cat is sitting patiently by the bowl.
LIGHTING: Warm, soft light from an unseen floor lamp, creating an intimate, everyday luxury vibe.
OUTPUT: 4K, cozy and sophisticated.""",
        """The Glass Pavilion: Professional photography of the provided bowl.
MANDATE: Maintain the absolute geometric perfection of the bowl.
ENVIRONMENT: A minimalist glass-walled pavilion surrounded by a pine forest. The bowl is placed on a raw concrete floor. A tabby cat is sitting by the glass wall, looking out at the trees.
LIGHTING: Cool, natural forest light, very soft and even, highlighting the bowl's form without artificial glare.
OUTPUT: Sharp 4K, serene and modern.""",
    ]
}

UPSCALE_PROMPT = {
    'UPSCALE': [
        """MANDATE: High-fidelity enhancement. Increase the pixel density and texture resolution while maintaining the exact geometry, material finish, and lighting of the original image.
TECHNICAL SPECS: Remove any noise or compression artifacts. Output in 8K resolution with a commercial-grade, sharp, and clean editorial aesthetic. Do not hallucinate new objects; stay true to the source composition."""
    ]
}


def apply_prompts_to_products(folders_or_files, prompts, codes, image_size="1K",
                              aspect="1:1", is_folder=True, replace=False, save_to=None,
                              on_progress=None):
    """
    on_progress: optional callable(current: int, total: int, filename: str)
                 called after each image is processed (or skipped).
    """
    if is_folder and folders_or_files[-1] == '/':
        folders_or_files = folders_or_files[:-1]

    INPUT_DIR = folders_or_files

    if save_to is not None:
        BASE_OUTPUT_DIRS = [f"{save_to}/{p}" for p in codes]
    else:
        BASE_OUTPUT_DIRS = [f"{folders_or_files}/processed_{p}" for p in codes]

    for d in BASE_OUTPUT_DIRS:
        os.makedirs(d, exist_ok=True)

    file_list = os.listdir(INPUT_DIR) if is_folder else folders_or_files
    image_files = [f for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total = len(image_files)

    for idx, filename in enumerate(tqdm(image_files)):
        if is_folder:
            img = Image.open(os.path.join(INPUT_DIR, filename))
        else:
            img = Image.open(filename)

        for i, prompt_text in enumerate(prompts):
            splits = filename.split('/')
            filen_new = '_'.join(splits[-2:])

            processed_filename = (
                f"{BASE_OUTPUT_DIRS[i]}/{filename}"
                if is_folder
                else f"{BASE_OUTPUT_DIRS[i]}/{filen_new}"
            )

            if os.path.exists(processed_filename) and not replace:
                continue

            try:
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=[img, prompt_text],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect, image_size=image_size)
                    )
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        part.as_image().save(processed_filename)
            except Exception as e:
                print(f"Error {filename} Style {i}: {e}")

        if on_progress:
            on_progress(idx + 1, total, filename)


def apply_colors_to_products(product_filepaths, colors_dir, replace=False, aspect="1:1"):

    color_samples = [
        f for f in os.listdir(colors_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    for filename in product_filepaths:
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        img_product = Image.open(filename)
        filename_no_ext = os.path.splitext(os.path.basename(filename))[0]
        output_subfolder = os.path.join(os.path.dirname(filename), filename_no_ext)
        os.makedirs(output_subfolder, exist_ok=True)

        for color_file in tqdm(color_samples):
            if not color_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            img_texture = Image.open(os.path.join(colors_dir, color_file))
            color_name = os.path.splitext(color_file)[0]
            save_path = os.path.join(output_subfolder, f'{color_name}.jpg')

            if os.path.exists(save_path) and not replace:
                continue

            prompt_text = (
                "TASK: Texture Transfer. Turn the first image in the material shown in the second image.\n"
                "Keep the EXACT product as in the first image (size, shape) and the EXACT image composition "
                "(light, background, camera framing...)\n"
                "High-end studio finish, 4k resolution, professional photography."
            )

            try:
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=[img_product, img_texture, prompt_text],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect, image_size="1k")
                    )
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        part.as_image().save(save_path)
                        print(f"✓ SVELDA Vault Updated: {save_path}")
            except Exception as e:
                print(f"Error {filename} Color {color_name}: {e}")
