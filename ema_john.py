# ema_john_responsive_row_images_responsive.py
import json
import urllib.request
import math
import flet as ft

PRODUCTS_JSON_URL = "https://raw.githubusercontent.com/MDAnwarHossen/ema-john/refs/heads/main/products.json"
COLORS = getattr(ft, "colors", getattr(ft, "Colors", None))

# ImageFit compatibility
try:
    from flet import ImageFit  # type: ignore
    FIT_CONTAIN = ImageFit.CONTAIN
except Exception:
    try:
        from flet_core import ImageFit  # type: ignore
        FIT_CONTAIN = ImageFit.CONTAIN
    except Exception:
        FIT_CONTAIN = "contain"


def safe_load_products(url=PRODUCTS_JSON_URL, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            cleaned = []
            for i, p in enumerate(data):
                cleaned.append({
                    "id": str(p.get("id", i)),
                    "name": p.get("name", "Unnamed product"),
                    "price": float(p.get("price", 0)),
                    "img": p.get("img", "") or p.get("image", ""),
                    "category": p.get("category", ""),
                    "seller": p.get("seller", ""),
                    "stock": int(p.get("stock", p.get("quantity", 10) or 0)),
                    "ratings": float(p.get("ratings", p.get("rating", 0)) or 0),
                    "ratingsCount": int(p.get("ratingsCount", p.get("ratingCount", 0) or 0)),
                    "shipping": float(p.get("shipping", 0) or 0),
                })
            return cleaned
    except Exception as e:
        print("Warning: failed to load remote products:", e)
        return [
            {"id": "f1", "name": "Headphones", "price": 19.99,
             "img": "https://via.placeholder.com/220x160?text=Headphones", "stock": 10, "ratings": 4.2, "ratingsCount": 34, "shipping": 2.5},
            {"id": "f2", "name": "Mug", "price": 7.5,
             "img": "https://via.placeholder.com/220x160?text=Mug", "stock": 15, "ratings": 4.6, "ratingsCount": 80, "shipping": 1.5},
        ]


def star_str(rating):
    full = "★" * int(math.floor(rating))
    empty = "☆" * max(0, 5 - int(math.floor(rating)))
    return full + empty


main_content = ft.Column(expand=True, spacing=12)


def main(page: ft.Page):
    page.title = "EMA-JOHN ResponsiveRow"
    page.scroll = "auto"
    page.window_width = 1000
    page.window_height = 800
    page.vertical_alignment = ft.MainAxisAlignment.START
    try:
        page.bgcolor = COLORS.WHITE
    except Exception:
        pass

    products = safe_load_products()
    cart = {}
    cart_count_txt = ft.Text(f"({len(cart)})")

    # Controls
    search_input = ft.TextField(
        hint_text="Search products...", col={"md": 10},)
    sort_dropdown = ft.Dropdown(col={"md": 2, "sm": 12}, value="Relevance", options=[
        ft.dropdown.Option("Relevance"),
        ft.dropdown.Option("Price: Low → High"),
        ft.dropdown.Option("Price: High → Low"),
        ft.dropdown.Option("Top Rated"),
    ])

    # Columns passed into ResponsiveRow
    products_column = ft.Column(spacing=8)
    cart_column = ft.Column(spacing=8)

    subtotal_txt = ft.Text("Subtotal: €0.00", weight=ft.FontWeight.BOLD)
    shipping_txt = ft.Text("Shipping: €0.00")
    total_txt = ft.Text("Total: €0.00", weight=ft.FontWeight.BOLD)

    # Use ListView for product list to keep existing behaviour
    products_listview = ft.ListView(expand=True, spacing=10, padding=6)
    cart_listview = ft.ListView(expand=True, spacing=6, padding=6)

    # Cart helpers (kept minimal)
    def recalc_totals():
        subtotal = sum(e["product"]["price"] * e["qty"] for e in cart.values())
        shipping = sum(e["product"].get("shipping", 0) * e["qty"]
                       for e in cart.values())
        subtotal_txt.value = f"Subtotal: €{subtotal:,.2f}"
        shipping_txt.value = f"Shipping: €{shipping:,.2f}"
        total_txt.value = f"Total: €{(subtotal + shipping):,.2f}"

    # --- CHANGES: add change_qty and improved refresh_cart_ui (image + +/- buttons) ---
    def change_qty(pid, delta):
        """Adjust quantity for product id `pid` by `delta` (±1). Remove item when qty <= 0."""
        entry = cart.get(pid)
        if not entry:
            return
        # enforce integer
        entry["qty"] = int(entry["qty"]) + int(delta)
        # respect stock if available
        stock = entry["product"].get("stock", None)
        if stock is not None and entry["qty"] > stock:
            entry["qty"] = stock
            # optional: inform user (kept minimal per instructions)
            try:
                page.snack_bar.open = True
                page.snack_bar.content = ft.Text(
                    "Reached available stock limit")
                page.update()
            except Exception:
                pass
        if entry["qty"] <= 0:
            del cart[pid]
        refresh_cart_ui()

    def refresh_cart_ui():
        cart_listview.controls.clear()
        if not cart:
            cart_listview.controls.append(
                ft.Text("Your cart is empty", italic=True))
        else:
            for pid, entry in cart.items():
                p = entry["product"]
                q = entry["qty"]

                # Left: small image thumbnail
                img = ft.Image(src=p.get("img", ""), width=80,
                               height=60, fit=FIT_CONTAIN)

                # Truncate name to 25 characters (add ellipsis when longer)
                raw_name = p.get("name", "Unnamed")
                display_name = (
                    raw_name[:10] + "...") if len(raw_name) > 10 else raw_name

                # Middle column: truncated name + unit price
                name_price = ft.Column(
                    [
                        ft.Text(display_name, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"€{p.get('price', 0):,.2f}", size=12),
                    ],
                    tight=True,
                )

                # Qty controls (use default arg in lambda to avoid closure capture)
                qty_controls = ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.REMOVE, on_click=lambda e, pid=pid: change_qty(pid, -1)),
                        ft.Text(str(q)),
                        ft.IconButton(ft.Icons.ADD, on_click=lambda e,
                                      pid=pid: change_qty(pid, +1)),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                )

                # Right: line total
                line_total = ft.Text(f"€{p.get('price', 0) * q:,.2f}")

                # Construct row
                row = ft.Row(
                    [img, name_price, qty_controls, line_total],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                cart_listview.controls.append(row)

        cart_count_txt.value = f"({len(cart)})"
        recalc_totals()
        page.update()

    def add_to_cart(p):
        pid = p["id"]
        entry = cart.get(pid)
        if entry:
            entry["qty"] += 1
        else:
            cart[pid] = {"product": p, "qty": 1}
        refresh_cart_ui()

    # ---------- Responsive image sizing logic ----------
    # ResponsiveRow col mapping used in this file:
    # products col: {"sm":12, "md":8, "xl":9}
    # cart col:     {"sm":12, "md":4, "xl":3}
    # We'll compute products column pixel width = page_width * share - padding
    def products_column_share(width):
        # matches the col map thresholds used elsewhere
        if width >= 1200:
            return 9/12  # xl
        elif width >= 900:
            return 8/12  # md
        else:
            return 1.0   # sm (full width)

    def compute_img_size(page_width):
        # estimate how wide the products column is in pixels
        share = products_column_share(page_width)
        # subtract container paddings/gutters: we used padding=12 in containers + some margins
        horizontal_padding = 24  # left+right container paddings approx
        available = max(200, int(page_width * share - horizontal_padding))
        # choose image size as a fraction of available column width but bounded
        #  - desktop: ~28% of column width (image beside details)
        #  - mobile (full width): image should be ~45-60% to remain visible
        if share == 1.0:
            # mobile stacked tile: image above details; make it wider
            img = min(available - 16, 360)
        else:
            # desktop/tablet side-by-side; image should be a fraction
            img = int(max(100, min(360, available * 0.30)))
        return img

    # ---------- Product card builder uses computed img_size ----------
    def build_product_card(p, img_size):
        # image uses FIT_CONTAIN (enum or string)
        image_box = ft.Container(
            content=ft.Image(src=p["img"], width=img_size,
                             height=img_size, fit=FIT_CONTAIN),
            padding=8,
            bgcolor=COLORS.WHITE,
            border_radius=4,
        )
        details = ft.Column([
            ft.Text(p["name"], weight=ft.FontWeight.W_600,
                    max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(f"€{p['price']:,.2f}", weight=ft.FontWeight.BOLD),
            ft.Text(star_str(p.get("ratings", 0)) +
                    f"  ({p.get('ratingsCount', 0)})", size=12, color=COLORS.GREY),
            ft.Text(f"Seller: {p.get('seller', '-')}  •  Stock: {p.get('stock', 0)}",
                    size=12, color=COLORS.GREY_600),
            ft.Row([ft.ElevatedButton("Add to cart", icon=ft.Icons.SHOPPING_CART, on_click=lambda e, prod=p: add_to_cart(prod),
                                      style=ft.ButtonStyle(bgcolor="#ffd814", padding=ft.padding.Padding(5, 11, 5, 11), color=COLORS.BLACK))], spacing=8)
        ], expand=True)

        # Decide layout: stacked on mobile (image above details), side-by-side otherwise
        page_w = getattr(page, "window_width", None) or getattr(
            page, "client_width", None) or getattr(page, "width", None) or 1000
        if products_column_share(int(page_w)) == 1.0:
            # mobile: stack
            content = ft.Column([image_box, details], spacing=8)
        else:
            content = ft.Row([image_box, details], spacing=12,
                             vertical_alignment=ft.CrossAxisAlignment.CENTER)

        tile = ft.Container(
            content=content,
            padding=12,
            bgcolor=COLORS.WHITE,
            border=ft.border.all(1, COLORS.GREY_200),
            border_radius=4,
            width=None,
        )
        return tile

    def render_products(list_of_products):
        # compute image size from current page width
        page_w = getattr(page, "window_width", None) or getattr(
            page, "client_width", None) or getattr(page, "width", None) or 1000
        img_size = compute_img_size(int(page_w))
        products_listview.controls.clear()
        for p in list_of_products:
            products_listview.controls.append(build_product_card(p, img_size))
        page.update()

    def render_home():
        main_content.controls.clear()
        main_content.controls.append(build_responsive_layout())
        page.update()

    def render_order_review():
        main_content.controls.clear()
        main_content.controls.append(ft.Column([
            ft.Text("Order Review", weight=ft.FontWeight.BOLD, size=24),
            ft.Divider(),
            ft.Text("Here you can review all your orders."),
            # optional: add a table of current cart or past orders
            cart_listview
        ], spacing=8))
        page.update()

    def render_contact():
        main_content.controls.clear()
        main_content.controls.append(ft.Column([
            ft.Text("Contact Us", weight=ft.FontWeight.BOLD, size=24),
            ft.Divider(),
            ft.Text("Email: support@example.com"),
            ft.Text("Phone: +123456789"),
            ft.Text("Address: 123 Main St, City, Country"),
            ft.TextField(label="Your Message", multiline=True, min_lines=3),
            ft.ElevatedButton(
                "Send", on_click=lambda e: page.snack_bar.show_message("Message sent!"))
        ], spacing=8))
        page.update()

    def render_about():
        main_content.controls.clear()
        main_content.controls.append(ft.Column([
            ft.Text("About Us", weight=ft.FontWeight.BOLD, size=24),
            ft.Divider(),
            ft.Text("EMA-John is a demo e-commerce platform built using Flet."),
            ft.Text(
                "We aim to provide a fully responsive and interactive shopping experience."),
        ], spacing=8))
        page.update()

    # Top area
    """
    top_area = ft.Column([
        ft.Row([ft.Image(src="logo.png", height=80, fit=FIT_CONTAIN)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=8),
        ft.Row([search_input, ft.Container(width=12), sort_dropdown],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(thickness=1, color=COLORS.GREY_300, height=20),
    ], spacing=6);

    """

    top_area = ft.Column(
        [
            ft.ResponsiveRow(
                [
                    ft.Container(
                        content=ft.Image(
                            src="./logo.png",
                            expand=True,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        col={"md": 4, "sm": 12},
                        padding=10,
                        border_radius=10,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),

            # ---------- Responsive Navbar (inserted here) ----------
            ft.ResponsiveRow(
                [
                    ft.Container(
                        # full-width container that itself contains a row with nav links + actions
                        content=ft.Row(
                            [
                                # Left: nav links - they will wrap on small screens
                                ft.Row(
                                    [
                                        ft.TextButton(
                                            "Home", on_click=lambda e: render_home()),
                                        ft.TextButton(
                                            "Order Review", on_click=lambda e: render_order_review()),
                                        ft.TextButton(
                                            "About", on_click=lambda e: render_about()),
                                        ft.TextButton(
                                            "Contact", on_click=lambda e: render_contact()),
                                    ],
                                    wrap=True,
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),

                                # Right: cart icon + signin (keeps to the right)
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.IconButton(
                                                    icon=ft.Icons.SHOPPING_CART,
                                                    tooltip="Cart",
                                                    on_click=lambda e: None
                                                ),
                                                cart_count_txt,
                                            ],
                                            spacing=2,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        # delete this part
                                        ft.ElevatedButton(
                                            "Sign In", on_click=lambda e: None),
                                    ],
                                    spacing=12,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            expand=True,
                        ),
                        padding=ft.padding.symmetric(
                            vertical=6, horizontal=12),
                        col={"sm": 12, "md": 12, "xl": 12},
                        bgcolor=COLORS.WHITE,
                    )
                ],
                run_spacing=6,
                spacing=6,
            ),

            ft.ResponsiveRow(
                [search_input, sort_dropdown],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Divider(thickness=1, color=COLORS.GREY_300, height=20),
        ]
    )

    # Build ResponsiveRow layout (products | cart)
    def build_responsive_layout():
        # populate product column
        render_products(products)
        refresh_cart_ui()

        products_column.controls.clear()
        products_column.controls.append(ft.Row([ft.Text("Products", weight=ft.FontWeight.BOLD),
                                                ft.Text(f"{len(products)} items", color=COLORS.GREY)],))
        products_column.controls.append(ft.Divider())
        products_column.controls.append(products_listview)

        cart_column.controls.clear()
        cart_column.controls.append(ft.Row([ft.Text("Your Cart", weight=ft.FontWeight.BOLD),
                                            ft.Text("", color=COLORS.GREY)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        cart_column.controls.append(ft.Divider())
        cart_column.controls.append(cart_listview)
        cart_column.controls.append(ft.Divider())
        cart_column.controls.append(subtotal_txt)
        cart_column.controls.append(shipping_txt)
        cart_column.controls.append(total_txt)
        cart_column.controls.append(ft.ElevatedButton(
            "Checkout", on_click=lambda e: None, expand=True))

        rr = ft.ResponsiveRow([
            ft.Container(products_column, padding=12, col={
                         "sm": 12, "md": 8, "xl": 9}),
            ft.Container(cart_column, padding=12, col={
                         "sm": 12, "md": 4, "xl": 3}),
        ], run_spacing=12, spacing=12)
        return rr

    # Search / sort handlers
    def on_search_or_sort(e=None):
        q = search_input.value.strip().lower()
        filtered = [p for p in products if (q in p["name"].lower() or q in p.get(
            "category", "").lower())] if q else products.copy()
        sort_val = sort_dropdown.value or "Relevance"
        if sort_val == "Price: Low → High":
            filtered.sort(key=lambda x: x["price"])
        elif sort_val == "Price: High → Low":
            filtered.sort(key=lambda x: -x["price"])
        elif sort_val == "Top Rated":
            filtered.sort(
                key=lambda x: (-x.get("ratings", 0), -x.get("ratingsCount", 0)))
        # render filtered list
        products_listview.controls.clear()
        for p in filtered:
            products_listview.controls.append(build_product_card(
                p, compute_img_size(int(getattr(page, "window_width", page.width or 1000)))))
        page.update()

    search_input.on_change = on_search_or_sort
    sort_dropdown.on_change = on_search_or_sort

    # Page layout builder
    # Page layout builder - do NOT add build_responsive_layout() here

    def layout_builder(e=None):
        page.controls.clear()
        page.add(top_area)
        page.add(main_content)
        page.update()

    # Ensure on_resize keeps layout but doesn't re-add product layout itself
    page.on_resize = layout_builder

    # Initial render: build layout first, then populate home
    layout_builder()
    render_home()
    refresh_cart_ui()


if __name__ == "__main__":
    ft.app(target=main)
