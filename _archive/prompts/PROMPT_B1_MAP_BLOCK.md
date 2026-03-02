# Fase B1: KadasterMap flowable afmaken (PDOK WMS integratie)

## Context

De `KadasterMap` flowable in `src/openaec_reports/components/map_block.py` is een lege shell — alle methoden gooien `NotImplementedError`. Maar de benodigde logica staat al grotendeels in `src/openaec_reports/data/kadaster.py` (`KadasterClient`). De map_block moet de KadasterClient **gebruiken**, niet dupliceren.

Bekijk voor je begint:
- `src/openaec_reports/data/kadaster.py` — WMS client met `wgs84_to_rd()` en `get_map()`
- `src/openaec_reports/components/image_block.py` — referentie voor het Flowable patroon (wrap/draw via intern Table)
- `src/openaec_reports/components/calculation.py` — referentie voor styling (BM_COLORS, BM_FONTS)
- `src/openaec_reports/core/styles.py` — BM_COLORS, BM_STYLES
- `src/openaec_reports/core/block_registry.py` — factory functie `create_map()` (al geregistreerd)

## Wat er moet gebeuren

### 1. Refactor `map_block.py` — gebruik KadasterClient

Verwijder alle TODO/NotImplementedError methoden. De KadasterMap moet:

1. **In `__init__`:** KadasterClient instantie aanmaken met optionele cache_dir
2. **`_fetch_map() → Path`:** Kaartlagen ophalen, compositen, cachen
3. **`wrap()`:** Afmetingen berekenen, `_fetch_map()` aanroepen
4. **`draw()`:** PNG renderen op canvas + caption + optionele schaalbalkindicatie

### 2. Composiet rendering (meerdere lagen)

De frontend stuurt `layers: ["percelen", "bebouwing", "luchtfoto", ...]`. Elke laag komt van een andere PDOK WMS service met andere laagnamen.

**Mapping van frontend laagnamen → PDOK WMS parameters:**

```python
LAYER_CONFIG = {
    "percelen": {
        "service": "kadaster",
        "layers": "Perceel,OpenbareRuimteNaam",
    },
    "bebouwing": {
        "service": "bag",
        "layers": "pand",
    },
    "bestemmingsplan": {
        "service": "kadaster",  # TODO: bestemmingsplan via ruimtelijkeplannen.nl — voor nu skip
        "layers": "Perceel",
    },
    "luchtfoto": {
        "service": "luchtfoto",
        "layers": "Actueel_orthoHR",
    },
}
```

**Composiet strategie:**
1. Als "luchtfoto" in layers → haal luchtfoto op als basis (opaque)
2. Haal overige lagen op met `transparent=true`
3. Composiet met Pillow: `base.paste(overlay, mask=overlay)` per laag
4. Sla composiet op als PNG

Dit vereist Pillow (`PIL`). Controleer of Pillow al een dependency is (het zou moeten via ReportLab). Zo niet, gebruik het NIET — render dan alleen de eerste laag en log een warning.

**Alternatief zonder Pillow:** Als composiet te complex is, haal per laag een aparte image op en teken ze als gestapelde `canvas.drawImage()` calls in `draw()`. ReportLab canvas ondersteunt transparante PNG overlays. Dit is eenvoudiger en vermijdt een extra dependency.

Kies de canvas-stack aanpak (geen Pillow dependency).

### 3. Caching

Gebruik een deterministische cache key:
```python
import hashlib
cache_key = hashlib.md5(f"{lat}:{lon}:{radius}:{sorted(layers)}:{width_px}:{height_px}".encode()).hexdigest()
cache_path = cache_dir / f"map_{cache_key}.png"
```

Default cache_dir: `tempfile.gettempdir() / "bm_maps"`. Controleer of cached file bestaat en niet ouder dan 24 uur.

### 4. Graceful fallback

Als PDOK niet bereikbaar is (timeout, DNS, HTTP error):
- Log een warning
- Render een placeholder: grijs vlak met tekst "Kaart niet beschikbaar" + coördinaten + gewenste lagen
- Gebruik `canvas.drawString()` in `draw()` voor de placeholder

### 5. Caption en schaalbalk

Onder de kaart:
- Caption (als opgegeven) in `BM_STYLES["Caption"]`
- Schaalbalk: simpele lijn met label "≈{radius*2}m" — exact als de ImageBlock caption pattern

### 6. Layout

Gebruik hetzelfde Table-wrapper patroon als `ImageBlock`:
- Rij 1: kaartafbeelding (of placeholder)
- Rij 2: caption (optioneel)
- Rij 3: schaalbalk tekst (optioneel)
- Turquoise linker accent-lijn (zoals CalculationBlock)

## Implementatie structuur

```python
class KadasterMap(Flowable):
    LAYER_CONFIG = { ... }  # mapping hierboven
    
    def __init__(self, latitude, longitude, radius_m, width_mm, height_mm, layers, caption, cache_dir):
        self._client = KadasterClient(cache_dir=cache_dir or Path(tempfile.gettempdir()) / "bm_maps")
        ...
    
    def _cache_key(self) -> str: ...
    def _get_cached(self) -> Path | None: ...
    def _fetch_layers(self) -> list[Path]: ...  # per laag een PNG
    def _build_content(self, available_width) -> Table: ...
    def wrap(self, aw, ah): ...
    def draw(self): ...
```

## Tests

Maak `tests/test_map_block.py` met:

1. **Unit test:** `KadasterMap` instantie aanmaken met default parameters → geen crash
2. **Unit test:** `LAYER_CONFIG` bevat alle verwachte lagen
3. **Unit test:** Cache key is deterministic (zelfde input → zelfde key)
4. **Mock test:** Mock `KadasterClient.get_map()` → retourneer een 1x1 witte PNG bytes → controleer dat `_fetch_layers()` bestanden schrijft
5. **Mock test:** Mock `requests.Session.get` om timeout te simuleren → controleer dat placeholder gerendered wordt (geen crash)
6. **Integratie test:** Maak een rapport met een map block via `Report.from_dict()` + `report.build()` → PDF wordt gegenereerd (mock de HTTP calls)

**Belangrijk:** De integratie test moet PDOK NIET daadwerkelijk aanroepen. Mock `KadasterClient.get_map` altijd in tests.

## Verificatie

Na implementatie:
```bash
python -m pytest tests/test_map_block.py -v
python -m pytest tests/ -v  # regressie check
```

Optioneel (handmatig, met internet):
```python
from openaec_reports import A4, Report
report = Report(format=A4, project="Map Test", brand="3bm_cooperatie")
report.add_cover(subtitle="Kadaster test")
report.add_section("Locatie", content=[])
# Handmatig een map block toevoegen via from_dict
import json
data = {
    "template": "structural",
    "project": "Map Test",
    "sections": [{
        "title": "Locatie",
        "content": [{
            "type": "map",
            "center": {"lat": 51.8125, "lon": 4.6757},
            "radius_m": 150,
            "layers": ["luchtfoto", "percelen"],
            "caption": "Projectlocatie — Nieuw-Lekkerland"
        }]
    }]
}
report = Report.from_dict(data, brand="3bm_cooperatie")
report.build("output/map_test.pdf")
```
