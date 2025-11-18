-- Create the main stocks table to hold company info
CREATE TABLE IF NOT EXISTS stocks (
    stock_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(100),
    sector VARCHAR(50)
);

-- Create the table for daily time-series price data
CREATE TABLE IF NOT EXISTS daily_price_data (
    price_id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(stock_id),
    date DATE NOT NULL,
    open_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    adjusted_close_price NUMERIC(10, 2),
    volume BIGINT,
    UNIQUE (stock_id, date) 
);

-- Create the table for calculated features/indicators
CREATE TABLE IF NOT EXISTS features (
    feature_id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(stock_id),
    date DATE NOT NULL,
    sma_50 NUMERIC(10, 2),
    sma_200 NUMERIC(10, 2),
    rsi_14 NUMERIC(5, 2),
    macd_value NUMERIC(10, 2),
    macd_signal NUMERIC(10, 2),
    UNIQUE (stock_id, date)
);

-- Create the table to store the final daily recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    rank INTEGER NOT NULL,
    stock_id INTEGER NOT NULL REFERENCES stocks(stock_id),
    final_score NUMERIC(6, 3),
    algorithm_scores JSONB, 
    UNIQUE (date, rank)
);

-- Create indexes for faster queries on foreign keys and dates
CREATE INDEX ON daily_price_data (stock_id, date DESC);
CREATE INDEX ON features (stock_id, date DESC);
CREATE INDEX ON recommendations (date DESC);

-- Let's add the NIFTY 50 stocks for convenience
INSERT INTO stocks (symbol, company_name) VALUES
    ('ADANIENT', 'Adani Enterprises Ltd.'),
    ('ADANIPORTS', 'Adani Ports and Special Economic Zone Ltd.'),
    ('APOLLOHOSP', 'Apollo Hospitals Enterprise Ltd.'),
    ('ASIANPAINT', 'Asian Paints Ltd.'),
    ('AXISBANK', 'Axis Bank Ltd.'),
    ('BAJAJ-AUTO', 'Bajaj Auto Ltd.'),
    ('BAJFINANCE', 'Bajaj Finance Ltd.'),
    ('BAJAJFINSV', 'Bajaj Finserv Ltd.'),
    ('BPCL', 'Bharat Petroleum Corporation Ltd.'),
    ('BHARTIARTL', 'Bharti Airtel Ltd.'),
    ('BRITANNIA', 'Britannia Industries Ltd.'),
    ('CIPLA', 'Cipla Ltd.'),
    ('COALINDIA', 'Coal India Ltd.'),
    ('DIVISLAB', 'Divis Laboratories Ltd.'),
    ('DRREDDY', 'Dr. Reddys Laboratories Ltd.'),
    ('EICHERMOT', 'Eicher Motors Ltd.'),
    ('GRASIM', 'Grasim Industries Ltd.'),
    ('HCLTECH', 'HCL Technologies Ltd.'),
    ('HDFCBANK', 'HDFC Bank Ltd.'),
    ('HDFCLIFE', 'HDFC Life Insurance Company Ltd.'),
    ('HEROMOTOCO', 'Hero MotoCorp Ltd.'),
    ('HINDALCO', 'Hindalco Industries Ltd.'),
    ('HINDUNILVR', 'Hindustan Unilever Ltd.'),
    ('ICICIBANK', 'ICICI Bank Ltd.'),
    ('ITC', 'ITC Ltd.'),
    ('INDUSINDBK', 'IndusInd Bank Ltd.'),
    ('INFY', 'Infosys Ltd.'),
    ('JSWSTEEL', 'JSW Steel Ltd.'),
    ('KOTAKBANK', 'Kotak Mahindra Bank Ltd.'),
    ('LTIM', 'LTIMindtree Ltd.'),
    ('LT', 'Larsen & Toubro Ltd.'),
    ('M&M', 'Mahindra & Mahindra Ltd.'),
    ('MARUTI', 'Maruti Suzuki India Ltd.'),
    ('NTPC', 'NTPC Ltd.'),
    ('NESTLEIND', 'Nestle India Ltd.'),
    ('ONGC', 'Oil & Natural Gas Corporation Ltd.'),
    ('POWERGRID', 'Power Grid Corporation of India Ltd.'),
    ('RELIANCE', 'Reliance Industries Ltd.'),
    ('SBILIFE', 'SBI Life Insurance Company Ltd.'),
    ('SBIN', 'State Bank of India'),
    ('SUNPHARMA', 'Sun Pharmaceutical Industries Ltd.'),
    ('TCS', 'Tata Consultancy Services Ltd.'),
    ('TATACONSUM', 'Tata Consumer Products Ltd.'),
    ('TATAMOTORS', 'Tata Motors Ltd.'),
    ('TATASTEEL', 'Tata Steel Ltd.'),
    ('TECHM', 'Tech Mahindra Ltd.'),
    ('TITAN', 'Titan Company Ltd.'),
    ('ULTRACEMCO', 'UltraTech Cement Ltd.'),
    ('UPL', 'UPL Ltd.'),
    ('WIPRO', 'Wipro Ltd.')
ON CONFLICT (symbol) DO NOTHING; 