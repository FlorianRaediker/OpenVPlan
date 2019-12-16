import asyncio
import json
import os
import pickle
import time
from functools import partial

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from bot.db.students import StudentDatabaseBot
from bot.db.teachers import TeacherDatabaseBot
from bot.sender.students import StudentMessageSender
from bot.sender.teachers import TeacherMessageSender
from common.db_connector import get_connection
from logging_tool import create_logger

os.chdir(os.path.abspath(os.path.dirname(__file__)))


class BotSender(FileSystemEventHandler):
    def __init__(self, bot_token_students, bot_token_teachers, connection, loop):
        self.__bot_token_students = bot_token_students
        self.__bot_token_teachers = bot_token_teachers
        self.connection_students = None
        self.connection_teachers = None
        self.connection = connection
        self.bot_students = StudentDatabaseBot(self.__bot_token_students, self.connection)
        self.bot_teachers = TeacherDatabaseBot(self.__bot_token_teachers, self.connection)
        self.sender_students = StudentMessageSender(self.bot_students, "data/sent_messages_students.json")
        self.sender_teachers = TeacherMessageSender(self.bot_teachers, "data/sent_messages_teachers.json")
        self.loop = loop

        self.last_status = None

    def on_modified(self, event):
        if event.src_path == "data/substitutions/substitutions.pickle":
            self.on_substitutions_modified()

    def on_substitutions_modified(self, *_):
        logger.info("Substitutions changed")
        try:
            with open("data/substitutions/substitutions.pickle", "rb") as f:
                status, data_students, data_teachers = pickle.load(f)
        except EOFError:
            logger.exception("Could not read substitutions.pickle, writing not finished yet")
            time.sleep(10)
            self.on_substitutions_modified()
        else:
            if status != self.last_status:
                logger.info(f"Status changed, sending messages {data_students}")
                self.last_status = status
                logger.info("set event loop")
                asyncio.set_event_loop(self.loop)
                logger.info("Starting loop")
                self.loop.run_until_complete(asyncio.gather(
                    self.sender_students.send_messages(data_students),
                    self.sender_teachers.send_messages(data_teachers)
                ))
                self.save()

    def save(self):
        if self.connection:
            self.sender_students.save_sent_messages()
            self.sender_teachers.save_sent_messages()


if __name__ == "__main__":
    logger = create_logger("bot-sender")

    with open("bot/secret.json", "r") as f:
        secret = json.load(f)

    connection = get_connection(secret)

    sender = BotSender(secret["token_students"], secret["token_teachers"], partial(get_connection, secret=secret),
                       asyncio.new_event_loop())
    observer = Observer()
    observer.schedule(sender, "data/substitutions")
    observer.start()
    try:
        i = 0
        while True:
            i += 1
            if i == 5:
                i = 0
                logger.debug("Waiting...")
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
else:
    import logging

    logger = logging.getLogger()
