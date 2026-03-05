# Deployment — OpenAEC Reports + Authentik SSO

Er zijn twee deployment varianten:

| Variant | Compose file | Caddyfile | Gebruik |
|---------|-------------|-----------|---------|
| **Standalone** | `docker-compose.yml` | `Caddyfile` | Eigen Caddy, verse server |
| **Bestaande Caddy** | `docker-compose.openaec.yml` | `Caddyfile.openaec` | Integratie met bestaande reverse proxy |

---

## Variant A: Standalone (eigen Caddy)

### Architectuur

```
Internet
  │
  ├── report.open-aec.com ──→ Caddy (:443) ──→ openaec-reports (:8000)
  └── auth.open-aec.com   ──→ Caddy (:443) ──→ authentik-server (:9000)
                                               ├── postgresql
                                               └── redis
```

Caddy regelt automatisch TLS-certificaten via Let's Encrypt.

---

## 1. Server voorbereiding

```bash
# SSH naar de server
ssh user@<server-ip>

# Docker + Docker Compose installeren (als nog niet aanwezig)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Deploy directory aanmaken
mkdir -p /opt/openaec
cd /opt/openaec
```

## 2. Bestanden uploaden

Upload de bestanden uit deze `deploy/` directory naar `/opt/openaec/`:

```bash
# Lokaal (vanuit deploy/ directory):
scp docker-compose.yml Caddyfile .env.example user@<server-ip>:/opt/openaec/

# Of via git clone:
git clone https://github.com/OpenAEC-Foundation/openaec-reports.git /tmp/openaec
cp /tmp/openaec/deploy/{docker-compose.yml,Caddyfile,.env.example} /opt/openaec/
```

## 3. Environment configureren

```bash
cd /opt/openaec

# .env aanmaken van template
cp .env.example .env

# Secrets genereren en invullen
AUTHENTIK_SECRET=$(openssl rand -base64 36)
PG_PASS=$(openssl rand -base64 24)
JWT_SECRET=$(openssl rand -base64 36)

sed -i "s|<genereer-met-openssl-rand-base64-36>|$AUTHENTIK_SECRET|" .env
sed -i "0,/<sterk-database-wachtwoord>/s||$PG_PASS|" .env
sed -i "0,/<genereer-met-openssl-rand-base64-36>/s||$JWT_SECRET|" .env

# Controleer
cat .env
```

## 4. DNS instellen

Maak A-records aan die naar het server IP wijzen:

| Record | Type | Waarde |
|--------|------|--------|
| `report.open-aec.com` | A | `<server-ip>` |
| `auth.open-aec.com` | A | `<server-ip>` |

**Let op:** DNS propagatie kan tot 24 uur duren. Caddy probeert automatisch TLS-certificaten op te halen zodra de domeinen bereikbaar zijn.

## 5. Starten

```bash
cd /opt/openaec

# GHCR login (voor private images)
echo $GITHUB_PAT | docker login ghcr.io -u <github-user> --password-stdin

# Alle services starten
docker compose up -d

# Logs volgen (eerste keer ~2 min voor Authentik init)
docker compose logs -f
```

Wacht tot je in de logs ziet:
```
authentik-server  | Starting webserver...
openaec-reports   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 6. Authentik configureren

### 6.1 Admin account

1. Open `https://auth.open-aec.com/if/flow/initial-setup/`
2. Maak het admin account aan (bewaar credentials veilig!)

### 6.2 Custom Scope Mapping

1. Ga naar **Customization → Property Mappings → Create**
2. Kies **Scope Mapping**
3. Vul in:
   - **Name:** `openaec_profile`
   - **Scope name:** `openaec_profile`
   - **Expression:**
     ```python
     return {
         "job_title": request.user.attributes.get("job_title", ""),
         "phone": request.user.attributes.get("phone", ""),
         "registration_number": request.user.attributes.get("registration_number", ""),
         "company": request.user.attributes.get("company", ""),
         "tenant": request.user.attributes.get("tenant", ""),
     }
     ```

### 6.3 OAuth2 Provider

1. Ga naar **Applications → Providers → Create**
2. Kies **OAuth2/OpenID Connect**
3. Vul in:
   - **Name:** `openaec-reports`
   - **Authorization flow:** `default-provider-authorization-implicit-consent`
   - **Client type:** `Public`
   - **Client ID:** `openaec-reports`
   - **Redirect URIs:**
     ```
     https://report.open-aec.com/auth/callback
     http://localhost:5173/auth/callback
     ```
   - **Scopes:** selecteer `openid`, `profile`, `email`, en `openaec_profile`
   - **Subject mode:** `Based on the User's Email`
   - **Signing Key:** kies de standaard RSA key

### 6.4 Application

1. Ga naar **Applications → Applications → Create**
2. Vul in:
   - **Name:** `OpenAEC Reports`
   - **Slug:** `openaec-reports`
   - **Provider:** selecteer de zojuist aangemaakte provider
   - **Launch URL:** `https://report.open-aec.com`

### 6.5 Gebruikers aanmaken

1. Ga naar **Directory → Users → Create**
2. Vul gebruikersgegevens in
3. Voeg custom attributes toe (optioneel):
   ```yaml
   job_title: "Constructeur"
   phone: "078 7400 250"
   registration_number: "IBS-12345"
   company: "OpenAEC"
   tenant: "default"
   ```

## 7. Verificatie

```bash
# Health check
curl https://report.open-aec.com/api/health

# OIDC config check (moet enabled: true tonen)
curl https://report.open-aec.com/api/auth/oidc/config

# Authentik discovery
curl https://auth.open-aec.com/application/o/openaec-reports/.well-known/openid-configuration
```

Open `https://report.open-aec.com` — je zou nu de **"Inloggen via SSO"** knop moeten zien.

---

## Beheer

### Updaten

```bash
cd /opt/openaec

# Nieuwste image ophalen
docker compose pull openaec-reports

# Herstart (zero-downtime met health check)
docker compose up -d openaec-reports
```

### Logs bekijken

```bash
# Alle services
docker compose logs -f

# Specifieke service
docker compose logs -f openaec-reports
docker compose logs -f authentik-server
```

### Backup

```bash
# Database backup (Authentik)
docker compose exec postgresql pg_dump -U authentik authentik > authentik_backup.sql

# OpenAEC data
docker compose cp openaec-reports:/app/data ./backup_data/
docker compose cp openaec-reports:/app/uploads ./backup_uploads/
```

### Stoppen

```bash
docker compose down          # Stop, behoud volumes
docker compose down -v       # Stop EN verwijder volumes (DATA VERLIES!)
```

---

## Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| SSO knop niet zichtbaar | Check `curl .../api/auth/oidc/config` — `enabled` moet `true` zijn |
| TLS certificaat mislukt | DNS A-records controleren, port 80/443 open? |
| Authentik start niet | `docker compose logs authentik-server` — check PostgreSQL connectie |
| OIDC login faalt | Redirect URI in Authentik provider controleren |
| Cookie werkt niet cross-domain | `OPENAEC_COOKIE_DOMAIN` moet `.open-aec.com` zijn (met punt) |

---

## Variant B: Bestaande Caddy (open-aec.com)

Voor deployment op een VPS waar al een Caddy reverse proxy draait (bijv. Hetzner).
Gebruikt `docker-compose.openaec.yml` — geen eigen Caddy, verbindt via extern Docker netwerk.

### Architectuur

```
Internet
  │
  ├── report.open-aec.com ──→ Bestaande Caddy ──→ openaec-reports (:8000)
  └── auth.open-aec.com    ──→ Bestaande Caddy ──→ authentik-server (:9000)
                                                    ├── postgresql  ┐
                                                    └── redis       ┘ internal network
```

### B1. DNS instellen

Maak A-records aan die naar het server IP wijzen:

| Record | Type | Waarde |
|--------|------|--------|
| `report.open-aec.com` | A | `<server-ip>` |
| `auth.open-aec.com` | A | `<server-ip>` |

### B2. Caddy netwerk opzoeken

```bash
# Op de VPS: zoek de netwerknaam van het bestaande Caddy netwerk
docker network ls | grep caddy

# Voorbeeld output:
# a1b2c3d4e5f6   caddy_net   bridge   local
```

Noteer de netwerknaam (bijv. `caddy_net`).

### B3. Bestanden uploaden

```bash
# Lokaal (vanuit deploy/ directory):
scp docker-compose.openaec.yml Caddyfile.openaec .env.openaec.example \
    user@<server-ip>:/opt/openaec/

# Of via git clone:
git clone https://github.com/OpenAEC-Foundation/openaec-reports.git /tmp/openaec
cp /tmp/openaec/deploy/{docker-compose.openaec.yml,Caddyfile.openaec,.env.openaec.example} \
   /opt/openaec/
```

### B4. Environment configureren

```bash
cd /opt/openaec

# .env aanmaken van template
cp .env.openaec.example .env

# Secrets genereren en invullen
AUTHENTIK_SECRET=$(openssl rand -base64 36)
PG_PASS=$(openssl rand -base64 24)
JWT_SECRET=$(openssl rand -base64 36)

sed -i "s|<genereer-met-openssl-rand-base64-36>|$AUTHENTIK_SECRET|" .env
sed -i "0,/<sterk-database-wachtwoord>/s||$PG_PASS|" .env
sed -i "0,/<genereer-met-openssl-rand-base64-36>/s||$JWT_SECRET|" .env

# Caddy netwerk invullen (indien anders dan caddy_net)
# sed -i "s|CADDY_NETWORK=caddy_net|CADDY_NETWORK=<jouw-netwerk>|" .env

# Controleer
cat .env
```

### B5. Starten

```bash
cd /opt/openaec

# GHCR login (voor private images)
echo $GITHUB_PAT | docker login ghcr.io -u <github-user> --password-stdin

# Alle services starten
docker compose -f docker-compose.openaec.yml up -d

# Logs volgen (eerste keer ~2 min voor Authentik init)
docker compose -f docker-compose.openaec.yml logs -f
```

### B6. Caddyfile snippet toevoegen

```bash
# Voeg de inhoud van Caddyfile.openaec toe aan de bestaande Caddyfile
cat /opt/openaec/Caddyfile.openaec >> /path/to/Caddyfile

# Herlaad Caddy
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### B7. Authentik configureren

Volg stappen 6.1 t/m 6.5 uit Variant A, maar met deze aangepaste waarden:

| Instelling | Waarde |
|-----------|--------|
| Admin setup URL | `https://auth.open-aec.com/if/flow/initial-setup/` |
| Redirect URIs | `https://report.open-aec.com/auth/callback` + `http://localhost:5173/auth/callback` |
| Launch URL | `https://report.open-aec.com` |

### B8. Eerste admin user aanmaken

```bash
docker compose -f docker-compose.openaec.yml exec openaec-reports \
    openaec-report create-user \
    --username admin --password <wachtwoord> --email admin@open-aec.com --admin
```

### B9. Verificatie

```bash
# Health check
curl https://report.open-aec.com/api/health

# OIDC config check (moet enabled: true tonen)
curl https://report.open-aec.com/api/auth/oidc/config

# Authentik discovery
curl https://auth.open-aec.com/application/o/openaec-reports/.well-known/openid-configuration
```

Open `https://report.open-aec.com` — je zou nu de **"Inloggen via SSO"** knop moeten zien.

### Beheer (Variant B)

```bash
# Updaten
docker compose -f docker-compose.openaec.yml pull openaec-reports
docker compose -f docker-compose.openaec.yml up -d openaec-reports

# Logs
docker compose -f docker-compose.openaec.yml logs -f openaec-reports

# Stoppen
docker compose -f docker-compose.openaec.yml down          # Behoud volumes
docker compose -f docker-compose.openaec.yml down -v       # DATA VERLIES!
```

### Troubleshooting (Variant B)

| Probleem | Oplossing |
|----------|-----------|
| Container niet bereikbaar via Caddy | Check of container in `caddy_net` zit: `docker network inspect caddy_net` |
| Netwerk niet gevonden | `CADDY_NETWORK` in `.env` moet matchen met bestaand netwerk |
| Cookie werkt niet cross-domain | `OPENAEC_COOKIE_DOMAIN` moet `.open-aec.com` zijn (met punt) |
| TLS certificaat mislukt | DNS A-records controleren, bestaande Caddy moet poort 80/443 open hebben |
