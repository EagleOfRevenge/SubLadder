-- ═══════════════════════════════════════════════════════════════
-- Sub Ladder v4.0 — MariaDB Schema
-- Server IP: 45.156.84.114
-- ═══════════════════════════════════════════════════════════════

-- Database
CREATE DATABASE IF NOT EXISTS sub_ladder
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sub_ladder;

-- ── Users ──────────────────────────────────────────────────────
-- Un utilisateur peut avoir un compte email/mot de passe
-- ET/OU un compte Discord lié. Au moins un est requis.

CREATE TABLE users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) DEFAULT NULL,
    password_hash   VARCHAR(255) DEFAULT NULL,
    discord_id      VARCHAR(32)  DEFAULT NULL,
    discord_username VARCHAR(64)  DEFAULT NULL,
    discord_avatar  VARCHAR(255) DEFAULT NULL,
    steam_id        VARCHAR(64)  DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_email (email),
    UNIQUE KEY uk_discord (discord_id),
    UNIQUE KEY uk_steam (steam_id),
    INDEX idx_discord (discord_id),
    INDEX idx_steam (steam_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Profiles (game profiles linked to a user) ──────────────────

CREATE TABLE profiles (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    game_name       VARCHAR(64) NOT NULL,
    avatar          VARCHAR(255) DEFAULT NULL,
    current_status  ENUM('offline', 'online', 'away', 'lobby', 'looking_for_match', 'match_found', 'loading_game', 'normal_game', 'ranked_game', 'tutorial', 'training', 'custom_game') NOT NULL DEFAULT 'offline',
    status_message  VARCHAR(255) DEFAULT NULL,
    last_seen_at    DATETIME DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_game (user_id, game_name),
    INDEX idx_game_name (game_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Social graph (friends, blocks, reports) ────────────────────

CREATE TABLE friends (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    player_id       INT UNSIGNED NOT NULL,
    friend_id       INT UNSIGNED NOT NULL,
    status          ENUM('pending', 'accepted', 'declined') NOT NULL DEFAULT 'pending',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (player_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_friend_pair (player_id, friend_id),
    INDEX idx_player_status (player_id, status),
    INDEX idx_friend_status (friend_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blocked_players (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    blocker_id      INT UNSIGNED NOT NULL,
    blocked_id      INT UNSIGNED NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (blocker_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_blocked_pair (blocker_id, blocked_id),
    INDEX idx_blocker (blocker_id),
    INDEX idx_blocked (blocked_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE player_reports (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reporter_id     INT UNSIGNED NOT NULL,
    reported_id     INT UNSIGNED NOT NULL,
    reason          VARCHAR(128) NOT NULL,
    description     TEXT DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporter_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_id) REFERENCES profiles(id) ON DELETE CASCADE,
    INDEX idx_reporter_created (reporter_id, created_at),
    INDEX idx_reported_created (reported_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Scores ─────────────────────────────────────────────────────

CREATE TABLE scores (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    profile_id          INT UNSIGNED NOT NULL,
    subs                INT NOT NULL DEFAULT 0,
    level               INT NOT NULL DEFAULT 0,
    won                 TINYINT(1) NOT NULL DEFAULT 0,
    walked              TINYINT(1) NOT NULL DEFAULT 0,
    mode                VARCHAR(16) NOT NULL DEFAULT 'normal',
    response_time_avg   FLOAT DEFAULT NULL,
    correct_answers     INT DEFAULT NULL,
    submitted_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    INDEX idx_subs (subs DESC),
    INDEX idx_level (level DESC),
    INDEX idx_won (won),
    INDEX idx_mode (mode),
    INDEX idx_profile (profile_id),
    INDEX idx_submitted (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── ELO Ratings (for ranked multiplayer) ───────────────────────

CREATE TABLE elo_ratings (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    profile_id      INT UNSIGNED NOT NULL,
    elo             INT NOT NULL DEFAULT 1000,
    games_played    INT NOT NULL DEFAULT 0,
    games_won       INT NOT NULL DEFAULT 0,
    decay_days      INT NOT NULL DEFAULT 21,
    last_decay_check DATETIME DEFAULT NULL,
    last_match_played DATETIME DEFAULT NULL,
    is_grand_champion TINYINT(1) NOT NULL DEFAULT 0,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_profile (profile_id),
    INDEX idx_elo (elo DESC),
    INDEX idx_decay_days (decay_days)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Seasons (annual ranked seasons) ─────────────────────────────

CREATE TABLE seasons (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(64) NOT NULL,
    year            INT NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_season_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE season_placements (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    season_id           INT UNSIGNED NOT NULL,
    profile_id          INT UNSIGNED NOT NULL,
    elo                 INT NOT NULL,
    rank_position       INT NOT NULL,
    reward_category     VARCHAR(64) DEFAULT NULL,
    reward_description  VARCHAR(255) DEFAULT NULL,
    recorded_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    INDEX idx_season_rank (season_id, rank_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Matchmaking / Game Sessions (for multiplayer) ──────────────

CREATE TABLE matches (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    room_id         VARCHAR(32) NOT NULL,
    player1_id      INT UNSIGNED NOT NULL,
    player2_id      INT UNSIGNED NOT NULL,
    winner_profile_id INT UNSIGNED DEFAULT NULL,
    mode            VARCHAR(16) NOT NULL DEFAULT 'normal',
    status          ENUM('waiting', 'active', 'finished', 'cancelled') NOT NULL DEFAULT 'waiting',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at     DATETIME DEFAULT NULL,

    FOREIGN KEY (player1_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (player2_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (winner_profile_id) REFERENCES profiles(id) ON DELETE SET NULL,
    UNIQUE KEY uk_room (room_id),
    INDEX idx_status (status),
    INDEX idx_mode (mode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── JWT Blacklist (for token revocation) ───────────────────────

CREATE TABLE jwt_blacklist (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    jti             VARCHAR(64) NOT NULL,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_jti (jti),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Stream Rooms (for Streamer vs Viewers mode) ────────────────

CREATE TABLE stream_rooms (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    streamer_profile_id INT UNSIGNED NOT NULL,
    room_code           VARCHAR(8) NOT NULL,
    stream_url          VARCHAR(512) DEFAULT NULL,
    platform            ENUM('twitch', 'youtube') NOT NULL DEFAULT 'twitch',
    stream_delay        INT NOT NULL DEFAULT 30,
    answer_time_limit   INT NOT NULL DEFAULT 30,
    current_question    INT NOT NULL DEFAULT 1,
    total_questions     INT NOT NULL DEFAULT 15,
    status              ENUM('waiting', 'playing', 'streamer_answered', 'revealed', 'finished') NOT NULL DEFAULT 'waiting',
    answers_closed      TINYINT(1) NOT NULL DEFAULT 0,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (streamer_profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_room_code (room_code),
    INDEX idx_status (status),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Viewer Answers (collected from chat) ────────────────────────

CREATE TABLE viewer_answers (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    room_id             INT UNSIGNED NOT NULL,
    viewer_name         VARCHAR(128) NOT NULL,
    question_number     INT NOT NULL,
    answer_choice       CHAR(1) NOT NULL,
    is_correct          TINYINT(1) NOT NULL DEFAULT 0,
    submitted_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (room_id) REFERENCES stream_rooms(id) ON DELETE CASCADE,
    INDEX idx_room (room_id),
    INDEX idx_question (question_number),
    INDEX idx_viewer (viewer_name),
    INDEX idx_correct (is_correct)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Viewer Stats (live leaderboard for stream rooms) ────────────

CREATE TABLE viewer_stats (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    room_id             INT UNSIGNED NOT NULL,
    viewer_name         VARCHAR(128) NOT NULL,
    correct_count       INT NOT NULL DEFAULT 0,
    total_answered      INT NOT NULL DEFAULT 0,
    last_question       INT NOT NULL DEFAULT 0,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (room_id) REFERENCES stream_rooms(id) ON DELETE CASCADE,
    UNIQUE KEY uk_room_viewer (room_id, viewer_name),
    INDEX idx_correct (correct_count DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Bans (admin moderation) ─────────────────────────────────────────
CREATE TABLE bans (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id             INT UNSIGNED DEFAULT NULL,
    profile_id          INT UNSIGNED DEFAULT NULL,
    reason              VARCHAR(255) DEFAULT NULL,
    banned_by           VARCHAR(64) DEFAULT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at          DATETIME DEFAULT NULL,
    active              TINYINT(1) NOT NULL DEFAULT 1,
    lifted_at           DATETIME DEFAULT NULL,
    lift_reason         VARCHAR(255) DEFAULT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    INDEX idx_banned_user (user_id),
    INDEX idx_banned_profile (profile_id),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Rank history (historize manual and automatic ELO changes) -------
CREATE TABLE rank_history (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    profile_id          INT UNSIGNED NOT NULL,
    old_elo             INT NOT NULL,
    new_elo             INT NOT NULL,
    change_reason       VARCHAR(255) DEFAULT NULL,
    changed_by          VARCHAR(64) DEFAULT NULL,
    recorded_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    INDEX idx_profile (profile_id),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
