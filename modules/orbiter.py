import random
from typing import Union

import aiohttp
from loguru import logger

from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account
from config import ORBITER_MAKER, RPC
from typing import List
from web3 import Web3
from eth_account import Account as EthereumAccount


class Orbiter(Account):
    def __init__(self, account_id: int,
                 private_key: str,
                 chains: List[str],
                 proxy: Union[None, str],
                 min_required_amount: float) -> None:
        chains_with_balance = self.find_balance(chains, private_key, min_required_amount)
        super().__init__(account_id=account_id, private_key=private_key, proxy=proxy, chain=chains_with_balance[0])

        self.chain_ids = {
            "ethereum": "1",
            "arbitrum": "42161",
            "optimism": "10",
            "zksync": "324",
            "nova": "42170",
            "zkevm": "1101",
            "scroll": "534352",
            "base": "8453",
            "linea": "59144",
            "zora": "7777777",
        }

        self.orbiter_ids = {
            'ethereum': '1',
            'optimism': '7',
            'bsc': '15',
            'arbitrum': '2',
            'nova': '16',
            'polygon': '6',
            'polygon_zkevm': '17',
            'zksync': '14',
            'zksync_lite': '3',
            'starknet': '4',
            'linea': '23',
            'base': '21',
            'mantle': '24',
            'scroll': '19',
            'zora': '30',
        }

    @retry
    async def get_bridge_amount(self, from_chain: str, to_chain: str, amount: float):
        url = "https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47"

        data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_calculatedAmount",
            "params": [f"{self.chain_ids[from_chain]}-{self.chain_ids[to_chain]}:ETH-ETH", float(amount)]
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=url,
                headers={"Content-Type": "application/json"},
                json=data,
            )

            response_data = await response.json()

            if response_data.get("result").get("error", None) is None:
                return int(response_data.get("result").get("_sendValue"))

            else:
                error_data = response_data.get("result").get("error")

                logger.error(f"[{self.account_id}][{self.address}] Orbiter error | {error_data}")

                return False

    def find_balance(self, chains, private_key, min_required_amount):
        chains_with_balance = []
        for chain in chains:
            self.w3 = Web3(
                Web3.HTTPProvider(random.choice(RPC[chain]["rpc"])),
            )
            account = EthereumAccount.from_key(private_key)
            balance_wei = self.w3.eth.get_balance(self.w3.to_checksum_address(account.address))
            balance = self.w3.from_wei(balance_wei, 'ether')
            if balance >= min_required_amount:
                chains_with_balance.append((chain, balance))
        if not chains_with_balance:
            raise ValueError('No chains with required balance! Change min_required_amount!')
        chains_with_balance.sort(key=lambda x: x[1], reverse=True)
        chains_with_balance = [chain for chain, balance in chains_with_balance]
        return chains_with_balance

    @retry
    @check_gas
    async def bridge(
            self,
            destination_chain: str,
            min_amount: float,
            max_amount: float,
            decimal: int,
            all_amount: bool,
            min_percent: int,
            max_percent: int,
            save_funds: List[float]
    ):
        amount_wei, amount, balance = await self.get_amount(
            "ETH",
            min_amount,
            max_amount,
            decimal,
            all_amount,
            min_percent,
            max_percent
        )

        from_chain_id = self.orbiter_ids[self.chain]
        to_chain_id = self.orbiter_ids[destination_chain]
        maker_x_maker = f'{from_chain_id}-{to_chain_id}'

        contract = ORBITER_MAKER[maker_x_maker]['ETH-ETH']['makerAddress']

        if all_amount:
            save_funds = Web3.from_wei(Web3.to_wei(random.uniform(*save_funds), 'ether'), 'ether')
            amount -= save_funds

        logger.info(
            f"[{self.account_id}][{self.address}] Bridge {self.chain} –> {destination_chain} | {amount} ETH"
        )

        bridge_amount = await self.get_bridge_amount(self.chain, destination_chain, amount)

        if bridge_amount is False:
            return

        balance = await self.w3.eth.get_balance(self.address)

        if bridge_amount > balance:
            logger.error(f"[{self.account_id}][{self.address}] Insufficient funds!")
        else:
            tx_data = await self.get_tx_data(bridge_amount)
            tx_data.update({"to": self.w3.to_checksum_address(contract)})

            signed_txn = await self.sign(tx_data)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
