-- InsightIQ analytical warehouse schema.
-- Local runs use SQLite; production can port these contracts to Postgres/BigQuery.

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    gender TEXT,
    city TEXT,
    signup_date DATE
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT NOT NULL,
    price REAL NOT NULL,
    rating REAL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    order_date TIMESTAMP NOT NULL,
    order_status TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    item_price REAL NOT NULL,
    item_total REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT,
    event_type TEXT NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT,
    product_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    review_text TEXT NOT NULL,
    review_date TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS release_notes (
    release_id TEXT PRIMARY KEY,
    release_date DATE NOT NULL,
    feature_area TEXT NOT NULL,
    release_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    expected_metric TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    feature_area TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    variant TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    lift_pct REAL NOT NULL,
    p_value REAL NOT NULL,
    decision TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feature_flags (
    flag_id TEXT PRIMARY KEY,
    feature_area TEXT NOT NULL,
    flag_name TEXT NOT NULL,
    enabled_pct INTEGER NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engineering_incidents (
    incident_id TEXT PRIMARY KEY,
    incident_date DATE NOT NULL,
    severity TEXT NOT NULL,
    affected_area TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    customer_impact TEXT NOT NULL,
    resolution TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS business_glossary (
    term TEXT PRIMARY KEY,
    definition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_documentation (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_user_date ON orders(user_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(order_status, order_date);
CREATE INDEX IF NOT EXISTS idx_items_product_order ON order_items(product_id, order_id);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_reviews_product_date ON reviews(product_id, review_date);
CREATE INDEX IF NOT EXISTS idx_release_notes_date_area ON release_notes(release_date, feature_area);
CREATE INDEX IF NOT EXISTS idx_experiments_area_dates ON experiments(feature_area, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_incidents_area_date ON engineering_incidents(affected_area, incident_date);

-- Partitioning note:
-- In production, orders/events/reviews should be partitioned by event/order/review date
-- and clustered by workspace_id plus product_id/user_id. SQLite does not support native
-- partitioning, so local runs store compact single-node tables.
