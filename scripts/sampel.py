import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path

# Atur output terminal agar mendukung karakter internasional (UTF-8) di Windows
sys.stdout.reconfigure(encoding='utf-8')

# Pastikan folder raw ada
Path("raw").mkdir(exist_ok=True)

print("=== 1. Mengambil Raw Data dari Crossref REST API ===")
crossref_url = "https://api.crossref.org/works?rows=50&filter=type:journal-article"
headers = {"User-Agent": "TugasDataEngineering/1.0 (mailto:ray.adhya4@gmail.com)"}

res_crossref = requests.get(crossref_url, headers=headers)
crossref_json = res_crossref.json()

# Simpan RAW JSON (Murni apa adanya)
with open("raw/crossref_raw.json", "w", encoding="utf-8") as f:
    json.dump(crossref_json, f, indent=2, ensure_ascii=False)

# Ekstrak items dengan aman
message = crossref_json.get("message", {})
items = message.get("items", []) if isinstance(message, dict) else []
crossref_rows = []
for item in items:
    doi = item.get("DOI", "")
    title = item.get("title", [""])[0] if item.get("title") else ""
    issn_list = item.get("ISSN", [])
    issn = issn_list[0] if issn_list else ""
    
    # Tahun publikasi
    issued = item.get("issued", {}).get("date-parts", [[None]])
    year = issued[0][0] if (issued and len(issued[0]) > 0) else None
    
    # Author
    authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])]
    author_str = "; ".join(authors) if authors else ""

    crossref_rows.append({
        "doi": doi,
        "title": title,
        "issn": issn,
        "publication_year": year,
        "author": author_str
    })

df_crossref = pd.DataFrame(crossref_rows)
df_crossref.to_csv("raw/crossref_raw.csv", index=False, encoding="utf-8")
print("-> Berhasil disimpan: raw/crossref_raw.json dan raw/crossref_raw.csv")

print("\n=== 2. Memeriksa Raw Data dari DOAJ (CSV) ===")
doaj_file = Path("raw/doaj_journals_raw.csv")
if not doaj_file.exists() or doaj_file.stat().st_size < 1000:
    print("Mengunduh DOAJ master dataset (~25MB)...")
    doaj_url = "https://doaj.org/csv"
    res_doaj = requests.get(doaj_url)
    with open(doaj_file, "wb") as f:
        f.write(res_doaj.content)
    print("-> Berhasil diunduh & disimpan: raw/doaj_journals_raw.csv")
else:
    print(f"-> File {doaj_file} sudah tersedia ({doaj_file.stat().st_size // 1024} KB).")

# Membaca sampel DOAJ (50 baris untuk file sampel)
df_doaj = pd.read_csv(doaj_file, nrows=50, encoding="utf-8")
doaj_important_cols = [
    "Journal title", 
    "Journal ISSN (print version)", 
    "Journal EISSN (online version)", 
    "Publisher", 
    "Country of publisher", 
    "Journal license", 
    "APC", 
    "APC amount", 
    "Subjects"
]
df_doaj_sample = df_doaj[doaj_important_cols]
df_doaj_sample.to_csv("raw/doaj_sample.csv", index=False, encoding="utf-8")
print("-> Berhasil membuat sampel ringkas: raw/doaj_sample.csv (50 record)")

print("\n=== 3. Contoh 5 Record Crossref (Deliverable Sprint 0) ===")
print(df_crossref[["doi", "title", "issn", "publication_year"]].head(5).to_string())

print("\n=== 4. Contoh 5 Record DOAJ (Deliverable Sprint 0) ===")
print(df_doaj_sample[["Journal title", "Journal ISSN (print version)", "Journal EISSN (online version)", "Publisher", "Country of publisher"]].head(5).to_string())


