import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, CRYPTO_PAY_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

PAY_API = "https://pay.crypt.bot/api"

# Загружаем пароли
with open("passwords.json", "r", encoding="utf-8") as f:
    PASSWORDS = json.load(f)

FAMILIES = {
    "🚪 Современная дверь": {
        "price": 2.5,
        "payload": "modern_door"
    },
    "🧱 Бетонная стена": {
        "price": 3.0,
        "payload": "concrete_wall"
    }
}


async def create_invoice(asset: str, amount: float, payload: str, description: str):
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    data = {
        "asset": asset,
        "amount": amount,
        "currency": "USDT",
        "description": description,
        "payload": payload
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PAY_API}/createInvoice", headers=headers, json=data) as resp:
            result = await resp.json()
            return result["result"]["invoice_id"], result["result"]["pay_url"]


async def check_payment(invoice_id: str) -> bool:
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PAY_API}/getInvoices?invoice_ids={invoice_id}", headers=headers) as resp:
            result = await resp.json()
            invoice = result["result"]["items"][0]
            return invoice["status"] == "paid"


@dp.message(F.text == "/start")
async def start(message: types.Message):
    buttons = [[types.KeyboardButton(text=name)] for name in FAMILIES]
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Выбери семейство, чтобы купить пароль к архиву:", reply_markup=kb)


@dp.message(F.text.in_(FAMILIES))
async def buy(message: types.Message):
    item = FAMILIES[message.text]
    payload = item["payload"]

    invoice_id, pay_url = await create_invoice(
        asset="USDT",
        amount=item["price"],
        payload=payload,
        description=f"Покупка пароля для {message.text}"
    )

    await message.answer(f"🔐 Оплати, чтобы получить пароль к архиву:\n{pay_url}")
    await message.answer("⏳ Ожидаем оплату...")

    for _ in range(12):
        await asyncio.sleep(5)
        if await check_payment(invoice_id):
            password = PASSWORDS.get(payload, "пароль не найден")
            await message.answer(f"✅ Оплата подтверждена!\nПароль к архиву: `{password}`", parse_mode="Markdown")
            return

    await message.answer("❌ Время ожидания истекло. Если вы оплатили — нажмите /start")



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
