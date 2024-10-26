import os
import time
import project
import datetime
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters


token = "8107598303:AAHQtgnHx3XiTH8HGLX_O5A47q-kWuIwix8"


async def start_command(update, context):
    await update.message.reply_text("Для проверки выполнения задания отправьте документ в расширении .pdf. \nК сожалению, телеграм устанавливает ограничение для ботов на скачивание файлов размером больше 20 мб.\nДокументы большего размера Вы можете проверить с помощью кода, представленного в репозитории.")


async def downloader(update, context):
    print(datetime.datetime.now())
    with open("users.txt", 'a') as f:
        f.write(f"{update.message.chat.first_name} {update.message.chat.last_name}, {update.message.chat.username}, {datetime.datetime.now()}\n")
    print(update.message.chat.first_name, update.message.chat.last_name, ",", update.message.chat.username)
    file_id = update.message.document.file_id
    new_file = await context.bot.get_file(file_id)
    output_file_name = new_file.file_path.split("/")[-1]
    if ".pdf" in output_file_name:
        await update.message.reply_text("Файл принят в обработку")
        try:
            file_name = new_file.file_id
            await new_file.download_to_drive(file_name)
            start = time.time()
            output_file_name = new_file.file_path.split("/")[-1]
            project.make_table_of_contents(file_name, output_file_name)
            print(time.time() - start)
            chat_id = update.message.chat_id
            document = open(output_file_name, 'rb')
            await update.message.reply_text("Обработанный документ")
            await context.bot.send_document(chat_id, document,)
            os.remove(output_file_name)
            os.remove(file_name)
        except Exception as err:
            await update.message.reply_text(err)
            

application = ApplicationBuilder().token(token).build()
application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.ATTACHMENT, downloader))

application.run_polling()
