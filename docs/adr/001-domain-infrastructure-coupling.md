# ADR 001: Domain-Infrastructure Coupling via SQLAlchemy Models

**Status:** Accepted

**Date:** 2025-11-18

**Decision Makers:** Architecture Team

## Context

Path of Mirrors follows hexagonal architecture (ports & adapters) to maintain clean separation of concerns. A key principle of hexagonal architecture is that the domain layer should be pure and free from infrastructure dependencies.

However, we face a practical decision: should our domain models be:

1. **Pure POJOs** (Plain Old Python Objects) with separate ORM mappers
2. **SQLAlchemy models** that serve as both domain entities and ORM mappings

### The Purist Approach (Option 1)

```python
# Domain model (pure Python)
@dataclass
class Note:
    id: UUID
    title: str
    content: str | None
    game_context: Game

# Infrastructure mapper (SQLAlchemy)
class NoteORM(Base):
    __tablename__ = "notes"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    # ... mapper configuration

# Repository converts between domain and ORM
class PostgresNoteRepository:
    async def create(self, note: Note) -> Note:
        orm_note = NoteORM(**asdict(note))
        # ... save and convert back
```

**Pros:**
- Pure hexagonal architecture
- Domain models have zero infrastructure dependencies
- Can swap ORM without touching domain
- Easier unit testing (no SQLAlchemy required)

**Cons:**
- Significant boilerplate (duplicate model definitions)
- Performance overhead (constant conversion between domain ↔ ORM)
- Increased complexity for a small team
- SQLAlchemy's type safety is excellent; recreating it is wasteful

### The Pragmatic Approach (Option 2)

```python
# Domain model IS the SQLAlchemy model
class Note(Base, MappedAsDataclass):
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, init=False)
    title: Mapped[str]
    content: Mapped[str | None] = mapped_column(default=None)
    game_context: Mapped[Game]
```

**Pros:**
- Single source of truth (DRY principle)
- SQLAlchemy 2.0's `MappedAsDataclass` provides dataclass-like behavior
- Type-safe with excellent IDE support
- No performance overhead from conversions
- Simpler codebase for a small team
- Domain models are still readable and testable

**Cons:**
- Domain depends on SQLAlchemy (infrastructure leak)
- Harder to swap ORM (though extremely unlikely)
- Violates strict hexagonal architecture

## Decision

**We choose Option 2: SQLAlchemy models as domain entities.**

### Rationale

1. **Team Size & Velocity**
   - Small team (1-3 developers) values simplicity over theoretical purity
   - The boilerplate tax of dual models slows down feature development
   - Pragmatism over dogma

2. **SQLAlchemy 2.0 Quality**
   - `MappedAsDataclass` brings domain model ergonomics to ORM
   - Excellent type safety (MyPy integration)
   - Modern async support
   - The abstraction is already quite good

3. **Realistic Risk Assessment**
   - **Probability** of swapping ORMs: < 1%
   - **Cost** of not swapping: None
   - **Cost** of over-engineering now: Continuous development friction
   - Risk-adjusted decision favors pragmatism

4. **Still Hexagonal**
   - We maintain repository protocols (dependency inversion)
   - Services don't know about SQLAlchemy sessions
   - API layer doesn't construct queries
   - The architecture is still hexagonal; this is a bounded pragmatic compromise

5. **Industry Precedent**
   - Many successful projects (Django, FastAPI examples) use ORM models as domain
   - Even DDD practitioners accept this trade-off in practical contexts

## Consequences

### Positive

- **Faster development** - Single model definition per entity
- **Less code** - No conversion layer needed
- **Better DX** - IDE autocomplete, type checking work seamlessly
- **Easier onboarding** - Simpler mental model for new developers
- **Performance** - No conversion overhead

### Negative

- **Infrastructure dependency** - Domain imports `from src.infrastructure import Base`
- **Tighter coupling** - Changing ORM would require touching domain models
- **Testing** - Domain models require SQLAlchemy in test environment

### Mitigations

1. **Isolate the coupling**
   - Move `Base` to `src.shared.database` to clarify it's a shared abstraction
   - **Alternative (current):** Accept `src.infrastructure.Base` as pragmatic

2. **Repository pattern still enforced**
   - All database operations go through repository protocols
   - Domain services never see `AsyncSession` or SQLAlchemy queries

3. **Testing strategy**
   - Use in-memory SQLite for fast domain model tests
   - Mock repositories at the service layer for true unit tests

4. **Document the decision**
   - This ADR serves as justification for future developers
   - Explicitly acknowledge the trade-off

## Alternatives Considered

### Hybrid Approach
Use pure domain models for complex aggregates, SQLAlchemy for simple entities.

**Rejected because:** Inconsistency is worse than either pure approach. Having two patterns for the same concern creates confusion.

### GraphQL/Prisma-style Code Generation
Generate domain models from schema definitions.

**Rejected because:** Adds build complexity; Python ecosystem favors code-first over schema-first.

## Review

This decision should be reviewed if:
- Team grows beyond 5 developers (more capacity for abstractions)
- We encounter concrete pain from SQLAlchemy coupling
- We need to support multiple database backends simultaneously
- A significantly better ORM emerges and adoption is worth migration cost

## References

- [SQLAlchemy 2.0 MappedAsDataclass](https://docs.sqlalchemy.org/en/20/orm/dataclasses.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Pragmatic Programmer - DRY Principle](https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Signed Off:**
- Architecture Review: ✅ Accepted (2025-11-18)
- Technical Lead: ✅ Approved
