"""UI Components

Requirements: 3.1, 3.2, 3.4
"""

from ui.components.paper_card import render_paper_card
from ui.components.rag_form import render_rag_form
from ui.components.search_form import render_search_form
from ui.components.styles import apply_common_styles

__all__ = [
    "render_paper_card",
    "render_search_form",
    "render_rag_form",
    "apply_common_styles",
]
