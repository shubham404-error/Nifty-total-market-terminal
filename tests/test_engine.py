import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import rsi_wilder, calculate_indicators, _safe_ratio

class TestEngine(unittest.TestCase):
    def test_safe_ratio(self):
        num = pd.Series([10.0, 20.0, 30.0])
        den = pd.Series([2.0, 0.0, np.nan])
        res = _safe_ratio(num, den)
        self.assertEqual(res.iloc[0], 5.0)
        self.assertTrue(pd.isna(res.iloc[1]))
        self.assertTrue(pd.isna(res.iloc[2]))

    def test_rsi_wilder(self):
        close_up = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
        rsi_up = rsi_wilder(close_up, 14)
        self.assertTrue(pd.isna(rsi_up.iloc[0]))
        self.assertTrue(rsi_up.iloc[-1] > 80)

        close_down = pd.Series([24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10])
        rsi_down = rsi_wilder(close_down, 14)
        self.assertTrue(rsi_down.iloc[-1] < 20)

    def test_calculate_indicators_empty(self):
        empty_df = pd.DataFrame()
        res = calculate_indicators(empty_df)
        self.assertTrue(res.empty)

    def test_calculate_indicators_missing_cols(self):
        df = pd.DataFrame({"Date": ["2023-01-01"], "Close": [100]})
        with self.assertRaises(ValueError):
            calculate_indicators(df)

    def test_calculate_indicators_logic(self):
        dates = pd.date_range(start="2023-01-01", periods=300, freq="D")
        df = pd.DataFrame({
            "Date": dates,
            "Yahoo Symbol": "TEST.NS",
            "Open": np.linspace(100, 200, 300),
            "High": np.linspace(105, 205, 300),
            "Low": np.linspace(95, 195, 300),
            "Close": np.linspace(100, 200, 300),
            "Volume": np.random.randint(1000, 10000, 300)
        })
        
        res = calculate_indicators(df)
        
        self.assertIn("EMA9", res.columns)
        self.assertIn("SMA200", res.columns)
        self.assertIn("BullRegime", res.columns)
        
        last_row = res.iloc[-1]
        self.assertTrue(last_row["BullRegime"])
        self.assertTrue(last_row["BullSwing"])
        self.assertTrue(last_row["BullMomentum"])

if __name__ == '__main__':
    unittest.main()
