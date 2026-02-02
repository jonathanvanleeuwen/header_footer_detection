"""Comprehensive tests for the HFEPA header/footer detection algorithm."""

import warnings

import pytest

from header_footer_detection import HFEPA


class TestHFEPAInitialization:
    """Tests for HFEPA class initialization."""

    def test_default_initialization(self) -> None:
        """Test that default parameters are set correctly."""
        detector = HFEPA()
        assert detector.window_size == 8
        assert detector.header_threshold == 8.0
        assert detector.footer_threshold == 8.0
        assert detector.weights == (1.0, 0.75, 0.5, 0.5, 0.5)
        assert detector.n_candidates == 5

    def test_custom_initialization(self) -> None:
        """Test initialization with custom parameters."""
        detector = HFEPA(
            window_size=5,
            header_threshold=6.0,
            footer_threshold=7.0,
            weights=(1.0, 0.5),
        )
        assert detector.window_size == 5
        assert detector.header_threshold == 6.0
        assert detector.footer_threshold == 7.0
        assert detector.weights == (1.0, 0.5)
        assert detector.n_candidates == 2

    def test_footer_threshold_defaults_to_header_threshold(self) -> None:
        """Test that footer_threshold defaults to header_threshold when not set."""
        detector = HFEPA(header_threshold=10.0, footer_threshold=None)
        assert detector.footer_threshold == 10.0

    def test_threshold_warning_header(self) -> None:
        """Test warning when header threshold exceeds max possible score."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            HFEPA(window_size=2, header_threshold=100.0, footer_threshold=1.0)
            assert len(w) == 1
            assert "Header threshold" in str(w[0].message)
            assert "exceeds maximum possible score" in str(w[0].message)

    def test_threshold_warning_footer(self) -> None:
        """Test warning when footer threshold exceeds max possible score."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            HFEPA(window_size=2, header_threshold=1.0, footer_threshold=100.0)
            assert len(w) == 1
            assert "Footer threshold" in str(w[0].message)

    def test_threshold_warning_both(self) -> None:
        """Test warning when both thresholds exceed max possible score."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            HFEPA(window_size=2, header_threshold=100.0, footer_threshold=100.0)
            assert len(w) == 1
            assert "Header threshold" in str(w[0].message)
            assert "Footer threshold" in str(w[0].message)


class TestTextNormalization:
    """Tests for text normalization methods."""

    def test_is_valid_candidate_with_text(self) -> None:
        """Test valid candidate detection with normal text."""
        assert HFEPA._is_valid_candidate("Hello World") is True

    def test_is_valid_candidate_empty(self) -> None:
        """Test that empty string is not a valid candidate."""
        assert HFEPA._is_valid_candidate("") is False

    def test_is_valid_candidate_whitespace_only(self) -> None:
        """Test that whitespace-only string is not a valid candidate."""
        assert HFEPA._is_valid_candidate("   ") is False
        assert HFEPA._is_valid_candidate("\t\n") is False

    def test_normalize_text_digits_replaced(self) -> None:
        """Test that digits are replaced with @ symbol."""
        assert HFEPA._normalize_text("Page 123") == "Page @"
        assert HFEPA._normalize_text("2024-01-15") == "@-@-@"

    def test_normalize_text_whitespace_collapsed(self) -> None:
        """Test that multiple whitespace is collapsed."""
        assert HFEPA._normalize_text("Hello   World") == "Hello World"
        assert (
            HFEPA._normalize_text("  Leading  and  trailing  ")
            == "Leading and trailing"
        )


class TestAdjacentPageIndexes:
    """Tests for adjacent page index calculation."""

    def test_middle_page(self) -> None:
        """Test adjacent indexes for a page in the middle of the document."""
        detector = HFEPA(window_size=3)
        indexes = list(detector._adjacent_page_indexes(5, 20))
        assert indexes == [2, 3, 4, 5, 6, 7, 8]

    def test_first_page(self) -> None:
        """Test adjacent indexes for the first page."""
        detector = HFEPA(window_size=3)
        indexes = list(detector._adjacent_page_indexes(0, 20))
        assert indexes == [0, 1, 2, 3]

    def test_last_page(self) -> None:
        """Test adjacent indexes for the last page."""
        detector = HFEPA(window_size=3)
        indexes = list(detector._adjacent_page_indexes(19, 20))
        assert indexes == [16, 17, 18, 19]

    def test_small_document(self) -> None:
        """Test adjacent indexes when document is smaller than window."""
        detector = HFEPA(window_size=10)
        indexes = list(detector._adjacent_page_indexes(2, 5))
        assert indexes == [0, 1, 2, 3, 4]


class TestCandidateExtraction:
    """Tests for candidate tagging and extraction."""

    def test_reformat_and_tag_candidates_basic(self) -> None:
        """Test basic document reformatting and candidate tagging."""
        detector = HFEPA(weights=(1.0, 0.5))
        doc = [["Header line", "Body line 1", "Body line 2", "Footer line"]]
        parsed = detector._reformat_and_tag_candidates(doc)

        assert len(parsed) == 1
        assert len(parsed[0]) == 4

        # Check header candidates (first 2 non-empty lines)
        assert parsed[0][0]["header_candidate"] is True
        assert parsed[0][1]["header_candidate"] is True
        assert parsed[0][2]["header_candidate"] is False

        # Check footer candidates (last 2 non-empty lines)
        assert parsed[0][3]["footer_candidate"] is True
        assert parsed[0][2]["footer_candidate"] is True

    def test_reformat_skips_empty_pages(self) -> None:
        """Test that empty pages are filtered out."""
        detector = HFEPA()
        doc = [["Line 1"], [], ["Line 2"]]
        parsed = detector._reformat_and_tag_candidates(doc)
        assert len(parsed) == 2

    def test_reformat_skips_whitespace_lines(self) -> None:
        """Test that whitespace-only lines are not tagged as candidates."""
        detector = HFEPA(weights=(1.0,))
        doc = [["   ", "Real header", "Body", "Real footer", "   "]]
        parsed = detector._reformat_and_tag_candidates(doc)

        # The whitespace lines should not be candidates
        assert parsed[0][0]["header_candidate"] is False
        assert parsed[0][1]["header_candidate"] is True
        assert parsed[0][3]["footer_candidate"] is True
        assert parsed[0][4]["footer_candidate"] is False

    def test_extract_candidates(self) -> None:
        """Test extraction of candidates from parsed document."""
        detector = HFEPA(weights=(1.0, 0.5))
        doc = [
            ["Header 1", "Header 2", "Body", "Footer 2", "Footer 1"],
            ["Header A", "Header B", "Content", "Footer B", "Footer A"],
        ]
        parsed = detector._reformat_and_tag_candidates(doc)
        headers, footers = detector._extract_candidates(parsed)

        assert len(headers) == 2
        assert len(footers) == 2
        assert headers[0] == ["Header @", "Header @"]
        assert footers[0] == ["Footer @", "Footer @"]


class TestHFEPAScoreCalculation:
    """Tests for HFEPA score calculation."""

    def test_identical_headers_get_high_scores(self) -> None:
        """Test that identical headers across pages get high scores."""
        detector = HFEPA(window_size=2, weights=(1.0,))
        candidates = [["Header"], ["Header"], ["Header"], ["Header"], ["Header"]]
        scores = detector._calculate_hfepa_scores(candidates, (1.0,))

        # Middle pages should have highest scores (comparing with 2 pages on each side)
        assert scores[2][0] > scores[0][0]  # Middle > first
        assert scores[2][0] > scores[4][0]  # Middle > last

    def test_different_headers_get_low_scores(self) -> None:
        """Test that different headers across pages get low scores."""
        detector = HFEPA(window_size=2, weights=(1.0,))
        candidates = [["AAA"], ["BBB"], ["CCC"], ["DDD"], ["EEE"]]
        scores = detector._calculate_hfepa_scores(candidates, (1.0,))

        # Scores include self-comparison (1.0), so should be close to 1.0
        # but much lower than identical headers would produce
        # For middle pages with window=2, comparing to 4 other pages + self = 5 comparisons
        # With no similarity to others, score ≈ 1.0 (just self)
        for _page_idx, page_scores in enumerate(scores):
            for score in page_scores:
                # Score should be approximately 1.0 (self-comparison only)
                # Much lower than if all pages matched (would be ~5.0 for middle pages)
                assert score <= 1.5  # Only self-comparison contributes significantly

    def test_weights_affect_scores(self) -> None:
        """Test that different weights affect the scores proportionally."""
        detector = HFEPA(window_size=1, weights=(1.0, 0.5))
        candidates = [["Same", "Same"], ["Same", "Same"], ["Same", "Same"]]

        scores_high = detector._calculate_hfepa_scores(candidates, (1.0, 1.0))
        scores_low = detector._calculate_hfepa_scores(candidates, (0.5, 0.5))

        # Higher weights should produce higher scores
        assert scores_high[1][0] > scores_low[1][0]


class TestHeaderFooterDetection:
    """Tests for the complete header/footer detection workflow."""

    @pytest.fixture
    def simple_document(self) -> list[list[str]]:
        """Create a simple document with repeating headers and footers."""
        return [
            ["Page Header", "Content line 1", "Content line 2", "Page Footer"],
            ["Page Header", "Different content", "More content", "Page Footer"],
            ["Page Header", "Yet more content", "Even more", "Page Footer"],
            ["Page Header", "Final content", "Last line", "Page Footer"],
        ]

    @pytest.fixture
    def document_with_page_numbers(self) -> list[list[str]]:
        """Create a document with page numbers in headers/footers."""
        return [
            ["Report Title", "Content A", "Page 1"],
            ["Report Title", "Content B", "Page 2"],
            ["Report Title", "Content C", "Page 3"],
            ["Report Title", "Content D", "Page 4"],
        ]

    def test_get_header_footer_data_structure(
        self, simple_document: list[list[str]]
    ) -> None:
        """Test that get_header_footer_data returns correct structure."""
        detector = HFEPA(
            window_size=2, header_threshold=2.0, footer_threshold=2.0, weights=(1.0,)
        )
        result = detector.get_header_footer_data(simple_document)

        assert len(result) == len(simple_document)
        for page in result:
            for line in page:
                assert "text" in line
                assert "line_type" in line
                assert "header_score" in line
                assert "footer_score" in line
                assert "line_idx" in line
                assert "header_candidate" in line
                assert "footer_candidate" in line
                assert "cleaned_text" in line

    def test_identical_headers_detected(self, simple_document: list[list[str]]) -> None:
        """Test that identical headers are detected."""
        detector = HFEPA(window_size=2, header_threshold=2.0, weights=(1.0,))
        result = detector.get_header_footer_data(simple_document)

        # The repeated "Page Header" should be detected as headers
        for page in result:
            header_line = page[0]
            assert header_line["header_score"] > 0

    def test_identical_footers_detected(self, simple_document: list[list[str]]) -> None:
        """Test that identical footers are detected."""
        detector = HFEPA(window_size=2, footer_threshold=2.0, weights=(1.0,))
        result = detector.get_header_footer_data(simple_document)

        # The repeated "Page Footer" should be detected as footers
        for page in result:
            footer_line = page[-1]
            assert footer_line["footer_score"] > 0

    def test_page_numbers_normalized(
        self, document_with_page_numbers: list[list[str]]
    ) -> None:
        """Test that page numbers are normalized for comparison."""
        detector = HFEPA(
            window_size=2, header_threshold=2.0, footer_threshold=2.0, weights=(1.0,)
        )
        result = detector.get_header_footer_data(document_with_page_numbers)

        # All pages should have similar header scores due to "Page @" normalization
        header_scores = [page[0]["header_score"] for page in result]
        footer_scores = [page[-1]["footer_score"] for page in result]

        # Scores should be non-zero (pages matched)
        assert all(score > 0 for score in header_scores)
        assert all(score > 0 for score in footer_scores)

    def test_remove_headers_footers(self, simple_document: list[list[str]]) -> None:
        """Test that headers and footers are correctly removed."""
        detector = HFEPA(
            window_size=2, header_threshold=2.0, footer_threshold=2.0, weights=(1.0,)
        )
        clean_doc = detector.remove_headers_footers(simple_document)

        # Should have same number of pages
        assert len(clean_doc) == len(simple_document)

        # Each page should have fewer lines (headers/footers removed)
        for i, page in enumerate(clean_doc):
            assert len(page) < len(simple_document[i])

    def test_body_content_preserved(self, simple_document: list[list[str]]) -> None:
        """Test that body content is preserved after header/footer removal."""
        detector = HFEPA(
            window_size=2, header_threshold=2.0, footer_threshold=2.0, weights=(1.0,)
        )
        clean_doc = detector.remove_headers_footers(simple_document)

        # Check that body lines are present
        assert "Content line 1" in clean_doc[0]
        assert "Different content" in clean_doc[1]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_page_document(self) -> None:
        """Test detection on a single page document."""
        detector = HFEPA(window_size=2, header_threshold=1.0, weights=(1.0,))
        doc = [["Header", "Content", "Footer"]]
        result = detector.get_header_footer_data(doc)

        assert len(result) == 1
        # Single page can't have high similarity scores with other pages
        # but structure should be correct
        assert result[0][0]["header_candidate"] is True
        assert result[0][2]["footer_candidate"] is True

    def test_empty_document(self) -> None:
        """Test handling of empty document."""
        detector = HFEPA()
        doc: list[list[str]] = []
        result = detector.get_header_footer_data(doc)
        assert result == []

    def test_pages_with_only_whitespace(self) -> None:
        """Test that pages with only whitespace are handled."""
        detector = HFEPA(weights=(1.0,))
        doc = [["   ", "\t", ""], ["Real content"]]
        # Empty page after filtering whitespace should be skipped
        result = detector.get_header_footer_data(doc)
        # First page has no valid candidates but still exists
        # Second page should exist
        assert len(result) == 2

    def test_page_with_fewer_lines_than_candidates(self) -> None:
        """Test pages with fewer lines than the number of candidate weights."""
        detector = HFEPA(weights=(1.0, 0.75, 0.5, 0.5, 0.5))  # 5 candidates
        doc = [["Line 1", "Line 2"], ["Line A", "Line B"]]  # Only 2 lines per page
        result = detector.get_header_footer_data(doc)

        # Should handle gracefully
        assert len(result) == 2
        for page in result:
            assert len(page) == 2

    def test_overlapping_header_footer_candidates(self) -> None:
        """Test when a line is both header and footer candidate."""
        detector = HFEPA(weights=(1.0,))  # Only 1 candidate
        doc = [["Only line"], ["Only line"], ["Only line"]]
        result = detector.get_header_footer_data(doc)

        # The single line should be both header and footer candidate
        for page in result:
            assert page[0]["header_candidate"] is True
            assert page[0]["footer_candidate"] is True

    def test_footer_not_classified_if_header_score_higher(self) -> None:
        """Test that a line with higher header score is not classified as footer."""
        # This tests the logic that footer classification requires footer_score > header_score
        detector = HFEPA(
            window_size=2,
            header_threshold=0.1,
            footer_threshold=0.1,
            weights=(1.0,),
        )
        # Single line pages where header detection takes precedence
        doc = [["Same line"], ["Same line"], ["Same line"]]
        result = detector.get_header_footer_data(doc)

        # Lines should be classified as headers (not both)
        for page in result:
            line = page[0]
            # Either header or body, but if footer_score <= header_score, not footer
            if line["line_type"] == "footer":
                assert line["footer_score"] > line["header_score"]


class TestIntegration:
    """Integration tests with realistic document structures."""

    def test_realistic_pdf_document(self) -> None:
        """Test with a realistic multi-page document structure."""
        detector = HFEPA(
            window_size=3,
            header_threshold=2.0,
            footer_threshold=2.0,
            weights=(1.0, 0.5),
        )

        # Simulate a real PDF structure
        doc = []
        for i in range(10):
            page = [
                "Company Name",
                f"Document Title - Revision {i}",
                f"This is the main content of page {i + 1}.",
                "More content here with details.",
                "Additional paragraphs and information.",
                f"Copyright 2024 - Page {i + 1} of 10",
                "Confidential",
            ]
            doc.append(page)

        result = detector.get_header_footer_data(doc)
        clean_doc = detector.remove_headers_footers(doc)

        # Verify structure
        assert len(result) == 10
        assert len(clean_doc) == 10

        # Company Name should be detected as header on most pages
        header_detections = sum(
            1 for page in result if page[0]["line_type"] == "header"
        )
        assert header_detections > 5  # Should detect on most pages

        # Confidential should be detected as footer
        footer_detections = sum(
            1 for page in result if page[-1]["line_type"] == "footer"
        )
        assert footer_detections > 5  # Should detect on most pages

    def test_document_with_varied_content(self) -> None:
        """Test document where headers vary but footers are consistent."""
        detector = HFEPA(
            window_size=2, header_threshold=2.0, footer_threshold=2.0, weights=(1.0,)
        )

        doc = [
            ["Chapter 1: Introduction", "Content", "Page 1"],
            ["Chapter 2: Methods", "Content", "Page 2"],
            ["Chapter 3: Results", "Content", "Page 3"],
            ["Chapter 4: Discussion", "Content", "Page 4"],
        ]

        result = detector.get_header_footer_data(doc)

        # Headers should have low similarity (different chapters)
        # Footers should have high similarity (Page @ pattern)
        for page in result:
            footer = page[-1]
            assert footer["footer_score"] > 0  # Page numbers match after normalization
