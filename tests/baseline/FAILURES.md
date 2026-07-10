# Baseline render failures

Elke sectie hieronder is een render die is mislukt tijdens `render_baseline.py`. Dit bestand wordt bij elke run aangevuld (niet overschreven) zodat historie behouden blijft.

## openaec_foundation / standaard — 2026-07-10T14:00:52.165742+00:00

```
Traceback (most recent call last):
  File "C:\Github\openaec-reports\scripts\render_baseline.py", line 143, in main
    gen.generate(dict(fixture), stationery_dir, tmp_pdf)
  File "C:\Github\openaec-reports\src\openaec_reports\core\renderer_v2.py", line 2559, in generate
    self._render_content(content, data)
  File "C:\Github\openaec-reports\src\openaec_reports\core\renderer_v2.py", line 2608, in _render_content
    renderer.render_section(section)
  File "C:\Github\openaec-reports\src\openaec_reports\core\renderer_v2.py", line 2220, in render_section
    self.heading_1(number, title)
  File "C:\Github\openaec-reports\src\openaec_reports\core\renderer_v2.py", line 1317, in heading_1
    self._text(n["x"], self.y, number, n["font"], n["size"], n["color"])
               ~^^^^^
KeyError: 'x'
```

