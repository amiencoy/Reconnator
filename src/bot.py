# =============================================================================================== #
# This is the main controller for Telegram chatbot.                                               #
# This codes act as the "limbs" for Reconnator to work on the chat-based command.                 #
# It handles Telegram interactions, talks to the AI models, and controls the execution flow.      #
# It features a Traffic Controller to ensure complex parallel tool calls run orderly.             #
# Because executing Ffuf before getting the subdomains will leave your AI models such a bad mood. #
# =============================================================================================== #

import asyncio
import os
import logging
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from modules.agent_core import chat_with_cave_sec, mcp_agent

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=bot_token)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("*Reconnator Enabled. Type your prompts to start.*", parse_mode="Markdown")

@dp.message()
async def handle_user_message(message: types.Message):
    chat_id = message.chat.id
    user_text = message.text

    ai_response = await chat_with_cave_sec(user_text)
    
    if "content" in ai_response and ai_response["content"]:
        await message.answer(f"`{ai_response['content']}`", parse_mode="Markdown")

    if "tool_calls" in ai_response:
        tool_calls = ai_response["tool_calls"]
        is_complex = len(tool_calls) > 1

        tool_priority = {
            "execute_subdomain_recon": 1,
            "execute_nmap": 2,
            "execute_nuclei": 3,
            "execute_ffuf": 4,
            "create_pdf_report": 5
        }
        
        tool_calls.sort(key=lambda x: tool_priority.get(x["function"]["name"], 99))

        final_results = []
        pdf_filepath = None

        if is_complex:
            await message.answer("`[SYS] | Scanning the target with the most complex method possible...`", parse_mode="Markdown")

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except:
                args = {}

            if func_name == "execute_subdomain_recon":
                await message.answer("`[SYS] | Running subdomain fetcher...`", parse_mode="Markdown")
            elif func_name == "create_pdf_report":
                await message.answer("`[SYS] | Compiling all data into PDF...`", parse_mode="Markdown")
            else:
                tool_display = func_name.replace('execute_', '').upper()
                await message.answer(f"`[SYS] | Running {tool_display}...`", parse_mode="Markdown")
            
            result_text = await mcp_agent.execute_mcp_tool(func_name, args)
            
            if func_name == "create_pdf_report":
                if "[SUCCESS]" in result_text:
                    pdf_filepath = result_text.split("at: ")[-1].strip()
            else:
                final_results.append(result_text)

        if final_results:
            header_text = "**Deep scanning complete**\n\n" if is_complex else "**Scan complete**\n\n"
            summary = header_text
            for res in final_results:
                summary += f"• `{res}`\n\n"
            await message.answer(summary, parse_mode="Markdown")
        
        if pdf_filepath and os.path.exists(pdf_filepath):
            try:
                report_file = FSInputFile(pdf_filepath)
                await bot.send_document(chat_id, report_file, caption="*SUCCESS* | REPORT ATTACHED")
            except Exception as e:
                logging.error(f"Failed to send PDF: {e}")

async def main():
    print("MCP Agentic Reconnator is running 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())