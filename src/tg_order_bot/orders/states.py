"""FSM states for the checkout flow.

The user walks through these states in order:

1. ``name``    — enter or confirm their name
2. ``phone``   — enter contact phone
3. ``comment`` — enter an optional comment (or skip)
4. ``confirm`` — review and confirm the order

All states are stored in Redis via the dispatcher's FSM storage, so
they survive bot restarts.
"""

from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    """Checkout form states."""

    name = State()
    phone = State()
    comment = State()
    confirm = State()


__all__ = ["OrderForm"]
