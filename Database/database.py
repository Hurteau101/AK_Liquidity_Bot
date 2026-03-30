import json
import os
from dataclasses import asdict
from datetime import datetime

from psycopg2.extras import execute_values
import psycopg2
from dotenv import load_dotenv

from liqudity_context import LiquidityContext

load_dotenv()

class Database:
    def __init__(self):
        self.conn = self._create_connection()
        self.is_production = os.getenv("PRODUCTION") == "True"

    def _create_connection(self) -> psycopg2.connect:
        """Creates a connection to the PostgreSQL database using credentials from environment variables."""
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )

    def create_tracking_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS novig_tracking_test_environment (
                id BIGSERIAL PRIMARY KEY,
                snapshot_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                player_name TEXT,
                stat_type TEXT,
                line NUMERIC,
                game_title TEXT,
                game_start_time TIMESTAMPTZ,
                total_over_liquidity NUMERIC,
                total_under_liquidity NUMERIC,
                highest_order_side TEXT,
                liquidity_highest_order NUMERIC,
                odds_highest_order NUMERIC,
                liquidity_difference NUMERIC,
                league TEXT,
                market_type TEXT,
                type_team_1_name TEXT,
                type_team_2_name TEXT,
                type_team_1_total_liquidity NUMERIC,
                type_team_2_total_liquidity NUMERIC,
                type_team_1_outcome_id TEXT,
                type_team_2_outcome_id TEXT

            )
        """)

        self.conn.commit()

    def create_filter_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filters (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    filter_category filter_type NOT NULL,
                    league TEXT NOT NULL,
                    market_selection market_type NOT NULL,
                    liquidity_difference_filter_amount INTEGER NOT NULL,
                    highest_order_filter_amount INTEGER NULL,
                    ping_difference_amount INTEGER NOT NULL,
                    raw_name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    active BOOLEAN NOT NULL,
                    max_odds INTEGER NULL,
                    database_selection_type database_filter_type NOT NULL,
                    run_strategy_per_run BOOLEAN NOT NULL DEFAULT FALSE,
                    liquidity_context JSONB NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            
            """)

            self.conn.commit()

    def create_enums(self):
        """Creates an ENUM type in the database to categorize different filter types."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'filter_type') THEN
                        CREATE TYPE filter_type AS ENUM (
                            'liquidity_difference',
                            'liquidity_difference_and_highest_order'
                        );
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'market_type') THEN
                        CREATE TYPE market_type AS ENUM (
                            'mainlines',
                            'prop'
                        );
                    
                    END IF;
                    
                     IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'database_filter_type') THEN
                        CREATE TYPE database_filter_type AS ENUM (
                            'liquidity_difference',
                            'highest_order'
                        );
                    
                    END IF;
                END
                
                $$
            """)

            self.conn.commit()

    def fetch_filters(self):
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT filter_category,league,market_selection,liquidity_difference_filter_amount,highest_order_filter_amount,"
                           "ping_difference_amount,raw_name, display_name, active, max_odds, run_strategy_per_run, database_selection_type  "
                           "FROM filters WHERE active = TRUE")
            return cursor.fetchall()

    def check_existing_record(self, liquidity_context: LiquidityContext):
        table_name = "novig_tracking" if self.is_production else "novig_tracking_test_environment"

        with self.conn.cursor() as cursor:
            market_type = liquidity_context.market_type
            player_name = liquidity_context.additional_data.get("player_name")
            stat_type = liquidity_context.additional_data.get("stat_type")
            line = liquidity_context.additional_data.get("line")
            game_title = liquidity_context.additional_data.get("game_title")
            league = liquidity_context.league

            if market_type == "mainlines":
                sql = f"""
                    SELECT id, liquidity_difference
                    FROM {table_name}
                    WHERE stat_type = %s
                      AND line = %s
                      AND game_title = %s
                      AND league = %s
                """
                params = (stat_type, line, game_title, league)
            else:
                sql = f"""
                    SELECT id, liquidity_highest_order
                    FROM {table_name}
                    WHERE player_name = %s
                      AND stat_type = %s
                      AND line = %s
                      AND game_title = %s
                      AND league = %s
                """
                params = (player_name, stat_type, line, game_title, league)

            cursor.execute(sql, params)
            return cursor.fetchone()

    def _insert_database(self, data, table_name):
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {table_name} (
                    player_name, stat_type, line, game_title, game_start_time,
                    total_over_liquidity, total_under_liquidity, highest_order_side, liquidity_highest_order,
                    odds_highest_order, liquidity_difference, league, over_outcome_id, under_outcome_id, market_type,
                    type_team_1_name, type_team_2_name, type_team_1_total_liquidity, type_team_2_total_liquidity,
                    type_team_1_outcome_id, type_team_2_outcome_id, liquidity_context
                ) VALUES (
                    %(player_name)s, %(stat_type)s, %(line)s, %(game_title)s, %(game_start_time)s,
                    %(total_over_liquidity)s, %(total_under_liquidity)s,
                    %(highest_order_side)s, %(liquidity_highest_order)s, %(odds_highest_order)s, %(liquidity_difference)s,
                    %(league)s, %(over_outcome_id)s, %(under_outcome_id)s, %(market_type)s, %(type_team_1_name)s,
                    %(type_team_2_name)s, %(type_team_1_total_liquidity)s, %(type_team_2_total_liquidity)s,
                    %(type_team_1_outcome_id)s, %(type_team_2_outcome_id)s, %(liquidity_context)s
                )
            """, data)

        self.conn.commit()

    def _update_database(self, data, existing_id, table_name):
        print(f"Updating existing record with ID {existing_id} in table {table_name} with new data: {data}")
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE {table_name} SET
                    snapshot_time = CURRENT_TIMESTAMP,
                    game_start_time=%(game_start_time)s,
                    total_over_liquidity=%(total_over_liquidity)s,
                    total_under_liquidity=%(total_under_liquidity)s,
                    highest_order_side=%(highest_order_side)s,
                    liquidity_highest_order=%(liquidity_highest_order)s,
                    odds_highest_order=%(odds_highest_order)s,
                    liquidity_difference=%(liquidity_difference)s,
                    over_outcome_id=%(over_outcome_id)s,
                    under_outcome_id=%(under_outcome_id)s,
                    type_team_1_name=%(type_team_1_name)s,
                    type_team_2_name=%(type_team_2_name)s,
                    type_team_1_total_liquidity=%(type_team_1_total_liquidity)s,
                    type_team_2_total_liquidity=%(type_team_2_total_liquidity)s,
                    type_team_1_outcome_id=%(type_team_1_outcome_id)s,
                    type_team_2_outcome_id=%(type_team_2_outcome_id)s,
                    liquidity_context=%(liquidity_context)s
                WHERE id=%(id)s
            """, {**data, "id": existing_id})

            self.conn.commit()

    def get_outcome_ids(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT outcome_id, highest_order_side
                FROM (
                    SELECT 
                        over_outcome_id AS outcome_id,
                        highest_order_side
                    FROM novig_tracking
                    WHERE over_result IS NULL
                      AND under_result IS NULL
                      AND over_outcome_id IS NOT NULL
    
                    UNION
    
                    SELECT 
                        under_outcome_id AS outcome_id,
                        highest_order_side
                    FROM novig_tracking
                    WHERE over_result IS NULL
                      AND under_result IS NULL
                      AND under_outcome_id IS NOT NULL
    
                    UNION
    
                    SELECT 
                        type_team_1_outcome_id AS outcome_id,
                        NULL AS highest_order_side
                    FROM novig_tracking
                    WHERE type_result IS NULL
                      AND type_team_1_outcome_id IS NOT NULL
    
                    UNION
    
                    SELECT 
                        type_team_2_outcome_id AS outcome_id,
                        NULL AS highest_order_side
                    FROM novig_tracking
                    WHERE type_result IS NULL
                      AND type_team_2_outcome_id IS NOT NULL
                ) AS combined
            """)

            return {row[0]: row[1] for row in cursor.fetchall()}

    def controller(self, liquidity_context: LiquidityContext):
        def is_moneyline_or_spread(listed_stat_type):
            if listed_stat_type in ["Moneyline", "Spread"]:
                return True
            return False

        table_name = "novig_tracking" if self.is_production else "novig_tracking_test_environment"

        side_1_name = liquidity_context.side_1_name
        side_2_name = liquidity_context.side_2_name

        side_1_order = liquidity_context.main_liquidity.get(side_1_name, {}).get("highest_order", {}).get("total_liquidity")
        side_2_order = liquidity_context.main_liquidity.get(side_2_name, {}).get("highest_order", {}).get("total_liquidity")

        side_1_outcome_id = liquidity_context.main_liquidity.get(side_1_name, {}).get("highest_order", {}).get("outcome_id")
        side_2_outcome_id = liquidity_context.main_liquidity.get(side_2_name, {}).get("highest_order", {}).get("outcome_id")

        stat_type = liquidity_context.additional_data.get("stat_type", None)

        storable_data = {
            "player_name": liquidity_context.additional_data.get("player_name", None),
            "stat_type": liquidity_context.additional_data.get("stat_type", None),
            "line": liquidity_context.additional_data.get("line", None),
            "game_title": liquidity_context.additional_data.get("game_title", None),
            "game_start_time": liquidity_context.additional_data.get("game_start_time", None),
            "total_over_liquidity": side_1_order if not is_moneyline_or_spread(stat_type) else None,
            "total_under_liquidity": side_2_order if not is_moneyline_or_spread(stat_type) else None,
            "highest_order_side": liquidity_context.highest_order.get("side"),
            "liquidity_highest_order": liquidity_context.highest_order.get("liquidity_left"),
            "odds_highest_order": liquidity_context.highest_order.get("american_price"),
            "liquidity_difference": liquidity_context.liquidity_difference,
            "league": liquidity_context.league,
            "over_outcome_id": side_1_outcome_id if not is_moneyline_or_spread(stat_type) else None,
            "under_outcome_id": side_2_outcome_id if not is_moneyline_or_spread(stat_type) else None,
            "market_type": liquidity_context.market_type,
            "type_team_1_name": side_1_name if is_moneyline_or_spread(stat_type) else None,
            "type_team_2_name": side_2_name if is_moneyline_or_spread(stat_type) else None,
            "type_team_1_total_liquidity": side_1_order if is_moneyline_or_spread(stat_type) else None,
            "type_team_2_total_liquidity": side_2_order if is_moneyline_or_spread(stat_type) else None,
            "type_team_1_outcome_id": side_1_outcome_id if is_moneyline_or_spread(stat_type) else None,
            "type_team_2_outcome_id": side_2_outcome_id if is_moneyline_or_spread(stat_type) else None,
            "liquidity_context": json.dumps(asdict(liquidity_context), default=str)
        }

        existing = self.check_existing_record(liquidity_context)

        selector = liquidity_context.found_mapping.get("database_selection_type", None)

        if not selector:
            raise ValueError(f"No database_selection_type found in found_mapping for liquidity context: {liquidity_context}")

        if existing:
            print("Existing Found")
            existing_id, existing_order = existing

            if selector == "liquidity_difference":
                print(selector)
                current_order = liquidity_context.liquidity_difference
            elif selector == "highest_order":
                print(selector)
                current_order = liquidity_context.highest_order.get("liquidity_left")
            else:
                raise ValueError(f"Unknown database_selection_type: {selector} for liquidity context: {liquidity_context}")

            if existing_order:
                existing_order = float(existing_order)

            if current_order and (existing_order is None or current_order > existing_order):
                self._update_database(storable_data, existing_id, table_name)

        else:
            self._insert_database(storable_data, table_name)

    def get_games(self, game_title: str, game_start_time: datetime, league: str, stat_type: str):
        table_name = "novig_tracking" if self.is_production else "novig_tracking_test_environment"

        with self.conn.cursor() as cursor:
            query = f"""
                    SELECT liquidity_context, snapshot_time
                    FROM {table_name}
                    WHERE game_start_time = %s
                      AND game_title = %s
                      AND league = %s
                      AND stat_type = %s \
                    """

            cursor.execute(query, (game_start_time, game_title, league, stat_type))
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]

            return [dict(zip(columns, row)) for row in rows]


    def bulk_update_results(self, results):
        with self.conn.cursor() as cursor:
            spread_results = [r for r in results if r[2] == 'SPREAD']
            normal_results = [r for r in results if r[2] != 'SPREAD']

            if normal_results:
                necessary_values = [(r[0], r[1]) for r in normal_results]

                sql_over = """
                           UPDATE novig_tracking t
                           SET over_result = v.result FROM (VALUES %s) AS v(outcome_id \
                             , result)
                           WHERE t.over_outcome_id = v.outcome_id \
                           """

                sql_under = """
                            UPDATE novig_tracking t
                            SET under_result = v.result FROM (VALUES %s) AS v(outcome_id \
                              , result)
                            WHERE t.under_outcome_id = v.outcome_id \
                            """

                execute_values(cursor, sql_over, necessary_values)
                execute_values(cursor, sql_under, necessary_values)


            if spread_results:
                spread_win_values = [(r[0], r[3]) for r in spread_results if r[1].upper() in ["WIN", "PUSH"]]

                if spread_win_values:
                    sql_spread = """
                        UPDATE novig_tracking t
                        SET 
                            spread_result = v.description
                        FROM (VALUES %s) AS v(outcome_id, description)
                        WHERE (t.spread_team_1_outcome_id = v.outcome_id OR t.spread_team_2_outcome_id = v.outcome_id)
                    """
                    execute_values(cursor, sql_spread, spread_win_values)
            self.conn.commit()






    #
    # def filter_insert(self):
    #     import json
    #     with open("filters_file.json", "r") as f:
    #         data = json.load(f)
    #
    #
    #     for data in data.get("data"):
    #         if data.get("filter_category") == "liquidity_difference":
    #             insert_query = """
    #                 INSERT INTO filters (filter_category, league, market_selection, liquidity_difference_filter_amount,
    #                 ping_difference_amount, raw_name, display_name, active, database_selection_type)
    #                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    #             """
    #             with self.conn.cursor() as cursor:
    #                 cursor.execute(insert_query, (
    #                     data.get("filter_category"),
    #                     data.get("league"),
    #                     data.get("market_selection"),
    #                     data.get("liquidity_difference"),
    #                     data.get("ping_difference"),
    #                     data.get("raw_name"),
    #                     data.get("display_name"),
    #                     data.get("active"),
    #                     data.get("database_selection")
    #                 ))
    #
    #                 self.conn.commit()
    #                 print(f"Inserted filter for {data.get('league')} - {data.get('market_selection')} with category {data.get('filter_category')}")
    #
    #         elif data.get("filter_category") == "liquidity_difference_and_highest_order":
    #             insert_query = """
    #                 INSERT INTO filters (filter_category, league, market_selection, liquidity_difference_filter_amount,
    #                 highest_order_filter_amount, ping_difference_amount, raw_name, display_name, active, database_selection_type)
    #                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #             """
    #             with self.conn.cursor() as cursor:
    #                 cursor.execute(insert_query, (
    #                     data.get("filter_category"),
    #                     data.get("league"),
    #                     data.get("market_selection"),
    #                     data.get("liquidity_difference"),
    #                     data.get("highest_order"),
    #                     data.get("ping_difference"),
    #                     data.get("raw_name"),
    #                     data.get("display_name"),
    #                     data.get("active"),
    #                     data.get("database_selection"),
    #                 ))
    #
    #                 self.conn.commit()
    #                 print(f"Inserted filter for {data.get('league')} - {data.get('market_selection')} with category {data.get('filter_category')}")
    #         else:
    #             raise ValueError(f"Unknown filter category: {data.get('filter_category')}")






if __name__ == "__main__":
    db = Database()
    db.create_filter_table()
