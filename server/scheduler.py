# ═══════════════════════════════════════════════════════════════
# Sub Ladder v6.0 — Ranked Scheduler
# Daily tasks for ranked mode: Champion/Grand Champion transitions, decay
# ═══════════════════════════════════════════════════════════════

import asyncio
import threading
import pymysql
from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)

class RankedScheduler:
    """Handles daily ranked tasks like decay and rank transitions."""
    
    def __init__(self, db_pool_getter):
        """
        Initialize scheduler.
        
        Args:
            db_pool_getter: Function that returns a DB connection
        """
        self.db_pool_getter = db_pool_getter
        self.running = False
        self.thread = None
        # Heure de réinitialisation quotidienne (minuit local serveur)
        self.reset_time = time(0, 0, 0)
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("✅ Ranked Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("❌ Ranked Scheduler stopped")
    
    def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now()
                next_reset = self._get_next_reset_time(now)
                wait_seconds = (next_reset - now).total_seconds()
                
                logger.info(f"Next ranked reset in {wait_seconds:.0f} seconds "
                           f"(at {next_reset.strftime('%Y-%m-%d %H:%M:%S')} local time)")
                
                # Sleep until next reset (check every 10 seconds to allow early stop)
                for _ in range(int(wait_seconds // 10) + 1):
                    if not self.running:
                        return
                    if wait_seconds > 10:
                        asyncio.run(asyncio.sleep(10))
                        wait_seconds -= 10
                    else:
                        asyncio.run(asyncio.sleep(wait_seconds))
                        break
                
                # Execute daily tasks
                if self.running:
                    self._execute_daily_tasks()
            
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                asyncio.run(asyncio.sleep(60))
    
    def _get_next_reset_time(self, now: datetime) -> datetime:
        """Get the next reset time (next local midnight)."""
        today_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if now < today_reset:
            return today_reset
        
        # Tomorrow's local midnight
        return today_reset + timedelta(days=1)
    
    def _execute_daily_tasks(self):
        """Execute all daily ranked tasks."""
        logger.info("🔄 Executing daily ranked tasks...")
        
        try:
            db = self.db_pool_getter()
            
            # Task 1: Apply decay to Champion and Grand Champion players
            self._apply_decay(db)
            
            # Task 2: Recalculate Champion/Grand Champion ranks
            self._recalculate_top_ranks(db)
            
            db.commit()
            logger.info("✅ Daily ranked tasks completed")
        
        except Exception as e:
            logger.error(f"Error executing daily tasks: {e}")
    
    def _apply_decay(self, db: pymysql.Connection):
        """
        Apply decay to Champion and Grand Champion players.
        
        - Decrease decay_days by 1 (minimum 0)
        - If decay_days reaches 0 and it's been 0 since last check: lose 15 ELO
        """
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Get all Champions and Grand Champions
            cursor.execute("""
                SELECT er.id, er.profile_id, er.elo, er.decay_days, er.last_decay_check
                FROM elo_ratings er
                WHERE er.elo >= 2400
                ORDER BY er.elo DESC
            """)
            
            players = cursor.fetchall()
            now = datetime.now()
            
            for player in players:
                player_id = player["id"]
                current_elo = player["elo"]
                current_decay = player["decay_days"]
                last_check = player["last_decay_check"]
                
                # Check if decay was already at 0 yesterday
                decay_penalty_applied = False
                if current_decay == 0 and last_check:
                    # Decay was already 0, apply penalty
                    new_elo = max(0, current_elo - 15)
                    decay_penalty_applied = True
                
                # Decrease decay_days (max 21, minimum 0)
                new_decay = max(0, current_decay - 1)
                
                # Update player
                cursor.execute("""
                    UPDATE elo_ratings
                    SET decay_days = %s,
                        last_decay_check = %s,
                        elo = %s
                    WHERE id = %s
                """, (new_decay, now, current_elo if not decay_penalty_applied else new_elo, player_id))
                
                if decay_penalty_applied:
                    logger.info(f"Applied -15 ELO decay penalty to player {player['profile_id']}")
    
    def _recalculate_top_ranks(self, db: pymysql.Connection):
        """
        Recalculate Champion/Grand Champion status based on ELO.
        
        - Top 500 at 2500+ ELO get Grand Champion
        - Others at 2400+ get Champion
        """
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Mark top 500 players with elo >= 2500 as Grand Champion
            cursor.execute("""
                SELECT id, profile_id, elo
                FROM elo_ratings
                WHERE elo >= 2500
                ORDER BY elo DESC, games_played DESC
                LIMIT 500
            """)
            top_gc = cursor.fetchall()

            top_gc_ids = [r["id"] for r in top_gc]

            if top_gc_ids:
                # Set is_grand_champion = 1 for top 500
                cursor.execute(
                    "UPDATE elo_ratings SET is_grand_champion = 0 WHERE is_grand_champion = 1"
                )
                cursor.execute(
                    "UPDATE elo_ratings SET is_grand_champion = 1 WHERE id IN (%s)" %
                    (', '.join(['%s'] * len(top_gc_ids))), tuple(top_gc_ids)
                )
                logger.info(f"Marked {len(top_gc_ids)} players as Grand Champion")
            else:
                # Clear any previous flag if no one meets the threshold
                cursor.execute("UPDATE elo_ratings SET is_grand_champion = 0 WHERE is_grand_champion = 1")

            # Ensure anyone below 2500 is not marked grand champion
            cursor.execute("UPDATE elo_ratings SET is_grand_champion = 0 WHERE elo < 2500 AND is_grand_champion = 1")

            # Optionally handle season rollover at year boundaries
            self._handle_season_rollover(db)

            # Log sample info
            cursor.execute("SELECT COUNT(*) as gc_total FROM elo_ratings WHERE is_grand_champion = 1")
            gc_total = cursor.fetchone()["gc_total"]
            logger.info(f"Grand Champion total after recalculation: {gc_total}")

    def _handle_season_rollover(self, db: pymysql.Connection):
        """
        Handle season start/end. Seasons are calendar years (Jan 1 - Dec 31).
        - On Jan 1: ensure season row exists
        - On Dec 31 (when scheduler runs at midnight going into Jan 1 next): snapshot top players for the season
        """
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            today = datetime.now().date()

            # If Jan 1: create season for this year if missing
            if today.month == 1 and today.day == 1:
                year = today.year
                season_name = f"Saison {year}"
                cursor.execute("SELECT id FROM seasons WHERE year = %s", (year,))
                if not cursor.fetchone():
                    # Create season entry
                    start_date = f"{year}-01-01"
                    end_date = f"{year}-12-31"
                    cursor.execute(
                        "INSERT INTO seasons (name, year, start_date, end_date) VALUES (%s, %s, %s, %s)",
                        (season_name, year, start_date, end_date)
                    )
                    logger.info(f"Created season row: {season_name}")

            # If Dec 31: snapshot season placements (we assume this runs at midnight end-of-day)
            if today.month == 12 and today.day == 31:
                year = today.year
                # Find season for this year
                cursor.execute("SELECT id FROM seasons WHERE year = %s", (year,))
                season = cursor.fetchone()
                if season:
                    season_id = season["id"]
                    # Snapshot top 100 players by ELO
                    cursor.execute(
                        """
                        SELECT er.profile_id, er.elo
                        FROM elo_ratings er
                        ORDER BY er.elo DESC
                        LIMIT 100
                        """
                    )
                    leaders = cursor.fetchall()
                    rank_pos = 1
                    for p in leaders:
                        reward_category, reward_description = self._season_reward_for_elo(p["elo"])
                        cursor.execute(
                            "INSERT INTO season_placements (season_id, profile_id, elo, rank_position, reward_category, reward_description) VALUES (%s, %s, %s, %s, %s, %s)",
                            (season_id, p["profile_id"], p["elo"], rank_pos, reward_category, reward_description)
                        )
                        rank_pos += 1
                    logger.info(f"Season {year} snapshot: recorded top {len(leaders)} placements")
    
    def _season_reward_for_elo(self, elo: int):
        """Return season reward category and description for a given ELO tier."""
        if elo >= 2500:
            return "Grand Champion", "Top-tier season reward for Grand Champion placement."
        if elo >= 2400:
            return "Champion", "Season reward for Champion-ranked players."
        if elo >= 2100:
            return "Diamond", "Season reward for Diamond-ranked players."
        if elo >= 1800:
            return "Platinum", "Season reward for Platinum-ranked players."
        if elo >= 1500:
            return "Gold", "Season reward for Gold-ranked players."
        if elo >= 1200:
            return "Silver", "Season reward for Silver-ranked players."
        return "Bronze", "Season reward for Bronze-ranked players."

    def add_decay_day(self, profile_id: int, db: pymysql.Connection):
        """
        Add 1 day of decay when player wins a match (max 21 days).
        """
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                UPDATE elo_ratings
                SET decay_days = LEAST(decay_days + 1, 21),
                    last_match_played = %s
                WHERE profile_id = %s
            """, (datetime.now(), profile_id))
