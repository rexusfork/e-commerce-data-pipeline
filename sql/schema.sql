
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


-- Pipeline execution history
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id BIGSERIAL PRIMARY KEY,
    source_key TEXT NOT NULL,
    file_checksum CHAR(64) NOT NULL,

    status VARCHAR(20) NOT NULL
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,

    duration_seconds DOUBLE PRECISION,
    metrics JSONB,

    error_message TEXT
);

-- Speed up successful-file lookup
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_lookup
ON pipeline_runs (
    source_key,
    file_checksum
)
WHERE status = 'SUCCESS';

-- Query latest pipeline executions
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started
ON pipeline_runs (started_at DESC);
