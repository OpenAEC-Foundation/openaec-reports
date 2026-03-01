"""Compare generated PDF with reference PDF text positions."""

from __future__ import annotations

import fitz


def compare_pdfs(ref_path: str, gen_path: str) -> None:
    """Compare text positions between reference and generated PDFs."""
    ref = fitz.open(ref_path)
    gen = fitz.open(gen_path)

    print(f"Reference: {ref.page_count} pages")
    print(f"Generated: {gen.page_count} pages")

    for i in range(min(ref.page_count, gen.page_count)):
        r_page = ref[i]
        g_page = gen[i]
        r_w = r_page.rect.width / 2.8346
        r_h = r_page.rect.height / 2.8346
        g_w = g_page.rect.width / 2.8346
        g_h = g_page.rect.height / 2.8346
        print(f"\nPage {i}: ref={r_w:.0f}x{r_h:.0f}mm  gen={g_w:.0f}x{g_h:.0f}mm")

        r_text = r_page.get_text("dict")
        r_count = sum(
            1
            for b in r_text.get("blocks", [])
            if b.get("type") == 0
            for l in b.get("lines", [])
            for s in l.get("spans", [])
            if s.get("text", "").strip()
        )
        g_text = g_page.get_text("dict")
        g_count = sum(
            1
            for b in g_text.get("blocks", [])
            if b.get("type") == 0
            for l in b.get("lines", [])
            for s in l.get("spans", [])
            if s.get("text", "").strip()
        )
        print(f"  Text spans: ref={r_count}  gen={g_count}")

    # Show generated text per page
    for page_idx in range(gen.page_count):
        g_page = gen[page_idx]
        g_text = g_page.get_text("dict")
        spans = []
        for b in g_text.get("blocks", []):
            if b.get("type") != 0:
                continue
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    text = s.get("text", "").strip()
                    if text:
                        x_mm = s["origin"][0] / 2.8346
                        y_mm = s["origin"][1] / 2.8346
                        spans.append((x_mm, y_mm, s["size"], s["font"], text))

        if spans:
            w_mm = g_page.rect.width / 2.8346
            h_mm = g_page.rect.height / 2.8346
            print(f"\n=== Generated page {page_idx} ({w_mm:.0f}x{h_mm:.0f}mm) ===")
            for x_mm, y_mm, size, font, text in spans:
                print(
                    f"  x={x_mm:6.1f} y={y_mm:6.1f} size={size:4.1f} "
                    f"font={font[:20]:20s} | {text[:60]}"
                )

    ref.close()
    gen.close()


if __name__ == "__main__":
    compare_pdfs(
        "output/customer_bic_test.pdf",
        "output/test_template_e2e.pdf",
    )
