import asyncio
import random
from urllib.parse import unquote
from time import time

import aiohttp
import json
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers

class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.peer_name = 'TonTetherBot'
        self.peer_url = 'https://tontether03082024.pages.dev/'
        self.tg_client = tg_client
        self.user_id = 0
        self.username = None

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer(self.peer_name)
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    fls *= 2
                    logger.info(f"{self.session_name} | FloodWait Sleep {fls}s")
                    await asyncio.sleep(fls)

            try:
                web_view = await self.tg_client.invoke(RequestWebView(
                    peer=peer,
                    bot=peer,
                    platform='android',
                    from_bot_menu=False,
                    url=self.peer_url
                ))
            except Exception as e:
                logger.error(f"{self.session_name} | Error invoking RequestWebView: {e}")
                raise

            try:
                auth_url = web_view.url
                tg_web_data = unquote(
                    string=unquote(
                        string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))
            except Exception as e:
                logger.error(f"{self.session_name} | Error parsing auth_url: {e}")
                raise

            self.user_id = (await self.tg_client.get_me()).id

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=30)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")
            await asyncio.sleep(delay=30)

    async def auth(self, http_client: aiohttp.ClientSession):
        try:
            auth_url = 'https://tontether.click/user/me'

            response = await http_client.get(url=auth_url)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Login  Error: {error} ")
            await asyncio.sleep(delay=30)

    async def config(self, http_client: aiohttp.ClientSession):
        try:
            auth_url = 'https://tontether.click/config'

            response = await http_client.get(url=auth_url)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Config  Error: {error} ")
            await asyncio.sleep(delay=30)

    async def clicks_collect(self, http_client: aiohttp.ClientSession, clicks):
        try:
            clicks_collect_url = "https://tontether.click/user/click"
            json_data = {'click_count': clicks, 'at': int(time()*1000)}

            response = await http_client.post(url=clicks_collect_url, json=json_data)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Clicks Collect: {error} ")
            await asyncio.sleep(delay=30)
            return False

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        tg_web_data = await self.get_tg_web_data(proxy=proxy)

        while True:
            try:
                #Variables
                random_sleep = random.randint(*settings.RANDOM_SLEEP)
                sleep_by_min_clicks = random.randint(*settings.SLEEP_BY_MIN_CLICKS)
                sleep_between_tap = random.randint(*settings.SLEEP_BETWEEN_TAP)

                if not tg_web_data:
                    continue

                if http_client.closed:
                    http_client = CloudflareScraper(headers=headers)

                if time() - access_token_created_time >= 3600:
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    http_client.headers["authorization"] = f"Bearer {tg_web_data}"
                    access_token_created_time = time()
                    await asyncio.sleep(delay=random_sleep)

                auth_data = await self.auth(http_client=http_client)

                auth_username = auth_data['data']['username']
                auth_clicks = auth_data['data']['last_remaining_clicks']
                auth_usdt_balance = auth_data['data']['usdt_balance']
                auth_tap_balance = auth_data['data']['tap_balance']

                logger.success(f"{self.session_name} | Auth username: <c>{auth_username}</c> | "
                               f"Balance: <g>{auth_usdt_balance:.2f}</g> usdt, <g>{auth_tap_balance:.2f}</g> xsdt")

                taps = random.randint(1,5)
                clicks_data = await self.clicks_collect(http_client=http_client, clicks=taps)
                auth_clicks = clicks_data['data']['last_remaining_clicks']
                logger.success(f"{self.session_name} | bot action: <red>[tap/{taps}]</red> clicks: <c>{auth_clicks}/1000</c> | sleep: {sleep_between_tap}s")
                await asyncio.sleep(delay=sleep_between_tap)

                while auth_clicks > settings.MIN_AVAILABLE_CLICKS:
                    taps = random.randint(*settings.RANDOM_TAPS_COUNT)
                    sleep_between_tap = random.randint(*settings.SLEEP_BETWEEN_TAP)

                    clicks_data = await self.clicks_collect(http_client=http_client, clicks=taps)

                    if clicks_data:
                        auth_clicks = clicks_data['data']['last_remaining_clicks']
                        logger.success(f"{self.session_name} | bot action: <red>[tap/{taps}]</red> clicks: <c>{auth_clicks}/1000</c> | sleep: {sleep_between_tap}s")
                        await asyncio.sleep(delay=sleep_between_tap)
                    else:
                        logger.error(f"{self.session_name} | Click error :( ")
                else:
                    taps = auth_clicks
                    clicks_data = await self.clicks_collect(http_client=http_client, clicks=taps)
                    auth_clicks = clicks_data['data']['last_remaining_clicks']
                    logger.success(
                        f"{self.session_name} | bot action: <red>[tap/{taps}]</red> clicks: <c>{auth_clicks}/1000</c>")

                logger.info(f"{self.session_name} | Minimum energy reached: {auth_clicks}")
                logger.info(f"{self.session_name} | Sleep {sleep_by_min_clicks:,}s")
                await asyncio.sleep(delay=sleep_by_min_clicks)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                access_token_created_time = 0
                await http_client.close()
                await asyncio.sleep(delay=300)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
