#  GaW-Vertretungsplan
#  Copyright (C) 2019-2021  Florian Rädiker
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from typing import Optional, Dict, Any, Union

from aiohttp import http, hdrs


class __Settings:
    VERSION = "5.0"

    PATH = None
    HOST = "0.0.0.0"
    PORT = 8080

    DEBUG = False

    DATA_DIR = "/var/lib/gawvertretung"
    CACHE_DIR = "/var/cache/gawvertretung"

    TELEGRAM_BOT_LOGGER_TOKEN: Optional[str] = None
    TELEGRAM_BOT_LOGGER_CHAT_ID: Optional[Union[int, str]] = None
    TELEGRAM_BOT_LOGGER_USE_FIXED_WIDTH: bool = False
    TELEGRAM_BOT_LOGGER_LEVEL: int = logging.WARNING

    PLAUSIBLE: dict = {
        "domain": None,
        "js": "https://plausible.io/js/plausible.js",
        "endpoint": None,
        "embed_code": ""
    }

    ENABLE_FERIEN = True
    FERIEN_START = None
    FERIEN_END = None

    PUBLIC_VAPID_KEY: Optional[str] = None
    PRIVATE_VAPID_KEY: Optional[str] = None
    VAPID_SUB: Optional[str] = None
    WEBPUSH_CONTENT_ENCODING: str = "aes128gcm"

    REQUEST_HEADERS: dict = {
        hdrs.USER_AGENT: f"Mozilla/5.0 (compatible; GaWVertretungBot/{VERSION}; "
                         f"+https://gawvertretung.florian-raediker.de) {http.SERVER_SOFTWARE}"
    }

    ADDITIONAL_CSP_DIRECTIVES = {}

    HEADERS_BLOCK_FLOC = True

    DEFAULT_PLAN_ID: Optional[str] = None

    SUBSTITUTION_PLANS: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None

    ABOUT_HTML: str = ""

    __locked = False

    def __setattr__(self, key, value):
        if self.__locked:
            raise AttributeError("Can't change setting")
        else:
            super().__setattr__(key, value)


try:
    import local_settings
except ImportError:
    pass
__Settings.__locked = True

settings = __Settings()
