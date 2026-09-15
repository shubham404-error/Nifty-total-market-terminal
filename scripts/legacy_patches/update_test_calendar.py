with open("tests/test_trading_calendar.py", "a", encoding="utf-8") as f:
    f.write("\nfrom trading_calendar import get_previous_sessions\n")
    f.write("def test_get_previous_sessions():\n")
    f.write("    # Sep 16, 2026 is Wed. T-5 should be Sep 8 (Tue)\n")
    f.write("    t_5 = get_previous_sessions('2026-09-16', 5)\n")
    f.write("    assert t_5.strftime('%Y-%m-%d') == '2026-09-08'\n")