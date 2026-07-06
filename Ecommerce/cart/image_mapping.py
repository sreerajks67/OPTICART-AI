import re


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def image_url_for_product(product_id, product_name, category_name):
    """
    Build a deterministic, product-specific image URL.
    Maps product names and categories to a single, high-quality, verified search tag
    to avoid Flickr search failures (which result in fallback cat pictures).
    """
    name = (product_name or "").lower()
    cat = (category_name or "").lower()

    tag = "product"

    # Specific name keyword checks first (independent of category to capture cross-classified items)
    if "phone" in name or "iphone" in name or "mobile" in name:
        tag = "smartphone"
    elif "laptop" in name or "macbook" in name:
        tag = "laptop"
    elif "washing" in name or "washer" in name:
        tag = "washing-machine"
    elif "refrigerator" in name or "fridge" in name:
        tag = "refrigerator"
    elif "microwave" in name or "oven" in name:
        tag = "microwave"
    elif "air conditioner" in name or "ac" in name or "ac " in name:
        tag = "air-conditioner"
    elif "purifier" in name:
        tag = "water-purifier"
    elif "sofa" in name or "couch" in name:
        tag = "sofa"
    elif "chair" in name:
        tag = "chair"
    elif "table" in name or "desk" in name:
        tag = "table"
    elif "bed" in name or "mattress" in name:
        tag = "bed"
    elif "wardrobe" in name or "cabinet" in name or "cupboard" in name:
        tag = "wardrobe"
    elif "controller" in name or "gamepad" in name:
        tag = "gamepad"
    elif "console" in name:
        tag = "gaming-console"
    elif "keyboard" in name:
        tag = "keyboard"
    elif "mouse" in name:
        tag = "mouse"
    elif "headset" in name or "headphones" in name or "earphone" in name or "headphone" in name:
        if "gaming" in name or "gaming" in cat:
            tag = "gaming-headset"
        else:
            tag = "headphones"
    elif "speaker" in name or "soundbar" in name or "audio" in name:
        tag = "speaker"
    elif "tv" in name or "television" in name or "monitor" in name:
        tag = "television"
    elif "toner" in name or "cartridge" in name or "printer" in name:
        tag = "printer"
    elif "shoe" in name or "sneaker" in name or "sandal" in name or "footwear" in name:
        tag = "shoes"
    elif "jeans" in name:
        tag = "jeans"
    elif "jacket" in name:
        tag = "jacket"
    elif "watch" in name:
        tag = "watch"
    elif "bag" in name or "backpack" in name or "wallet" in name:
        tag = "backpack"
    elif "wash" in name or "cleanser" in name:
        tag = "facewash"
    elif "moisturizer" in name or "cream" in name or "lotion" in name:
        tag = "moisturizer"
    elif "lipstick" in name:
        tag = "lipstick"
    elif "sunscreen" in name:
        tag = "sunscreen"
    elif "shampoo" in name:
        tag = "shampoo"
    elif "serum" in name:
        tag = "serum"
    elif "atta" in name or "flour" in name:
        tag = "flour"
    elif "rice" in name:
        tag = "rice"
    elif "tea" in name:
        tag = "tea"
    elif "coffee" in name:
        tag = "coffee"
    elif "oil" in name:
        tag = "cooking-oil"
    elif "biscuits" in name or "cookie" in name:
        tag = "cookies"
    elif "ghee" in name or "butter" in name:
        tag = "butter"
    # General category-based fallbacks if name matches nothing specific
    elif "mobile" in cat:
        tag = "smartphone"
    elif "laptop" in cat:
        tag = "laptop"
    elif "book" in cat:
        tag = "book"
    elif "beauty" in cat or "cosmetics" in cat:
        tag = "cosmetics"
    elif "gaming" in cat:
        tag = "gaming"
    elif "grocer" in cat or "food" in cat:
        tag = "grocery"
    elif "appliances" in cat:
        tag = "home-appliance"
    elif "furniture" in cat or "home" in cat:
        tag = "furniture"
    elif "fashion" in cat or "apparel" in cat:
        tag = "clothing"
    elif "electronics" in cat or "electronic" in cat:
        tag = "gadget"
    elif "sports" in cat or "fitness" in cat:
        tag = "sports"
    elif "automotive" in cat:
        tag = "car"

    lock = int(product_id or 1)
    return f"https://loremflickr.com/600/600/{tag}?lock={lock}"


def image_url_seed_for_row(product_id, product_name, category_name):
    """
    Helper for dataset generator scripts (same mapping logic).
    """
    return image_url_for_product(product_id, product_name, category_name)

