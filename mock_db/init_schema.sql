-- users 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('male', 'female', 'other')),
    birth_date DATE,
    country TEXT,
    city TEXT,
    signup_date DATE NOT NULL,
    account_status TEXT DEFAULT 'active' CHECK(account_status IN ('active', 'dormant', 'deleted')),
    is_adult_verified INTEGER DEFAULT 0,
    last_login_date DATE,
    device_last_used TEXT,
    push_opt_in INTEGER DEFAULT 1
);

-- tmdb_contents 테이블
CREATE TABLE IF NOT EXISTS tmdb_contents (
    content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    original_title TEXT,
    content_type TEXT CHECK(content_type IN ('movie', 'tv')),
    genre_ids TEXT,
    release_date DATE,
    runtime INTEGER,
    country TEXT,
    adult_only INTEGER DEFAULT 0,
    popularity REAL,
    vote_average REAL
);

-- subscription_plans 테이블
CREATE TABLE IF NOT EXISTS subscription_plans (
    subscription_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    duration_days INTEGER DEFAULT 30,
    max_devices INTEGER DEFAULT 1,
    quality TEXT CHECK(quality IN ('SD', 'HD', 'UHD'))
);

-- user_subscriptions 테이블
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'expired')),
    auto_renew_flag INTEGER DEFAULT 1,
    cancel_reserved_flag INTEGER DEFAULT 0,
    payment_method TEXT,
    trial_used_flag INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (subscription_id) REFERENCES subscription_plans(subscription_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_status ON users(account_status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);