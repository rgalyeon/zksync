import asyncio
import traceback

from . import ZkSync
from config import OKX_API_INFO
from loguru import logger
import random

import ccxt.async_support as ccxt_async
import math
import re
from utils.helpers import retry


class Okx(ZkSync):

    def __init__(self, _id: int, private_key: str, proxy, chain) -> None:
        super().__init__(account_id=_id, private_key=private_key, proxy=proxy, chain=chain)
        self.api_info = OKX_API_INFO

    async def get_ccxt(self):
        exchange_config = self.api_info
        exchange_options = {
            'apiKey': exchange_config['apiKey'],
            'secret': exchange_config['secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        }

        if 'password' in exchange_config:
            exchange_options['password'] = exchange_config['password']

        if exchange_config.get('proxy_url'):
            exchange_options['proxies'] = {
                'http': exchange_config['proxy_url'],
                'https': exchange_config['proxy_url'],
            }

        exchange_class = getattr(ccxt_async, "okx")
        exchange = exchange_class(exchange_options)

        return exchange

    @staticmethod
    def smart_round(number):
        if isinstance(number, (int, float)):
            abs_num = abs(number)
            if abs_num == 0:
                return 0
            elif abs_num >= 1:
                return round(number, 2)
            elif 0 < abs_num < 1e-4:
                return "{:.8f}".format(number)
            else:
                return round(number, 3 - int(math.floor(math.log10(abs_num)) + 1))
        else:
            raise ValueError("    Функция принимает только числа (целые и с плавающей точкой) [function smart_round]")

    async def okx_get_withdrawal_info(self, exchange, token):
        currencies = await exchange.fetch_currencies()

        networks = []
        network_data = {}

        if currencies is not None:
            for currency_code, currency in currencies.items():
                if currency_code == token.upper():
                    networks_info = currency.get('networks')
                    if networks_info is not None:
                        for network, network_info in networks_info.items():

                            fee = network_info.get('fee')
                            if fee is not None:
                                fee = float(fee)
                                fee = self.smart_round(fee)

                            min_withdrawal = network_info.get('limits', {}).get('withdraw', {}).get('min')
                            if min_withdrawal is not None:
                                min_withdrawal = float(min_withdrawal)

                            id = network_info.get('id')
                            is_withdraw_enabled = network_info.get('withdraw', False)

                            if is_withdraw_enabled:
                                network_data[network] = (id, fee, min_withdrawal)
                                networks.append(network)
                    else:
                        raise ValueError(f"Currency {currency_code} doesn't contain 'networks' attribute")
        else:
            raise ValueError("Currencies not found")

        return networks, network_data

    @retry
    async def okx_withdraw(self, min_amount, max_amount, token_name, network, terminate=True):
        amount = round(random.uniform(min_amount, max_amount), 8)

        logger.info(f'[{self.account_id}][{self.address}] Start withdrawal from OKX {amount} {token_name}')
        curr_balance = await self.w3.eth.get_balance(self.address)

        exchange = await self.get_ccxt()
        networks, networks_data = await self.okx_get_withdrawal_info(exchange, token_name)

        if network not in networks:
            raise ValueError(f'Cannot withdraw token {token_name} to {network} chain')
        okx_network_name, fee, min_withdrawal = networks_data[network]
        pattern = "^[^-]*-"
        network_name = re.sub(pattern, "", okx_network_name)
        try:
            await exchange.withdraw(token_name, amount, self.address,
                                    params={
                                        "chainName": okx_network_name,
                                        "fee": fee,
                                        "pwd": '-',
                                        "amt": self.smart_round(amount),
                                        "network": network_name,
                                    })
        except Exception as e:
            logger.error(f'Error {e} in withdrawal. Try to change min amount.')
            traceback.print_exc()
            if terminate:
                exit()

        logger.info(f'Transaction sent. Waiting money from OKX')
        while curr_balance == await self.w3.eth.get_balance(self.address):
            await asyncio.sleep(60)

        logger.success(f'[{self.account_id}][{self.address}] Successfully withdrawn {amount} {token_name} ')
        await exchange.close()
