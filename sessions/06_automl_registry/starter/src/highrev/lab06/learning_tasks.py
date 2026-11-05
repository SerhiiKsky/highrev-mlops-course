"""Implement the promotion policy during Lab 06."""


def gate_reasons(candidate, champion, policy):
    """Return rejection reasons, or an empty list if the candidate passes.

    Check minimum validation AUC, permitted AUC regression against an existing
    champion, maximum artifact bytes and maximum p95 prediction latency.
    """
    raise NotImplementedError("Implement the promotion gate")
