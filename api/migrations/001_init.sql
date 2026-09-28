CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE drops (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  total_stock INT NOT NULL CHECK (total_stock >= 0),
  available_stock INT NOT NULL CHECK (available_stock >= 0),  -- DB refuses negative stock
  starts_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drop_id UUID NOT NULL REFERENCES drops(id),
  user_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','completed','expired')),
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One ACTIVE reservation per user per drop, enforced by the database
CREATE UNIQUE INDEX one_active_reservation_per_user
  ON reservations (drop_id, user_id) WHERE status = 'active';

-- The worker scans this
CREATE INDEX reservations_expiry_idx
  ON reservations (expires_at) WHERE status = 'active';

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID NOT NULL UNIQUE REFERENCES reservations(id),
  status TEXT NOT NULL DEFAULT 'reserved'
    CHECK (status IN ('reserved','payment_pending','paid','confirmed',
                      'expired','failed','refunded')),
  payment_intent_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_transitions (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('user','webhook','worker')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE idempotency_keys (
  key TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  status_code INT,
  response_body JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (key, endpoint)
);

CREATE TABLE webhook_events (
  event_id TEXT PRIMARY KEY,           -- dedupe duplicates
  event_type TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);