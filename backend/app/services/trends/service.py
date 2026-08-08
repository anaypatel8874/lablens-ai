"""LabLens AI - Trend Analysis Service"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger(__name__)


class TrendAnalysisService:
    def analyze_trends(
        self,
        reports: List[Dict[str, Any]],
        parameter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze trends across multiple reports."""

        if parameter:
            return self._analyze_single_parameter(reports, parameter)

        return self._analyze_all_parameters(reports)

    def _analyze_single_parameter(
        self, reports: List[Dict[str, Any]], param: str
    ) -> Dict[str, Any]:
        """Analyze trend for a single parameter."""
        data_points = []

        for report in reports:
            for result in report.get("test_results", []):
                if result.get("normalized_test_name") == param or result.get("test_name") == param:
                    if result.get("result") is not None:
                        data_points.append({
                            "date": report.get("report_date") or report.get("created_at"),
                            "value": result["result"],
                            "unit": result.get("unit", ""),
                            "status": result.get("status", "unknown"),
                            "reference_low": result.get("reference_low"),
                            "reference_high": result.get("reference_high"),
                        })

        data_points.sort(key=lambda x: x["date"])

        if len(data_points) < 2:
            return {
                "parameter": param,
                "data_points": data_points,
                "trend": "insufficient_data",
                "change_percent": None,
                "message": "Need at least 2 data points for trend analysis.",
            }

        # Calculate trend
        first = data_points[0]["value"]
        last = data_points[-1]["value"]
        change = ((last - first) / abs(first)) * 100 if first != 0 else 0

        if change > 10:
            trend = "increasing"
        elif change < -10:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "parameter": param,
            "data_points": data_points,
            "trend": trend,
            "change_percent": round(change, 2),
            "message": f"{param} is {trend} ({change:+.1f}% change)",
        }

    def _analyze_all_parameters(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends for all comparable parameters."""
        param_history = defaultdict(list)

        for report in reports:
            for result in report.get("test_results", []):
                norm_name = result.get("normalized_test_name")
                if norm_name and norm_name != "UNKNOWN_TEST_REQUIRES_REVIEW" and result.get("result") is not None:
                    param_history[norm_name].append({
                        "date": report.get("report_date") or report.get("created_at"),
                        "value": result["result"],
                        "unit": result.get("unit", ""),
                        "status": result.get("status", "unknown"),
                    })

        trends = []
        for param, points in param_history.items():
            if len(points) >= 2:
                # Check unit consistency
                units = set(p["unit"] for p in points)
                if len(units) > 1:
                    trends.append({
                        "parameter": param,
                        "trend": "incompatible_units",
                        "message": f"Cannot compare: mixed units {units}",
                        "data_points": points,
                    })
                    continue

                first = points[0]["value"]
                last = points[-1]["value"]
                change = ((last - first) / abs(first)) * 100 if first != 0 else 0

                if change > 10:
                    trend = "increasing"
                elif change < -10:
                    trend = "decreasing"
                else:
                    trend = "stable"

                trends.append({
                    "parameter": param,
                    "trend": trend,
                    "change_percent": round(change, 2),
                    "message": f"{param}: {trend} ({change:+.1f}%)",
                    "data_points": points,
                })

        return {
            "trends": trends,
            "total_parameters": len(param_history),
            "comparable_parameters": len(trends),
        }

    def compare_reports(
        self, current: Dict[str, Any], previous: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compare two reports parameter by parameter."""
        comparisons = []

        current_results = {r.get("normalized_test_name") or r["test_name"]: r 
                          for r in current.get("test_results", [])}
        previous_results = {r.get("normalized_test_name") or r["test_name"]: r 
                           for r in previous.get("test_results", [])}

        all_params = set(current_results.keys()) | set(previous_results.keys())

        for param in all_params:
            curr = current_results.get(param)
            prev = previous_results.get(param)

            if curr and prev:
                curr_val = curr.get("result")
                prev_val = prev.get("result")

                if curr_val is not None and prev_val is not None:
                    change = curr_val - prev_val
                    change_pct = ((curr_val - prev_val) / abs(prev_val)) * 100 if prev_val != 0 else 0

                    comparisons.append({
                        "parameter": param,
                        "current_value": curr_val,
                        "previous_value": prev_val,
                        "unit": curr.get("unit", ""),
                        "change": round(change, 2),
                        "change_percent": round(change_pct, 2),
                        "current_status": curr.get("status", "unknown"),
                        "previous_status": prev.get("status", "unknown"),
                        "significant": abs(change_pct) > 15,
                    })
                else:
                    comparisons.append({
                        "parameter": param,
                        "current_value": curr_val,
                        "previous_value": prev_val,
                        "unit": curr.get("unit", "") if curr else prev.get("unit", ""),
                        "change": None,
                        "change_percent": None,
                        "current_status": curr.get("status", "unknown") if curr else "missing",
                        "previous_status": prev.get("status", "unknown") if prev else "missing",
                        "significant": False,
                    })
            elif curr:
                comparisons.append({
                    "parameter": param,
                    "current_value": curr.get("result"),
                    "previous_value": None,
                    "unit": curr.get("unit", ""),
                    "change": None,
                    "change_percent": None,
                    "current_status": curr.get("status", "unknown"),
                    "previous_status": "missing",
                    "significant": False,
                    "note": "New parameter in current report",
                })
            else:
                comparisons.append({
                    "parameter": param,
                    "current_value": None,
                    "previous_value": prev.get("result"),
                    "unit": prev.get("unit", ""),
                    "change": None,
                    "change_percent": None,
                    "current_status": "missing",
                    "previous_status": prev.get("status", "unknown"),
                    "significant": False,
                    "note": "Parameter not in current report",
                })

        return comparisons
