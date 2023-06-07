class CreatedContract:
    def __init__(
        self,
        address: str,
        deployer: str,
        block_number: int,
        timestamp: int,
        tx_hash: str,
    ):
        self.address = address
        self.deployer = deployer
        self.block_number = block_number
        self.timestamp = timestamp
        self.tx_hash = tx_hash


def handle_contract(created_contract):
    provider = get_ethers_fork_provider(
        created_contract.block_number, [created_contract.deployer]
    )
    contract_code = provider.get_code(
        created_contract.address, created_contract.block_number
    )
    signer = provider.get_signer(created_contract.deployer)
    sighashes = get_sighashes(contract_code)

    timestamp = provider.get_block(created_contract.block_number).timestamp

    for value in [10 * 1e18, 0]:
        for sighash in sighashes:
            program_counter = -1
            is_signature_found = False
            for word_count in range(5):
                for calldata in gen_calldata(
                    word_count=word_count, addresses=[created_contract.deployer]
                ):
                    try:
                        tx = signer.send_transaction(
                            to=created_contract.address,
                            data=sighash + calldata,
                            value=value,
                        )
                        receipt = tx.wait()
                        if not is_signature_found:
                            is_signature_found = True

                        (
                            interfaces_by_token_address,
                            total_balance_changes_by_address,
                        ) = get_total_balance_changes(tx, receipt, provider)

                        if (
                            len(total_balance_changes_by_address) == 2
                            and total_balance_changes_by_address[
                                created_contract.address
                            ]
                            and total_balance_changes_by_address[
                                created_contract.deployer
                            ]
                        ):
                            ...

                    except Exception as e:
                        if not e.data.program_counter:
                            logger.warn("handle_contract error", e)
                            return

                        if not is_signature_found and (
                            e.data.reason or len(e.data.result) > 2
                        ):
                            logger.debug(
                                "Signature found by changed revert",
                                created_contract.address,
                                sighash,
                                calldata,
                            )
                            is_signature_found = True

                        if is_signature_found:
                            continue

                        if (
                            program_counter > -1
                            and program_counter == e.data.program_counter
                        ):
                            break

                        program_counter = e.data.program_counter
