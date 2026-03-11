from Strategy.strategy import Strategy


class NCAABTotalSkyHigh(Strategy):
    LOWEST_LINE = 160
    STRATEGY_COLOR = 0x1E90FF

    def __init__(self):
        super().__init__(strategy_type="Sky High Total")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass
        # order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference", highest_order_side="over")
        # if not order or not metrics:
        #     return False
        #
        # matched = (
        #     metrics["line"] > self.LOWEST_LINE
        # )
        #
        # if not matched:
        #     return False
        #
        #
        # self.send_message(
        #     strategy_bot_instance=strategy_bot_instance,
        #     highest_order=order,
        #     strategy_type=self.strategy_type,
        #     start_date=start_date,
        #     strategy_color=self.STRATEGY_COLOR,
        #     stat_type="total"
        # )
        #
        # return True

    def run_match_modified_analysis(self, order: dict, strategy_bot_instance, start_date: str) -> bool:
        if not order:
            return False

        matched = (
            order["highest_order_side"] == "over"
            and order["line"] > self.LOWEST_LINE

        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True


class NCAABTotalUnder(Strategy):
    HIGHEST_LINE = 150
    LOWEST_ODDS = -105
    HIGHEST_ODDS = 105
    STRATEGY_COLOR = 0xFF1493

    def __init__(self):
        super().__init__(strategy_type="Under Strategy")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass
        # order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference", highest_order_side="under")
        # if not order or not metrics:
        #     return False
        #
        # matched = (
        #     metrics["line"] < self.HIGHEST_LINE
        #     and self.LOWEST_ODDS < metrics["odds"] < self.HIGHEST_ODDS
        # )
        #
        # if not matched:
        #     return False
        #
        #
        # self.send_message(
        #     strategy_bot_instance=strategy_bot_instance,
        #     highest_order=order,
        #     strategy_type=self.strategy_type,
        #     start_date=start_date,
        #     strategy_color=self.STRATEGY_COLOR,
        #     stat_type="total"
        # )
        #
        # return True

    def run_match_modified_analysis(self, order: dict, strategy_bot_instance, start_date: str) -> bool:
        if not order:
            return False

        matched = (
            order["highest_order_side"] == "under"
            and order["line"] < self.HIGHEST_LINE
            and self.LOWEST_ODDS < order["odds"] < self.HIGHEST_ODDS
        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True


class NCAABTotalGoldMine(Strategy):
    HIGHEST_LINE = 150
    LOWEST_ODDS = -105
    HIGHEST_ODDS = 100
    STRATEGY_COLOR = 0xFFD700

    def __init__(self):
        super().__init__(strategy_type="Gold Mine")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass
        # order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")
        # if not order or not metrics:
        #     return False
        #
        # matched = (
        #     metrics["line"] <= self.HIGHEST_LINE
        #     and self.LOWEST_ODDS <= metrics["odds"] <= self.HIGHEST_ODDS
        # )
        #
        # if not matched:
        #     return False
        #
        #
        # self.send_message(
        #     strategy_bot_instance=strategy_bot_instance,
        #     highest_order=order,
        #     strategy_type=self.strategy_type,
        #     start_date=start_date,
        #     strategy_color=self.STRATEGY_COLOR,
        #     stat_type="total"
        # )
        #
        # return True

    def run_match_modified_analysis(self, order: dict, strategy_bot_instance, start_date: str) -> bool:
        if not order:
            return False

        matched = (
            order["line"] <= self.HIGHEST_LINE
            and self.LOWEST_ODDS <= order["odds"] <= self.HIGHEST_ODDS
        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True


class NCAABTotalLowLine(Strategy):
    HIGHEST_LINE = 140
    STRATEGY_COLOR = 0x2F2F2F

    def __init__(self):
        super().__init__(strategy_type="Low Lines")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass
        # order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference")
        # if not order or not metrics:
        #     return False
        #
        # matched = (
        #     metrics["line"] < self.HIGHEST_LINE
        # )
        #
        # if not matched:
        #     return False
        #
        #
        # self.send_message(
        #     strategy_bot_instance=strategy_bot_instance,
        #     highest_order=order,
        #     strategy_type=self.strategy_type,
        #     start_date=start_date,
        #     strategy_color=self.STRATEGY_COLOR,
        #     stat_type="total"
        # )
        #
        # return True

    def run_match_modified_analysis(self, order: dict, strategy_bot_instance, start_date: str) -> bool:
        if not order:
            return False

        matched = (
            order["line"] < self.HIGHEST_LINE
        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True


class NCAABTotalOverHighJuice(Strategy):
    HIGHEST_ODDS = -111
    STRATEGY_COLOR = 0x800080

    def __init__(self):
        super().__init__(strategy_type="Over High Juice")

    def part_of_strategy(self, stat_type: str, league: str) -> bool:
        return stat_type == "total" and league == "ncaab"

    def run_match_analysis(self, matches: list, strategy_bot_instance, start_date: str) -> bool:
        pass
        # order, metrics = self._get_highest_order_metrics(matches=matches, highest_type="highest_liquidity_difference", highest_order_side="over")
        # if not order or not metrics:
        #     return False
        #
        # matched = (
        #
        #     metrics["odds"] <= self.HIGHEST_ODDS
        # )
        #
        # if not matched:
        #     return False
        #
        #
        # self.send_message(
        #     strategy_bot_instance=strategy_bot_instance,
        #     highest_order=order,
        #     strategy_type=self.strategy_type,
        #     start_date=start_date,
        #     strategy_color=self.STRATEGY_COLOR,
        #     stat_type="total"
        # )
        #
        # return True

    def run_match_modified_analysis(self, order: dict, strategy_bot_instance, start_date: str) -> bool:
        if not order:
            return False

        matched = (
            order["highest_order_side"] == "over"
            and order["odds"] <= self.HIGHEST_ODDS
        )

        if not matched:
            return False


        self.send_message(
            strategy_bot_instance=strategy_bot_instance,
            highest_order=order,
            strategy_type=self.strategy_type,
            start_date=start_date,
            strategy_color=self.STRATEGY_COLOR,
            stat_type="total"
        )

        return True