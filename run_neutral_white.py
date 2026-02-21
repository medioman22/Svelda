import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "libs"))
from svelda import apply_prompts_to_products, NEUTRAL_WHITE_PROMPT

AVAILABLE_PROMPTS = list(NEUTRAL_WHITE_PROMPT.keys())

DEFAULT_FOLDER = (
    "/Users/mmacchini/Library/CloudStorage/GoogleDrive-matteo.macchini@gmail.com"
    "/My Drive/Svelda/PHOTOS/Raw/ciotols bassa anteprima/selection_resized/pil_mix"
)

parser = argparse.ArgumentParser(description="Apply a neutral-white prompt to a folder of product images.")
parser.add_argument(
    "folder",
    nargs="?",
    default=DEFAULT_FOLDER,
    help=f"Input folder (default: pil_mix)",
)
parser.add_argument(
    "-p", "--prompt",
    choices=AVAILABLE_PROMPTS,
    default="NEUTRAL_WHITE_FRAMING",
    help=f"Prompt to apply. Choices: {AVAILABLE_PROMPTS} (default: NEUTRAL_WHITE_FRAMING)",
)
parser.add_argument(
    "-s", "--size",
    default="1K",
    help="Output image size (default: 1K)",
)
parser.add_argument(
    "-r", "--replace",
    action="store_true",
    help="Re-process and overwrite already-generated files",
)
args = parser.parse_args()

prompts = NEUTRAL_WHITE_PROMPT[args.prompt]
codes   = [args.prompt]

print(f"Folder : {args.folder}")
print(f"Prompt : {args.prompt}")
print(f"Size   : {args.size}")
print(f"Replace: {args.replace}")
print()

apply_prompts_to_products(
    folders_or_files=args.folder,
    prompts=prompts,
    codes=codes,
    image_size=args.size,
    aspect="1:1",
    is_folder=True,
    replace=args.replace,
)
