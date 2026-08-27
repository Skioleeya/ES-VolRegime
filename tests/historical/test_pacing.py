from src.historical.pacing import HistoricalPacer


def test_pacer_waits_for_identical_request_gap():
    clock = [100.0]
    slept: list[float] = []

    def now() -> float:
        return clock[0]

    def sleeper(delay: float) -> None:
        slept.append(delay)
        clock[0] += delay

    pacer = HistoricalPacer(now=now, sleeper=sleeper)
    signature = ("ESU6", "CME", "TRADES")

    pacer.acquire(signature)
    pacer.acquire(signature)

    assert slept == [15.0]


def test_pacer_limits_five_requests_in_two_seconds():
    clock = [100.0]
    pacer = HistoricalPacer(
        now=lambda: clock[0],
        sleeper=lambda delay: clock.__setitem__(0, clock[0] + delay),
        same_signature_gap=0.0,
    )
    signatures = [("ESU6", "CME", "TRADES") for _ in range(6)]

    for signature in signatures[:5]:
        pacer.acquire(signature)
    pacer.acquire(signatures[5])

    assert clock[0] == 102.0
    assert len(pacer._global_history) == 6
