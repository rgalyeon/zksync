import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import count

import questionary
from loguru import logger
from questionary import Choice

from modules_settings import *
from utils.helpers import remove_wallet
from utils.sleeping import sleep
from utils.logs_handler import filter_out_utils
from utils.password_handler import get_wallet_data
from settings import (
    USE_PROXY,
    RANDOM_WALLET,
    SLEEP_FROM,
    SLEEP_TO,
    QUANTITY_THREADS,
    THREAD_SLEEP_FROM,
    THREAD_SLEEP_TO, REMOVE_WALLET
)


def get_module():
    counter = count(1)
    result = questionary.select(
        "Select a method to get started",
        choices=[
            Choice(f"{next(counter)}) Encrypt private keys and proxies", encrypt_privates),
            Choice(f"{next(counter)}) Make deposit from OKX", withdraw_okx),
            Choice(f"{next(counter)}) Make bridge ZkSync", bridge_zksync),
            Choice(f"{next(counter)}) Make withdraw from ZkSync", withdraw_zksync),
            Choice(f"{next(counter)}) Make bridge on Orbiter", bridge_orbiter),
            Choice(f"{next(counter)}) Wrap ETH", wrap_eth),
            Choice(f"{next(counter)}) Unwrap ETH", unwrap_eth),
            Choice(f"{next(counter)}) Make swap on SyncSwap", swap_syncswap),
            Choice(f"{next(counter)}) Add liquidity on SyncSwap", liquidity_syncswap),
            Choice(f"{next(counter)}) Make swap on Mute", swap_mute),
            Choice(f"{next(counter)}) Make swap on Space.fi", swap_spacefi),
            Choice(f"{next(counter)}) Add liquidity on Space.fi", liquidity_spacefi),
            Choice(f"{next(counter)}) Make swap on PancakeSwap", swap_pancake),
            Choice(f"{next(counter)}) Make swap on WooFi", swap_woofi),
            Choice(f"{next(counter)}) Make swap on Odos", swap_odos),
            Choice(f"{next(counter)}) Make swap on ZkSwap", swap_zkswap),
            Choice(f"{next(counter)}) Make swap on XYSwap", swap_xyswap),
            Choice(f"{next(counter)}) Make swap on OpenOcean", swap_openocean),
            Choice(f"{next(counter)}) Make swap on 1inch", swap_inch),
            Choice(f"{next(counter)}) Make swap on Maverick", swap_maverick),
            Choice(f"{next(counter)}) Make swap on VeSync", swap_vesync),
            Choice(f"{next(counter)}) Make bungee refuel", bungee_refuel),
            Choice(f"{next(counter)}) Stargate bridge MAV", stargate_bridge),
            Choice(f"{next(counter)}) Deposit Eralend", deposit_eralend),
            Choice(f"{next(counter)}) Withdraw Eralend", withdraw_erlaned),
            Choice(f"{next(counter)}) Enable collateral on Eralend", enable_collateral_eralend),
            Choice(f"{next(counter)}) Disable collateral on Eralend", disable_collateral_eralend),
            Choice(f"{next(counter)}) Deposit Basilisk", deposit_basilisk),
            Choice(f"{next(counter)}) Withdraw Basilisk", withdraw_basilisk),
            Choice(f"{next(counter)}) Enable collateral on Basilisk", enable_collateral_basilisk),
            Choice(f"{next(counter)}) Disable collateral on Basilisk", disable_collateral_basilisk),
            Choice(f"{next(counter)}) Deposit ReactorFusion", deposit_reactorfusion),
            Choice(f"{next(counter)}) Withdraw ReactorFusion", withdraw_reactorfusion),
            Choice(f"{next(counter)}) Enable collateral on ReactorFusion", enable_collateral_reactorfusion),
            Choice(f"{next(counter)}) Disable collateral on ReactorFusion", disable_collateral_reactorfusion),
            Choice(f"{next(counter)}) Deposit ZeroLend", deposit_zerolend),
            Choice(f"{next(counter)}) Withdraw ZeroLend", withdraw_zerolend),
            Choice(f"{next(counter)}) Mint ZkStars NFT", mint_zkstars),
            Choice(f"{next(counter)}) Create NFT collection on Omnisea", create_omnisea),
            Choice(f"{next(counter)}) Mint and bridge NFT L2Telegraph", bridge_nft),
            Choice(f"{next(counter)}) Mint Tavaera ID + NFT", mint_tavaera),
            Choice(f"{next(counter)}) Mint MailZero NFT", mint_mailzero_nft),
            Choice(f"{next(counter)}) Mint NFT on NFTS2ME", mint_nft),
            Choice(f"{next(counter)}) Mint ZKS Domain", mint_zks_domain),
            Choice(f"{next(counter)}) Mint Era Domain", mint_era_domain),
            Choice(f"{next(counter)}) Send message L2Telegraph", send_message),
            Choice(f"{next(counter)}) Dmail sending mail", send_mail),
            Choice(f"{next(counter)}) Create gnosis safe", create_safe),
            Choice(f"{next(counter)}) Owlto daily check in", owlto_check_in),
            Choice(f"{next(counter)}) Swap tokens to ETH", swap_tokens),
            Choice(f"{next(counter)}) MultiSwap", swap_multiswap),
            Choice(f"{next(counter)}) Use custom routes", custom_routes),
            Choice(f"{next(counter)}) Use automatic routes", automatic_routes),
            Choice(f"{next(counter)}) MultiApprove", multi_approve),
            Choice(f"{next(counter)}) Check transaction count", "tx_checker"),
            Choice(f"{next(counter)}) Exit", "exit"),
        ],
        qmark="⚙️ ",
        pointer="✅ "
    ).ask()
    if result == "exit":
        print("❤️ Project author – https://t.me/sybilwave\n")
        print("❤️ Fork author – https://t.me/rgalyeon\n")
        sys.exit()
    return result


def get_wallets():
    wallet_data = get_wallet_data()

    accounts, proxies = [], []
    for wallet, data in wallet_data.items():
        accounts.append(data['private_key'])
        proxies.append(data['proxy'])
    if USE_PROXY:
        account_with_proxy = dict(zip(accounts, proxies))

        wallets = [
            {
                "id": _id,
                "key": key,
                "proxy": account_with_proxy[key]
            } for _id, key in enumerate(account_with_proxy, start=1)
        ]
    else:
        wallets = [
            {
                "id": _id,
                "key": key,
                "proxy": None
            } for _id, key in enumerate(accounts, start=1)
        ]
    return wallets


async def run_module(module, account_id, key, proxy):
    try:
        await module(account_id, key, proxy)
    except Exception as e:
        logger.error(e)

    if REMOVE_WALLET:
        remove_wallet(key)

    await sleep(SLEEP_FROM, SLEEP_TO)


def _async_run_module(module, account_id, key, recipient):
    asyncio.run(run_module(module, account_id, key, recipient))


def main(module):
    if module == encrypt_privates:
        return encrypt_privates(force=True)
    wallets = get_wallets()

    if RANDOM_WALLET:
        random.shuffle(wallets)

    with ThreadPoolExecutor(max_workers=QUANTITY_THREADS) as executor:
        for _, account in enumerate(wallets, start=1):
            executor.submit(
                _async_run_module,
                module,
                account.get("id"),
                account.get("key"),
                account.get("proxy")
            )
            time.sleep(random.randint(THREAD_SLEEP_FROM, THREAD_SLEEP_TO))


if __name__ == '__main__':
    print("❤️ Project author – https://t.me/sybilwave\n")
    print("❤️ Fork author – https://t.me/rgalyeon\n")

    logger.add('logs.txt', filter=filter_out_utils)

    module = get_module()
    if module == "tx_checker":
        get_tx_count()
    else:
        main(module)

    print("ALL DONE!")
