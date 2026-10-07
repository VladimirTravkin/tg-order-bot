"""Google Sheets export service.

Uses a Service Account to authenticate and ``gspread`` to write to a
pre-configured spreadsheet. The spreadsheet must be shared with the
Service Account email (Editor role).

The header row is (re)written on every export so the sheet is
self-documenting even if a user cleared it.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tg_order_bot.config import get_settings
from tg_order_bot.database.models.order import Order

logger = logging.getLogger(__name__)

# Scopes required by gspread.
SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)

# Sheet name inside the spreadsheet.
WORKSHEET_NAME = "Orders"

# Header row written at the top of the worksheet.
HEADERS = [
    "#",
    "Дата",
    "Клиент",
    "Телефон",
    "Статус",
    "Товары",
    "Итого, ₽",
]


class GoogleSheetsError(RuntimeError):
    """Raised when Google Sheets export fails."""


def _build_client() -> gspread.Client:
    """Create an authorized gspread client.

    Raises GoogleSheetsError if credentials file is missing or invalid.
    """
    settings = get_settings()
    path = Path(settings.google_credentials_path)

    if not path.is_file():
        raise GoogleSheetsError(
            f"Google credentials file not found: {path}"
        )

    try:
        creds = Credentials.from_service_account_file(str(path), scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as exc:  # pragma: no cover — depends on env
        raise GoogleSheetsError(f"Failed to authorize gspread: {exc}") from exc


def _format_products(order: Order) -> str:
    """Compose a short product summary like 'Маргарита×1, Пепперони×2'."""
    parts = []
    for item in order.items:
        parts.append(f"{item.product_name}×{item.quantity}")
    return ", ".join(parts)


def _order_to_row(order: Order) -> list[str]:
    """Convert an Order into a single row for the spreadsheet."""
    return [
        str(order.id),
        order.created_at.strftime("%Y-%m-%d %H:%M"),
        order.customer_name,
        order.customer_phone,
        order.status.value,
        _format_products(order),
        f"{order.total}",
    ]


async def _fetch_orders(session: AsyncSession) -> list[Order]:
    """Load all orders (newest first) with items eagerly loaded."""
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _write_rows_sync(spreadsheet_id: str, rows: list[list[str]]) -> int:
    """Blocking export — must be called via asyncio.to_thread.

    Opens the spreadsheet, selects (or creates) the worksheet, clears
    it, writes the header + rows, and returns the number of data rows
    written.
    """
    client = _build_client()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except gspread.SpreadsheetNotFound as exc:
        raise GoogleSheetsError(
            f"Spreadsheet not found or not shared with service account: {spreadsheet_id}"
        ) from exc

    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME, rows=1000, cols=len(HEADERS)
        )

    worksheet.clear()
    worksheet.append_row(HEADERS)
    if rows:
        worksheet.append_rows(rows)
    return len(rows)


async def export_orders(session: AsyncSession) -> tuple[int, str]:
    """Export all orders to the configured Google Sheet.

    Returns a tuple of (rows_written, timestamp). Raises
    GoogleSheetsError on any failure.
    """
    settings = get_settings()
    if not settings.google_sheets_enabled:
        raise GoogleSheetsError(
            "GOOGLE_SPREADSHEET_ID is not set — export disabled"
        )

    orders = await _fetch_orders(session)
    rows = [_order_to_row(order) for order in orders]

    # gspread is synchronous — run it in a thread to avoid blocking the loop.
    written = await asyncio.to_thread(
        _write_rows_sync, settings.google_spreadsheet_id, rows
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(
        "Exported %d orders to Google Sheets (%s)",
        written,
        settings.google_spreadsheet_id,
    )
    return written, timestamp


__all__ = ["GoogleSheetsError", "export_orders"]
