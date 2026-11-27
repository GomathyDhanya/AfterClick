"""Build a reversible, credential-redacted candidate; never publishes any data."""

import argparse
import copy
import gzip
import hashlib
import io
import json
import re
import tarfile
import time
import zipfile
from pathlib import Path, PurePosixPath

PATTERNS = {
    "MODAL_API_TOKEN_ID": re.compile(rb"\bak-[A-Za-z0-9]{18,}\b"),
    "MODAL_API_TOKEN_SECRET": re.compile(rb"\bas-[A-Za-z0-9]{18,}\b"),
    "MODAL_PROXY_TOKEN_ID": re.compile(rb"\bwk-[A-Za-z0-9]{18,}\b"),
    "MODAL_PROXY_TOKEN_SECRET": re.compile(rb"\bws-[A-Za-z0-9]{18,}\b"),
    "GITHUB_TOKEN": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "MODEL_API_TOKEN": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b"),
    "GOOGLE_API_KEY": re.compile(rb"\bAIza[A-Za-z0-9_-]{35}\b"),
    "PRIVATE_KEY": re.compile(
        (
            b"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----."
            b"*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        ),
        re.S,
    ),
}


class Redactor:
    def __init__(self):
        self.findings = []
        self.checked = 0
        self.bytes = 0
        self.manifest = {}
        self.nested = 0

    def safe(self, name):
        p = PurePosixPath(name)
        assert not p.is_absolute() and ".." not in p.parts, name

    def transform(self, name, data, depth=0):
        self.safe(name)
        self.checked += 1
        self.bytes += len(data)
        assert depth <= 4 and self.bytes < 24 * 1024**3, "Archive expansion bound exceeded"
        original = hashlib.sha256(data).hexdigest()
        counts = {}
        if name.endswith((".tar.gz", ".tgz")) and data[:2] == b"\x1f\x8b":
            self.nested += 1
            target = io.BytesIO()
            changed = False
            with (
                tarfile.open(fileobj=io.BytesIO(data), mode="r|gz") as src,
                gzip.GzipFile(fileobj=target, mode="wb", compresslevel=1, mtime=0) as zipped,
                tarfile.open(fileobj=zipped, mode="w|") as dst,
            ):
                for m in src:
                    self.safe(m.name)
                    assert not m.issym() and not m.islnk(), "Nested links not allowed"
                    mi = copy.copy(m)
                    mi.uid = mi.gid = 0
                    mi.uname = mi.gname = ""
                    mi.pax_headers = {
                        k: v for k, v in m.pax_headers.items() if k not in {"uname", "gname"}
                    }
                    if m.isfile():
                        raw = src.extractfile(m).read()
                        new = self.transform(name + "!/" + m.name, raw, depth + 1)
                        changed |= raw != new
                        mi.size = len(new)
                        dst.addfile(mi, io.BytesIO(new))
                    elif m.isdir():
                        dst.addfile(mi)
                    else:
                        raise ValueError("Unsupported nested archive member")
            if changed:
                data = target.getvalue()
        elif name.endswith(".zip") and data[:2] == b"PK":
            self.nested += 1
            target = io.BytesIO()
            changed = False
            with (
                zipfile.ZipFile(io.BytesIO(data)) as src,
                zipfile.ZipFile(
                    target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
                ) as dst,
            ):
                for m in src.infolist():
                    self.safe(m.filename)
                    assert (m.external_attr >> 16) & 0o170000 != 0o120000, "ZIP symlink not allowed"
                    raw = src.read(m)
                    new = self.transform(name + "!/" + m.filename, raw, depth + 1)
                    changed |= raw != new
                    dst.writestr(m, new)
            if changed:
                data = target.getvalue()
        else:
            for kind, pattern in PATTERNS.items():
                data, n = pattern.subn(("REDACTED_" + kind).encode(), data)
                if n:
                    counts[kind] = n
        if counts:
            self.findings.append(
                dict(
                    path=name,
                    counts=counts,
                    source_sha256=original,
                    derived_sha256=hashlib.sha256(data).hexdigest(),
                    matched_values_not_recorded=True,
                )
            )
        if depth == 0:
            self.manifest[name] = dict(
                source_sha256=original,
                derived_sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data),
                changed=original != hashlib.sha256(data).hexdigest(),
            )
        return data


def main(source, output):
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".partial")
    assert not temp.exists()
    started = time.monotonic()
    r = Redactor()
    count = 0
    with (
        tarfile.open(str(source), "r|gz") as src,
        gzip.open(temp, "wb", compresslevel=1) as zipped,
        tarfile.open(fileobj=zipped, mode="w|") as dst,
    ):
        for m in src:
            r.safe(m.name)
            assert m.isfile() and not m.issym() and not m.islnk(), (
                "Original top-level archive must contain regular files"
            )
            data = r.transform(m.name, src.extractfile(m).read())
            mi = copy.copy(m)
            mi.size = len(data)
            mi.uid = mi.gid = 0
            mi.uname = mi.gname = ""
            mi.pax_headers = {k: v for k, v in m.pax_headers.items() if k not in {"uname", "gname"}}
            dst.addfile(mi, io.BytesIO(data))
            count += 1
            if count % 25000 == 0:
                print(json.dumps(dict(files_processed=count, findings=len(r.findings))), flush=True)
        report = dict(
            schema_version=1,
            source_archive_sha256=hashlib.file_digest(source.open("rb"), "sha256").hexdigest(),
            source_archive_bytes=source.stat().st_size,
            original_top_level_members=count,
            nested_archives_audited=r.nested,
            expanded_members_audited=r.checked,
            expanded_bytes_audited=r.bytes,
            changed_top_level_files=sum(v["changed"] for v in r.manifest.values()),
            findings=r.findings,
            files=r.manifest,
            public_upload_performed=False,
            credential_pattern_audit_not_universal_secret_proof=True,
            policy=(
                "Replace actual-looking auth token IDs/secrets and priva"
                "te-key blocks; retain research states, synthetic princi"
                "pals, public authorship and original manifest. Nested a"
                "rchives audited recursively. No matched credential valu"
                "es are logged."
            ),
            original_manifest_describes_original_bytes=True,
        )
        blob = json.dumps(report, indent=2).encode()
        mi = tarfile.TarInfo("afterclick-v12/PUBLIC_DERIVATIVE_MANIFEST.json")
        mi.size = len(blob)
        dst.addfile(mi, io.BytesIO(blob))
        note = (
            b"# Public evidence candidate\n\nThis is a locally prepared"
            b" credential-redacted derivative, not the original byte-"
            b"identical archive. It has NOT been uploaded. PUBLIC_DER"
            b"IVATIVE_MANIFEST.json maps original and public file has"
            b"hes and records redaction coverage without credential v"
            b"alues. Original RELEASE_FILE_MANIFEST.json remains unch"
            b"anged and describes original bytes; redacted log hashes"
            b" differ. Research state, synthetic identities and publi"
            b"c authorship are retained. Original restricted/local ar"
            b"chive is preserved. Automated credential-pattern audit "
            b"is not a proof that arbitrary sensitive data cannot exi"
            b"st. Numeric reproducibility and frozen-source checks mu"
            b"st be independently executed before release.\n"
        )
        mi = tarfile.TarInfo("afterclick-v12/PUBLIC_DATA_README.md")
        mi.size = len(note)
        dst.addfile(mi, io.BytesIO(note))
    temp.rename(output)
    report_path = output.with_suffix(output.suffix + ".audit.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    digest = hashlib.file_digest(output.open("rb"), "sha256").hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n")
    summary = dict(
        candidate=str(output),
        sha256=digest,
        bytes=output.stat().st_size,
        original_top_level_members=count,
        expanded_members_audited=r.checked,
        changed_top_level_files=report["changed_top_level_files"],
        credential_findings=len(r.findings),
        elapsed_seconds=time.monotonic() - started,
        public_upload_performed=False,
    )
    output.with_suffix(output.suffix + ".summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.source, a.output)
