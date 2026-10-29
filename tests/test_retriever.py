"""
tests/test_retriever.py
Unit tests for the BM25 retriever.
"""
import pytest
from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.retrieval.indexer import build_index
from gmc_extractor.retrieval.retriever import retrieve


def make_page(num: int, text: str) -> PageDoc:
    return PageDoc(page_num=num, text=text, tables_md=[])


PAGES = [
    make_page(1, "[PAGE 1] This is the cover page of the group mediclaim policy."),
    make_page(2, "[PAGE 2] Insurer: Horizon General Insurance. TPA: MediAssist."),
    make_page(3, "[PAGE 3] Policy period 01-April-2024 to 31-March-2025. Premium Rs. 18 lakh."),
    make_page(4, "[PAGE 4] Room rent: 1% of Sum Insured per day. ICU: 2% of SI."),
    make_page(5, "[PAGE 5] Maternity benefit: Normal delivery Rs. 50,000 metro."),
    make_page(6, "[PAGE 6] Pre-existing disease waiting period waived for all members."),
    make_page(7, "[PAGE 7] Day care procedures covered. AYUSH treatment Rs. 15,000."),
    make_page(8, "[PAGE 8] Corporate buffer Rs. 10,00,000. Disease-wise capping applicable."),
    make_page(9, "[PAGE 9] ANNEXURE - Special conditions and endorsements apply."),
    make_page(10, "[PAGE 10] Total members: Employees 450, Spouses 380, Children 620."),
]

KEYWORDS = {
    "identity": {
        "primary": ["insurer", "TPA"],
        "synonyms": ["third party administrator", "insurance company"],
    },
    "room_hospitalization": {
        "primary": ["room rent", "ICU"],
        "synonyms": ["hospitalization", "bed charges"],
    },
    "maternity": {
        "primary": ["maternity", "delivery"],
        "synonyms": ["normal delivery", "caesarean"],
    },
}


def test_retriever_finds_relevant_page():
    index = build_index(PAGES)
    results = retrieve(index, KEYWORDS, "identity", top_k=3)
    page_nums = [p.page_num for p in results]
    assert 2 in page_nums  # Page 2 has insurer/TPA info


def test_retriever_finds_room_rent_page():
    index = build_index(PAGES)
    results = retrieve(index, KEYWORDS, "room_hospitalization", top_k=3)
    page_nums = [p.page_num for p in results]
    assert 4 in page_nums  # Page 4 has room rent info


def test_structural_boost():
    """Annexure page should be boosted."""
    index = build_index(PAGES)
    assert 9 in index.structural_pages  # Page 9 has ANNEXURE


def test_neighbor_inclusion():
    """Neighbour pages should be included."""
    index = build_index(PAGES)
    results = retrieve(index, KEYWORDS, "identity", top_k=1, neighbor_window=1)
    # Should include at least 2 pages (the top hit + neighbours)
    assert len(results) >= 2


def test_char_budget_enforced():
    """Char budget should limit total characters returned."""
    index = build_index(PAGES)
    budget = 200
    results = retrieve(index, KEYWORDS, "identity", top_k=10, char_budget=budget)
    total = sum(len(p.full_text) for p in results)
    assert total <= budget


def test_unknown_group_returns_pages():
    """Unknown group key should return first top_k pages gracefully."""
    index = build_index(PAGES)
    results = retrieve(index, KEYWORDS, "nonexistent_group", top_k=3)
    assert len(results) == 3
