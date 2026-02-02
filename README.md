# Header Footer Detection

A Python library for detecting and removing headers and footers from multi-page documents using the **HFEPA (Header and Footer Extraction by Page-Association)** algorithm.

Based on the research paper: [Header and Footer Extraction by Page-Association](https://www.hpl.hp.com/techreports/2002/HPL-2002-129.pdf)

## Features

- Automatically detect repeating headers and footers across document pages
- Handle page numbers and other varying content through text normalization
- Configurable detection thresholds and window sizes
- Return detailed scoring data or simply clean documents

## Installation

### From PyPI (when published)

```bash
pip install header-footer-detection
```

### From GitHub

```bash
pip install git+https://github.com/jonathanvanleeuwen/header_footer_detection.git
```

### From Source

```bash
git clone https://github.com/jonathanvanleeuwen/header_footer_detection.git
cd header_footer_detection
pip install .
```

## Quick Start

```python
from header_footer_detection import HFEPA

# Create a detector with default settings
detector = HFEPA()

# Your document as a list of pages, each page is a list of lines
document = [
    ["Company Report", "Introduction content here", "More text", "Page 1"],
    ["Company Report", "Chapter 2 content here", "Details", "Page 2"],
    ["Company Report", "Chapter 3 content here", "More details", "Page 3"],
]

# Remove headers and footers
clean_doc = detector.remove_headers_footers(document)
print(clean_doc)
# Output: [['Introduction content here', 'More text'], ['Chapter 2 content here', 'Details'], ...]

# Or get detailed analysis data
analysis = detector.get_header_footer_data(document)
for page in analysis:
    for line in page:
        print(f"{line['text']}: {line['line_type']} (header_score={line['header_score']:.2f})")
```

## API Reference

### HFEPA Class

```python
HFEPA(
    window_size: int = 8,
    header_threshold: float = 8.0,
    footer_threshold: float | None = None,
    weights: tuple[float, ...] = (1.0, 0.75, 0.5, 0.5, 0.5),
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `window_size` | `int` | `8` | Number of pages to compare on each side of the current page |
| `header_threshold` | `float` | `8.0` | Minimum score for a line to be classified as a header |
| `footer_threshold` | `float` | `None` | Minimum score for footer classification (defaults to `header_threshold`) |
| `weights` | `tuple[float, ...]` | `(1.0, 0.75, 0.5, 0.5, 0.5)` | Weights for candidate lines (top-to-bottom for headers, reversed for footers) |

#### Score Calculation

The maximum possible score depends on your settings:
- **Maximum score**: `(2 × window_size × max(weights)) + 1`
- **Edge pages** (first/last): `window_size × max(weights) + 1`

Example with default settings (`window_size=8`, `weights=(1.0, ...)`):
- Maximum score for middle pages: `(2 × 8 × 1.0) + 1 = 17`
- Maximum score for edge pages: `8 × 1.0 + 1 = 9`

### Methods

#### `remove_headers_footers(doc: list[list[str]]) -> list[list[str]]`

Remove detected headers and footers from a document.

**Parameters:**
- `doc`: Document as a list of pages, where each page is a list of line strings

**Returns:** Document with header/footer lines removed

#### `get_header_footer_data(doc: list[list[str]]) -> list[list[dict]]`

Analyze a document and return detailed classification data.

**Parameters:**
- `doc`: Document as a list of pages, where each page is a list of line strings

**Returns:** List of pages with line dictionaries containing:
- `text`: Original line text
- `line_type`: `'header'`, `'footer'`, or `'body'`
- `header_score`: HFEPA score for header classification
- `footer_score`: HFEPA score for footer classification
- `header_candidate`: Whether the line was evaluated as a potential header
- `footer_candidate`: Whether the line was evaluated as a potential footer

## Algorithm Overview

The HFEPA algorithm works by:

1. **Candidate Selection**: For each page, the top N non-empty lines are header candidates, and the bottom N non-empty lines are footer candidates (where N = number of weights).

2. **Text Normalization**: Lines are normalized by:
   - Collapsing multiple whitespace characters
   - Replacing digits with `@` (so "Page 1" and "Page 2" become "Page @")

3. **Similarity Scoring**: Each candidate is compared against corresponding candidates on adjacent pages within the window using Levenshtein similarity.

4. **Classification**: Lines with scores meeting or exceeding the threshold are classified as headers or footers.

## Configuration Tips

### For short documents (< 20 pages)
```python
detector = HFEPA(window_size=3, header_threshold=2.0)
```

### For documents with prominent headers only
```python
detector = HFEPA(weights=(1.0,), header_threshold=5.0)  # Only check first line
```

### For documents with subtle headers
```python
detector = HFEPA(header_threshold=3.0)  # Lower threshold for more sensitive detection
```

## Development

### Setup

```bash
git clone https://github.com/jonathanvanleeuwen/header_footer_detection.git
cd header_footer_detection
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use this library in academic work, please cite the original paper:

```
Ding, Y., Oxley, G., & Gerber, M. (2002).
Header and Footer Extraction by Page-Association.
HP Laboratories Technical Report HPL-2002-129.
```

# Coverage Report
