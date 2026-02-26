# Backend Spec: API Key Support (optioneel)

> Status: **Voorstel** — pas implementeren als JWT token caching onvoldoende blijkt  
> Prioriteit: Laag (huidige JWT + DPAPI-oplossing werkt)

---

## Aanleiding

De Report Generator API gebruikt JWT tokens via `/api/auth/login`. 
Voor machine-to-machine integraties (pyRevit, MCP, CI/CD) is een statische 
API key eenvoudiger dan een login-flow met token refresh.

De **huidige oplossing** (client-side) lost dit op met:
- Windows DPAPI-encrypted credential opslag
- Automatische login + token caching
- Auto-refresh bij verlopen token

Als dit onvoldoende blijkt (bijv. bij server-side integraties zonder 
Windows, of als je geen wachtwoord wilt opslaan), kan API Key support 
worden toegevoegd.

---

## Wat er zou moeten veranderen

### 1. Nieuw model: `ApiKey`

```python
# In auth/models.py

class ApiKey:
    id: str              # UUID
    name: str            # Beschrijving ("pyRevit werkstation Jochem")
    key_hash: str        # bcrypt hash van de key
    key_prefix: str      # Eerste 8 chars voor identificatie ("3bm_a1b2...")
    user_id: str         # Gekoppelde user
    created_at: datetime
    expires_at: Optional[datetime]  # None = nooit
    is_active: bool
```

Database: nieuwe tabel `api_keys` in bestaande `auth.db`.

### 2. Token extractie uitbreiden

```python
# In auth/dependencies.py, _extract_token() aanvullen:

def _extract_token(request: Request) -> str | None:
    # 1. Cookie (browser)
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    # 2. Bearer token (pyRevit / scripts)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 3. NIEUW: API Key header
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return _validate_api_key(api_key)  # retourneert een JWT of None

    return None
```

### 3. Admin endpoints

| Methode | Endpoint | Omschrijving |
|---------|----------|--------------|
| `POST` | `/api/admin/api-keys` | Nieuwe key aanmaken (retourneert plaintext key éénmalig) |
| `GET` | `/api/admin/api-keys` | Lijst actieve keys (zonder plaintext) |
| `DELETE` | `/api/admin/api-keys/{id}` | Key intrekken |

### 4. Key formaat

```
3bm_sk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
     ^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     prefix (8 chars)   random (32 chars)
```

- Prefix `3bm_sk_` voor herkenbaarheid
- 40 chars random hex
- Wordt bij aanmaak éénmalig getoond, daarna alleen hash opgeslagen

---

## Geschatte impact

- **Bestanden:** `auth/models.py`, `auth/dependencies.py`, `admin/routes.py`
- **Effort:** ~2-3 uur
- **Breaking changes:** Geen — uitbreiding op bestaande auth flow
- **Migratie:** Nieuwe SQLite tabel, geen bestaande data geraakt

---

## Voorlopige conclusie

**Niet nodig op korte termijn.** De client-side JWT caching met DPAPI 
dekt de pyRevit use case volledig. API keys worden pas relevant bij:
- CI/CD pipelines die rapporten genereren
- Integraties vanaf Linux/Mac (geen DPAPI beschikbaar)
- Multi-user omgevingen met gedeelde service accounts
