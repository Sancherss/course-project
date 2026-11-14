#!/usr/bin/env python3
"""Render with LibreOffice and fill cached TOC page numbers from actual PDF outlines."""
from __future__ import annotations
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import fitz

ROOT=Path(__file__).resolve().parents[1]

def pagination(path: Path) -> tuple[dict,dict]:
    document=fitz.open(path)
    body_start=next(i for i,p in enumerate(document) if 'ОГЛАВЛЕНИЕ' in p.get_text())
    contents={title:physical-body_start+1 for _,title,physical in document.get_toc()}
    footer_numbers=[]
    for i,page in enumerate(document):
        footer=page.get_text(clip=fitz.Rect(0,page.rect.height-50,page.rect.width,page.rect.height))
        numbers=[int(x) for x in footer.splitlines() if re.fullmatch(r'\d+',x.strip())]
        expected=[] if i<body_start else [i-body_start+2]
        if numbers!=expected:
            raise RuntimeError(f'Page {i+1}: footer {numbers}, expected {expected}')
        footer_numbers.append(numbers)
    return contents,dict(physical_pages=len(document),assignment_pages=body_start-1,
                         contents_physical_page=body_start+1,contents_printed_page=2,
                         footer_numbers_verified=True,outline_entries=len(contents),footer_numbers=footer_numbers)

def main() -> None:
    binary=shutil.which('soffice') or shutil.which('libreoffice')
    if not binary:raise SystemExit('LibreOffice is needed for PDF layout verification; DOCX can be generated separately.')
    target=ROOT/'report/toc_pages.json'
    current=json.loads(target.read_text()) if target.exists() else {}
    with tempfile.TemporaryDirectory(prefix='bsu-layout-') as folder:
        scratch=Path(folder)
        env=dict(os.environ);env['XDG_CACHE_HOME']=str(scratch/'cache')
        (scratch/'cache').mkdir()
        for iteration in range(1,4):
            subprocess.run([sys.executable,str(ROOT/'scripts/export_report.py'),'--toc-pages',str(target)],check=True)
            output=scratch/f'pass-{iteration}';output.mkdir()
            result=subprocess.run([binary,'--headless','--convert-to','pdf','--outdir',str(output),str(ROOT/'report/coursework_draft.docx')],env=env,capture_output=True,text=True,timeout=60)
            pdf=output/'coursework_draft.pdf'
            if result.returncode or not pdf.is_file():raise RuntimeError(result.stdout+'\n'+result.stderr)
            measured,audit=pagination(pdf)
            if measured==current:
                shutil.copy2(pdf,ROOT/'report/coursework_draft.pdf')
                audit.update(toc_pages=measured,toc_matches_rendered_headings=True,render_passes=iteration,
                             renderer=subprocess.check_output([binary,'--version'],text=True).strip(),
                             scope='Confirmed structure and pagination; numeric typography requirements are not provided by the BSU source.')
                audit['docx_sha256']=hashlib.sha256((ROOT/'report/coursework_draft.docx').read_bytes()).hexdigest()
                audit['pdf_sha256']=hashlib.sha256((ROOT/'report/coursework_draft.pdf').read_bytes()).hexdigest()
                (ROOT/'evidence/report-layout-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
                print(json.dumps({k:v for k,v in audit.items() if k not in ('toc_pages','footer_numbers')},ensure_ascii=False,indent=2))
                return
            current=measured;target.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
        raise RuntimeError('Pagination did not stabilize in three passes; do not publish an unverified PDF.')

if __name__=='__main__':main()
