import logging
from typing import Optional, List, Union
from hexbytes.main import HexBytes
from eth_abi.abi import encode_single
from ethereum_dasm.evmdasm import EvmCode, Contract
from brownie.network.rpc import Rpc
from brownie.network.web3 import web3
from web3 import HTTPProvider

# ref https://github.com/blockchain-etl/ethereum-etl/pull/267
logging.getLogger("ethereum_dasm.evmdasm").setLevel(logging.ERROR)
logging.getLogger("evmdasm.disassembler").setLevel(logging.FATAL)


def get_sighashes(bytecode: Optional[Union[str, HexBytes]]) -> List[str]:
    bytecode = clean_bytecode(bytecode)
    if bytecode is None:
        return []

    evm_code = EvmCode(
        contract=Contract(bytecode=bytecode),
        static_analysis=False,
        dynamic_analysis=False,
    )
    evm_code.disassemble(bytecode)
    basic_blocks = evm_code.basicblocks

    # store from https://github.com/blockchain-etl/ethereum-etl/pull/282
    push4_instructions = set()
    for block in basic_blocks:
        for inst in block.instructions:
            if inst.name == "PUSH4":
                push4_instructions.add("0x" + inst.operand)
    return sorted(push4_instructions)


class BaseN:
    def __init__(self, elements, word_count):
        self.elements = elements
        self.word_count = word_count
        self.indices = [0] * len(elements)

    def __iter__(self):
        return self

    def __next__(self):
        if self.word_count == 0:
            raise StopIteration

        result = []
        for i in range(self.word_count):
            result.append(self.elements[self.indices[i]])

        self.indices[-1] += 1

        for i in reversed(range(self.word_count - 1)):
            if self.indices[i] == len(self.elements[i]):
                self.indices[i] = 0
                self.indices[i - 1] += 1

        return result


def gen_calldata(word_count: int, addresses: List[str]):
    if word_count == 0:
        yield ""
    else:
        params = [
            encode_single("uint256", 0),
            encode_single("uint256", 1),
            encode_single("uint256", 10_000),
            encode_single("uint256", 1_000_000),
            encode_single("uint256", 10**22),
            *([encode_single("address", address) for address in addresses]),
        ]
        params = [p.hex() for p in params]

        it = BaseN(params, word_count)

        for group in it:
            yield "".join(group)


def clean_bytecode(bytecode: Optional[Union[str, HexBytes]]) -> Optional[str]:
    if isinstance(bytecode, HexBytes):
        bytecode = bytecode.hex()

    if bytecode is None or bytecode == "0x":
        return None
    elif bytecode.startswith("0x"):
        return bytecode[2:]
    else:
        return bytecode


def get_ethers_fork_provider(
    fork_url: str, blknum: int, addresses: List[str], network_id: int
) -> Rpc:
    cmd = "anvil"
    # https://github.com/eth-brownie/brownie/blob/master/brownie/network/rpc/anvil.py#L14
    kwargs = dict(
        host="0.0.0.0",
        port=8545,
        fork=fork_url,
        fork_block=blknum,
        chain_id=network_id,
    )
    rpc: Rpc = Rpc()
    # rpc.unlock will use the builtin web3
    # set web3.provider to auto connect and check the connection
    web3.provider = HTTPProvider("http://127.0.0.1:8545")
    err = rpc.launch(cmd, **kwargs)
    if err is not None:
        raise Exception(err)
    for address in addresses:
        rpc.unlock_account(address)
    return rpc
