import sqlite3

from typing import List
from .contract import CreatedContract


class QueuedContract(CreatedContract):
    def __init__(self, priority):
        self.priority = priority


class IDatabase:
    def add_contract(self, contract: CreatedContract, priority: int) -> None:
        ...

    def delete_contract(self, address: str) -> None:
        ...

    def update_priority(self, address: str, priority: int) -> None:
        ...

    def get_contracts(self) -> List[QueuedContract]:
        ...

    def clear(self) -> None:
        ...

    def close(self) -> None:
        ...


class SqlDatabase(IDatabase):
    def __init__(self, filename=":memory:"):
        self.db = sqlite3.connect(filename)
        self.db.row_factory = sqlite3.Row

        self.db.execute(
            """CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY,
            address text NOT NULL,
            deployer text NOT NULL,
            block_number int,
            timestamp int,
            tx_hash text,
            priority int
        )"""
        )

        self.db.execute("CREATE INDEX IF NOT EXISTS address_idx ON contracts(address)")

        self.add_statement = "INSERT INTO contracts VALUES (NULL, ?, ?, ?, ?, ?, ?)"
        self.update_statement = "UPDATE contracts SET priority = ? WHERE address = ?"
        self.delete_statement = "DELETE FROM contracts WHERE address = ?"

    def add_contract(self, contract: CreatedContract, priority: int) -> None:
        self.db.execute(
            self.add_statement,
            (
                contract.address,
                contract.deployer,
                contract.block_number,
                contract.timestamp,
                contract.tx_hash,
                priority,
            ),
        )

    def delete_contract(self, address: str) -> None:
        self.db.execute(self.delete_statement, address)

    def update_priority(self, address: str, priority: int) -> None:
        self.db.execute(self.update_statement, (priority, address))

    def get_contracts(self) -> list[QueuedContract]:
        rows = self.db.execute("SELECT * FROM contracts").fetchall()
        return [QueuedContract(row["priority"]) for row in rows]

    def clear(self) -> None:
        self.db.execute("DELETE FROM contracts")

    def close(self) -> None:
        self.db.close()


class InMemoryDatabase(IDatabase):
    def __init__(self):
        self.contract_set = set()

    def add_contract(self, contract: CreatedContract, priority: int) -> None:
        self.contract_set.add(QueuedContract(priority, **contract.__dict__))

    def delete_contract(self, address: str) -> None:
        for contract in self.contract_set:
            if contract.address == address:
                self.contract_set.remove(contract)
                break

    def update_priority(self, address: str, priority: int) -> None:
        for contract in self.contract_set:
            if contract.address == address:
                contract.priority = priority
                break

    def get_contracts(self) -> list[QueuedContract]:
        return list(self.contract_set)

    def clear(self) -> None:
        self.contract_set.clear()
