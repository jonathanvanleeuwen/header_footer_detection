"""Header and Footer Extraction by Page-Association (HFEPA) algorithm implementation."""

import re
import warnings
from typing import TypeAlias

from Levenshtein import ratio

# Type aliases for better readability
Document: TypeAlias = list[list[str]]
ParsedDocument: TypeAlias = list[list[dict]]
Candidates: TypeAlias = list[list[str]]
Scores: TypeAlias = list[list[float]]


class HFEPA:
    """Header and Footer Extraction by Page-Association.

    Implementation based on the paper:
    https://www.hpl.hp.com/techreports/2002/HPL-2002-129.pdf

    The algorithm identifies headers and footers by comparing lines across
    adjacent pages. Lines that are similar across multiple pages are likely
    to be headers or footers.

    Note:
        The geometry score from the original paper is not implemented.

    Score Calculation Example:
        For a PDF with 20 pages, identical lines, weights=1, window_size=5:
        - Page 1, line 1: score = 6
        - Page 2, line 1: score = 7
        - Page 3, line 1: score = 8
        - Pages 10-12, line 1: score = 11 (maximum)
        - Page 18, line 1: score = 8
        - Page 19, line 1: score = 7
        - Page 20, line 1: score = 6

        Maximum possible score: (2 * window_size * max(weights)) + 1
        For first/last pages: window_size * max(weights) + 1

        Consider these limits when setting thresholds.
    """

    def __init__(
        self,
        window_size: int = 8,
        header_threshold: float = 8.0,
        footer_threshold: float | None = None,
        weights: tuple[float, ...] = (1.0, 0.75, 0.5, 0.5, 0.5),
    ) -> None:
        """Initialize the HFEPA detector.

        Args:
            window_size: Number of pages to consider on each side of the current
                page for comparison. Defaults to 8 (8 left + 8 right = 16 total).
            header_threshold: Minimum score for a line to be classified as a header.
                Should be <= (2 * window_size * max(weights)) + 1.
            footer_threshold: Minimum score for a line to be classified as a footer.
                Defaults to the same value as header_threshold.
            weights: Weights for candidate lines, ordered from top to bottom for
                headers (reversed for footers). Values should be between 0 and 1.
                The length determines how many candidate lines are considered.
        """
        self.window_size = window_size
        self.header_threshold = header_threshold
        self.footer_threshold = (
            footer_threshold if footer_threshold is not None else header_threshold
        )
        self.weights = weights
        self.n_candidates = len(weights)

        # Validate thresholds against maximum possible score
        self._validate_thresholds()

    def _validate_thresholds(self) -> None:
        """Warn if thresholds exceed the maximum possible score."""
        max_score = (self.window_size * 2 * max(self.weights)) + 1
        warning_messages = []

        if self.header_threshold > max_score:
            warning_messages.append(f"Header threshold ({self.header_threshold})")
        if self.footer_threshold > max_score:
            warning_messages.append(f"Footer threshold ({self.footer_threshold})")

        if warning_messages:
            thresholds = " and ".join(warning_messages)
            warnings.warn(
                f"{thresholds} exceeds maximum possible score ({max_score}).",
                stacklevel=3,
            )

    def remove_headers_footers(self, doc: Document) -> Document:
        """Remove headers and footers from a document.

        Args:
            doc: A document represented as a list of pages, where each page
                is a list of line strings.

        Returns:
            The document with header and footer lines removed.
        """
        parsed_doc = self.get_header_footer_data(doc)
        return [
            [
                line["text"]
                for line in page
                if line["line_type"] not in ("header", "footer")
            ]
            for page in parsed_doc
        ]

    def get_header_footer_data(self, doc: Document) -> ParsedDocument:
        """Analyze a document and return header/footer classification data.

        Args:
            doc: A document represented as a list of pages, where each page
                is a list of line strings.

        Returns:
            A list of pages, where each page is a list of dictionaries containing:
            - text: Original line text
            - line_type: 'header', 'footer', or 'body'
            - header_score: HFEPA score for header classification
            - footer_score: HFEPA score for footer classification
            - line_idx: Original line index on the page
            - header_candidate: Whether line was considered for header detection
            - footer_candidate: Whether line was considered for footer detection
            - cleaned_text: Normalized text used for comparison
        """
        parsed_doc = self._reformat_and_tag_candidates(doc)
        header_candidates, footer_candidates = self._extract_candidates(parsed_doc)
        header_scores = self._calculate_hfepa_scores(header_candidates, self.weights)
        footer_scores = self._calculate_hfepa_scores(
            footer_candidates, self.weights[::-1]
        )
        return self._populate_doc_with_results(parsed_doc, header_scores, footer_scores)

    def _reformat_and_tag_candidates(self, doc: Document) -> ParsedDocument:
        """Reformat document and tag potential header/footer candidates.

        Args:
            doc: A document as a list of pages with line strings.

        Returns:
            Parsed document with candidate tagging and metadata.
        """
        parsed_doc = [
            [
                {
                    "text": text,
                    "line_type": "body",
                    "header_score": 0.0,
                    "footer_score": 0.0,
                    "line_idx": line_idx,
                    "header_candidate": False,
                    "footer_candidate": False,
                    "cleaned_text": "",
                }
                for line_idx, text in enumerate(page)
            ]
            for page in doc
            if page
        ]

        for page_idx, page in enumerate(parsed_doc):
            self._tag_header_candidates(parsed_doc, page_idx, page)
            self._tag_footer_candidates(parsed_doc, page_idx, page)

        return parsed_doc

    def _tag_header_candidates(
        self, parsed_doc: ParsedDocument, page_idx: int, page: list[dict]
    ) -> None:
        """Tag the top non-empty lines as header candidates."""
        n_headers = 0
        for line_idx, line_data in enumerate(page):
            if n_headers >= self.n_candidates:
                break
            if self._is_valid_candidate(line_data["text"]):
                parsed_doc[page_idx][line_idx]["header_candidate"] = True
                parsed_doc[page_idx][line_idx]["cleaned_text"] = self._normalize_text(
                    line_data["text"]
                )
                n_headers += 1

    def _tag_footer_candidates(
        self, parsed_doc: ParsedDocument, page_idx: int, page: list[dict]
    ) -> None:
        """Tag the bottom non-empty lines as footer candidates."""
        n_footers = 0
        max_line_idx = page[-1]["line_idx"]
        for line_idx, line_data in enumerate(reversed(page)):
            if n_footers >= self.n_candidates:
                break
            if self._is_valid_candidate(line_data["text"]):
                actual_idx = max_line_idx - line_idx
                parsed_doc[page_idx][actual_idx]["footer_candidate"] = True
                parsed_doc[page_idx][actual_idx]["cleaned_text"] = self._normalize_text(
                    line_data["text"]
                )
                n_footers += 1

    @staticmethod
    def _is_valid_candidate(text: str) -> bool:
        """Check if a line is a valid candidate (non-empty and not just whitespace)."""
        return bool(text and not text.isspace())

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison by collapsing whitespace and replacing digits."""
        return re.sub(r"\d+", "@", " ".join(text.split()))

    def _extract_candidates(
        self, parsed_doc: ParsedDocument
    ) -> tuple[Candidates, Candidates]:
        """Extract header and footer candidates from parsed document.

        Args:
            parsed_doc: Document as returned from _reformat_and_tag_candidates.

        Returns:
            Tuple of (header_candidates, footer_candidates), each being a list
            of candidate texts per page.
        """
        header_candidates: Candidates = []
        footer_candidates: Candidates = []

        for page in parsed_doc:
            header_candidates.append(self._extract_page_header_candidates(page))
            footer_candidates.append(self._extract_page_footer_candidates(page))

        return header_candidates, footer_candidates

    def _extract_page_header_candidates(self, page: list[dict]) -> list[str]:
        """Extract header candidate texts from a single page."""
        candidates = ["" for _ in range(self.n_candidates)]
        candidate_idx = 0
        for line in page:
            if line["header_candidate"]:
                candidates[candidate_idx] = line["cleaned_text"]
                candidate_idx += 1
        return candidates

    def _extract_page_footer_candidates(self, page: list[dict]) -> list[str]:
        """Extract footer candidate texts from a single page."""
        candidates = ["" for _ in range(self.n_candidates)]
        candidate_idx = 0
        for line in reversed(page):
            if line["footer_candidate"]:
                candidates[-(candidate_idx + 1)] = line["cleaned_text"]
                candidate_idx += 1
        return candidates

    def _calculate_hfepa_scores(
        self, candidates: Candidates, weights: tuple[float, ...]
    ) -> Scores:
        """Calculate HFEPA scores for all candidates.

        Args:
            candidates: Candidate texts for each page.
            weights: Weights for each candidate position.

        Returns:
            Scores for each candidate on each page.
        """
        all_page_scores: Scores = []
        num_pages = len(candidates)

        for page_idx, page_candidates in enumerate(candidates):
            page_scores = [
                self._calculate_line_score(
                    line_text, line_idx, page_idx, num_pages, candidates, weights
                )
                for line_idx, line_text in enumerate(page_candidates)
            ]
            all_page_scores.append(page_scores)

        return all_page_scores

    def _calculate_line_score(
        self,
        current_line: str,
        line_idx: int,
        page_idx: int,
        num_pages: int,
        candidates: Candidates,
        weights: tuple[float, ...],
    ) -> float:
        """Calculate the HFEPA score for a single line."""
        score = 0.0
        for adjacent_page_idx in self._adjacent_page_indexes(page_idx, num_pages):
            adjacent_line = candidates[adjacent_page_idx][line_idx]
            similarity = ratio(current_line, adjacent_line)
            score += similarity * weights[line_idx]
        return score

    def _adjacent_page_indexes(self, current_page_idx: int, num_pages: int) -> range:
        """Get the range of page indexes to compare against.

        Args:
            current_page_idx: Index of the current page (0-based).
            num_pages: Total number of pages in the document.

        Returns:
            Range of page indexes within the window (including current page).
        """
        min_idx = max(current_page_idx - self.window_size, 0)
        max_idx = min(current_page_idx + self.window_size + 1, num_pages)
        return range(min_idx, max_idx)

    def _populate_doc_with_results(
        self,
        parsed_doc: ParsedDocument,
        header_scores: Scores,
        footer_scores: Scores,
    ) -> ParsedDocument:
        """Add scores and classifications to the parsed document.

        Args:
            parsed_doc: Document from _reformat_and_tag_candidates.
            header_scores: Scores from _calculate_hfepa_scores for headers.
            footer_scores: Scores from _calculate_hfepa_scores for footers.

        Returns:
            Updated document with scores and line_type classifications.
        """
        for page_idx, page in enumerate(parsed_doc):
            self._apply_header_scores(parsed_doc, page_idx, page, header_scores)
            self._apply_footer_scores(parsed_doc, page_idx, page, footer_scores)
        return parsed_doc

    def _apply_header_scores(
        self,
        parsed_doc: ParsedDocument,
        page_idx: int,
        page: list[dict],
        header_scores: Scores,
    ) -> None:
        """Apply header scores and classify header lines."""
        candidate_idx = 0
        for line_idx, line in enumerate(page):
            if line["header_candidate"]:
                score = header_scores[page_idx][candidate_idx]
                parsed_doc[page_idx][line_idx]["header_score"] = score
                if score >= self.header_threshold:
                    parsed_doc[page_idx][line_idx]["line_type"] = "header"
                candidate_idx += 1

    def _apply_footer_scores(
        self,
        parsed_doc: ParsedDocument,
        page_idx: int,
        page: list[dict],
        footer_scores: Scores,
    ) -> None:
        """Apply footer scores and classify footer lines.

        A line is classified as a footer only if its footer score meets the threshold
        AND is higher than its header score (to avoid double-classification).
        """
        candidate_idx = 0
        for reverse_idx, line in enumerate(reversed(page)):
            line_idx = -(reverse_idx + 1)
            if line["footer_candidate"]:
                score = footer_scores[page_idx][-(candidate_idx + 1)]
                parsed_doc[page_idx][line_idx]["footer_score"] = score
                header_score = parsed_doc[page_idx][line_idx]["header_score"]
                if score >= self.footer_threshold and score > header_score:
                    parsed_doc[page_idx][line_idx]["line_type"] = "footer"
                candidate_idx += 1
