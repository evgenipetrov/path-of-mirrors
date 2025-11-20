# Documentation Index

**Path of Mirrors** - Economic intelligence platform for Path of Exile 1 and Path of Exile 2

This directory contains all project documentation organized by purpose.

## 📚 Quick Navigation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Essential commands and workflows for development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Full development setup and conventions
- **[scripts/README.md](../scripts/README.md)** - One-liners (start, test, generate API client)

### Architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture patterns and decisions
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - Visual architecture diagrams (hexagonal, system, data flow)
- **[adr/](adr/)** - Architecture Decision Records
  - [001-domain-infrastructure-coupling.md](adr/001-domain-infrastructure-coupling.md) - SQLAlchemy as domain models

### Product & Planning
- **[PRODUCT.md](PRODUCT.md)** - Product vision and feature roadmap
- **[SPRINT.md](SPRINT.md)** - Current sprint priorities and progress
- **[BACKLOG.md](BACKLOG.md)** - Full feature backlog and epic breakdowns
- **[EPIC_SEQUENCE.md](EPIC_SEQUENCE.md)** - Epic execution sequence and dependencies

### Infrastructure
- **[INFRASTRUCTURE_SETUP.md](INFRASTRUCTURE_SETUP.md)** - Infrastructure configuration guide
- **[MIGRATION_TEST_PLAN.md](MIGRATION_TEST_PLAN.md)** - Database migration testing procedures

### Archive
- **[_archived/](_archived/)** - Historical documents for reference

---

## 📖 Documentation by Audience

### For New Developers
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Sections 1-3
3. Review [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for visual overview
4. Check [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards

### For Product Managers
1. [PRODUCT.md](PRODUCT.md) - Vision and features
2. [SPRINT.md](SPRINT.md) - Current progress
3. [BACKLOG.md](BACKLOG.md) - Roadmap and priorities
4. [EPIC_SEQUENCE.md](EPIC_SEQUENCE.md) - Release planning

### For DevOps/SREs
1. [INFRASTRUCTURE_SETUP.md](INFRASTRUCTURE_SETUP.md)
2. [MIGRATION_TEST_PLAN.md](MIGRATION_TEST_PLAN.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Section 7 (Deployment)

### For Architects
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Complete reference
2. [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - Visual diagrams
3. [adr/](adr/) - Architecture decisions
4. [CONTRIBUTING.md](CONTRIBUTING.md) - Coding patterns

---

## 📝 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| QUICKSTART.md | ✅ Current | 2025-11-20 |
| ARCHITECTURE.md | ✅ Current | 2025-11-20 |
| ARCHITECTURE_DIAGRAM.md | ✅ Current | 2025-11-20 |
| CONTRIBUTING.md | ✅ Current | 2025-11-20 |
| PRODUCT.md | ✅ Current | 2025-11-20 |
| SPRINT.md | ✅ Current | 2025-11-20 |
| BACKLOG.md | ✅ Current | 2025-11-20 |
| EPIC_SEQUENCE.md | ✅ Current | 2025-11-20 |
| INFRASTRUCTURE_SETUP.md | ✅ Current | 2025-11-20 |
| MIGRATION_TEST_PLAN.md | ✅ Current | 2025-11-20 |
| adr/001-domain-infrastructure-coupling.md | ✅ Current | 2025-11-20 |

---

## 📋 Documentation Conventions

### Writing Guidelines
- Use GitHub-flavored Markdown
- Include code examples where appropriate
- Link to related documents
- Keep language clear and concise
- Update "Last Updated" date when making changes

### Document Types

#### Architecture Decision Records (ADRs)
- **Location:** `adr/`
- **Format:** `NNN-short-title.md`
- **Status:** Proposed, Accepted, Deprecated, Superseded
- **Template:** Context, Decision, Rationale, Consequences

#### Product Documents
- **Purpose:** Vision, features, roadmap
- **Audience:** Product managers, stakeholders
- **Update Frequency:** Per sprint/release

#### Technical Guides
- **Purpose:** How-to guides, setup instructions
- **Audience:** Developers, DevOps
- **Update Frequency:** As features change

#### Architecture Docs
- **Purpose:** System design, patterns, principles
- **Audience:** Architects, senior developers
- **Update Frequency:** Major releases or refactors

---

## 🗂️ Archive Policy

Documents are moved to `_archived/` when:
- The information is outdated (e.g., pre-refactor reviews)
- The task/sprint is completed (e.g., sprint summaries)
- The document is superseded by a newer version

Archived documents are kept for historical reference.

### Current Archives
- `ARCHITECTURE_REVIEW.md` - Pre-refactor architecture review (completed)
- `PURIST_REFACTOR_PLAN.md` - Refactor plan (completed)
- `SPRINT_DEV_SCRIPTS_COMPLETE.md` - Completed sprint summary
- `SPRINT_PHASE0_ARCHIVE.md` - Phase 0 sprint archive
- `SPRINT_PHASE1_SUMMARY.md` - Phase 1 sprint summary

---

## 🔄 Keeping Docs Updated

### When to Update Documentation

**Immediately:**
- Adding/removing features (→ update PRODUCT.md, BACKLOG.md)
- Architectural changes (→ update ARCHITECTURE.md, create ADR)
- New development patterns (→ update CONTRIBUTING.md)
- API changes (→ update relevant docs)

**Per Sprint:**
- SPRINT.md - Update progress and priorities
- BACKLOG.md - Adjust epic priorities

**Major Releases:**
- Review all docs for accuracy
- Archive completed sprint/phase docs
- Update version numbers in examples

### Review Schedule
- **Weekly:** SPRINT.md
- **Bi-weekly:** BACKLOG.md, PRODUCT.md
- **Monthly:** Architecture docs
- **Per Release:** All documentation

---

## 📞 Documentation Questions?

- Found outdated info? Open an issue
- Need clarification? Check `CONTRIBUTING.md` or ask the team
- Want to improve docs? PRs welcome!

---

## 🔗 External References

### Technologies
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [React 19 Documentation](https://react.dev/)
- [TanStack Router](https://tanstack.com/router)
- [TanStack Query](https://tanstack.com/query)

### Architectural Patterns
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### Path of Exile
- [poe.ninja API](https://poe.ninja/) - Economy data source
- [Path of Exile Trade API](https://www.pathofexile.com/trade) - Official trade data
- [poedb](https://poedb.tw/) - Game data reference

---

**Last Updated:** 2025-11-18
**Maintainer:** Development Team
