# header_footer_detection - AI Coding Agent Instructions

---
## 📋 Generic Code Standards (Reusable Across All Projects)

### Code Quality Principles

**DRY (Don't Repeat Yourself)**
- No duplicate code - extract common logic into reusable functions/classes
- If you copy-paste code, you're doing it wrong
- Shared utilities belong in `utils/` or helper modules

**CLEAN Code**
- **C**lear: Code intent is obvious from reading it
- **L**ogical: Functions do one thing, follow single responsibility principle
- **E**asy to understand: Junior developers should be able to review it
- **A**ccessible: Avoid clever tricks; prefer explicit over implicit
- **N**ecessary: Every line serves a purpose; no dead code

**Production-Grade Simplicity**
- Code must be production-ready (robust, tested, maintainable)
- Use the simplest solution that solves the problem completely
- Complexity is a last resort, not a goal
- **Target audience**: Code should be readable by junior software developers/data scientists

### Comments & Documentation Philosophy

**No Commented-Out Code**
- Never commit commented code blocks - use version control instead
- Delete unused code; git history preserves it if needed

**Docstrings: Only When Necessary**
- If code requires a docstring to be understood, it's probably too complex
- Refactor for clarity first, document as a last resort
- When used, docstrings explain **WHY**, not **HOW**
- Good function/variable names eliminate most documentation needs

**Comment Guidelines**
- Explain business logic rationale, not implementation mechanics
- Document non-obvious constraints or requirements
- If a comment explains what code does, rewrite the code to be self-explanatory
- Example:
  ```python
  # ❌ BAD: Explains what (obvious from code)
  # Normalize the text
  normalized = text.replace('1', 'X')

  # ✅ GOOD: Explains why (research paper requirement)
  # HFEPA algorithm requires number normalization to match varying page numbers
  normalized = text.replace('1', 'X')
  ```

### Code Organization Standards

**Function Design**
- Functions should do **one thing** and do it well
- If a function has "and" in its description, it likely does too much
- Keep functions short (aim for <20 lines when possible)

**Import Management**
- Keep `__init__.py` files minimal - only version info and essential public API
- Prefer explicit imports: `from module.submodule import specific_function`
- Avoid importing from `__init__.py` in application code
- Long import statements are fine; they show dependencies clearly

**Separation of Concerns**
- Each module/class has a single, well-defined responsibility
- Business logic separated from I/O, API layers, and presentation
- Configuration separated from implementation

**Readability First**
- Variable names should be descriptive: `user_count` not `uc`
- Consistent naming conventions throughout the project
- Code is read 10x more than written - optimize for reading

### Development Tooling Standards

**Python Version**
- Follow Python syntax for the version specified in `pyproject.toml` (currently >=3.11)
- Backwards compatibility is NOT required - use modern Python features

**Package & Environment Management**
- Use `uv` for all virtual environment operations
- Always create venvs with: `uv venv .venv`
- Install dependencies with: `uv pip install -e ".[dev]"`

**Code Quality Tools**
- **ruff**: Primary linter and formatter (replaces black, isort, flake8)
  - Format code: `ruff format .`
  - Check code: `ruff check .`
  - Fix issues: `ruff check --fix .`
- Follow ruff's formatting style (no manual formatting needed)

**Testing**
- **pytest**: Only testing framework to use
- Always run tests in the `.venv` environment
- Execute with: `pytest` (picks up config from pyproject.toml)
- Coverage reports generated in `reports/htmlcov/`

### Meta-Instruction
**Keep these instructions updated** based on chat interactions when patterns emerge or decisions are made that should guide future development.

---

## Library Purpose

Implements the **HFEPA (Header and Footer Extraction by Page-Association)** algorithm from the HP Labs research paper to detect and remove repeating headers/footers from multi-page documents.

Paper: [Header and Footer Extraction by Page-Association (HP Labs, 2002)](https://www.hpl.hp.com/techreports/2002/HPL-2002-129.pdf)

## Core Algorithm

**Input Format**: Document as `list[list[str]]` (list of pages, each page is list of lines)

**Score Calculation**
- Each line gets a header/footer score based on similarity to lines in neighboring pages
- Uses sliding window of pages (default 8 pages on each side)
- Weighted scoring: closer candidates get higher weights (default: `1.0, 0.75, 0.5, 0.5, 0.5`)
- **Text normalization**: Numbers and special chars normalized to handle varying content (e.g., "Page 1" vs "Page 2")

**Maximum Scores**
- Middle pages: `(2 × window_size × max(weights)) + 1` (e.g., 17 with defaults)
- Edge pages (first/last): `window_size × max(weights) + 1` (e.g., 9 with defaults)

**Classification Threshold**
- Lines scoring ≥ threshold are classified as headers/footers
- Default: 8.0 (balances precision/recall)
- Adjust based on document characteristics

## API Usage

**Basic: Remove headers/footers**
```python
from header_footer_detection import HFEPA

detector = HFEPA()
clean_doc = detector.remove_headers_footers(document)
```

**Advanced: Get detailed analysis**
```python
analysis = detector.get_header_footer_data(document)
# Returns list of pages, each with line metadata:
# - 'text': original line text
# - 'line_type': 'header', 'footer', or 'content'
# - 'header_score': float score
# - 'footer_score': float score
```

**Custom Configuration**
```python
detector = HFEPA(
    window_size=10,           # Compare with 10 pages on each side
    header_threshold=6.0,     # Lower threshold = more aggressive
    footer_threshold=8.0,     # Different threshold for footers
    weights=(1.0, 0.8, 0.6, 0.4, 0.2)  # Custom weight decay
)
```

## Development Workflow

**Setup**
```bash
uv venv .venv                    # Create virtual environment with uv
uv pip install -e ".[dev]"      # Install package and dev dependencies
pre-commit install              # Install pre-commit hooks
pre-commit run --all-files      # Run hooks on all files
```

**Code Quality**
```bash
ruff format .                   # Format all code
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
```

**Testing**
```bash
pytest                          # Run all tests with coverage (reports/htmlcov/)
pytest -v                       # Verbose output
```

**Building & Distribution**
```bash
python setup.py bdist_wheel     # Creates wheel in dist/
```

## Code Conventions

**Algorithm Implementation**
- Main HFEPA class should follow the paper's methodology
- Text normalization uses character replacement for page numbers and special chars
- Scoring logic must be optimized for large documents (avoid O(n²) comparisons)

**Testing Strategy**
- Test with documents of varying lengths (edge cases: 1 page, 2 pages, 100+ pages)
- Verify edge page handling (first/last pages have different score ranges)
- Test text normalization with various page number formats

## Common Pitfalls

- **Not normalizing text** → page numbers prevent header/footer detection
- **Window size too small** → misses repeating patterns in long documents
- **Threshold too high** → misses actual headers/footers
- **Threshold too low** → incorrectly classifies content as headers/footers
- **Assuming uniform spacing** → some documents have varying header/footer positions

## Implementation Notes

- Algorithm is deterministic - same input always produces same output
- Performance: O(n × m × w) where n=pages, m=lines per page, w=window size
- Memory: Stores scores for all lines in memory (optimize for very large documents if needed)
