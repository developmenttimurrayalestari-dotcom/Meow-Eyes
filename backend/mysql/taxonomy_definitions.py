"""Flat product masters shared by API validation and seed tools."""
from typing import Literal, get_args

ProductType = Literal['frame', 'lens', 'package', 'accessories']
PRODUCT_TYPES = get_args(ProductType)
PRODUCT_TYPE_OPTIONS = (
    {'code': 'frame', 'name': 'Frame'}, {'code': 'lens', 'name': 'Lensa'},
    {'code': 'package', 'name': 'Paket'}, {'code': 'accessories', 'name': 'Aksesoris'},
)

GroupType = Literal['product_type', 'lens_type', 'gender', 'frame_shape', 'material']
GROUPS = (
    {'key': 'product_type', 'label': 'Jenis Produk', 'selection': 'single'},
    {'key': 'lens_type', 'label': 'Jenis Lensa', 'selection': 'multiple'},
    {'key': 'gender', 'label': 'Gender', 'selection': 'multiple'},
    {'key': 'frame_shape', 'label': 'Frame Shape', 'selection': 'multiple'},
    {'key': 'material', 'label': 'Material', 'selection': 'multiple'},
)
INITIAL_MASTERS = (
    ('product_type', 'frame', 'Frame'), ('product_type', 'lens', 'Lensa'), ('product_type', 'package', 'Paket'),
    ('lens_type', 'single-vision', 'Single Vision'), ('lens_type', 'bifocal', 'Bifocal'),
    ('lens_type', 'progressive', 'Progresif'), ('lens_type', 'uv420', 'Anti Radiasi (UV420)'), ('lens_type', 'photochromic', 'Photochromic'),
    ('gender', 'pria', 'Pria'), ('gender', 'wanita', 'Wanita'), ('gender', 'anak-anak', 'Anak-anak'), ('gender', 'unisex', 'Unisex'),
    ('frame_shape', 'aviator', 'Aviator'), ('frame_shape', 'cat-eye', 'Cat Eye'), ('frame_shape', 'geometric', 'Geometris'),
    ('frame_shape', 'rectangle', 'Rectangle'), ('frame_shape', 'rimless', 'Rimless'), ('frame_shape', 'round', 'Round'),
    ('frame_shape', 'square', 'Square'), ('frame_shape', 'oval', 'Oval'),
    ('material', 'acetate', 'Acetate'), ('material', 'titanium', 'Titanium'), ('material', 'metal', 'Metal'),
)
