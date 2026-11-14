#!/usr/bin/env python3
"""Build an editable draft using confirmed BSU structure, not invented typography rules."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TITLE = 'Разработка программных средств для экспериментального анализа безопасности протокола FIDO2 на основе FIDO2Verif'

def field(paragraph, instruction: str, cached: str = '') -> None:
    run = paragraph.add_run()
    for kind in ('begin', 'instruction', 'separate', 'text', 'end'):
        if kind == 'instruction':
            element=OxmlElement('w:instrText');element.set(qn('xml:space'),'preserve');element.text=instruction
        elif kind == 'text':
            element=OxmlElement('w:t');element.text=cached
        else:
            element=OxmlElement('w:fldChar');element.set(qn('w:fldCharType'),kind)
        run._r.append(element)

def add_text(doc, text='', *, align=None, before=0, after=6, bold=False):
    p=doc.add_paragraph();p.paragraph_format.space_before=Pt(before);p.paragraph_format.space_after=Pt(after)
    if align is not None:p.alignment=align
    for index,part in enumerate(text.split('**')):
        run=p.add_run(part.replace('`',''));run.bold=bold or bool(index%2)
    return p

def make_cover(doc):
    center=WD_ALIGN_PARAGRAPH.CENTER
    for text in ['МИНИСТЕРСТВО ОБРАЗОВАНИЯ РЕСПУБЛИКИ БЕЛАРУСЬ',
                 'БЕЛОРУССКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ',
                 '[ФАКУЛЬТЕТ]', 'Кафедра [КАФЕДРА]']:
        add_text(doc,text,align=center,after=5)
    p=add_text(doc,TITLE.upper(),align=center,before=72,after=18,bold=True)
    p.paragraph_format.keep_with_next=True
    add_text(doc,'Курсовой проект',align=center,after=6)
    add_text(doc,'Черновик для согласования',align=center,after=42)
    for text in ['[ФИО ОБУЧАЮЩЕГОСЯ]', 'обучающегося [КУРС] курса',
                 'специальности «[СПЕЦИАЛЬНОСТЬ]»', 'группа [ГРУППА]',
                 'Научный руководитель:', '[СТЕПЕНЬ, ЗВАНИЕ]', '[ФИО РУКОВОДИТЕЛЯ]']:
        p=add_text(doc,text,after=3);p.paragraph_format.left_indent=Mm(83)
    add_text(doc,'Минск, [ГОД]',align=center,before=72,after=0)

def make_assignment(doc):
    add_text(doc,'Белорусский государственный университет',align=WD_ALIGN_PARAGRAPH.CENTER,bold=True)
    add_text(doc,'Факультет [ФАКУЛЬТЕТ]    Кафедра [КАФЕДРА]')
    add_text(doc,'ЗАДАНИЕ ПО КУРСОВОМУ ПРОЕКТУ',align=WD_ALIGN_PARAGRAPH.CENTER,bold=True)
    add_text(doc,'Проект задания; даты, формулировки и подписи подлежат согласованию.')
    for text in ['Студент: [ФИО ОБУЧАЮЩЕГОСЯ]', '1. Тема: '+TITLE,
                 '2. Срок представления к защите: [ДАТА]. Дата выдачи задания: [ДАТА].',
                 '3. Исходные данные: FIDO2Verif, commit 2d8eaf326117bd7e4706c48b2d24e27b4a006fa6; ProVerif 2.05; локальные формальные модели.',
                 'Основные источники: Guan et al., ESORICS 2022; исходники CactiLab/FIDO2Verif; официальный manual ProVerif; спецификации WebAuthn и CTAP.',
                 'Графический материал: таблица основной матрицы и рисунок результатов; сводки сохранённых запусков.',
                 '4. Содержание (структура):',
                 '4.1. Теоретические основы FIDO2.', '4.2. Формальная верификация FIDO2.',
                 '4.3. Экспериментальное исследование.', '5. Индивидуальный график выполнения:']:
        add_text(doc,text,after=4)
    table=doc.add_table(rows=1,cols=2);table.style='Table Grid'
    table.rows[0].cells[0].text='Этап работы';table.rows[0].cells[1].text='Срок'
    for name in ['Анализ источников и постановка задачи','Реализация и экспериментальные проверки','Анализ, пояснительная записка и подготовка защиты']:
        cells=table.add_row().cells;cells[0].text=name;cells[1].text='[ДАТА]'
    for text in ['Руководитель: ____________  [ДАТА]  [ИНИЦИАЛЫ, ФАМИЛИЯ]',
                 'Задание принял к исполнению: ____________  [ДАТА]',
                 'Проинформирован о недопустимости привлечения третьих лиц к выполнению курсовой работы (курсового проекта), плагиата, фальсификации или подлога материалов.',
                 '____________  [ИНИЦИАЛЫ, ФАМИЛИЯ ОБУЧАЮЩЕГОСЯ]']:
        add_text(doc,text,before=4,after=4)

def parse_body(source: Path) -> list[tuple]:
    text=source.read_text(encoding='utf-8')
    text=text[text.index('## Перечень обозначений'):]
    # Editorial caveats belong in the accompanying checklist, not inside the academic conclusion.
    lines=text.splitlines();blocks=[];i=0;code=False;code_lines=[]
    while i<len(lines):
        line=lines[i]
        if line.startswith('```'):
            if code:blocks.append(('code','\n'.join(code_lines)));code_lines=[]
            code=not code;i+=1;continue
        if code:code_lines.append(line);i+=1;continue
        if line.startswith('|') and i+1<len(lines) and re.fullmatch(r'\|[-:| ]+\|',lines[i+1]):
            rows=[[x.strip() for x in line.strip('|').split('|')]];i+=2
            while i<len(lines) and lines[i].startswith('|'):
                rows.append([x.strip() for x in lines[i].strip('|').split('|')]);i+=1
            blocks.append(('table',rows));continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));title=line[n:].strip()
            level=1 if n==2 else (3 if re.match(r'^\d+\.\d+\.\d+',title) else 2)
            if level==1:title=title.upper()
            blocks.append(('heading',level,title))
        elif line.startswith('!['):blocks.append(('image',source.parent/'figures/matrix.png','Рисунок 1 — Результаты основной матрицы в исторической модели'))
        elif line.strip():
            if blocks and blocks[-1][0]=='heading' and blocks[-1][-1]=='ПЕРЕЧЕНЬ ОБОЗНАЧЕНИЙ':
                # The BSU guidance calls for an alphabetical list, not a dense semicolon paragraph.
                terms=[part.strip().rstrip('.') for part in line.split(';') if part.strip()]
                blocks.extend(('paragraph',term+'.') for term in sorted(terms,key=str.casefold))
            else:blocks.append(('paragraph',line))
        i+=1
    return blocks

def bookmark(paragraph, name: str, number: int):
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(number));start.set(qn('w:name'),name)
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(number))
    paragraph._p.insert(1 if paragraph._p.pPr is not None else 0,start);paragraph._p.append(end)

def make_toc(doc, headings, pages):
    p=add_text(doc,'ОГЛАВЛЕНИЕ',align=WD_ALIGN_PARAGRAPH.CENTER,bold=True,after=16)
    p.paragraph_format.keep_with_next=True
    width=doc.sections[-1].page_width-doc.sections[-1].left_margin-doc.sections[-1].right_margin
    for index,(level,title,name) in enumerate(headings):
        p=doc.add_paragraph()
        p.paragraph_format.space_after=Pt(3)
        p.paragraph_format.left_indent=Mm((level-1)*5)
        p.paragraph_format.tab_stops.add_tab_stop(width-Mm(2),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        if index==0:
            r=p.add_run();e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'begin');r._r.append(e)
            e=OxmlElement('w:instrText');e.set(qn('xml:space'),'preserve');e.text=' TOC \\o "1-3" \\h \\z \\u ';r._r.append(e)
            e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'separate');r._r.append(e)
        link=OxmlElement('w:hyperlink');link.set(qn('w:anchor'),name)
        run=OxmlElement('w:r');text=OxmlElement('w:t');text.text=title;run.append(text);link.append(run);p._p.append(link)
        p.add_run('\t')
        field(p,' PAGEREF '+name+' \\h ',str(pages.get(title,'?')))
        if index==len(headings)-1:
            r=p.add_run();e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'end');r._r.append(e)

def export(pages_file: Path | None=None) -> Path:
    pages=json.loads(pages_file.read_text()) if pages_file and pages_file.exists() else {}
    doc=Document()
    # A4 matches the supplied sample's sheet geometry; typography remains Word's base settings.
    # Neither choice is asserted to be a numeric BSU requirement absent from the source PDF.
    for section in doc.sections:section.page_width=Mm(210);section.page_height=Mm(297)
    for name in ['Heading 1','Heading 2','Heading 3']:
        style=doc.styles[name];style.font.color.rgb=RGBColor(0,0,0)
        style.paragraph_format.keep_with_next=True
    doc.styles['Heading 1'].paragraph_format.page_break_before=True
    doc.core_properties.title=TITLE
    doc.core_properties.subject='GENERATED DRAFT — структура по методическим рекомендациям БГУ; требуется проверка студентом и руководителем'
    doc.core_properties.comments='Личные реквизиты и утверждение задания не заполнены; численные нормы шрифта/полей/интервала в предоставленном PDF не установлены.'
    make_cover(doc)
    assignment=doc.add_section(WD_SECTION_START.NEW_PAGE)
    assignment.header.is_linked_to_previous=False;assignment.footer.is_linked_to_previous=False
    make_assignment(doc)
    body=doc.add_section(WD_SECTION_START.NEW_PAGE)
    body.header.is_linked_to_previous=False;body.footer.is_linked_to_previous=False
    page_num=OxmlElement('w:pgNumType');page_num.set(qn('w:start'),'2');body._sectPr.append(page_num)
    footer=body.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;field(footer,' PAGE ','2')
    header=body.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=header.add_run('GENERATED DRAFT · ЧЕРНОВИК ДЛЯ ПРОВЕРКИ');r.font.size=Pt(8);r.font.color.rgb=RGBColor.from_string('666666')
    settings=doc.settings.element
    update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
    blocks=parse_body(ROOT/'report/coursework_draft.md')
    headings=[]
    for block in blocks:
        if block[0]=='heading':headings.append((block[1],block[2],f'_CourseHeading{len(headings)+1:03d}'))
    make_toc(doc,headings,pages)
    counter=0
    for block in blocks:
        if block[0]=='heading':
            level,title=block[1:];p=doc.add_heading(title,level=level)
            counter+=1;bookmark(p,f'_CourseHeading{counter:03d}',counter)
        elif block[0]=='paragraph':add_text(doc,block[1])
        elif block[0]=='code':
            for line in block[1].splitlines():
                p=add_text(doc,line,after=0)
                for run in p.runs:run.font.name='Consolas';run.font.size=Pt(8)
        elif block[0]=='image':
            # Respect the actual text width, avoiding overflow when the paper size changes.
            width=body.page_width-body.left_margin-body.right_margin
            doc.add_picture(str(block[1]),width=width)
            doc.paragraphs[-1].paragraph_format.keep_with_next=True
            add_text(doc,block[2],align=WD_ALIGN_PARAGRAPH.CENTER,after=10)
        elif block[0]=='table':
            rows=block[1];table=doc.add_table(rows=1,cols=len(rows[0]));table.style='Table Grid'
            for cell,text in zip(table.rows[0].cells,rows[0]):cell.text=text
            repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
            for row in rows[1:]:
                cells=table.add_row().cells
                for cell,text in zip(cells,row):cell.text=text
            if rows[0] == ['ID','Фаза','Query','Набор','Результат']:
                table.autofit=False
                widths=[10,35,24,15,62.5]
                for row in table.rows:
                    for cell,width in zip(row.cells,widths):cell.width=Mm(width)
                for col,width in zip(table.columns,widths):col.width=Mm(width)
            for row in table.rows:
                no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
                for cell in row.cells:
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after=Pt(3)
                        for r in p.runs:r.font.size=Pt(9)
    destination=ROOT/'report/coursework_draft.docx';doc.save(destination)
    (ROOT/'report/heading_index.json').write_text(json.dumps(headings,ensure_ascii=False,indent=2)+'\n')
    print(f'{destination}: {len(doc.sections)} sections, {len(headings)} TOC entries, {len(doc.tables)} tables')
    return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--toc-pages',type=Path,default=ROOT/'report/toc_pages.json')
    export(parser.parse_args().toc_pages)
