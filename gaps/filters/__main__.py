"""Lists what the filters are made of: `python -m gaps.filters`."""

import sys

from gaps.filters.config import ANVIL_LENGTH_M
from gaps.filters.generic import GENERIC_FILTERS
from gaps.filters.predicates import PREDICATES

print("Generic filters:")
for name, pinch_filter in GENERIC_FILTERS.items():
    print(f"\n  {name}")
    explanation = pinch_filter.__doc__ or sys.modules[pinch_filter.__module__].__doc__
    print(f"    {' '.join(explanation.split())}")
print(f"\n  settings: ANVIL_LENGTH_M = {ANVIL_LENGTH_M}")

print("\nPredicates for level files:")
for name, test in PREDICATES.items():
    print(f"  {name:20s} {' '.join(test.__doc__.split())}")
