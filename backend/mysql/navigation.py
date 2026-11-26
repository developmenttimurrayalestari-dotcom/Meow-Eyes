"""Editable customer navigation. Admin authorization/navigation remains separate."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from mysql.content_collections import ContentCollection
from mysql.home_categories import safe_url

HEADER = [
    ('nav-home', 'Beranda', '/', 'none'), ('nav-shop-now', 'Shop Now', '/shop-now', 'none'),
    ('nav-new-arrival', 'New Arrival', '/new-arrival', 'none'), ('nav-meowsurement', 'Meowsurement', '/meowsurement/', 'none'),
    ('nav-virtual-try-on', 'Virtual Try-On', '/virtual-try-on', 'none'), ('nav-our-product', 'Our Product', '/our-product', 'none'),
    ('nav-articles', 'Article', '/articles', 'none'), ('nav-flashsale', 'Flash Sale', '/flash-sale', 'flash'),
    ('nav-games', 'Games', '/games', 'games'), ('nav-contact', 'Contact', '/contact', 'none'),
]
FOOTER = [
    ('footer-shop', 'Shop Now', '/shop-now', 'none'), ('footer-new', 'New Arrival', '/new-arrival', 'none'),
    ('footer-meowsurement', 'Meowsurement', '/meowsurement/', 'none'), ('footer-frame', 'Frame New Arrival', '/new-arrival?product_type=frame', 'none'),
    ('footer-flash', 'Flash Sale', '/flash-sale', 'none'), ('footer-products', 'Our Product', '/our-product', 'none'),
    ('footer-articles', 'Article', '/articles', 'none'), ('footer-games', 'Mini Games', '/games', 'none'),
    ('footer-vto', 'Virtual Try-On', '/virtual-try-on', 'none'), ('footer-roulette', 'Roulette Reward', '/roulette', 'none'),
]
MOBILE = [
    ('bn-home', 'Home', '/', 'home'), ('bn-shop', 'Shop', '/shop-now', 'shop'),
    ('bn-games', 'Games', '/games', 'games'), ('bn-cart', 'Cart', '/cart', 'cart'), ('bn-profile', 'Profil', '/profile', 'profile'),
]
DEFAULTS = [dict(id=id, label=label, url=url, icon=icon, location=location, sort_order=order, is_active=True, new_tab=False)
    for location, items in [('header', HEADER), ('footer', FOOTER), ('mobile', MOBILE)]
    for order, (id, label, url, icon) in enumerate(items)]
STORE = ContentCollection('storefront.menus', DEFAULTS, 'Menu website', 100)


class MenuInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(ge=0)
    label: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1, max_length=2048)
    location: Literal['header', 'footer', 'mobile'] = 'header'
    icon: Literal['none', 'home', 'shop', 'games', 'cart', 'profile', 'sparkles', 'glasses', 'article', 'tag', 'flash', 'contact'] = 'none'
    sort_order: int = Field(default=0, ge=0, le=9999)
    is_active: bool = True
    new_tab: bool = False

    @field_validator('url')
    @classmethod
    def validate_url(cls, value):
        return safe_url(value)
