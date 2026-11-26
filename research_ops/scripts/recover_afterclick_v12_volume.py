"""Read-only recovery of a completed batch whose RPC return was lost."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import modal
from modal.types import FileEntryType


def main(run,prefix):
    volume=modal.Volume.from_name('afterclick-v12-research-evidence');entries=volume.listdir(prefix,recursive=True);destination=run/'cloud-batches'/prefix;destination.mkdir(exist_ok=False);target=destination/prefix;target.mkdir();manifest=[]
    def download(entry):
        relative=Path(entry.path).relative_to(prefix);assert '..' not in relative.parts
        path=target/relative;path.parent.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256();size=0
        with path.open('xb') as stream:
            for chunk in volume.read_file(entry.path):stream.write(chunk);digest.update(chunk);size+=len(chunk)
        assert size==entry.size,(entry.path,size,entry.size)
        return dict(remote=entry.path,local=str(path),bytes=size,sha256=digest.hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for row in pool.map(download,[e for e in entries if e.type==FileEntryType.FILE]):manifest.append(row)
    runtime=json.loads((target/'runtime.json').read_text());report=dict(**runtime,recovered_from_volume=True,original_rpc_failed=True,downloaded_files=len(manifest),downloaded_bytes=sum(r['bytes'] for r in manifest),recovery_manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest());(destination/'recovery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(destination/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--prefix',required=True);a=p.parse_args();main(a.run,a.prefix)
