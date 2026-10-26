"""Draw the three sample pictures (fish, house, ball) as PNG files.
The artwork is original and drawn in code, so it can be shared freely.
Usage: python3 tools/make_sample_pictures.py   (writes tools/pictures/*.png)
"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'pictures')
os.makedirs(OUT, exist_ok=True)

SCENES = {
    'fish': (
        '<rect width="300" height="300" fill="#D6F1FF"/>'
        '<circle cx="252" cy="48" r="24" fill="#FFD84D"/>'
        '<rect y="185" width="300" height="115" fill="#4FAEE3"/>'
        '<path d="M40 300 C30 260 55 240 42 200 C65 235 55 265 62 300Z" fill="#2E9E57"/>'
        '<path d="M78 300 C70 270 92 250 84 225 C102 250 96 275 100 300Z" fill="#2E9E57"/>'
        '<polygon points="88,130 36,92 36,168" fill="#F26B1D"/>'
        '<path d="M120 92 Q150 52 188 92Z" fill="#F26B1D"/>'
        '<ellipse cx="150" cy="130" rx="72" ry="44" fill="#FF9A3C"/>'
        '<path d="M112 100 Q104 130 112 160" stroke="#F26B1D" stroke-width="6" fill="none"/>'
        '<path d="M146 98 Q138 130 146 162" stroke="#F26B1D" stroke-width="6" fill="none"/>'
        '<circle cx="184" cy="120" r="9" fill="#fff"/><circle cx="186" cy="120" r="4.5" fill="#222"/>'
        '<path d="M196 142 Q205 147 211 140" stroke="#B5470F" stroke-width="3" fill="none" stroke-linecap="round"/>'
        '<circle cx="232" cy="92" r="5" fill="#fff" opacity=".85"/><circle cx="244" cy="74" r="3.5" fill="#fff" opacity=".85"/>'),
    'house': (
        '<rect width="300" height="300" fill="#D6F1FF"/>'
        '<circle cx="38" cy="42" r="22" fill="#FFD84D"/>'
        '<rect y="215" width="300" height="85" fill="#7CC576"/>'
        '<rect x="256" y="170" width="12" height="50" fill="#8B5A2B"/>'
        '<circle cx="262" cy="150" r="34" fill="#3E9B4F"/>'
        '<rect x="186" y="78" width="20" height="40" fill="#B0463F"/>'
        '<rect x="80" y="125" width="140" height="95" fill="#F7D774" stroke="#555" stroke-width="2"/>'
        '<polygon points="66,128 150,62 234,128" fill="#D9534F" stroke="#555" stroke-width="2"/>'
        '<rect x="136" y="158" width="32" height="62" fill="#8B5A2B" stroke="#555" stroke-width="2"/>'
        '<circle cx="160" cy="192" r="3" fill="#FFD84D"/>'
        '<rect x="182" y="150" width="30" height="30" fill="#9AD7FF" stroke="#555" stroke-width="2"/>'
        '<line x1="197" y1="150" x2="197" y2="180" stroke="#555" stroke-width="2"/>'
        '<line x1="182" y1="165" x2="212" y2="165" stroke="#555" stroke-width="2"/>'),
    'ball': (
        '<rect width="300" height="300" fill="#D6F1FF"/>'
        '<rect y="210" width="300" height="90" fill="#7CC576"/>'
        '<circle cx="150" cy="140" r="72" fill="#E53935"/>'
        '<ellipse cx="124" cy="114" rx="14" ry="9" fill="#fff" opacity=".6" transform="rotate(-30 124 114)"/>'),
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 900, 'height': 900})
    for name, inner in SCENES.items():
        pg.set_content('<body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 300 300">%s</svg></body>' % inner)
        pg.locator('svg').screenshot(path=os.path.join(OUT, name + '.png'))
    b.close()
print('wrote', sorted(os.listdir(OUT)))
