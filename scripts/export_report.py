#!/usr/bin/env python3
"""Export the reviewed Markdown draft to editable DOCX; no claimed BSU typography."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Pt

ROOT=Path(__file__).resolve().parents[1]

def export() -> Path:
    source=ROOT/'report/coursework_draft.md'
    doc=Document()
    # Keep Word defaults: no invented mandatory margins/font/spacing.
    lines=source.read_text().splitlines(); i=0; code=False
    while i<len(lines):
        line=lines[i]
        if line.startswith('```'):
            code=not code;i+=1;continue
        if code:
            p=doc.add_paragraph();r=p.add_run(line);r.font.name='Consolas';r.font.size=Pt(9)
        elif line.startswith('|') and i+1<len(lines) and re.match(r'^\|[-:| ]+\|$',lines[i+1]):
            headers=[x.strip() for x in line.strip('|').split('|')]
            table=doc.add_table(rows=1,cols=len(headers));table.style='Table Grid'
            for cell,text in zip(table.rows[0].cells,headers):cell.text=text
            i+=2
            while i<len(lines) and lines[i].startswith('|'):
                cells=table.add_row().cells
                for cell,text in zip(cells,lines[i].strip('|').split('|')):cell.text=text.strip()
                i+=1
            continue
        elif line.startswith('#'):
            level=len(line)-len(line.lstrip('#'))
            doc.add_heading(line[level:].strip(),level=min(level-1,3))
        elif line.strip():
            p=doc.add_paragraph()
            for j,part in enumerate(line.split('**')):
                run=p.add_run(part.replace('`',''));run.bold=bool(j%2)
        i+=1
    destination=ROOT/'report/coursework_draft.docx'
    doc.save(destination)
    reopened=Document(destination)
    assert len(reopened.paragraphs)>100 and len(reopened.tables)>=1
    assert 'UNKNOWN' in '\n'.join(p.text for p in reopened.paragraphs)
    print(f'{destination}: {len(reopened.paragraphs)} paragraphs, {len(reopened.tables)} tables; reopened successfully')
    return destination

if __name__=='__main__':export()
