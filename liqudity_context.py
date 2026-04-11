from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class LiquidityStrategy:
    strategy_name: Optional[str] = None
    # liquidity_difference: Optional[float] = None
    discord_color: Optional[int] = None
    include_tag: Optional[bool] = False
    snapshot_time: Optional[datetime] = None
    include_snapshot: Optional[bool] = False
    player_name: Optional[str] = None

@dataclass
class LiquidityContext:
    league: str
    market_type: str
    ping_movement_amount: int
    already_sent: bool
    found_mapping: dict
    highest_order: dict
    highest_order_key: str
    liquidity_difference: float
    liquidity_key: str
    start_date_dt: datetime | str
    start_date_buffer: datetime
    main_liquidity: dict
    additional_data: dict
    run_strategy_per_run: bool
    side_1_name: str
    side_2_name: str
    strategy: Optional[LiquidityStrategy] = None


