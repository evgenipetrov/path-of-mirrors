"""Upgrades context.

This context handles finding item upgrades for character builds.

Key functionality:
- Parse Path of Building (PoB) files and import codes
- Search for better items on Trade API
- Rank items by improvement (stat deltas)
- Compare items by weighted scores

This context is stateless - no database operations required for MVP.
"""
