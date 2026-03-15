# Build context: monorepo root (docker build -f rust/Dockerfile .)
#
# ---- Stage 1: Frontend build ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Rust build ----
FROM rust:1.88-bookworm AS builder

WORKDIR /build

# Copy workspace and all crates
COPY rust/Cargo.toml ./
COPY rust/crates/ ./crates/

# Build the server binary in release mode
RUN cargo build --release -p openaec-server

# ---- Stage 3: Runtime ----
FROM debian:bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from builder
COPY --from=builder /build/target/release/openaec-server /app/openaec-server

# Copy frontend dist from stage 1
COPY --from=frontend-build /app/frontend/dist /app/static

# Copy font assets (Liberation Sans for fallback rendering)
COPY src/openaec_reports/assets/fonts/ /app/fonts/

# Environment
ENV OPENAEC_FONTS_DIR=/app/fonts
ENV OPENAEC_STATIC_DIR=/app/static

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8001/api/health || exit 1

CMD ["/app/openaec-server"]
