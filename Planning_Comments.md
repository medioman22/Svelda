# detailed planning & comments

## Comments on the Current Website state
The website currently has a lot of placeholder texts and links that go nowhere (e.g., `"/"`), especially in the `index.json` template. The homepage has rich content blocks (image with text describing premium materials, stones, and toys) that are inexplicably disabled (`"disabled": true`). Since this is a luxury brand, disabling storytelling sections weakens the brand's aesthetic. Small things like missing button labels (e.g., `"button_label": ""`) and generic footer structures also indicate WIP status. 

## Detailed Planning of Changes

1. **Enable Narrative Sections in `index.json`**:
   - `image-with-text-1` (Premium Marble Bowls) - enable and update button links.
   - `image-with-text-2` (Pure Wool Mats) - enable and update button text and button links.
   - `image-with-text-3` (Topini) - enable and update button text and button links.
   - `cards_grid_hDzEAd` - Add descriptive subheadings for the cards, ensure links go somewhere.

2. **Fix Links & Placeholders in `index.json`**:
   - In slideshow slide 3: update link to `shopify://collections/play`.
   - In "Our Story" block: update link to `shopify://pages/about-us`.
   - In "Craftsmanship" block: update link to `shopify://pages/craftsmanship`.
   - Update image-with-text buttons from empty / `"Follow"` to action-oriented texts like `"Explore Bowls"`, `"Discover Mats"`, `"Shop Toys"`.
   - Link the Stone Collection, Fabric Collection properly so they match an intuitive ecommerce flow.
   
3. **Commit Workflow**:
   - Enable Image with Text storytelling blocks and set their content and button labels.
   - Fix Slideshow and 3-col blocks links.
   - Update any empty / `"Follow"` links to correct collection/product paths.
   - Push to remote on completion.
