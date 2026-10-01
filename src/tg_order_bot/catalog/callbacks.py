"""Callback data schemas for the catalog.

Using ``CallbackData`` factories gives us typed, validated callback
payloads. The prefix namespaces our callbacks so they don't collide
with other domains.
"""

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class CatalogCallback(CallbackData, prefix="catalog"):
    """Callback for catalog navigation.

    ``action`` distinguishes what the user pressed:

    - ``open``     — open the catalog (list categories)
    - ``category`` — enter a category (list its products); ``id`` is the category id
    - ``product``  — open a product card; ``id`` is the product id
    """

    action: Literal["open", "category", "product"]
    id: int | None = None


__all__ = ["CatalogCallback"]
