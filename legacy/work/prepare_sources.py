from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from urllib.parse import parse_qs, urlsplit
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "outputs" / "benchmark"
MIRA = Path("/var/folders/x1/zryt_5w95_q00h_0b1wq3_mr0000gn/T/codex-file-preview-aRDWyM/s41586-026-10675-5.pdf")
PMCIDS = [
    "PMC12905702",  # cardiac / endocarditis
    "PMC12441332",  # cardiac / myocarditis
    "PMC13217375",  # sepsis / urinary pouch
    "PMC12052731",  # pulmonary / chylothorax
    "PMC11780579",  # oncologic / pleura
    "PMC12676967",  # endocrine / adrenal TB
    "PMC11939122",  # hematologic / immune toxicity
    "PMC11864156",  # neurologic / spinal hematoma
    "PMC13092731",  # abdominal surgery / migrated stent
    "PMC13124342",  # gynecologic / ectopic pregnancy
]
JOURNAL_YEAR = [
    ("JACC Case Reports", 2025),
    ("JACC Case Reports", 2025),
    ("BMJ Case Reports", 2026),
    ("Respirology Case Reports", 2025),
    ("BMJ Case Reports", 2025),
    ("Frontiers in Medicine", 2025),
    ("American Journal of Case Reports", 2025),
    ("International Journal of Surgery Case Reports", 2025),
    ("Journal of Surgical Case Reports", 2026),
    ("Medicine (Baltimore)", 2026),
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "MIRA-2026-Benchmark/0.1 (research source verification)"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def yaml_quote(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def main() -> None:
    (ROOT / "docs" / "reference").mkdir(parents=True, exist_ok=True)
    ref_dst = ROOT / "docs" / "reference" / "mira_nature_2026.pdf"
    shutil.copyfile(MIRA, ref_dst)
    (ROOT / "docs" / "reference" / "source_metadata.yaml").write_text(
        "title: \"Towards autonomous medical artificial intelligence agents\"\n"
        "journal: Nature\npublication_year: 2026\n"
        "doi: \"10.1038/s41586-026-10675-5\"\n"
        "source: user_attached_pdf\nrole: methodology_reference_not_benchmark_case\n"
        f"sha256: {hashlib.sha256(ref_dst.read_bytes()).hexdigest()}\n",
        encoding="utf-8",
    )
    rows = []
    for index, pmcid in enumerate(PMCIDS, 1):
        case_dir = ROOT / "cases" / f"case_{index:03d}"
        case_dir.mkdir(parents=True, exist_ok=True)
        meta_url = f"https://pmc-oa-opendata.s3.amazonaws.com/metadata/{pmcid}.1.json"
        meta = json.loads(fetch(meta_url))
        assert meta["pmcid"] == pmcid
        assert meta["is_pmc_openaccess"] and not meta["is_retracted"]
        s3_pdf_url = meta["pdf_url"]
        assert s3_pdf_url
        pdf_url = s3_pdf_url.replace("s3://pmc-oa-opendata/", "https://pmc-oa-opendata.s3.amazonaws.com/")
        pdf_path = case_dir / "source.pdf"
        expected_md5 = parse_qs(urlsplit(pdf_url).query).get("md5", [None])[0]
        cached = pdf_path.read_bytes() if pdf_path.exists() else b""
        pdf = cached if expected_md5 and hashlib.md5(cached).hexdigest() == expected_md5 else fetch(pdf_url)
        assert pdf.startswith(b"%PDF-"), f"Not a PDF: {pmcid}"
        assert not expected_md5 or hashlib.md5(pdf).hexdigest() == expected_md5, f"MD5 mismatch: {pmcid}"
        pdf_path.write_bytes(pdf)
        journal, publication_year = JOURNAL_YEAR[index - 1]
        license_url = f"https://creativecommons.org/licenses/{meta['license_code'].lower().replace('cc ', '')}/4.0/"
        (case_dir / "source_metadata.yaml").write_text(
            "\n".join(
                [
                    f"case_id: case_{index:03d}",
                    f"pmcid: {pmcid}",
                    f"title: {yaml_quote(meta['title'])}",
                    f"journal: {yaml_quote(journal)}",
                    f"publication_year: {publication_year}",
                    f"citation: {yaml_quote(meta['citation'])}",
                    f"doi: {yaml_quote(meta['doi'])}",
                    f"article_url: https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
                    f"pdf_url: {yaml_quote(pdf_url)}",
                    f"metadata_url: {yaml_quote(meta_url)}",
                    f"license_code: {yaml_quote(meta['license_code'])}",
                    f"license_url: {yaml_quote(license_url)}",
                    "access_status: downloaded_verified_public_pdf",
                    "case_packet_status: pending_clinician_review",
                    f"retrieved_on: {date.today().isoformat()}",
                    f"sha256: {hashlib.sha256(pdf).hexdigest()}",
                    f"bytes: {len(pdf)}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        rows.append({"case_id": f"case_{index:03d}", "pmcid": pmcid, "doi": meta["doi"], "journal": journal, "publication_year": publication_year, "license": meta["license_code"], "bytes": len(pdf), "sha256": hashlib.sha256(pdf).hexdigest(), "title": meta["title"], "citation": meta["citation"], "pdf_url": pdf_url})
        print(f"case_{index:03d}: {pmcid}, {len(pdf)} bytes, {meta['license_code']}")
    (ROOT / "docs" / "source_manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MIRA reference: {ref_dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
