"""Orders domain — checkout flow and order storage.

Handles the FSM-driven checkout, creates Order + OrderItem rows with
product snapshots, and notifies admins.
"""
