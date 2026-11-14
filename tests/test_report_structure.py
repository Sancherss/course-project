"""Check the supplied BSU structural rules against the actual exported DOCX."""
from pathlib import Path
import hashlib,json,re
from docx import Document
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]

def test_title_and_assignment_are_not_numbered_and_body_starts_at_two():
    doc=Document(ROOT/'report/coursework_draft.docx')
    assert len(doc.sections)==3
    for section in doc.sections[:2]:
        assert not section.footer._element.findall('.//'+qn('w:instrText'))
    body=doc.sections[2]
    assert body._sectPr.find(qn('w:pgNumType')).get(qn('w:start'))=='2'
    assert any('PAGE' in (field.text or '') for field in body.footer._element.findall('.//'+qn('w:instrText')))
    text='\n'.join(p.text for p in doc.paragraphs)
    assert 'МИНИСТЕРСТВО ОБРАЗОВАНИЯ РЕСПУБЛИКИ БЕЛАРУСЬ' in text
    assert 'ЗАДАНИЕ ПО КУРСОВОМУ ПРОЕКТУ' in text
    assert '[ДАТА]' in text and '[ФИО ОБУЧАЮЩЕГОСЯ]' in text


def test_toc_has_live_fields_and_populated_page_cache():
    doc=Document(ROOT/'report/coursework_draft.docx')
    fields=[x.text or '' for x in doc.element.findall('.//'+qn('w:instrText'))]
    toc=[x for x in fields if x.strip().startswith('TOC ')]
    assert len(toc)==1 and '\\h' in toc[0]
    refs=[x for x in fields if x.strip().startswith('PAGEREF ')]
    pages=json.loads((ROOT/'report/toc_pages.json').read_text())
    assert len(refs)==len(pages)==len(doc.element.findall('.//'+qn('w:bookmarkStart')))
    assert all(type(n) is int and n>=2 for n in pages.values())
    assert not any(p.text.strip()=='?' for p in doc.paragraphs)


def test_appendices_include_actual_material_and_are_referenced():
    doc=Document(ROOT/'report/coursework_draft.docx')
    assert len(doc.tables)>=5
    text='\n'.join(p.text for p in doc.paragraphs)
    for label in ['ПРИЛОЖЕНИЕ А.','ПРИЛОЖЕНИЕ Б.','ПРИЛОЖЕНИЕ В.']:assert label in text
    for label in ['приложении А','приложение Б','приложение В']:assert label in text
    table=next(t for t in doc.tables if [c.text for c in t.rows[0].cells]==['ID','Фаза','Query','Набор','Результат'])
    assert len(table.rows)==13
    assert 'R01' in table.rows[1].cells[0].text and 'R12' in table.rows[-1].cells[0].text


def test_layout_audit_matches_published_bytes():
    audit=json.loads((ROOT/'evidence/report-layout-audit.json').read_text())
    assert audit['toc_matches_rendered_headings'] and audit['footer_numbers_verified']
    assert audit['contents_printed_page']==2
    for kind in ('docx','pdf'):
        assert hashlib.sha256((ROOT/f'report/coursework_draft.{kind}').read_bytes()).hexdigest()==audit[kind+'_sha256']
    assert audit['footer_numbers'][:audit['contents_physical_page']-1]==[[]]*(audit['contents_physical_page']-1)


def test_protocol_figures_are_distinct_and_match_the_markdown_paths():
    from scripts.export_report import parse_body
    blocks=parse_body(ROOT/'report/coursework_draft.md')
    images=[b for b in blocks if b[0]=='image']
    assert [b[1].name for b in images]==['architecture.png','gettoken.png','matrix.png']
    assert len({hashlib.sha256(b[1].read_bytes()).hexdigest() for b in images})==3
    assert len(Document(ROOT/'report/coursework_draft.docx').inline_shapes)==3
