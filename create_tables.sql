-- Drop existing tables if they exist
DROP TABLE IF EXISTS listings CASCADE;

-- Create listings table
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    price DECIMAL(10,2),
    size DECIMAL(10,2),
    rooms INTEGER,
    location TEXT,
    url TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);


-- Create indexes
CREATE INDEX idx_listing_id ON listings(listing_id);
CREATE INDEX idx_status ON listings(status);
CREATE INDEX idx_created_at ON listings(created_at);