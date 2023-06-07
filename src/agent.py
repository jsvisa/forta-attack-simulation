from web3 import Web3, HTTPProvider
from forta_agent import get_json_rpc_url, TransactionEvent

from src.logger import logger
from src.contract import CreatedContract

web3 = Web3(HTTPProvider(get_json_rpc_url()))


def initialize():
    logger.info("finish initialize")


def handle_created_contract(contract: CreatedContract):
    pass


def provide_handle_transaction(w3: Web3):
    def handle_transaction(tx_event: TransactionEvent):
        return

    return handle_transaction


real_handle_transaction = provide_handle_transaction(web3)


def handle_transaction(tx_event: TransactionEvent):
    return real_handle_transaction(tx_event)
