#!/usr/bin/env python3
"""Write the sample store-credit PDF into data/wiki/."""

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "wiki" / "13-store-credit-terms.pdf"

BODY = [
    ("Store credit terms", "h1"),
    (
        "This page is the written rule for VoltPath store credit. CX should quote it "
        "instead of improvising expiry dates or cash-out exceptions.",
        "p",
    ),
    ("When we issue credit", "h2"),
    (
        "Store credit is issued for trade-ins after inspection, for approved goodwill, "
        "and when a rider chooses credit instead of a card refund. The returns policy "
        "adds 10 percent extra store credit on that choice.",
        "p",
    ),
    ("Expiry and cash-out", "h2"),
    (
        "VoltPath store credits never expire. We do not redeem store credit for cash, "
        "Interac, or a transfer to a different person. The credit lives on the original "
        "customer account in Shopify.",
        "p",
    ),
    ("Combining with promos", "h2"),
    (
        "Store credit can be combined with a current site promo unless the promo page "
        "says otherwise. It cannot be stacked with a second store-credit grant on the "
        "same order without L2 approval.",
        "p",
    ),
    ("Lost or missing credit", "h2"),
    (
        "If a rider says credit is missing, search Zendesk for the original grant. "
        "If we find the ticket, Finance can reissue the same amount. If we cannot find "
        "the ticket, do not recreate the credit. Escalate to L2.",
        "p",
    ),
]


def main() -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    for text, kind in BODY:
        if kind == "h1":
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 10, text)
            pdf.ln(4)
        elif kind == "h2":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, text)
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, text)
            pdf.ln(2)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
