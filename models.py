# from dataclasses import dataclass, field
# from typing import Optional, Dict, List
#
# @dataclass
# class GameDetails:
#     game_title: str
#     game_start_time: str
#
#
# @dataclass
# class LiquidityData:
#     total_liquidity: float
#     total_cost_avg: float
#
# @dataclass
# class AdditionalInformation:
#     highest_order: Optional["Orders"] = None
#     over_liquidity_data: Optional[LiquidityData] = None
#     under_liquidity_data: Optional[LiquidityData] = None
#
#
# @dataclass
# class Orders:
#     outcome_id: str
#     qty: float
#     decimal_price: float
#     original_qty: float
#     created_at: str
#     american_price: float
#     total_win: float
#     total_risk: float
#     liquidity_left: float
#     is_highest_order: Optional[bool] = None
#
#
# @dataclass
# class Player:
#     player_name: str
#     main_market_description: str
#     stat_type: str
#     bet_info: str
#     orders: List[Orders]
#     game_details: GameDetails
#
#
#




from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class GameDetails:
    game_title: str
    game_start_time: str


@dataclass
class LiquidityData:
    total_liquidity: float
    total_cost_avg: float


@dataclass
class Orders:
    outcome_id: str
    qty: float
    decimal_price: float
    original_qty: float
    created_at: str
    american_price: float
    total_win: float
    total_risk: float
    liquidity_left: float

@dataclass
class LiquidityData:
    highest_order: Dict


@dataclass
class Player:
    player_name: str
    key_name: str
    stat_type: str
    bet_info: str
    line: float
    orders: List[Orders]
    liquidity_data: LiquidityData
    game_details: GameDetails

