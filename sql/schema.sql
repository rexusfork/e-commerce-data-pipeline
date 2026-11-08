
CREATE TABLE IF NOT EXISTS sales (
    source_hash VARCHAR(64) PRIMARY KEY,
    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,
    quantity NUMERIC(18, 4) NOT NULL CHECK (quantity > 0),
    invoice_date TIMESTAMP NOT NULL,
    unit_price NUMERIC(18, 4) NOT NULL CHECK (unit_price > 0),
    total_amount NUMERIC(20, 2) NOT NULL,
    customer_id BIGINT,
    country TEXT,
    is_anonymous BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cancellations (
    source_hash VARCHAR(64) PRIMARY KEY,
    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,
    quantity NUMERIC(18, 4) NOT NULL CHECK (quantity < 0),
    invoice_date TIMESTAMP NOT NULL,
    unit_price NUMERIC(18, 4) NOT NULL CHECK (unit_price > 0),
    total_amount NUMERIC(20, 2) NOT NULL,
    customer_id BIGINT,
    country TEXT,
    is_anonymous BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rejected (
    source_hash VARCHAR(64) PRIMARY KEY,
    raw_record JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_invoice_date
ON sales (invoice_date);

CREATE INDEX IF NOT EXISTS idx_sales_customer_id
ON sales (customer_id);

CREATE INDEX IF NOT EXISTS idx_cancellations_invoice_no
ON cancellations (invoice_no);
