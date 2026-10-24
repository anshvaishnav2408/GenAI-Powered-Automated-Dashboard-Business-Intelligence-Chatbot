"""
Data Loader Module
Robust ingestion for single and multiple CSV/Excel files with delimiter sniffing,
encoding auto-detection, multi-sheet support, and metadata extraction.
"""

import csv
import io
import os
import re
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd


MAX_FILE_SIZE_MB = 100
ALLOWED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx", ".xls"}


class DataLoaderError(Exception):
    """Custom exception for data loading errors."""
    pass


def validate_file_size(file_bytes: bytes, max_mb: int = MAX_FILE_SIZE_MB) -> float:
    """Validate that file does not exceed size limit. Returns size in MB."""
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise DataLoaderError(f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit ({max_mb} MB).")
    return size_mb


def _detect_delimiter(sample_text: str) -> str:
    """Sniff the most probable delimiter for CSV/TSV/delimited text."""
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text[:4096])
        if dialect.delimiter in {",", ";", "\t", "|"}:
            return dialect.delimiter
    except Exception:
        pass
    # Heuristic count fallback
    candidates = [",", ";", "\t", "|"]
    counts = {c: sample_text.count(c) for c in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_dataset(
    file_source: Any,
    filename: str,
    sheet_name: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load a single CSV or Excel dataset safely, handling messy formats and delimiters.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DataLoaderError(f"Unsupported format '{ext}'. Upload .csv, .xlsx, .xls, or .tsv files.")

    # Ingest bytes
    if isinstance(file_source, (str, os.PathLike)):
        if not os.path.exists(file_source):
            raise DataLoaderError(f"File not found: {file_source}")
        with open(file_source, "rb") as f:
            file_bytes = f.read()
    elif hasattr(file_source, "read"):
        file_bytes = file_source.read()
        if hasattr(file_source, "seek"):
            file_source.seek(0)
    elif isinstance(file_source, bytes):
        file_bytes = file_source
    else:
        raise DataLoaderError("Invalid file input provided.")

    if len(file_bytes) == 0:
        raise DataLoaderError("The uploaded file is empty.")

    size_mb = validate_file_size(file_bytes)
    
    df = None
    encoding_used = "utf-8"
    available_sheets = []
    delimiter_used = ","

    if ext in {".csv", ".tsv", ".txt"}:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        last_err = None

        for enc in encodings:
            try:
                sample_str = file_bytes[:8192].decode(enc, errors="ignore")
                delimit = "\t" if ext == ".tsv" else _detect_delimiter(sample_str)
                delimiter_used = delimit

                # Parse with pandas
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=enc,
                    sep=delimit,
                    on_bad_lines="skip"
                )
                encoding_used = enc
                break
            except Exception as e:
                last_err = e
                continue

        if df is None:
            raise DataLoaderError(f"Failed to parse CSV/delimited text file. Error: {last_err}")

    elif ext in {".xlsx", ".xls"}:
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            available_sheets = excel_file.sheet_names
            target_sheet = sheet_name if (sheet_name and sheet_name in available_sheets) else available_sheets[0]
            df = pd.read_excel(excel_file, sheet_name=target_sheet)
            encoding_used = "excel-binary"
        except Exception as e:
            raise DataLoaderError(f"Failed to read Excel file: {str(e)}")

    if df is None or df.empty:
        raise DataLoaderError("The dataset contains zero records.")

    # Clean raw column headers
    clean_cols = []
    for i, col in enumerate(df.columns):
        c_str = str(col).strip()
        # Drop redundant Unnamed prefix if index column
        if re.match(r"^Unnamed:\s*\d+$", c_str, re.IGNORECASE):
            c_str = f"Index_{i}"
        clean_cols.append(c_str if c_str else f"Column_{i+1}")
    df.columns = clean_cols

    # Drop completely empty rows or columns if any
    df = df.dropna(how="all").dropna(axis=1, how="all")

    metadata = {
        "filename": filename,
        "extension": ext,
        "size_mb": round(size_mb, 3),
        "encoding": encoding_used,
        "delimiter": delimiter_used,
        "available_sheets": available_sheets,
        "selected_sheet": sheet_name or (available_sheets[0] if available_sheets else None),
        "raw_rows": len(df),
        "raw_cols": len(df.columns)
    }

    return df, metadata


def load_multiple_datasets(
    file_list: List[Any]
) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
    """
    Load multiple CSV or Excel files into a dictionary of {clean_name: (df, meta)}.
    """
    results = {}
    for item in file_list:
        fname = getattr(item, "name", os.path.basename(str(item)))
        # Normalize key name for table aliasing
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(fname)[0]).lower()
        if not clean_key or clean_key[0].isdigit():
            clean_key = f"tbl_{clean_key}"

        df, meta = load_dataset(item, fname)
        results[clean_key] = (df, meta)
    return results
