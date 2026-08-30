import math


def histogram(values: list[float], bins: list[float]) -> list[int]:
    counts = [0 for _ in range(len(bins) - 1)]
    if not counts:
        return []
    for value in values:
        placed = False
        for index in range(len(bins) - 1):
            if bins[index] <= value < bins[index + 1]:
                counts[index] += 1
                placed = True
                break
        if not placed:
            if value < bins[0]:
                counts[0] += 1
            else:
                counts[-1] += 1
    return counts


def population_stability_index(reference_counts: list[int], current_counts: list[int], epsilon: float = 1e-6) -> float | None:
    if len(reference_counts) != len(current_counts) or not reference_counts:
        return None
    reference_total = sum(reference_counts)
    current_total = sum(current_counts)
    if reference_total == 0 or current_total == 0:
        return None
    psi = 0.0
    for reference_count, current_count in zip(reference_counts, current_counts, strict=True):
        reference_pct = max(reference_count / reference_total, epsilon)
        current_pct = max(current_count / current_total, epsilon)
        psi += (current_pct - reference_pct) * math.log(current_pct / reference_pct)
    return round(float(psi), 6)


def jensen_shannon_divergence(reference_counts: list[int], current_counts: list[int], epsilon: float = 1e-12) -> float | None:
    if len(reference_counts) != len(current_counts) or not reference_counts:
        return None
    reference_total = sum(reference_counts)
    current_total = sum(current_counts)
    if reference_total == 0 or current_total == 0:
        return None
    reference = [max(count / reference_total, epsilon) for count in reference_counts]
    current = [max(count / current_total, epsilon) for count in current_counts]
    midpoint = [(left + right) / 2 for left, right in zip(reference, current, strict=True)]
    divergence = 0.5 * _kl(reference, midpoint) + 0.5 * _kl(current, midpoint)
    return round(float(divergence), 6)


def ks_statistic(reference_values: list[float], current_values: list[float]) -> float | None:
    if not reference_values or not current_values:
        return None
    reference = sorted(reference_values)
    current = sorted(current_values)
    values = sorted(set(reference + current))
    reference_index = 0
    current_index = 0
    max_distance = 0.0
    for value in values:
        while reference_index < len(reference) and reference[reference_index] <= value:
            reference_index += 1
        while current_index < len(current) and current[current_index] <= value:
            current_index += 1
        distance = abs(reference_index / len(reference) - current_index / len(current))
        max_distance = max(max_distance, distance)
    return round(float(max_distance), 6)


def classify_metric(value: float | None, warning_threshold: float, drift_threshold: float) -> str:
    if value is None:
        return "insufficient_data"
    if value >= drift_threshold:
        return "drift_detected"
    if value >= warning_threshold:
        return "warning"
    return "stable"


def _kl(left: list[float], right: list[float]) -> float:
    return sum(left_value * math.log(left_value / right_value) for left_value, right_value in zip(left, right, strict=True))
