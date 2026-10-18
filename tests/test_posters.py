"""Regression coverage for real data labels and narrow seven-column layouts."""
from types import SimpleNamespace

import pytest
from PIL import Image

from research.render import poster


@pytest.mark.parametrize('template', ['black_gold', 'navy', 'ivory'])
@pytest.mark.parametrize('count', [1, 7, 15])
def test_stock_cards_are_readable_and_do_not_overlap(tmp_path, template, count):
    stocks = [SimpleNamespace(symbol='WWWWWWWWWWWWWWWW' if i == 0 else f'TEST{i}',
                              name='Example American Company Incorporated',
                              close=1234.56, change_pct=-2.37, support=1200.12,
                              resistance=1299.99, outlook='看跌') for i in range(count)]
    target = tmp_path / 'poster.png'
    layout = poster(target, '03 Magnificent Seven', stocks,
                    '2026-10-16', '2026-10-19', True, template)
    labels = [item['text'] for item in layout]
    assert labels.count('$1,234.56') == count
    assert labels.count('-2.37%') == count
    assert labels.count('BEARISH') == count
    assert 'SIMULATED DATA / NOT LIVE QUOTES' in labels
    assert not any('forecast range' in label.lower() for label in labels)
    for i, entry in enumerate(layout):
        assert entry['text'].isascii()
        x0, y0, x1, y1 = entry['box']
        assert 0 <= x0 < x1 <= 1080 and 0 <= y0 < y1 <= 1920
        for other in layout[i + 1:]:
            a, b, c, d = other['box']
            assert min(x1, c) <= max(x0, a) or min(y1, d) <= max(y0, b), (entry, other)
    with Image.open(target) as image:
        assert image.size == (1080, 1920)
        image.verify()
