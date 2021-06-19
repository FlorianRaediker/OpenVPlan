import datetime
import io
from abc import ABC, abstractmethod
from typing import Tuple, Union

from aiohttp import StreamReader

from subs_crawler.storage import SubstitutionStorage


class AsyncBytesIOWrapper(io.BytesIO):
    async def readline(self, **kwargs):
        return super().readline(**kwargs)

    async def readany(self):
        return super().read()


Stream = Union[StreamReader, AsyncBytesIOWrapper]


class BaseSubstitutionParser(ABC):
    """ Base class for all substitution parsers. """

    @staticmethod
    @abstractmethod
    async def get_status(data: bytes) -> Tuple[str, datetime.datetime]:
        """ Return the status of the data in original format and in parsed format (datetime). """
        ...

    @abstractmethod
    def __init__(self, storage: SubstitutionStorage, current_timestamp: int, stream: Stream, **kwargs):
        self._storage = storage
        self._current_timestamp = current_timestamp
        self._stream = stream

    @abstractmethod
    async def parse(self):
        """ Parse the data provided by stream. """
        ...


class BaseMultiPageSubstitutionParser(BaseSubstitutionParser):
    """
    Base class for substitution parsers that
      1. work with a substitution plan which consists of an unknown number of sites and
      2. where you can determine from one site which site comes next.

    An instance of a subclass of this class is always used to parse a single site only.
    """
    @abstractmethod
    def __init__(self, storage: SubstitutionStorage, current_timestamp: int, stream: Stream, site_num: int, **kwargs):
        super().__init__(storage, current_timestamp, stream)
        self._site_num = site_num

    @abstractmethod
    async def parse_next_site(self) -> str:
        ...