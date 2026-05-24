async def main():
    try:
        print("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"ОШИБКА: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
