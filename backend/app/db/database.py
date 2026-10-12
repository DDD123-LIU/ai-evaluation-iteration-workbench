"""单进程目录锁、显式事务和本模块Alembic迁移。"""
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from threading import RLock

from alembic import command
from alembic.config import Config
from filelock import FileLock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


class Database:
    def __init__(self, directory: Path):
        self.directory = directory
        self.write_lock = RLock()
        self.engine = None
        self.directory_lock = None

    def start(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.directory_lock = FileLock(str(self.directory / "workbench.lock"), timeout=0)
        self.directory_lock.acquire()
        try:
            path = self.directory / "workbench.sqlite3"
            with closing(sqlite3.connect(path, autocommit=True)) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=FULL")
            self.engine = create_engine("sqlite:///" + path.as_posix(), connect_args={"autocommit": False, "check_same_thread": False, "timeout": 5})

            @event.listens_for(self.engine, "connect")
            def configure(connection, _):
                original = connection.autocommit
                connection.autocommit = True
                try:
                    connection.execute("PRAGMA foreign_keys=ON")
                    connection.execute("PRAGMA synchronous=FULL")
                finally:
                    connection.autocommit = original

            config = Config()
            config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "migrations"))
            with self.engine.begin() as connection:
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        except BaseException:
            self.stop()
            raise

    def stop(self):
        if self.engine is not None:
            self.engine.dispose()
        if self.directory_lock is not None:
            self.directory_lock.release()

    @contextmanager
    def session(self):
        with Session(self.engine) as session:
            yield session
