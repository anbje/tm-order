-- Translation Order Management Database Schema

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    customer_name VARCHAR(255) NOT NULL,
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL,
    word_count INTEGER,
    topic TEXT,
    deadline_at TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reminder_sent BOOLEAN DEFAULT FALSE,
    source_file_path TEXT,
    target_file_path TEXT,
    telegram_user_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_deadline ON orders(deadline_at);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_telegram_user ON orders(telegram_user_id);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample customer for testing
INSERT INTO customers (name, email) VALUES 
    ('Test Customer', 'test@example.com')
ON CONFLICT DO NOTHING;
