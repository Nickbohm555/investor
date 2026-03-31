from app.services.broker_eligibility import is_broker_eligible_ticker


def test_is_broker_eligible_ticker_uses_uppercase_blocked_set():
    assert is_broker_eligible_ticker("nvda", blocked_tickers={"NVDA"}) is False
    assert is_broker_eligible_ticker("msft", blocked_tickers={"NVDA"}) is True
