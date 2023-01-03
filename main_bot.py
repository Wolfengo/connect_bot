from aiogram.utils import executor
from handlers import admin, client, other
from handlers.client import AlbumMiddleware
from create_bot import dp


async def on_startup(_):
    print('Бот запущен')


async def on_shutdown(_):
    print('Досвидания!')

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
other.register_handlers_other(dp)
dp.middleware.setup(AlbumMiddleware())

executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

