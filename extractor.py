import pandas as pd
import re
from typing import List, Tuple, Optional

# --------------------------
# CONFIG: final fixed columns
# --------------------------
FINAL_COLUMNS = [
    "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File",
    "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
    "Discount(%)", "Discount Amount",
    "IGST(%)", "IGST Amount",
    "CGST(%)", "CGST Amount",
    "SGST(%)", "SGST Amount",
    "Net Amount"
]

# --------------------------
# Header synonyms mapping
# --------------------------
HEADER_MAP = {
    # invoice / metadata
    "invoice no": "Invoice No", "invoice number": "Invoice No", "inv no": "Invoice No", "bill no": "Invoice No",

    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN", "our gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN", "recipient gstin": "Customer GSTIN",
    "gstin": "Supplier GSTIN",  # fallback if only one

    # item columns
    "hsn": "HSN", "hsn code": "HSN",
    "item": "Item Name", "description": "Item Name", "product": "Item Name", "item name": "Item Name",
    "particulars": "Item Name",

    "qty": "Quantity", "quantity": "Quantity", "qnty": "Quantity",

    "rate": "Rate", "price": "Rate", "unit price": "Rate",

    # amounts
    "amount": "Gross Amount", "gross": "Gross Amount", "gross amount": "Gross Amount", "taxable value": "Gross Amount",

    # discount
    "discount": "Discount(%)", "discount%": "Discount(%)", "disc%": "Discount(%)",
    "discount amount": "Discount Amount", "disc amount": "Discount Amount",

    # IGST/CGST/SGST
    "igst": "IGST(%)", "igst%": "IGST(%)", "igst amount": "IGST Amount",
    "cgst": "CGST(%)", "cgst%": "CGST(%)", "cgst amount": "CGST Amount",
    "sgst": "SGST(%)", "sgst%": "SGST(%)", "sgst amount": "SGST Amount",

    # totals
    "net amount": "Net Amount", "total": "Net Amount", "grand total": "Net Amount",
    "invoice total": "Net Amount", "total amount": "Net Amount"
}

# lower-case synonyms set for header-detection scoring
SYNONYMS = set(HEADER_MAP.keys())

# --------------------------
# Utility parsing/cleaning
# --------------------------
def _strip_to_numeric(s: Optional[str]) -> Optional[str]:
    """Return cleaned numeric string or None."""
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    # keep percent marker to detect %
    if "%" in s:
        # keep numeric and dot and minus
        num = re.sub(r"[^\d.\-]", "", s)
        return num if num != "" else None
    # remove currency symbols, commas, spaces and letters
    num = re.sub(r"[^\d.\-]", "", s)
    return num if num != "" else None

def to_float_safe(s: Optional[str]) -> Optional[float]:
    """Convert cleaned numeric string to float or return None."""
    n = _strip_to_numeric(s)
    if n is None:
        return None
    try:
        return float(n)
    except:
        return None

def contains_percent(s: Optional[str]) -> bool:
    if not s: return False
    return "%" in str(s)

# --------------------------
# Header detection helpers
# --------------------------
def _normalize_header_token(token: str) -> str:
    t = token.lower().strip().replace(":", "")
    return HEADER_MAP.get(t, token.strip())

def detect_header_row(table: List[List[str]]) -> int:
    """
    Try to detect which row is header by scoring synonyms occurrences.
    Returns header_row_index (default 0).
    """
    max_score = -1
    best_idx = 0
    rows_to_check = min(3, len(table))
    for i in range(rows_to_check):
        row = table[i]
        tokens = [str(c).lower().strip() for c in row if c is not None]
        score = 0
        for tok in tokens:
            # exact keyword presence or partial match
            for syn in SYNONYMS:
                if syn in tok:
                    score += 1
        # immediate strong signals
        if any(tok in ("hsn", "item", "qty", "quantity", "rate", "amount") for tok in tokens):
            score += 3
        if score > max_score:
            max_score = score
            best_idx = i
    return best_idx

# --------------------------
# Row processing helpers
# --------------------------
def choose_item_name_from_row(clean_row: List[str], hsn_idx: int) -> str:
    """
    Best-effort: return item name string by finding longest non-numeric cell
    after HSN or between first few cells.
    """
    candidates = []
    # check cells after HSN
    for i, c in enumerate(clean_row):
        if i == hsn_idx:
            continue
        s = str(c).strip()
        if s == "": 
            continue
        if not re.search(r"^\s*[\d,.\-]+\s*$", s) and not re.search(r"IGST|CGST|SGST|%|Rs|INR", s, re.I):
            candidates.append(s)
    if candidates:
        # choose longest candidate
        return max(candidates, key=len)
    # fallback join middle cells
    return " ".join([c for c in clean_row[:3] if c]).strip() or "Item"

def interpret_discount(raw_percent: Optional[str], raw_amount: Optional[str], gross: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Return (discount_percent, discount_amount)
    Rule:
     - if raw_percent contains '%' => percent authoritative -> compute amount
     - elif raw_amount present => amount authoritative -> compute percent
     - else None, None
    """
    dp = None
    da = None
    if raw_percent and contains_percent(raw_percent):
        dp = to_float_safe(raw_percent)
        if dp is not None and gross is not None:
            da = round((gross * dp) / 100.0, 2)
    elif raw_amount:
        da = to_float_safe(raw_amount)
        if da is not None and gross and gross != 0:
            dp = round((da / gross) * 100.0, 2)
    return dp, da

def interpret_tax(raw_percent: Optional[str], raw_amount: Optional[str], gross_after_disc: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Return (tax_percent, tax_amount)
    Rules (per latest instruction):
     - If percent value is explicitly present (contains '%') => percent authoritative -> compute amount
     - Else if an amount is present (no '%') => amount authoritative -> compute percent (for convenience) but keep amount as authoritative
     - Else None, None
    """
    tp = None
    ta = None
    if raw_percent and contains_percent(raw_percent):
        tp = to_float_safe(raw_percent)
        if tp is not None and gross_after_disc is not None:
            ta = round((gross_after_disc * tp) / 100.0, 2)
    elif raw_amount:
        ta = to_float_safe(raw_amount)
        if ta is not None and gross_after_disc and gross_after_disc != 0:
            tp = round((ta / gross_after_disc) * 100.0, 2)
    return tp, ta

# --------------------------
# GSTIN / Invoice No extraction (doc-level)
# --------------------------
def extract_invoice_no(all_text: str) -> Optional[str]:
    m = re.search(r"(?:Invoice\s*No\.?|Invoice\s*Number|Bill\s*No\.?)[:\s]*([\w\-\/]+)", all_text, re.IGNORECASE)
    return m.group(1).strip() if m else None

def extract_gstins(all_text: str) -> Tuple[Optional[str], Optional[str]]:
    # capture 15-char GSTIN patterns
    found = re.findall(r"\b[0-9A-Z]{15}\b", all_text)
    supplier = None
    customer = None
    # Try to find explicit labelled GSTINs
    sm = re.search(r"Supplier\s*GSTIN[:\s]*([0-9A-Z]{15})", all_text, re.IGNORECASE)
    cm = re.search(r"Customer\s*GSTIN[:\s]*([0-9A-Z]{15})", all_text, re.IGNORECASE)
    if sm:
        supplier = sm.group(1).strip()
    if cm:
        customer = cm.group(1).strip()
    # fallback assign found list
    if not supplier and len(found) >= 1:
        supplier = found[0]
    if not customer and len(found) >= 2:
        customer = found[1]
    return supplier, customer

# --------------------------
# Core parse function
# --------------------------
def parse_invoice(pdf, text: str, source_file: str) -> pd.DataFrame:
    """
    Main entry: pdf = pdfplumber.PDF instance, text = combined extracted text (may be "" if scanned),
    source_file = filename string.

    Returns pandas.DataFrame with the FINAL_COLUMNS order.
    """
    invoice_no = extract_invoice_no(text) or "Unknown"
    supplier_gstin, customer_gstin = extract_gstins(text)

    extracted_rows = []

    # Attempt table-based extraction first
    for page in pdf.pages:
        tables = page.extract_tables() or []
        for table in tables:
            # skip empty tables
            if not table or len(table) < 2:
                continue

            # detect header row
            header_idx = detect_header_row(table)
            header_row = table[header_idx]
            data_rows = table[header_idx+1:]

            # normalize headers
            normalized_headers = [_normalize_header_token(str(h).strip() if h is not None else "") for h in header_row]

            # for each data row, map values
            for raw_row in data_rows:
                clean_row = [("" if c is None else str(c).strip()) for c in raw_row]
                # attempt to detect hsn
                hsn = None
                for i, cell in enumerate(clean_row):
                    if re.match(r"\d{4,}", cell):
                        hsn = cell
                        hsn_idx = i
                        break
                # If no HSN, still attempt if row has numeric columns (qty/rate)
                # build raw map: normalized_header -> raw value (if header present)
                row_map = {}
                for col_name, raw_cell in zip(normalized_headers, clean_row):
                    row_map[col_name] = raw_cell

                # Now produce final fields with safe parsing:
                # Quantity detection
                q = None
                if "Quantity" in row_map and row_map.get("Quantity"):
                    q = to_float_safe(row_map.get("Quantity"))
                else:
                    # find numeric in row excluding currency-like totals
                    for c in clean_row:
                        if re.match(r"^\d+(\.\d+)?$", c):
                            q = to_float_safe(c)
                            break

                # Rate detection
                r = None
                if "Rate" in row_map and row_map.get("Rate"):
                    r = to_float_safe(row_map.get("Rate"))
                else:
                    # try near end columns
                    if len(clean_row) >= 3:
                        r = to_float_safe(clean_row[-3])
                # Gross detection
                gross = None
                if "Gross Amount" in row_map and row_map.get("Gross Amount"):
                    gross = to_float_safe(row_map.get("Gross Amount"))
                else:
                    # if gross not present compute qty * rate
                    if q is not None and r is not None:
                        gross = round(q * r, 2)

                # Discount
                raw_disc_percent = None
                raw_disc_amount = None
                if "Discount(%)" in row_map and row_map.get("Discount(%)"):
                    raw_disc_percent = row_map.get("Discount(%)")
                if "Discount Amount" in row_map and row_map.get("Discount Amount"):
                    raw_disc_amount = row_map.get("Discount Amount")
                # Also scan row for 'disc' or '%' not in header columns
                if not raw_disc_percent or not raw_disc_amount:
                    for c in clean_row:
                        if re.search(r"disc", c, re.I) or (re.search(r"%", c) and not re.search(r"GST", c, re.I)):
                            # guess this is discount info
                            if "%" in c:
                                raw_disc_percent = raw_disc_percent or c
                            else:
                                raw_disc_amount = raw_disc_amount or c

                disc_pct, disc_amt = interpret_discount(raw_disc_percent, raw_disc_amount, gross)

                gross_after_disc = gross - (disc_amt or 0)

                # TAXES: IGST / CGST / SGST
                def _find_raw_for_tax(key_prefix):
                    # try header-based values
                    raw_pct = row_map.get(f"{key_prefix}(%)") or row_map.get(f"{key_prefix}%") or row_map.get(key_prefix)
                    raw_amt = row_map.get(f"{key_prefix} Amount") or row_map.get(f"{key_prefix}amount")
                    # also scan row cells for keywords
                    if not raw_pct and not raw_amt:
                        for c in clean_row:
                            if re.search(key_prefix, c, re.I):
                                # e.g., "IGST 18%" or "IGST 180.00"
                                raw_text = c
                                # try to split number
                                if "%" in raw_text:
                                    raw_pct = raw_text
                                else:
                                    raw_amt = raw_text
                                break
                    return raw_pct, raw_amt

                igst_raw_pct, igst_raw_amt = _find_raw_for_tax("IGST")
                cgst_raw_pct, cgst_raw_amt = _find_raw_for_tax("CGST")
                sgst_raw_pct, sgst_raw_amt = _find_raw_for_tax("SGST")

                igst_pct, igst_amt = interpret_tax(igst_raw_pct, igst_raw_amt, gross_after_disc)
                cgst_pct, cgst_amt = interpret_tax(cgst_raw_pct, cgst_raw_amt, gross_after_disc)
                sgst_pct, sgst_amt = interpret_tax(sgst_raw_pct, sgst_raw_amt, gross_after_disc)

                # Net amount: prefer explicit Net if present in row (last numeric cell that looks like total)
                net_val = None
                # check if normalized header contains Net Amount column
                if "Net Amount" in row_map and row_map.get("Net Amount"):
                    net_val = to_float_safe(row_map.get("Net Amount"))
                else:
                    # examine trailing numeric values in clean_row
                    trailing_nums = [to_float_safe(c) for c in clean_row if re.search(r"\d+\.\d{2}$", c)]
                    trailing_nums = [x for x in trailing_nums if x is not None]
                    if trailing_nums:
                        cand = trailing_nums[-1]
                        # compute expected net to compare
                        computed_net = round((gross_after_disc or 0) + (igst_amt or 0) + (cgst_amt or 0) + (sgst_amt or 0), 2)
                        # if last numeric is close to computed_net or obviously the total, take it
                        if abs(cand - computed_net) <= 1.0 or cand > computed_net:
                            net_val = cand

                if net_val is None:
                    net_val = round((gross_after_disc or 0) + (igst_amt or 0) + (cgst_amt or 0) + (sgst_amt or 0), 2)

                # item name extraction
                item_name = "Item"
                if hsn:
                    try:
                        # find index
                        idx = clean_row.index(hsn)
                        item_name = choose_item_name_from_row(clean_row, idx)
                    except:
                        item_name = choose_item_name_from_row(clean_row, -1)
                else:
                    item_name = choose_item_name_from_row(clean_row, -1)

                # finalize row
                final_row = {
                    "Invoice No": invoice_no,
                    "Supplier GSTIN": supplier_gstin or "Unknown",
                    "Customer GSTIN": customer_gstin or "Unknown",
                    "Source File": source_file,
                    "HSN": hsn or None,
                    "Item Name": item_name,
                    "Quantity": q if q is not None else None,
                    "Rate": r if r is not None else None,
                    "Gross Amount": gross if gross is not None else None,
                    "Discount(%)": round(disc_pct, 2) if disc_pct is not None and disc_pct != "" else None,
                    "Discount Amount": round(disc_amt, 2) if disc_amt is not None and disc_amt != "" else None,
                    "IGST(%)": round(igst_pct, 2) if igst_pct is not None else None,
                    "IGST Amount": round(igst_amt, 2) if igst_amt is not None else None,
                    "CGST(%)": round(cgst_pct, 2) if cgst_pct is not None else None,
                    "CGST Amount": round(cgst_amt, 2) if cgst_amt is not None else None,
                    "SGST(%)": round(sgst_pct, 2) if sgst_pct is not None else None,
                    "SGST Amount": round(sgst_amt, 2) if sgst_amt is not None else None,
                    "Net Amount": round(net_val, 2) if net_val is not None else None
                }
                extracted_rows.append(final_row)

    # If no rows extracted via tables, fallback to text-line parsing (best-effort)
    if not extracted_rows:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # try to find lines that look like item lines: contain HSN & a numeric qty & a numeric rate
        for ln in lines:
            if re.search(r"\b\d{4,}\b", ln) and re.search(r"\d+\s+\d+(\.\d+)?", ln):
                parts = re.split(r"\s{2,}|\t|\s\|\s", ln)
                parts = [p.strip() for p in parts if p.strip()]
                # attempt to parse last columns as rate/gross
                hsn = next((p for p in parts if re.match(r"\d{4,}", p)), None)
                qty = None
                rate = None
                gross = None
                # heuristics: last numeric is gross, 2nd last numeric is rate or qty
                nums = [to_float_safe(re.sub(r"[^\d.\-]", "", p)) for p in parts]
                nums = [n for n in nums if n is not None]
                if nums:
                    gross = nums[-1]
                    if len(nums) >= 2:
                        rate = nums[-2]
                    if len(nums) >= 3:
                        qty = nums[-3]
                if not qty:
                    qty = 1
                # discounts/taxes - try to find patterns in whole text (nearby)
                # simple fallback: look for "IGST <num>" in text
                igst_pct = None; igst_amt = None
                m = re.search(r"IGST[:\s]*([\d.]+)%?", text, re.I)
                if m:
                    val = to_float_safe(m.group(1))
                    if "%" in m.group(0):
                        igst_pct = val
                        igst_amt = round((gross - 0) * igst_pct/100.0, 2)
                    else:
                        igst_amt = val
                        igst_pct = round((igst_amt / (gross or 1)) * 100.0, 2)
                # create row
                net_val = round((gross or 0) + (igst_amt or 0), 2)
                item_name = " ".join([p for p in parts if not re.match(r"^\d+(\.\d+)?$", p)][:2]) or "Item"
                final_row = {
                    "Invoice No": invoice_no,
                    "Supplier GSTIN": supplier_gstin or "Unknown",
                    "Customer GSTIN": customer_gstin or "Unknown",
                    "Source File": source_file,
                    "HSN": hsn,
                    "Item Name": item_name,
                    "Quantity": qty,
                    "Rate": rate,
                    "Gross Amount": gross,
                    "Discount(%)": None,
                    "Discount Amount": None,
                    "IGST(%)": igst_pct,
                    "IGST Amount": igst_amt,
                    "CGST(%)": None,
                    "CGST Amount": None,
                    "SGST(%)": None,
                    "SGST Amount": None,
                    "Net Amount": net_val
                }
                extracted_rows.append(final_row)

    # Build dataframe and enforce final column ordering
    if not extracted_rows:
        # no rows, return empty df with final columns
        return pd.DataFrame(columns=FINAL_COLUMNS)

    df = pd.DataFrame(extracted_rows)
    # ensure all final columns exist, in exact order
    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[FINAL_COLUMNS]

    # Convert numeric columns types where possible
    numeric_cols = ["Quantity", "Rate", "Gross Amount", "Discount(%)", "Discount Amount",
                    "IGST(%)", "IGST Amount", "CGST(%)", "CGST Amount", "SGST(%)", "SGST Amount", "Net Amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
