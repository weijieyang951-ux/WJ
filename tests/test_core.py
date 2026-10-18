from stockresearch.main import normalized, indicators
import pandas as pd
def test_normalized_bounds():
    result=normalized(pd.Series([1,2,3,4,5]))
    assert result.between(0,1).all()
def test_indicators_insufficient_history():
    assert indicators(pd.DataFrame({"Close":[1.0]})) is None
