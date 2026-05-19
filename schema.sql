
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mood INTEGER CHECK(mood BETWEEN 1 AND 5),
    work_hours REAL CHECK(work_hours >= 0),
    sleep_hours REAL CHECK(sleep_hours >= 0),
    comment TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE INDEX idx_user_date ON daily_logs(user_id, date);
CREATE INDEX idx_mood ON daily_logs(mood);
CREATE INDEX idx_work_hours ON daily_logs(work_hours);
CREATE INDEX idx_sleep_hours ON daily_logs(sleep_hours);