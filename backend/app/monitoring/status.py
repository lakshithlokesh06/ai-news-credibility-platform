from app.schemas.monitoring import MonitoringMetric


def overall_status(metrics: list[MonitoringMetric], *, has_enough_data: bool, has_profile: bool) -> tuple[str, list[str]]:
    if not has_profile:
        return "insufficient_data", ["No reference monitoring profile is available."]
    if not has_enough_data:
        return "insufficient_data", ["Not enough saved analyses for the configured monitoring window."]

    drifted = [metric.metric_name for metric in metrics if metric.status == "drift_detected"]
    warnings = [metric.metric_name for metric in metrics if metric.status == "warning"]
    if drifted:
        return "drift_detected", [f"{name} reported drift_detected." for name in drifted]
    if warnings:
        return "watch", [f"{name} reported warning." for name in warnings]
    return "healthy", ["All available drift checks are stable for this monitoring window."]


def aggregate_input_status(metrics: list[MonitoringMetric]) -> str:
    statuses = {metric.status for metric in metrics}
    if "drift_detected" in statuses:
        return "drift_detected"
    if "warning" in statuses:
        return "warning"
    if statuses == {"stable"}:
        return "stable"
    return "insufficient_data"
