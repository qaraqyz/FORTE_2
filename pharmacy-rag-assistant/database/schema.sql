CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    region VARCHAR(100) NOT NULL,
    pharmacy VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    product VARCHAR(255) NOT NULL,
    units_sold INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    cost_price DECIMAL(10, 2) NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    profit DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50),
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_region ON sales(region);
CREATE INDEX idx_sales_pharmacy ON sales(pharmacy);
CREATE INDEX idx_sales_category ON sales(category);
CREATE INDEX idx_sales_product ON sales(product);