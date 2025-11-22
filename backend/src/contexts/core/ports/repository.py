"""Repository interfaces for core bounded context.

This module defines repository protocols (interfaces) for the core context.
The core context is being migrated to separate catalog and builds contexts.

Planned scope:
- Item repository protocol (moved to catalog)
- Build repository protocol (moved to builds)
- Currency repository protocol (moved to economy)

Status: Deprecated - migrate to catalog/builds/economy contexts
"""


# This file is intentionally minimal as the core context is being refactored.
# New bounded contexts (catalog, builds, economy) will have their own repository interfaces.
