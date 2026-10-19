CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    definition TEXT,
    translation TEXT,
    example TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, word, language)
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    word_id INT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    correct BOOLEAN NOT NULL,
    reviewed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_words_user ON words(user_id);
CREATE INDEX idx_reviews_word ON reviews(word_id);