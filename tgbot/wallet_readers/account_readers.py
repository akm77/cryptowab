import asyncio
import datetime
import logging
import random
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Dict, Any, Generator

import aiohttp
import base58
import tenacity
from aiohttp.typedefs import StrOrURL
from fake_useragent import UserAgent


class UrlReaderMode(IntEnum):
    HTML = 0
    JSON = 1


@dataclass
class AccountBalance:
    address: str
    native_balance: int
    token_balance: int


@dataclass
class AccountTransaction:
    address: str
    amount: int
    timestamp: datetime.datetime


class UrlReader:
    """
    This is base class get JSON data or HTML page from various API.
    """

    def __init__(self,
                 session: Optional[aiohttp.ClientSession] = None,
                 url: Optional[StrOrURL] = None,
                 params: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 data: Optional[Dict] = None,
                 mode: UrlReaderMode = UrlReaderMode.JSON,
                 method: str = "GET",
                 logger: Optional[logging.Logger] = None,
                 **kwargs) -> None:
        self.__session = session or aiohttp.ClientSession()
        self.__url: StrOrURL = url
        self.__params = params or None
        self.__headers = headers or None
        self.__data = data or None
        self.__mode = mode
        self.__method = method
        self.__response_status = 0
        self.__response_url: StrOrURL = ''
        self.__logger = logger or logging.getLogger(self.__class__.__module__)
        self.__result = None

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, session: aiohttp.ClientSession):
        self.__session = session

    @property
    def url(self) -> StrOrURL:
        return self.__url

    @url.setter
    def url(self, url: StrOrURL):
        self.__url = url

    @property
    def params(self) -> Dict:
        return self.__params

    @params.setter
    def params(self, params: Dict):
        self.__params = params

    @property
    def headers(self) -> Dict:
        return self.__headers

    @headers.setter
    def headers(self, headers: Dict):
        self.__headers = headers

    @property
    def data(self) -> Dict:
        return self.__data

    @data.setter
    def data(self, data: Dict):
        self.__data = data

    @property
    def status(self):
        return self.__response_status

    @property
    def response_url(self) -> StrOrURL:
        return self.__response_url

    @property
    def logger(self):
        return self.__logger

    @tenacity.retry(stop=tenacity.stop_after_attempt(6), wait=tenacity.wait_random(min=0.2, max=0.5),
                    after=tenacity.after_log(logging.getLogger(__name__), logging.ERROR))
    async def get_raw_data(self) -> Optional[Dict[str, Any] | str]:
        """
        :return JSON Result:
        """
        if not self.url:
            self.__logger.error("Url can not be None.")
            raise ValueError("Url can not be None.")
        self.__result = None
        method = self.session.get if self.__method == "GET" else self.session.post
        async with method(url=self.url, params=self.params, headers=self.headers, json=self.data) as response:
            self.__response_url = response.url
            self.__response_status = response.status
            self.__result = await response.json(encoding='utf-8') \
                if self.__mode == UrlReaderMode.JSON else await response.text()
        return self.__result


TRON_API_URL: str = "https://api.trongrid.io/v1/accounts/"
TRON_USDT_CONTRACT: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


class TronAccountReader(UrlReader):
    def __init__(self,
                 session: aiohttp.ClientSession,
                 address: str,
                 api_keys: list[str],
                 url: StrOrURL = TRON_API_URL,
                 usdt_contract: str = TRON_USDT_CONTRACT,
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(session=session, url=url, logger=logger)
        self.__base_url = url
        self.__address = address
        self.__api_keys = api_keys
        self.__api_key = random.choice(api_keys)
        self.__usdt_contract = usdt_contract
        self.__ua = UserAgent()

        if not self.headers:
            self.headers = {}
        self.headers['User-Agent'] = self.__ua.random
        self.headers['Content-Type'] = "application/json"
        self.headers['Accept'] = "application/json"
        self.headers['TRON-PRO-API-KEY'] = self.__api_key

        if not self.params:
            self.params = {}

    @property
    def address(self):
        return self.__address

    @address.setter
    def address(self, wallet):
        self.__address = wallet
        self.__api_key = random.choice(self.__api_keys)
        self.headers['TRON-PRO-API-KEY'] = self.__api_key
        self.headers['User-Agent'] = self.__ua.random

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key):
        self.__api_key = api_key

    @property
    def usdt_contract(self):
        return self.__usdt_contract

    @usdt_contract.setter
    def usdt_contract(self, usdt_contract):
        self.__usdt_contract = usdt_contract

    @staticmethod
    def hex_to_base58(hex_string):
        if hex_string[:2] in ["0x", "0X"]:
            hex_string = "41" + hex_string[2:]
        bytes_str = bytes.fromhex(hex_string)
        base58_str = base58.b58encode_check(bytes_str)
        return base58_str.decode("UTF-8")

    async def get_account_data(self) -> Optional[AccountBalance]:
        self.url = self.__base_url + self.__address
        raw_data = await self.get_raw_data()
        result = raw_data.get("success") if raw_data else None
        if result:
            data = next((data for data in raw_data.get("data")), None)
            if not data:
                return
            trx_balance = data.get("balance") or 0
            trc20 = data.get("trc20")
            trc20_usdt_balance = int(next((item.get(self.__usdt_contract, 0) for item in trc20
                                           if item.get(self.__usdt_contract)), 0)) if trc20 else 0
            return AccountBalance(address=self.__address,
                                  native_balance=trx_balance,
                                  token_balance=trc20_usdt_balance)

    def __process_native_transaction(self, trn) -> Optional[AccountTransaction]:
        contract = next((item for item in trn.get("raw_data").get("contract")), None)
        if not contract or contract.get("type") != "TransferContract":
            return
        amount = contract.get("parameter").get("value").get("amount")
        owner_address = TronAccountReader.hex_to_base58(contract.get("parameter").get("value").get("owner_address"))
        to_address = TronAccountReader.hex_to_base58(contract.get("parameter").get("value").get("to_address"))
        timestamp = datetime.datetime.fromtimestamp(trn.get("block_timestamp") / 1000.0,
                                                    datetime.timezone.utc)
        return (AccountTransaction(address=to_address, amount=-amount, timestamp=timestamp)
                if owner_address == self.__address else
                AccountTransaction(address=owner_address, amount=amount, timestamp=timestamp))

    async def get_native_transactions(self):
        self.url = self.__base_url + self.__address + "/transactions"
        params = self.params
        headers = self.headers
        self.params["only_confirmed"] = "true"
        self.params["search_internal"] = "false"
        try:
            raw_data = await self.get_raw_data()
        finally:
            self.params = params
            self.headers = headers
        result = raw_data.get("success") if raw_data else None

        if result:
            data = raw_data.get("data")
            return (record for trn in data if (record := self.__process_native_transaction(trn)))

    async def get_token_transactions(self) -> Optional[Generator[AccountTransaction, Any, None]]:
        self.url = self.__base_url + self.__address + "/transactions/trc20"
        params = self.params
        headers = self.headers
        self.params["contract_address"] = self.__usdt_contract
        self.params["only_confirmed"] = "true"
        try:
            raw_data = await self.get_raw_data()
        finally:
            self.params = params
            self.headers = headers
        result = raw_data.get("success") if raw_data else None
        if result:
            data = raw_data.get("data")
            return (AccountTransaction(address=trn["to"],
                                       amount=-int(trn["value"]),
                                       timestamp=datetime.datetime.fromtimestamp(trn.get('block_timestamp') / 1000.0,
                                                                                 datetime.timezone.utc))
                    if self.__address == trn["from"]
                    else AccountTransaction(address=trn["from"],
                                            amount=int(trn["value"]),
                                            timestamp=datetime.datetime.fromtimestamp(
                                                trn.get('block_timestamp') / 1000.0,
                                                datetime.timezone.utc))
                    for trn in data if int(trn["value"]))


ETHERSCAN_API_URL: str = "https://api.etherscan.io/api"
ETHERSCAN_USDT_CONTRACT: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
BSCSCAN_API_URL: str = "https://api.bscscan.com/api"
BSCSCAN_USDT_CONTRACT: str = "0x55d398326f99059ff775485246999027b3197955"


class EthereumAccountReader(UrlReader):
    def __init__(self,
                 session: aiohttp.ClientSession,
                 address: str,
                 api_keys: list[str],
                 url: StrOrURL = ETHERSCAN_API_URL,
                 usdt_contract: str = ETHERSCAN_USDT_CONTRACT,
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(session=session, url=url, logger=logger)
        self.__base_url = url
        self.__address = address
        self.__api_keys = api_keys
        self.__api_key = random.choice(api_keys)
        self.__usdt_contract = usdt_contract
        self.__ua = UserAgent()

        if not self.headers:
            self.headers = {}
        self.headers['User-Agent'] = self.__ua.random
        self.headers['Content-Type'] = "application/json"
        self.headers['Accept'] = "application/json"

        if not self.params:
            self.params = {}
        self.__native_balance_params = {"module": "account",
                                        "action": "balance",
                                        "address": address,
                                        "tag": "latest",
                                        "apikey": self.__api_key}
        self.__token_balance_params = {"module": "account",
                                       "action": "tokenbalance",
                                       "contractaddress": usdt_contract,
                                       "address": address,
                                       "tag": "latest",
                                       "apikey": self.__api_key}
        self.__native_transactions_params = {"module": "account",
                                             "action": "txlist",
                                             "address": address,
                                             "page": 1,
                                             "offset": 100,
                                             "startblock": 0,
                                             "endblock": 99999999,
                                             "sort": "desc",
                                             "apikey": self.__api_key}
        self.__token_transactions_params = {"module": "account",
                                            "action": "tokentx",
                                            "contractaddress": usdt_contract,
                                            "address": address,
                                            "page": 1,
                                            "offset": 100,
                                            "startblock": 0,
                                            "endblock": 99999999,
                                            "sort": "desc",
                                            "apikey": self.__api_key}

    @property
    def address(self):
        return self.__address

    @address.setter
    def address(self, address):
        self.__address = address
        self.__api_key = random.choice(self.__api_keys)
        self.headers['User-Agent'] = self.__ua.random
        self.__native_balance_params["address"] = address
        self.__native_balance_params["apikey"] = self.__api_key
        self.__token_balance_params["address"] = address
        self.__token_balance_params["apikey"] = self.__api_key
        self.__native_transactions_params["address"] = address
        self.__native_transactions_params["apikey"] = self.__api_key
        self.__token_transactions_params["address"] = address
        self.__token_transactions_params["apikey"] = self.__api_key

    @property
    def api_keys(self):
        return self.__api_keys

    @api_keys.setter
    def api_keys(self, api_keys):
        self.__api_keys = api_keys
        self.__api_key = random.choice(api_keys)
        self.__native_balance_params["apikey"] = self.__api_key
        self.__token_balance_params["apikey"] = self.__api_key
        self.__native_transactions_params["apikey"] = self.__api_key
        self.__token_transactions_params["apikey"] = self.__api_key

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key):
        self.__api_key = api_key
        self.__native_balance_params["apikey"] = api_key
        self.__token_balance_params["apikey"] = api_key
        self.__native_transactions_params["apikey"] = api_key
        self.__token_transactions_params["apikey"] = api_key

    @property
    def usdt_contract(self):
        return self.__usdt_contract

    @usdt_contract.setter
    def usdt_contract(self, usdt_contract):
        self.__usdt_contract = usdt_contract
        self.__token_balance_params["contractaddress"] = usdt_contract
        self.__token_transactions_params["contractaddress"] = usdt_contract

    async def get_account_data(self) -> Optional[AccountBalance]:
        self.params = self.__native_balance_params
        native_balance_raw_data = await self.get_raw_data()
        if native_balance_raw_data and native_balance_raw_data.get("message") != "OK":
            return
        await asyncio.sleep(0.2)
        self.params = self.__token_balance_params
        token_balance_raw_data = await self.get_raw_data()
        if token_balance_raw_data and token_balance_raw_data.get("message") != "OK":
            return
        return AccountBalance(address=self.__address,
                              native_balance=int(native_balance_raw_data.get("result")),
                              token_balance=int(token_balance_raw_data.get("result")), )

    def __process_transaction(self, data):
        return (AccountTransaction(address=trn["to"],
                                   amount=-int(trn["value"]),
                                   timestamp=datetime.datetime.fromtimestamp(int(trn.get('timeStamp')),
                                                                             datetime.timezone.utc))
                if self.__address.lower() == trn["from"].lower()
                else AccountTransaction(address=trn["from"],
                                        amount=int(trn["value"]),
                                        timestamp=datetime.datetime.fromtimestamp(
                                            int(trn.get('timeStamp')),
                                            datetime.timezone.utc))
                for trn in data if int(trn["value"]))

    async def get_native_transactions(self):
        self.params = self.__native_transactions_params
        native_transactions_raw_data = await self.get_raw_data()
        if native_transactions_raw_data and native_transactions_raw_data.get("message") != "OK":
            return
        return self.__process_transaction(native_transactions_raw_data.get("result", []))

    async def get_token_transactions(self) -> Optional[Generator[AccountTransaction, Any, None]]:
        self.params = self.__token_transactions_params
        token_transactions_raw_data = await self.get_raw_data()
        if token_transactions_raw_data and token_transactions_raw_data.get("message") != "OK":
            return
        return self.__process_transaction(token_transactions_raw_data.get("result", []))
