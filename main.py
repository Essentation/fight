import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, CRYPTO_PAY_TOKEN, PASSWORDS

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

PAY_API = "https://pay.crypt.bot/api"

FAMILIES = {
    "1_Revit_Household_Appliances (125 Families)": {
        "price": 22.0,
        "payload": "1"
    },
    "2_Kitchen_Revit_Families_Professional": {
        "price": 33.0,
        "payload": "2"
    },
    "3_Revit_Window_and_Doors_Mega_Pack": {
        "price": 18.0,
        "payload": "3"
    },
    "4_Shutters V1": {
        "price": 10.0,
        "payload": "4"
    },
    "5_Outdoor_Fur_V2": {
        "price": 5.0,
        "payload": "5"
    },
    "6_Room Dividers and Screens": {
        "price": 5.0,
        "payload": "6"
    },
    "7_Curtain Wall Facade System": {
        "price": 20.0,
        "payload": "7"
    },
    "8_2D_Residential Families_Pro": {
        "price": 12.0,
        "payload": "8"
    },
    "9_3D_Casual People": {
        "price": 8.0,
        "payload": "9"
    },
    "10_3D_Athletic People": {
        "price": 7.0,
        "payload": "10"
    },
    "11_Advanced_Stairs_and_Railing_01": {
        "price": 11.0,
        "payload": "11"
    },
    "12_Advanced_Stairs_and_Railing_02": {
        "price": 11.0,
        "payload": "12"
    },
    "13_Bathtubs_02": {
        "price": 3.0,
        "payload": "13"
    },
    "14_Accessible Bathroom Equipment": {
        "price": 5.0,
        "payload": "14"
    },
    "15_3D_Bussines People": {
        "price": 5.0,
        "payload": "15"
    },
    "16_Spa and Wellness": {
        "price": 5.0,
        "payload": "16"
    },
    "17_Structural Columns Wood": {
        "price": 5.0,
        "payload": "17"
    },
    "18_Elevator and Elevator Doors": {
        "price": 6.0,
        "payload": "18"
    },
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
