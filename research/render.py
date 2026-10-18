"""Data-driven portrait cards with original decorative artwork."""
import math
import os
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = (1080, 1920)
PALETTES = {
    'black_gold': ('#030b1b', '#ffd575', '#f2f6ff'),
    'navy': ('#04162b', '#70dbff', '#f2f6ff'),
    'ivory': ('#eee9df', '#936525', '#15253a'),
}
OUTLOOK = {'看涨': 'BULLISH', '震荡': 'NEUTRAL', '看跌': 'BEARISH'}
ACCENTS = ['#9baec9', '#29a9ff', '#69e060', '#e4ebff', '#ffb947', '#5394ff', '#ff5265']


@lru_cache(maxsize=192)
def font(size, bold=False):
    suffix = '-Bold' if bold else ''
    candidates = [os.getenv('POSTER_FONT', ''),
                  f'/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf',
                  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError('Font required: install fonts-dejavu-core or set POSTER_FONT')


def _rgb(color):
    return tuple(bytes.fromhex(color.lstrip('#')))


@lru_cache(maxsize=3)
def _background(template):
    """Original geometric artwork, independent of the supplied reference image."""
    bg, accent, _ = PALETTES[template]
    im = Image.new('RGB', SIZE, bg)
    draw = ImageDraw.Draw(im)
    base = _rgb(bg)
    for y in range(1920):
        strength = math.exp(-((y - 510) / 350) ** 2)
        color = tuple(min(255, int(c + strength * n)) for c, n in zip(base, (0, 12, 30)))
        draw.line((0, y, 1080, y), fill=color)
    glow = Image.new('RGBA', SIZE)
    gd = ImageDraw.Draw(glow)
    for x in range(560, 1100, 52):
        gd.line((x, 65, x - 115, 600), fill=(26, 125, 255, 28), width=2)
    # Fixed abstract motif, not a plotted price history or return prediction.
    for i in range(14):
        x = 565 + i * 36
        y = 455 - i * 21 + (i % 3) * 28
        color = (43, 164, 255, 75) if i % 4 else (241, 77, 110, 65)
        gd.line((x, y - 34, x, y + 47), fill=color, width=3)
        gd.rounded_rectangle((x - 8, y - 12, x + 8, y + 24), radius=3, fill=color)
    for i, height in enumerate((65, 100, 142, 185, 242, 300)):
        x = 700 + i * 53
        gd.rounded_rectangle((x, 570 - height, x + 33, 570), radius=3,
                             fill=(7, 94, 243, 80), outline=(104, 204, 255, 160), width=2)
        gd.line((x + 4, 574 - height, x + 4, 566), fill=(102, 221, 255, 130), width=3)
    arrow = [(715, 475), (955, 213), (923, 195), (1030, 130),
             (1017, 257), (989, 235), (744, 499)]
    gd.polygon(arrow, fill=(*_rgb(accent), 170))
    gd.line((0, 586, 1080, 586), fill=(37, 188, 255, 145), width=3)
    im = Image.alpha_composite(im.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(13)))
    im = Image.alpha_composite(im, glow)
    return im.convert('RGB')


def poster(path, title, rows, day, next_day, simulated, template):
    if template not in PALETTES:
        raise ValueError('Unknown poster template')
    if len(rows) > 15:
        raise ValueError('A poster supports at most 15 stocks')
    im = _background(template).copy()
    d = ImageDraw.Draw(im)
    layout = []
    _, gold, white = PALETTES[template]
    muted = '#aec1dc' if template != 'ivory' else '#526379'
    panel = '#07152b' if template != 'ivory' else '#fffaf0'

    def text(x, y, value, width, size=28, color=white, bold=False, center=False):
        value = str(value)
        if not value.isascii():
            raise ValueError('Poster text must be English / ASCII')
        while size > 16 and d.textbbox((0, 0), value, font=font(size, bold))[2] > width:
            size -= 1
        f = font(size, bold)
        bounds = d.textbbox((0, 0), value, font=f)
        actual_width = bounds[2] - bounds[0]
        if actual_width > width:
            raise ValueError('Text exceeds its column: ' + value)
        left = x + (width - actual_width) / 2 if center else x
        origin = (left - bounds[0], y - bounds[1])
        box = d.textbbox(origin, value, font=f)
        if not (0 <= box[0] < box[2] <= SIZE[0] and 0 <= box[1] < box[3] <= SIZE[1]):
            raise ValueError('Text exceeds poster bounds: ' + value)
        d.text(origin, value, font=f, fill=color)
        layout.append({'text': value, 'box': list(box)})
        return box[3]

    def lines(value, width, size=26, bold=False):
        result, current = [], ''
        for word in value.split():
            candidate = (current + ' ' + word).strip()
            if current and d.textbbox((0, 0), candidate, font=font(size, bold))[2] > width:
                result.append(current)
                current = word
            else:
                current = candidate
        if current:
            result.append(current)
        return result

    def panel_box(box, accent, radius=22):
        x0, y0, x1, y1 = box
        for spread in (7, 4):
            d.rounded_rectangle((x0-spread, y0-spread, x1+spread, y1+spread),
                                radius=radius+spread,
                                outline=tuple(int(c * .22) for c in _rgb(accent)), width=2)
        d.rounded_rectangle(box, radius=radius, fill=panel, outline=accent, width=2)

    d.rounded_rectangle((42, 40, 502, 106), radius=27, fill='#bd243b', outline='#ff7280', width=2)
    text(62, 58, f'OUTLOOK  {next_day}', 420, 30, bold=True, color='#ffffff')
    text(44, 137, 'US EQUITY', 650, 94, bold=True)
    text(44, 242, 'DAILY MARKET WATCH', 790, 65, gold, True)
    clean_title = title.split(' ', 1)[1] if title[:2].isdigit() else title
    for i, line in enumerate(lines(clean_title.upper(), 880, 43, True)):
        if i >= 2:
            raise ValueError('Poster title exceeds two lines')
        text(46, 332 + i * 53, line, 880, 43, gold, True)
    text(46, 463, f'Based on {day} closing prices', 900, 27)
    badge = 'SIMULATED DATA / NOT LIVE QUOTES' if simulated else 'RULE-BASED TECHNICAL SIGNALS'
    text(46, 509, badge, 900, 25, '#ffce78' if template != 'ivory' else '#936525', True)
    text(46, 551, 'PRICE ACTION  /  VOLUME  /  TECHNICAL OUTLOOK', 950, 20, muted)

    count = len(rows)
    columns = 7 if 6 <= count <= 7 else 5 if count > 7 else max(3, count)
    grid_rows = math.ceil(count / columns) if count else 1
    gap, left, top, bottom = 12, 36, 624, 1430
    card_width = (1008 - gap * (columns - 1)) / columns
    card_height = (bottom - top - gap * (grid_rows - 1)) / grid_rows
    for i, report in enumerate(rows):
        col, row = i % columns, i // columns
        x = left + col * (card_width + gap)
        y = top + row * (card_height + gap)
        width = card_width - 20
        accent = ACCENTS[i % len(ACCENTS)]
        panel_box((x, y, x + card_width, y + card_height), accent, 17)
        compact = grid_rows > 1
        tile_height = 48 if compact else 126
        d.rounded_rectangle((x+9, y+10, x+card_width-9, y+tile_height), radius=11,
                            fill='#102842', outline=accent, width=2)
        symbol_parts, fragment = [], ''
        for character in report.symbol:
            if fragment and d.textbbox((0, 0), fragment+character, font=font(16, True))[2] > width:
                symbol_parts.append(fragment)
                fragment = ''
            fragment += character
        if fragment:
            symbol_parts.append(fragment)
        for part_index, part in enumerate(symbol_parts):
            text(x+10, y+(16 if compact else 36)+part_index*(18 if compact else 28),
                 part, width, 16 if len(symbol_parts)>1 else 23 if compact else 30,
                 '#ffffff', True, True)
        cy = y + tile_height + (12 if compact else 27)
        if not compact:
            name = report.name if report.name.isascii() else 'SIMULATED EQUITY'
            for line in lines(name, width, 17, True)[:3]:
                text(x+10, cy, line, width, 17, muted, True, True)
                cy += 23
            cy += 25
        text(x+10, cy, 'CLOSE', width, 16 if compact else 19, muted, center=True)
        cy += 24 if compact else 37
        text(x+10, cy, f'$' + f'{report.close:,.2f}', width, 24 if compact else 30, white, True, True)
        cy += 35 if compact else 68
        d.line((x+13, cy, x+card_width-13, cy), fill='#29405c', width=1)
        cy += 10 if compact else 29
        text(x+10, cy, 'CHANGE', width, 16 if compact else 19, muted, center=True)
        cy += 24 if compact else 39
        color = '#64e5a0' if report.change_pct >= 0 else '#ff8091'
        text(x+10, cy, f'{report.change_pct:+.2f}%', width, 25 if compact else 36, color, True, True)
        cy += 38 if compact else 77
        if not compact:
            for label, value in [('SUPPORT', report.support), ('RESISTANCE', report.resistance)]:
                text(x+10, cy, label, width, 17, muted, center=True)
                cy += 29
                text(x+10, cy, '$' + f'{value:,.2f}', width, 25, white, True, True)
                cy += 57
            text(x+10, cy, 'RULE SIGNAL', width, 17, muted, center=True)
        pill_y = y + card_height - (49 if compact else 72)
        signal_color = {'看涨': '#136c46', '震荡': '#304963', '看跌': '#a1223c'}[report.outlook]
        d.rounded_rectangle((x+9, pill_y, x+card_width-9, pill_y+(36 if compact else 48)),
                            radius=13, fill=signal_color)
        text(x+12, pill_y+(10 if compact else 14), OUTLOOK[report.outlook], card_width-24,
             18 if compact else 21, '#ffffff', True, True)
    if not rows:
        panel_box((36, 624, 1044, 1430), '#3e9de2')
        text(72, 922, 'NO QUALIFYING STOCKS', 936, 48, gold, True, True)
        text(72, 1001, "No members in today's screened Top 300.", 936, 30, muted, center=True)

    panel_box((36, 1478, 1044, 1765), '#3a9ce5')
    text(66, 1506, 'MARKET VIEW', 940, 41, gold, True)
    bullish = sum(r.outlook == '看涨' for r in rows)
    bearish = sum(r.outlook == '看跌' for r in rows)
    view = ('Bullish bias; monitor resistance.' if bullish > bearish else
            'Bearish bias; monitor support.' if bearish > bullish else 'Mixed signals; wait for confirmation.')
    text(66, 1574, view if rows else 'No sector signal without qualifying data.', 940, 30, white, True)
    text(66, 1623, f'{count} stocks  |  {bullish} bullish / {count-bullish-bearish} neutral / {bearish} bearish',
         940, 26, muted)
    text(66, 1668, 'Signals use moving averages and MACD, not return forecasts.', 940, 24, muted)
    text(66, 1711, 'News, social and earnings coverage may be incomplete.', 940, 23, muted)
    text(45, 1810, 'Research only. Not investment advice. Returns are not guaranteed.', 990, 22, muted, center=True)
    text(45, 1850, 'SYNTHETIC TEST DATA' if simulated else 'See full reports for sources and limitations.',
         990, 21, gold, center=True)
    im.save(path)
    with Image.open(path) as check:
        if check.size != SIZE:
            raise ValueError('bad image size')
        check.verify()
    return layout
