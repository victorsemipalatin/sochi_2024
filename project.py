import os # системный модуль
import fitz # модуль для работы с pdf файлами
import shutil # системный модуль
import pdfoutline # модуль, позволяющий добавлять toc
import pytesseract # модуль для оцифровки pdf
from fpdf import FPDF # модуль для сборки нового pdf файла
from PIL import Image # модуль для работы с изображениями
import concurrent.futures # модуль для использования параллельных вычислений
from concurrent.futures import ProcessPoolExecutor # модуль для использования параллельных вычислений
from bert import * # языковая модель для поиска заголовков


pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' # путь к утсановленному tesseract-ocr
trash = "trash" # мусорная папка


def image_to_text(img): # оцифровка картинки
    return pytesseract.image_to_string(Image.open(img), lang='rus')


def get_text_from_not_ocr_pdf(document): # функция для оцифровки документов, не содержащих текста
    try:
        shutil.rmtree(trash)
        os.mkdir(trash)
    except FileNotFoundError:
        os.mkdir(trash)
    doc = fitz.open(document)
    for i, page in enumerate(doc):
        width = page.rect.width
        height = page.rect.height
        if width > height:
            page.set_rotation(90)
        pix = page.get_pixmap(dpi=200)
        output = f"{i+1}.png"
        pix.save(os.path.join(trash, output))
    doc.close()
    pics = sorted(os.listdir(trash), key=lambda x: int(x[:x.find(".")]))
    pics = [os.path.join(trash, pic) for pic in pics]
    with ProcessPoolExecutor(max_workers=os.cpu_count() // 2 - 1) as executor: # параллельная оцифровка
        tasks = {executor.submit(image_to_text, img_path): img_path for img_path in pics}
        for future in concurrent.futures.as_completed(tasks):
            tmp = tasks[future].split("/")[1]
            page_number = int(tmp[:tmp.find(".")])
            data = future.result(), page_number
            yield data


def add_toc(document, toc, new_document_name): # добавление бокового содержания
    pdfoutline.pdfoutline(document, toc, new_document_name)


def make_hyperlinks_page(toc, new_name): # добавление страницы содержания с ссылками
    pdf = FPDF()
    pics = sorted(os.listdir(trash), key=lambda x: int(x[:x.find(".")]))
    pics = [os.path.join(trash, pic) for pic in pics]
    for pic in pics:
        pdf.add_page()
        pdf.image(Image.open(pic), x=0, y=0, w=210, h=297)
    pdf.add_page()
    font_dir = '/usr/share/fonts/truetype/freefont'
    pdf.add_font("Serif", style="B", fname=f"{font_dir}/FreeSerif.ttf")
    pdf.set_font("Serif", "B", size=20)
    pdf.cell(w=pdf.epw, text="Содержание", align="C")
    pdf.set_font("Serif", "B", size=15)
    pdf.cell(0, 10, "", new_x="LMARGIN", new_y="NEXT")
    for el in toc:
        pdf.multi_cell(0, 10, f"{el[0]} стр {el[1]}", new_x="LMARGIN", new_y="NEXT", link=pdf.add_link(page=el[1]))
    output = new_name.replace(".pdf", "_tmp.pdf")
    pdf.output(output)


def make_table_of_contents(document, new_name): # рабочая лошадка
    # with fitz.open(document) as doc:
    #     if len(doc.get_toc()) != 0:
    #         print("TOC already exists")
    #         f = ""
    #         make_hyperlinks_page(f, toc)
    #         exit(0)
    # all_text = {}
    # with fitz.open(document) as doc:
    #     for num, page in enumerate(doc.pages()):
    #         all_text[num] = page.get_text()

    # err = 5
    # lines_count = sum([len(all_text[page].split()) for page in all_text.keys()])
    # if lines_count + err * 30 < len(all_text.keys()) * 30: # проверка количества заранее неоцифрованных строк (ешё надо подумать)
    text_per_page = get_text_from_not_ocr_pdf(document)
    text_per_page = [e[0] for e in sorted(text_per_page, key=lambda el: el[1])]
    # text_per_page = [el[0] for el in text_per_page]

    # else:
        # text_per_page = [all_text[page] for page in all_text.keys()]

    toc = []
    for i, text in enumerate(text_per_page):
        output = get_key_words(text)
        output = [(el, i + 1) for el in output]
        toc += output
    
    make_hyperlinks_page(toc, new_name)
    output = new_name.replace(".pdf", "_tmp.pdf")
    toc_name = new_name.replace(".pdf", ".toc")
    with open(toc_name, 'w') as f:
        for i in range(len(toc)):
            f.write(f"{toc[i][0]} {toc[i][1]}\n")

    add_toc(output, toc_name, new_name)
    os.remove(output)
    os.remove(toc_name)
    try:
        shutil.rmtree(trash)
    except:
        pass
