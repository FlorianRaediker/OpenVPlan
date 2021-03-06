#  OpenVPlan
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

import datetime
import logging
import re
from html.parser import HTMLParser
from typing import Optional, Tuple, List

from ..parsers.base import BaseMultiPageSubstitutionParser, Stream
from ..storage import Substitution, SubstitutionDay, SubstitutionGroup, SubstitutionStorage
from ..utils import get_lesson_num, simplify_class_name, split_class_name

_LOGGER = logging.getLogger("openvplan")

_REGEX_STATUS = re.compile(br"Stand: (\d\d\.\d\d\.\d\d\d\d \d\d:\d\d)")
_REGEX_TITLE = re.compile(r"(\d+.\d+.\d\d\d\d) (\w+), Woche (\w+)")
_REGEX_NEXT_SITE = re.compile(r"\d+; URL=subst_(\d\d\d)\.htm")


class SubstitutionsTooOldException(Exception):
    pass


class FoundNextSite(Exception):
    def __init__(self, next_site):
        self.next_site = next_site


class DidNotFindNextSiteException(Exception):
    pass


class UntisSubstitutionParser(HTMLParser, BaseMultiPageSubstitutionParser):
    # some of the tags from https://developer.mozilla.org/en-US/docs/Web/HTML/Element#inline_text_semantics and
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element#inline_text_semantics
    ALLOWED_NEWS_FORMATTING_TAGS = ("b", "code", "em", "i", "kbd", "mark", "s", "small", "strong", "sub", "sub", "u",
                                    "big", "blink", "center", "strike", "tt")

    @staticmethod
    async def get_status(text: bytes) -> Tuple[str, datetime.datetime]:
        status = _REGEX_STATUS.search(text)
        if status:
            status = status.group(1).decode()
            return status, datetime.datetime.strptime(status, "%d.%m.%Y %H:%M")
        raise ValueError(f"Did not find status in {repr(text)}")

    def __init__(self, storage: SubstitutionStorage, current_date: datetime.date, stream: Stream, site_num: int,
                 encoding: str = "utf-8",
                 group_name_column: int = 0, lesson_column: int = None, class_column: int = None,
                 group_name_is_class: bool = True, affected_groups_columns: List[int] = None):
        HTMLParser.__init__(self)
        BaseMultiPageSubstitutionParser.__init__(self, storage, current_date, stream, site_num)
        self._is_parsing_until_next_site = False
        self._encoding = encoding
        self._group_name_column = group_name_column
        self._lesson_column = lesson_column
        self._class_column = class_column
        self._group_name_is_class = group_name_is_class
        self._affected_groups_columns = affected_groups_columns
        self._current_substitution_day: Optional[SubstitutionDay] = None

        self._has_read_news_heading = False
        self._current_section = ""
        self._current_substitution = []
        self._current_strikes = []
        self._reached_news = False
        self._is_in_tag = False
        self._is_in_td = False
        self._is_in_strike = False
        self._current_news_format_tag = None
        self._current_day_info = None

    async def parse_next_site(self) -> str:
        self._is_parsing_until_next_site = True
        try:
            while True:
                r = (await self._stream.readany()).decode(self._encoding)
                if not r:
                    raise DidNotFindNextSiteException()
                try:
                    self.feed(r)
                except FoundNextSite as e:
                    next_site: str = e.next_site
                    if len(next_site) != 3 or not next_site.isdigit():
                        raise DidNotFindNextSiteException(next_site)
                    return next_site
        except Exception as e:
            _LOGGER.error(f"{self._site_num} Exception while parsing")
            raise e

    async def parse(self):
        self._is_parsing_until_next_site = False
        try:
            # parse anything that is buffered because parse_next_site exits without parsing further than
            # <meta http-equiv="refresh" ...>:
            self.goahead(False)
            while True:
                r = (await self._stream.readany()).decode(self._encoding)
                if not r:
                    return
                self.feed(r)
        except SubstitutionsTooOldException:
            _LOGGER.debug(f"{self._site_num} is outdated, skipping")
            return
        except Exception as e:
            _LOGGER.error(f"{self._site_num} Exception while parsing")
            raise e

    def on_new_substitution_start(self):
        self._current_substitution = []
        self._current_strikes = []

    def handle_starttag(self, tag, attrs):
        if self._is_parsing_until_next_site and \
                tag == "meta" and attrs[0] == ("http-equiv", "refresh") and attrs[1][0] == "content":
            match = _REGEX_NEXT_SITE.fullmatch(attrs[1][1])
            if match is None:
                raise DidNotFindNextSiteException(attrs[1][1])
            raise FoundNextSite(match.group(1))
        if tag == "td":
            self._is_in_td = True
            if self._current_section == "info-table" and \
                    (self._reached_news or attrs == [("class", "info"), ("colspan", "2")]):
                self._reached_news = True
                self._current_substitution_day.news.append("")
        elif tag == "tr":
            if self._current_section == "substitution-table":
                self.on_new_substitution_start()
        elif tag == "table":
            if len(attrs) == 1 and attrs[0][0] == "class":
                if attrs[0][1] == "info":
                    self._current_section = "info-table"
                elif attrs[0][1] == "mon_list":
                    self._current_section = "substitution-table"
        elif tag == "div":
            if len(attrs) == 1 and attrs[0] == ("class", "mon_title"):
                self._current_section = "title"
        elif self._current_section == "info-table" and self._is_in_td and self._reached_news:
            if tag == "br":
                self._current_substitution_day.news.append("")
            elif tag in self.ALLOWED_NEWS_FORMATTING_TAGS:
                self._current_substitution_day.news[-1] += "<" + tag + ">"
        elif tag == "strike":
            self._is_in_strike = True
        self._is_in_tag = True

    def handle_endtag(self, tag):
        if self._is_parsing_until_next_site and tag == "head":
            raise DidNotFindNextSiteException()
        if self._current_section == "substitution-table":
            if tag == "tr" and self._current_substitution:
                subs_data = self._current_substitution
                striked = self._current_strikes[0]
                self._current_substitution = None
                self._current_strikes = None
                if len(subs_data) == 1 and subs_data[0] == "Keine Vertretungen":
                    return
                group_id = (subs_data[self._group_name_column].strip(), striked)
                if self._class_column is not None:
                    subs_data[self._class_column] = simplify_class_name(subs_data[self._class_column])
                if self._lesson_column:
                    lesson_num = get_lesson_num(subs_data[self._lesson_column])
                else:
                    lesson_num = None
                del subs_data[self._group_name_column]
                substitution = Substitution(tuple(subs_data), lesson_num, self._group_name_is_class, self._affected_groups_columns)
                if (group := self._current_substitution_day.get_group(group_id)) is not None:
                    group.substitutions.append(substitution)
                else:
                    self._current_substitution_day.add_group(
                        SubstitutionGroup(group_id[0], group_id[1], [substitution], self._group_name_is_class))
        if tag == "td":
            self._is_in_td = False
        elif self._is_in_td and self._current_section == "info-table" and self._reached_news:
            if tag in self.ALLOWED_NEWS_FORMATTING_TAGS:
                self._current_substitution_day.news[-1] += "</" + tag + ">"
        elif tag == "strike":
            self._is_in_strike = False
        self._is_in_tag = False

    def handle_data(self, data):
        if self._is_in_tag and self._current_section == "substitution-table":
            self.handle_substitution_data(data)
        elif self._current_section == "info-table":
            if self._is_in_td:
                if not self._reached_news:
                    if self._current_day_info:
                        self._current_substitution_day.info.append((self._current_day_info, data))
                        self._current_day_info = None
                    else:
                        self._current_day_info = data.strip()
                        if self._current_day_info == "Nachrichten zum Tag":
                            self._current_day_info = None
                else:
                    self._current_substitution_day.news[-1] += data
        elif self._current_section == "title":
            match = _REGEX_TITLE.search(data)
            if match:
                datestr = match.group(1)
                date = datetime.datetime.strptime(datestr, "%d.%m.%Y").date()
                if date < self._current_date:
                    raise SubstitutionsTooOldException
                if self._storage.has_day(date):
                    self._current_substitution_day = self._storage.get_day(date)
                else:
                    self._current_substitution_day = SubstitutionDay(date,
                                                                     match.group(2), datestr,
                                                                     match.group(3))
                    self._storage.add_day(self._current_substitution_day)
                self._current_section = None
            else:
                raise ValueError("no date detected in title")

    def handle_substitution_data(self, data):
        if self._is_in_td:
            self._current_substitution.append(data.strip())
            self._current_strikes.append(self._is_in_strike)

    def error(self, message):
        pass
