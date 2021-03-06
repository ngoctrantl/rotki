import logging
from importlib import import_module
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from rotkehlchen.exchanges.exchange import ExchangeInterface
from rotkehlchen.logging import RotkehlchenLogsAdapter
from rotkehlchen.typing import ApiCredentials, ApiKey, ApiSecret
from rotkehlchen.user_messages import MessagesAggregator

if TYPE_CHECKING:
    from rotkehlchen.db.dbhandler import DBHandler

logger = logging.getLogger(__name__)
log = RotkehlchenLogsAdapter(logger)

SUPPORTED_EXCHANGES = [
    'kraken',
    'poloniex',
    'bittrex',
    'bitmex',
    'binance',
    'coinbase',
    'coinbasepro',
]


class ExchangeManager():

    def __init__(self, msg_aggregator: MessagesAggregator) -> None:
        self.connected_exchanges: Dict[str, ExchangeInterface] = {}
        self.msg_aggregator = msg_aggregator

    def has_exchange(self, name: str) -> bool:
        return name in self.connected_exchanges

    def delete_exchange(self, name: str) -> None:
        self.connected_exchanges.pop(name)

    def delete_all_exchanges(self) -> None:
        self.connected_exchanges.clear()

    def get_connected_exchange_names(self) -> List[str]:
        return [e.name for _, e in self.connected_exchanges.items()]

    def setup_exchange(
            self,
            name: str,
            api_key: ApiKey,
            api_secret: ApiSecret,
            database: 'DBHandler',
            passphrase: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Setup a new exchange with an api key, an api secret and for some exchanges a passphrase.

        By default the api keys are always validated unless validate is False.
        """
        if name not in SUPPORTED_EXCHANGES:
            return False, 'Attempted to register unsupported exchange {}'.format(name)

        if name in self.connected_exchanges:
            return False, 'Exchange {} is already registered'.format(name)

        credentials_dict = {}
        api_credentials = ApiCredentials(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
        )
        credentials_dict[name] = api_credentials
        self.initialize_exchanges(credentials_dict, database)

        exchange = self.connected_exchanges[name]
        result, message = exchange.validate_api_key()
        if not result:
            log.error(
                'Failed to validate API key for exchange',
                name=name,
                error=message,
            )
            self.delete_exchange(name)
            return False, message

        return True, ''

    def initialize_exchanges(
            self,
            exchange_credentials: Dict[str, ApiCredentials],
            database: 'DBHandler',
    ) -> None:
        # initialize exchanges for which we have keys and are not already initialized
        for name, credentials in exchange_credentials.items():
            if name not in self.connected_exchanges:
                try:
                    module = import_module(f'rotkehlchen.exchanges.{name}')
                except ModuleNotFoundError:
                    # This should never happen
                    raise AssertionError(
                        f'Tried to initialize unknown exchange {name}. Should never happen.',
                    )

                exchange_ctor = getattr(module, name.capitalize())
                extra_args = {}
                if credentials.passphrase is not None:
                    extra_args['passphrase'] = credentials.passphrase
                exchange_obj = exchange_ctor(
                    api_key=credentials.api_key,
                    secret=credentials.api_secret,
                    database=database,
                    msg_aggregator=self.msg_aggregator,
                    **extra_args,
                )
                self.connected_exchanges[name] = exchange_obj
