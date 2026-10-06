"""Admin domain — order management and broadcasts.

Handlers here are restricted to Telegram IDs listed in ``ADMIN_IDS``.
Access is enforced by ``AdminFilterMiddleware`` attached to this
router in ``bot.py``.
"""
