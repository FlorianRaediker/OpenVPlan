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

import argparse
import json
import os
from functools import partial
from typing import Callable

import aiocron
import jinja2
from aiohttp import client, web
from aiojobs.aiohttp import setup, get_scheduler_from_app

import settings
import subs_crawler
from settings import settings
from website import logger
from website.db import SubstitutionPlanDB
from website.substitution_plan import RESPONSE_HEADERS, SubstitutionPlan

os.chdir(os.path.dirname(__file__))

for directory in (
    settings.DATA_DIR,
    settings.CACHE_DIR,
    os.path.dirname(settings.LOGFILE)
):
    os.makedirs(directory, exist_ok=True)


_LOGGER = logger.get_logger()

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("assets/templates"),
    bytecode_cache=jinja2.FileSystemBytecodeCache(os.path.join(settings.CACHE_DIR)),
    enable_async=True,
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
    auto_reload=settings.DEBUG
)

TEMPLATE_ABOUT = partial(env.get_template, "about.min.html")
TEMPLATE_PLAUSIBLE = partial(env.get_template, "plausible.min.html")
TEMPLATE_ERROR404 = partial(env.get_template, settings.TEMPLATE_404)
TEMPLATE_ERROR500 = partial(env.get_template, settings.TEMPLATE_500)


_CACHE_BUSTING = None

def template_static(path: str):
    global _CACHE_BUSTING
    if settings.DEBUG or _CACHE_BUSTING is None:  # always reload cache_busting.json in debug mode
        with open("assets/cache_busting.json", "r") as f:
            _CACHE_BUSTING = json.load(f)
    if path in _CACHE_BUSTING:
        return "/" + path + "?v=" + _CACHE_BUSTING[path]
    _LOGGER.warn(f"Missing cache busting parameter for '{path}'")
    return "/" + path


DEFAULT_RENDER_ARGS = {"options": settings.TEMPLATE_OPTIONS, "static": template_static}


@web.middleware
async def error_middleware(request: web.Request, handler):
    # noinspection PyBroadException
    try:
        return await handler(request)
    except web.HTTPException as e:
        if e.status == 404:
            return web.Response(text=await TEMPLATE_ERROR404().render_async(**DEFAULT_RENDER_ARGS),
                                status=404, content_type="text/html", charset="utf-8", headers=RESPONSE_HEADERS)
        raise e from None
    except Exception:
        _LOGGER.exception(f"{request.method} {request.path} Exception while handling request")
    except BaseException as e:
        _LOGGER.exception(f"{request.method} {request.path} BaseException while handling request")
        raise e
    return web.Response(text=await TEMPLATE_ERROR500().render_async(**DEFAULT_RENDER_ARGS),
                        status=500, content_type="text/html", charset="utf-8", headers=RESPONSE_HEADERS)


def template_handler(template: Callable[[], jinja2.Template], response_headers: dict = None, render_args: dict = None):
    if response_headers:
        response_headers = {**RESPONSE_HEADERS, **response_headers}
    else:
        response_headers = RESPONSE_HEADERS
    if not render_args:
        render_args = {}
    # noinspection PyUnusedLocal
    async def handler(request: web.Request):
        response = web.Response(text=await template().render_async(**DEFAULT_RENDER_ARGS, **render_args),
                                content_type="text/html", headers=response_headers)
        await response.prepare(request)
        await response.write_eof()
        return response
    return handler


def redirect_handler(location, **kwargs):
    async def handler(r):
        raise web.HTTPMovedPermanently(location, **kwargs)
    return handler


async def client_session_context(app: web.Application):
    _LOGGER.debug(f"Create ClientSession (headers: {settings.REQUEST_HEADERS})")
    session = client.ClientSession(headers=settings.REQUEST_HEADERS)
    for substitution_plan in app["substitution_plans"].values():
        substitution_plan.set_client_session(session)
    yield
    await session.close()


async def databases_context(app: web.Application):
    db = SubstitutionPlanDB(os.path.join(settings.DATA_DIR, "db.sqlite3"))
    for substitution_plan in app["substitution_plans"].values():
        substitution_plan.set_db(db)
    yield
    db.close()


async def shutdown(app):
    _LOGGER.info("Shutting down...")
    for subs_plan in app["substitution_plans"].values():
        await subs_plan.close()
    await logger.cleanup()


def get_update_subs_func(app, plan):
    async def update():
        logger.REQUEST_ID_CONTEXTVAR.set("bg-tasks")
        await plan.update_substitutions(get_scheduler_from_app(app))
    return update


async def app_factory(dev_mode, start_log_msg):
    await logger.init(settings.LOGFILE)
    _LOGGER.info(start_log_msg)

    app = web.Application(middlewares=[logger.logging_middleware, error_middleware])
    setup(app)

    app["substitution_plans"] = {}

    app.on_shutdown.append(shutdown)

    for plan_id, plan_config in settings.SUBSTITUTION_PLANS.items():
        crawler_id = plan_config["crawler"]["name"]
        try:
            crawler_class = subs_crawler.CRAWLERS[crawler_id]
        except KeyError:
            raise ValueError(f"Invalid crawler id '{crawler_id}")
        parser_id = plan_config["parser"]["name"]
        try:
            parser_class = subs_crawler.PARSERS[parser_id]
        except KeyError:
            raise ValueError(f"Invalid parser id '{parser_id}'")
        crawler_options = plan_config["crawler"].get("options", {})
        parser_options = plan_config["parser"].get("options", {})
        template_options = {**settings.TEMPLATE_OPTIONS, **plan_config.get("template_options", {}), "id": plan_id}
        crawler = crawler_class(None,  # last_version_id will be set in SubstitutionPlan.set_db
                                parser_class, parser_options, **crawler_options)
        plan = SubstitutionPlan(plan_id,
                                crawler,
                                partial(env.get_template, "substitution-plan.min.html"),
                                partial(env.get_template, "error-500-substitution-plan.min.html"),
                                {"options": template_options, "static": template_static},
                                plan_config.get("uppercase_selection", False))

        update_subs = get_update_subs_func(app, plan)
        for cron_time in plan_config.get("background_updates", []):
            aiocron.crontab(cron_time, func=update_subs)

        app.add_subapp(f"/{plan_id}/",
                       plan.create_app(os.path.abspath("assets/static/" + plan_id) if settings.DEBUG else None))

        app["substitution_plans"][plan_id] = plan

    async def root_handler(request: web.Request):
        location = f"/{settings.DEFAULT_PLAN_ID}/"
        if request.query_string:
            location += "?" + request.query_string
        raise web.HTTPPermanentRedirect(location=location)

    app.add_routes([
        web.get("/", root_handler),
        web.get("/privacy", redirect_handler("/about")),
        web.get("/about", template_handler(TEMPLATE_ABOUT, render_args={"about_html": settings.ABOUT_HTML})),
        web.get("/plausible", template_handler(TEMPLATE_PLAUSIBLE, {"X-Robots-Tag": "noindex"}))
    ])

    if settings.DEBUG:
        async def test500_handler(request: web.Request):
            if "log" in request.query:
                _LOGGER.error("Test error")
            raise ValueError
        app.add_routes([web.get("/test500", test500_handler)])

    if dev_mode:
        app.router.add_static("/", "assets/static/")

    app.cleanup_ctx.extend((client_session_context, databases_context))

    return app


def main(path, host, port, dev_mode=False):
    web.run_app(app_factory(dev_mode,
                            f"Starting server on {path if path else str(host) + ':' + str(port)} "
                            f"{' in dev mode' if dev_mode else ''}"),
                path=path, host=host, port=port, print=_LOGGER.info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gawvertretung server")
    parser.add_argument("--path")
    parser.add_argument("--host")
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.path:
        path = args.path
        host = None
        port = None
    else:
        path = None
        host = args.host if args.host else settings.HOST
        port = args.port if args.port else settings.PORT
    main(path, host, port, settings.DEBUG)
