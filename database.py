import os
from datetime import datetime
from psycopg2.extras import RealDictCursor
from psycopg2.extras import execute_values
import psycopg2
from dotenv import load_dotenv


class Database:
    def __init__(self):
        load_dotenv()
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()


    def create_connection(self):
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )

    def create_tracking_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS novig_tracking (
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
                spread_team_1_name TEXT,
                spread_team_2_name TEXT,
                spread_team_1_total_liquidity NUMERIC,
                spread_team_2_total_liquidity NUMERIC,
                spread_team_1_outcome_id TEXT,
                spread_team_2_outcome_id TEXT
                
            )
        """)

        self.conn.commit()

    def get_games(self, game_title: str, game_start_time: datetime, league: str, stat_type: str):

        query = """
                SELECT *
                FROM novig_tracking
                WHERE game_start_time = %s
                  AND game_title = %s
                  AND league = %s
                  AND stat_type = %s \
                """

        self.cursor.execute(query, (game_start_time, game_title, league, stat_type))
        rows = self.cursor.fetchall()

        columns = [desc[0] for desc in self.cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        return result

    def _update_database(self, data, existing_id):
        self.cursor.execute("""
            UPDATE novig_tracking SET
                game_start_time=%(game_start_time)s,
                total_over_liquidity=%(total_over_liquidity)s,
                total_under_liquidity=%(total_under_liquidity)s,
                highest_order_side=%(highest_order_side)s,
                liquidity_highest_order=%(liquidity_highest_order)s,
                odds_highest_order=%(odds_highest_order)s,
                liquidity_difference=%(liquidity_difference)s,
                over_outcome_id=%(over_outcome_id)s,
                under_outcome_id=%(under_outcome_id)s,
                spread_team_1_name=%(spread_team_1_name)s,
                spread_team_2_name=%(spread_team_2_name)s,
                spread_team_1_total_liquidity=%(spread_team_1_total_liquidity)s,
                spread_team_2_total_liquidity=%(spread_team_2_total_liquidity)s,
                spread_team_1_outcome_id=%(spread_team_1_outcome_id)s,
                spread_team_2_outcome_id=%(spread_team_2_outcome_id)s
            WHERE id=%(id)s
        """, {**data, "id": existing_id})

        self.conn.commit()

    def _insert_database(self, data):
        self.cursor.execute("""
            INSERT INTO novig_tracking (
                player_name, stat_type, line, game_title, game_start_time,
                total_over_liquidity, total_under_liquidity, highest_order_side, liquidity_highest_order,
                odds_highest_order, liquidity_difference, league, over_outcome_id, under_outcome_id, market_type,
                spread_team_1_name, spread_team_2_name, spread_team_1_total_liquidity, spread_team_2_total_liquidity,
                spread_team_1_outcome_id, spread_team_2_outcome_id
            ) VALUES (
                %(player_name)s, %(stat_type)s, %(line)s, %(game_title)s, %(game_start_time)s,
                %(total_over_liquidity)s, %(total_under_liquidity)s,
                %(highest_order_side)s, %(liquidity_highest_order)s, %(odds_highest_order)s, %(liquidity_difference)s,
                %(league)s, %(over_outcome_id)s, %(under_outcome_id)s, %(market_type)s, %(spread_team_1_name)s,
                %(spread_team_2_name)s, %(spread_team_1_total_liquidity)s, %(spread_team_2_total_liquidity)s,
                %(spread_team_1_outcome_id)s, %(spread_team_2_outcome_id)s
            )
        """, data)

        self.conn.commit()

    def insert_data(self, record, league, market_type):
        additional = record["additional_data"]
        player_name = additional["player_name"]
        stat_type = additional["stat_type"]
        line = additional["line"]
        game_title = additional["game_title"]
        game_start_time = additional["game_start_time"]
        liquidity_difference = record.get("liqudity_difference")

        over_data = record["liquidity"].get("over", {}).get("highest_order", {})
        under_data = record["liquidity"].get("under", {}).get("highest_order", {})

        spread_keyword = "Spread"

        # Handle Spreads as they are different
        if stat_type == spread_keyword:
            spread_sides = list(record["liquidity"].keys())
            spread_1 = record["liquidity"].get(spread_sides[0], {}).get("highest_order", {}) if len(
                spread_sides) > 0 else {}
            spread_2 = record["liquidity"].get(spread_sides[1], {}).get("highest_order", {}) if len(
                spread_sides) > 1 else {}
        else:
            spread_sides = []
            spread_1 = {}
            spread_2 = {}

        highest = max(
            record["liquidity"].values(),
            key=lambda x: x["highest_order"]["total_liquidity"]
        )["highest_order"]

        data = {
            "player_name": player_name,
            "stat_type": stat_type,
            "line": line,
            "game_title": game_title,
            "game_start_time": game_start_time,
            "total_over_liquidity": over_data.get("total_liquidity", 0) if stat_type != spread_keyword else None,
            "total_under_liquidity": under_data.get("total_liquidity", 0) if stat_type != spread_keyword else None,
            "highest_order_side": highest["side"],
            "liquidity_highest_order": highest["liquidity_left"],
            "odds_highest_order": highest["american_price"],
            "liquidity_difference": liquidity_difference,
            "league": league,
            "over_outcome_id": over_data.get("outcome_id") if stat_type != spread_keyword else None,
            "under_outcome_id": under_data.get("outcome_id") if stat_type != spread_keyword else None,
            "market_type": market_type,
            "spread_team_1_name": spread_sides[0] if len(spread_sides) > 0 else None,
            "spread_team_2_name": spread_sides[1] if len(spread_sides) > 1 else None,
            "spread_team_1_total_liquidity": spread_1.get("total_liquidity"),
            "spread_team_2_total_liquidity": spread_2.get("total_liquidity"),
            "spread_team_1_outcome_id": spread_1.get("outcome_id"),
            "spread_team_2_outcome_id": spread_2.get("outcome_id")
        }

        if market_type != "mainlines":
            query = ("""
                SELECT id, liquidity_highest_order 
                FROM novig_tracking 
                WHERE player_name=%s AND stat_type=%s AND line=%s AND game_title=%s AND league=%s
            """, (player_name, stat_type, line, game_title, league))

        else:
            query = ("""
                SELECT id, liquidity_difference 
                FROM novig_tracking 
                WHERE stat_type=%s AND line=%s AND game_title=%s AND league=%s
            """, (stat_type, line, game_title, league))

        self.cursor.execute(*query)
        existing = self.cursor.fetchone()

        if existing:
            existing_id, existing_order = existing
            current_order = highest.get("liquidity_left") if market_type != "mainlines" else liquidity_difference

            if existing_order:
                existing_order = float(existing_order)

            if current_order and (existing_order is None or current_order > existing_order):
                self._update_database(data, existing_id)

        else:
            self._insert_database(data)


    def get_outcome_ids(self):
        self.cursor.execute("""
            SELECT outcome_id
            FROM (
                SELECT over_outcome_id AS outcome_id
                FROM novig_tracking
                WHERE over_result IS NULL AND over_outcome_id IS NOT NULL

                UNION

                SELECT under_outcome_id AS outcome_id
                FROM novig_tracking
                WHERE under_result IS NULL AND under_outcome_id IS NOT NULL
                
                UNION
                
                SELECT spread_team_1_outcome_id AS outcome_id
                FROM novig_tracking
                WHERE spread_result IS NULL AND spread_team_1_outcome_id IS NOT NULL
                
                UNION
                
                SELECT spread_team_2_outcome_id AS outcome_id
                FROM novig_tracking
                WHERE spread_result IS NULL AND spread_team_2_outcome_id IS NOT NULL
                
            ) AS combined
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def bulk_update_results(self, results):
        spread_results = [r for r in results if r[2] == 'SPREAD']
        normal_results = [r for r in results if r[2] != 'SPREAD']


        if normal_results:
            sql = """
                UPDATE novig_tracking t
                SET
                    over_result  = CASE WHEN t.over_outcome_id  = v.outcome_id THEN v.result ELSE t.over_result END,
                    under_result = CASE WHEN t.under_outcome_id = v.outcome_id THEN v.result ELSE t.under_result END
                FROM (VALUES %s) AS v(outcome_id, result)
                WHERE t.over_outcome_id = v.outcome_id
                   OR t.under_outcome_id = v.outcome_id
            """

            necessary_values = [(r[0], r[1]) for r in normal_results]
            execute_values(self.cursor, sql, necessary_values)

        if spread_results:
            spread_win_values = [(r[0], r[3]) for r in spread_results if r[1].upper() == 'WIN']

            if spread_win_values:
                sql_spread = """
                    UPDATE novig_tracking t
                    SET 
                        spread_result = v.description
                    FROM (VALUES %s) AS v(outcome_id, description)
                    WHERE (t.spread_team_1_outcome_id = v.outcome_id OR t.spread_team_2_outcome_id = v.outcome_id)
                """
                execute_values(self.cursor, sql_spread, spread_win_values)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    db = Database()
    # db.create_tracking_table()
    result = db.get_outcome_ids()
