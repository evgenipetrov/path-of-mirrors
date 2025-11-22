"""PostgreSQL repository implementations for core bounded context.

This module provides concrete PostgreSQL implementations of repository interfaces.
The core context is being migrated to separate catalog and builds contexts.

Planned scope:
- Item repository implementation (moved to catalog)
- Build repository implementation (moved to builds)
- Currency repository implementation (moved to economy)

Status: Deprecated - migrate to catalog/builds/economy contexts
"""


# This file is intentionally minimal as the core context is being refactored.
# New bounded contexts (catalog, builds, economy) will have their own repository implementations.
