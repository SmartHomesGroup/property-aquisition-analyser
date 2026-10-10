-- Core schema. Raw sources land in `core.*` typed tables; derived analysis lives in `map.*`.
-- Coordinates are British National Grid (EPSG:27700) throughout; tiles are produced in 3857.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS core;   -- loaded source data, lightly typed
CREATE SCHEMA IF NOT EXISTS map;    -- derived aggregates and tile functions
CREATE SCHEMA IF NOT EXISTS meta;   -- build bookkeeping

CREATE TABLE IF NOT EXISTS meta.build_info (
    key        text PRIMARY KEY,
    value      text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- OS Code-Point Open: one row per current GB unit postcode, centroid in BNG.
-- Postcodes are stored normalised: upper case, no spaces.
CREATE TABLE IF NOT EXISTS core.postcode (
    postcode      text PRIMARY KEY,
    pqi           smallint NOT NULL,          -- positional quality indicator (10 best .. 90 none)
    easting       integer,
    northing      integer,
    country_code  text,                       -- GSS: E92000001 England, W92000004 Wales, ...
    district_code text,                       -- GSS local authority district; joins UK HPI AreaCode
    geom          geometry(Point, 27700)
);
CREATE INDEX IF NOT EXISTS postcode_geom_gist ON core.postcode USING gist (geom);

-- UK House Price Index, unpivoted. property_type 'A' = all types; D/S/T/F match PPD codes.
CREATE TABLE IF NOT EXISTS core.hpi (
    area_code     text NOT NULL,
    month         date NOT NULL,              -- first of month
    property_type char(1) NOT NULL,
    idx           numeric NOT NULL,
    PRIMARY KEY (area_code, month, property_type)
);

-- HM Land Registry Price Paid Data, one row per transaction.
CREATE TABLE IF NOT EXISTS core.sale (
    transaction_id   uuid PRIMARY KEY,
    price            integer NOT NULL,
    date_of_transfer date NOT NULL,
    postcode         text,                    -- normalised; NULL when PPD has none
    property_type    char(1) NOT NULL,        -- D S T F O
    new_build        boolean NOT NULL,
    tenure           char(1),                 -- F L U
    paon             text,
    saon             text,
    street           text,
    locality         text,
    town             text,
    district         text,
    county           text,
    ppd_category     char(1) NOT NULL,        -- A standard, B additional
    record_status    char(1) NOT NULL DEFAULT 'A'  -- A add, C change, D delete
);
CREATE INDEX IF NOT EXISTS sale_postcode_idx ON core.sale (postcode);
CREATE INDEX IF NOT EXISTS sale_date_idx ON core.sale (date_of_transfer);

-- HM Land Registry transaction -> UPRN lookup (monthly, from Aug 2026; not back-dated).
CREATE TABLE IF NOT EXISTS core.sale_uprn (
    transaction_id uuid PRIMARY KEY,
    uprn           bigint NOT NULL
);

-- Domestic EPC certificates (England & Wales). Only the columns we use.
CREATE TABLE IF NOT EXISTS core.epc (
    certificate_number     text PRIMARY KEY,
    uprn                   bigint,
    uprn_source            text,
    address1               text,
    address2               text,
    address3               text,
    postcode               text,              -- normalised
    property_type          text,              -- House, Flat, Bungalow, Maisonette, Park home
    built_form             text,              -- Detached, Semi-Detached, Mid-Terrace, ...
    total_floor_area       numeric,           -- m²
    lodgement_date         date,
    current_energy_rating  char(1),
    construction_age_band  text,
    number_habitable_rooms smallint,
    extension_count        smallint
);
CREATE INDEX IF NOT EXISTS epc_postcode_idx ON core.epc (postcode);
CREATE INDEX IF NOT EXISTS epc_uprn_idx ON core.epc (uprn);
