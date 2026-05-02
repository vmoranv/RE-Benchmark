"""6 general metrics applicable to every dimension."""

from benchmark.metrics.common.automation_support import AutomationSupportMetric
from benchmark.metrics.common.completion_rate import CompletionRateMetric
from benchmark.metrics.common.complexity_reduction import ComplexityReductionMetric
from benchmark.metrics.common.correctness import CorrectnessMetric
from benchmark.metrics.common.readability import ReadabilityMetric
from benchmark.metrics.common.token_consumption import TokenConsumptionMetric

__all__ = [
    "AutomationSupportMetric",
    "CompletionRateMetric",
    "ComplexityReductionMetric",
    "CorrectnessMetric",
    "ReadabilityMetric",
    "TokenConsumptionMetric",
]
