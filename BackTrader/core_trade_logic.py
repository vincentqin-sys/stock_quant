"""
 Author       : adolf
 Date         : 2022-12-01 23:29:44
 LastEditors  : adolf adolf1321794021@gmail.com
 LastEditTime : 2022-12-04 23:47:04
 FilePath     : /stock_quant/BackTrader/core_trade_logic.py
"""
import pandas as pd
from typing import List
from Utils.base_utils import get_logger
from dataclasses import dataclass, field

from .position_analysis import BaseTransactionAnalysis


@dataclass
class OneTransactionRecord:
    pos_asset: str = field(default=None, metadata={"help": "持仓资产"})
    buy_date: str = field(default=None, metadata={"help": "买入时间"})
    buy_price: float = field(default=0.0, metadata={"help": "买入价格"})
    sell_date: str = field(default=None, metadata={"help": "卖出时间"})
    sell_price: float = field(default=0.0, metadata={"help": "卖出价格"})
    holding_time: int = field(default=0, metadata={"help": "持仓时间"})
    take_profit: float = field(default=None, metadata={"help": "止盈价格"})
    stop_loss: float = field(default=None, metadata={"help": "止损价格"})


class CoreTradeLogic:
    def __init__(self) -> None:
        self.trade_rate = 1.5 / 1000

        self.logger = get_logger(
            level=self.config.LOG_LEVEL, console=True, logger_file=None
        )

        # 针对交易结果进行分析
        self.transaction_analysis = BaseTransactionAnalysis(logger=self.logger)

    def buy_logic(self, trading_step, one_transaction_record):
        raise NotImplementedError

    def sell_logic(self, trading_step, one_transaction_record):
        raise NotImplementedError

    def buy(self, index, trading_step, one_transaction_record):
        self.logger.debug(f"buy {index} {trading_step} {one_transaction_record}")

        one_transaction_record.pos_asset = trading_step.code
        one_transaction_record.buy_date = trading_step.date
        one_transaction_record.buy_price = trading_step.close
        one_transaction_record.holding_time = index

        self.logger.debug(one_transaction_record)
        return one_transaction_record

    def sell(self, index, trading_step, one_transaction_record):
        self.logger.debug(f"sell {index} \n {trading_step} \n {one_transaction_record}")

        one_transaction_record.sell_date = trading_step.date
        one_transaction_record.sell_price = trading_step.close
        one_transaction_record.holding_time = (
            index - one_transaction_record.holding_time
        )

        self.logger.debug(one_transaction_record)
        return one_transaction_record

    def base_trade(self, data) -> List[dict]:
        one_transaction_record = OneTransactionRecord()

        history_trading_step = []
        transaction_record_list = []
        # self.logger.debug(one_transaction_record)

        for index, trading_step in data.iterrows():
            if (
                self.buy_logic(
                    trading_step, one_transaction_record, history_trading_step
                )
                and one_transaction_record.buy_date is None
            ):
                one_transaction_record = self.buy(
                    index, trading_step, one_transaction_record
                )
                continue

            if (
                self.sell_logic(
                    trading_step, one_transaction_record, history_trading_step
                )
                and one_transaction_record.buy_date is not None
            ):
                one_transaction_record = self.sell(
                    index, trading_step, one_transaction_record
                )

                transaction_record_list.append(one_transaction_record)
                one_transaction_record = OneTransactionRecord()

                if self.buy_logic(trading_step, one_transaction_record):
                    one_transaction_record = self.buy(
                        index, trading_step, one_transaction_record
                    )
            history_trading_step.append(trading_step)
            if len(history_trading_step) > 1:
                history_trading_step.pop(0)

        self.logger.debug(transaction_record_list)
        transaction_record_df = pd.DataFrame(transaction_record_list)
        self.logger.debug(transaction_record_df)

        if len(transaction_record_df) == 0:
            return transaction_record_df

        transaction_record_df["pct"] = (
            transaction_record_df["sell_price"] / transaction_record_df["buy_price"]
        ) * (1 - self.trade_rate) - 1

        self.logger.info(transaction_record_df)

        return transaction_record_df
