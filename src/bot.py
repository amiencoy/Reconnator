# ==================================================================================== #
# This is Reconnator's Telegram ChatOps entrypoint and user-facing command controller. #
# It authorizes chats, invokes the policy-gated agent core, and returns scan results.  #
# ==================================================================================== #

"""Telegram ChatOps consumer for Reconnator's policy-gated agent core."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Iterable

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from agent_core import AuthorizationContext
from modules.agent_core import chat_with_agent, close_agent_runtime, get_agent_runtime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

bot = Bot(token=bot_token)
dp = Dispatcher()
authorization_by_chat: dict[int, AuthorizationContext] = {}


def _configured_operator_chats() -> set[str]:
    configured = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", os.getenv("TELEGRAM_CHAT_ID", ""))
    return {item.strip() for item in configured.split(",") if item.strip()}


def _is_operator(chat_id: int) -> bool:
    return str(chat_id) in _configured_operator_chats()


async def _require_operator(message: types.Message) -> bool:
    if _is_operator(message.chat.id):
        return True
    await message.answer("[REFUSED] | This chat is not configured as an operator.")
    return False


def _parse_authorization_args(text: str | None) -> tuple[tuple[str, ...], str | None]:
    tokens = (text or "").split()[1:]
    ticket = None
    scope: list[str] = []
    for token in tokens:
        if token.startswith("ticket="):
            ticket = token.removeprefix("ticket=") or None
        else:
            scope.extend(item.strip() for item in token.split(",") if item.strip())
    return tuple(dict.fromkeys(scope)), ticket


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await _require_operator(message):
        return
    await message.answer(
        "*Reconnator enabled.*\n"
        "Use `/authorize <target...> ticket=<id>` before active scans.\n"
        "Use `/scope` to inspect authorization and `/revoke` when finished.",
        parse_mode="Markdown",
    )


@dp.message(Command("authorize"))
async def cmd_authorize(message: types.Message):
    chat_id = message.chat.id
    if not await _require_operator(message):
        return
    scope, ticket = _parse_authorization_args(message.text)
    if not scope:
        await message.answer(
            "`[INVALID] | Usage: /authorize example.com 192.0.2.0/24 ticket=ENG-001`",
            parse_mode="Markdown",
        )
        return
    authorization_by_chat[chat_id] = AuthorizationContext(
        approved=True,
        approved_by=f"telegram-chat:{chat_id}",
        ticket=ticket,
        scope=scope,
    )
    await message.answer(
        f"`[AUTHORIZED] | Scope: {', '.join(scope)} | Ticket: {ticket or 'not-set'}`",
        parse_mode="Markdown",
    )


@dp.message(Command("scope"))
async def cmd_scope(message: types.Message):
    if not await _require_operator(message):
        return
    authorization = authorization_by_chat.get(message.chat.id)
    if not authorization:
        await message.answer("`[SCOPE] | No active authorization.`", parse_mode="Markdown")
        return
    await message.answer(
        f"`[SCOPE] | {', '.join(authorization.scope)} | Ticket: {authorization.ticket or 'not-set'}`",
        parse_mode="Markdown",
    )


@dp.message(Command("revoke"))
async def cmd_revoke(message: types.Message):
    if not await _require_operator(message):
        return
    authorization_by_chat.pop(message.chat.id, None)
    await message.answer("`[REVOKED] | Active scan authorization cleared.`", parse_mode="Markdown")


def _tool_order(name: str) -> int:
    return {
        "execute_subdomain_recon": 1,
        "execute_nmap": 2,
        "execute_nuclei": 3,
        "execute_ffuf": 4,
        "create_pdf_report": 5,
    }.get(name, 99)


async def _send_denials(message: types.Message, calls: Iterable) -> None:
    for call in calls:
        await message.answer(
            f"`[DENIED] | {call.name}: {call.decision.code} - {call.decision.reason}`",
            parse_mode="Markdown",
        )


async def _execute_approved_workflow(runtime, calls, on_start=None):
    """Run independent scanners concurrently, then execute report calls as a barrier."""
    scanners = [call for call in calls if call.name != "create_pdf_report"]
    reports = [call for call in calls if call.name == "create_pdf_report"]

    async def invoke(call):
        if on_start is not None:
            await on_start(call)
        try:
            result = await runtime.mcp.call_tool(call.name, call.arguments)
        except Exception as exc:
            logger.exception("MCP tool failed: %s", call.name)
            result = f"[ERROR] {call.name} failed: {exc}"
        return call, result

    completed = []
    if scanners:
        completed.extend(await asyncio.gather(*(invoke(call) for call in scanners)))
    for call in reports:
        completed.append(await invoke(call))
    return completed


@dp.message()
async def handle_user_message(message: types.Message):
    if not message.text:
        return
    if not await _require_operator(message):
        return
    chat_id = message.chat.id
    authorization = authorization_by_chat.get(chat_id, AuthorizationContext())

    try:
        turn = await chat_with_agent(message.text, authorization=authorization)
    except Exception as exc:
        logger.exception("Agent planning failed")
        await message.answer(f"`[ERROR] | Agent unavailable: {exc}`", parse_mode="Markdown")
        return

    if turn.content:
        await message.answer(f"`{turn.content}`", parse_mode="Markdown")

    denied = [call for call in turn.planned_calls if not call.decision.allowed]
    allowed = sorted(
        (call for call in turn.planned_calls if call.decision.allowed),
        key=lambda call: _tool_order(call.name),
    )
    await _send_denials(message, denied)
    if not allowed:
        return

    if len(allowed) > 1:
        await message.answer("`[SYS] | Running approved scan workflow...`", parse_mode="Markdown")

    runtime = get_agent_runtime()

    async def announce_start(call):
        display = call.name.replace("execute_", "").replace("_", " ").upper()
        await message.answer(f"`[SYS] | Running {display}...`", parse_mode="Markdown")

    completed = await _execute_approved_workflow(runtime, allowed, announce_start)
    final_results: list[str] = []
    pdf_filepath = None
    for call, result_text in completed:
        if call.name == "create_pdf_report" and "[SUCCESS]" in result_text:
            pdf_filepath = result_text.split("at: ")[-1].strip()
        else:
            final_results.append(result_text)

    if final_results:
        summary = "**Scan workflow complete**\n\n" + "".join(f"• `{item}`\n\n" for item in final_results)
        await message.answer(summary, parse_mode="Markdown")

    if pdf_filepath and os.path.exists(pdf_filepath):
        try:
            await bot.send_document(
                chat_id,
                FSInputFile(pdf_filepath),
                caption="SUCCESS | REPORT ATTACHED",
            )
        except Exception:
            logger.exception("Failed to send PDF report")


async def main():
    logger.info("Provider-agnostic Reconnator is running")
    try:
        await dp.start_polling(bot)
    finally:
        await close_agent_runtime()


if __name__ == "__main__":
    asyncio.run(main())
