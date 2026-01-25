CREATE TABLE points (
    user_id BIGINT PRIMARY KEY,
    points INTEGER DEFAULT 0
);

CREATE TABLE config (
    guild_id BIGINT PRIMARY KEY,
    points_channel BIGINT
);

CREATE TABLE salaries (
    user_id BIGINT PRIMARY KEY,
    last_salary REAL
);

CREATE TABLE antifarm (
    user_id BIGINT PRIMARY KEY,
    last_msg TEXT,
    last_time REAL
);

CREATE TABLE cooldowns (
    user_id BIGINT PRIMARY KEY,
    last_message REAL
);
