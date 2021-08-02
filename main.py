from guizero import App, Text, PushButton, TextBox, Combo, Window, Box, Picture, Drawing
import sqlite3
import datetime
import math
import csv
import serial
import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Flowable, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import barcode
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF


conn = sqlite3.connect('agitescale.db')

ser = serial.Serial('COM10', 9800, timeout=0.1)


def read_kern():
    line = ser.readline()
    if line:
        weight = int(line[11:16])/1000
        print(line, weight)
    else:
        print("No line")
        weight = None
    return weight


def get_weight():
    global label
    weight = read_kern()
    print("Weight: {}".format(weight))
    if weight:
        if label:
            label['weight'] = weight
            draw_label()
            if status_box.bg == 'green':
                # We print and save the label
                generate_pdf_label(label)
                save_label(label)


def get_products_dict():
    cur = conn.cursor()
    cur.execute("SELECT id, name, description FROM products")

    rows = cur.fetchall()

    products_dict = {"": 0}
    for row in rows:
        products_dict["{} - {}".format(row[1], row[2])] = row[0]
    return products_dict


def get_product(product_id):
    cur = conn.cursor()
    product_query = """SELECT id, name, description, price_kg, price_fixed, expiration_days FROM products WHERE id=?"""
    cur.execute(product_query, (product_id,))

    row = cur.fetchone()

    product = {"id": row[0], "name": row[1], "description": row[2], "price_kg": row[3], "price_fixed": row[4], "expiration_days": row[5], }
    return product


def save_product(product):
    cur = conn.cursor()
    if 'id' in product:
        product_query = """UPDATE products SET name=?, description=?, price_kg=?, price_fixed=?, expiration_days=? WHERE id=?"""
        cur.execute(product_query, (product['name'], product['description'], product['price_kg'], product['price_fixed'], product['expiration_days'], product['id'],))
        conn.commit()
    else:
        product_query = """INSERT INTO products (name, description, price_kg, price_fixed, expiration_days) VALUES (?, ?, ?, ?, ?)"""
        cur.execute(product_query, (product['name'], product['description'], product['price_kg'], product['price_fixed'],
                                    product['expiration_days']))
        conn.commit()
        product_query = """SELECT id FROM products ORDER BY id DESC"""
        cur.execute(product_query)
        row = cur.fetchone()
        product['id'] = row[0]
    return product


def get_sellers_dict():
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM sellers")

    rows = cur.fetchall()

    sellers_dict = {}
    for row in rows:
        sellers_dict[row[1]] = row[0]
    return sellers_dict


def save_label(label):
    cur = conn.cursor()
    query = """INSERT INTO labels (product_id, weight, price, price_kg, packing_date, expiry_date, seller_id) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?);"""
    cur.execute(query, (label['product_id'], label['weight'], label['price'], label['price_kg'],
                        label['packing_date'], label['expiry_date'], label['seller_id']))
    conn.commit()


def get_labels():
    cur = conn.cursor()
    cur.execute("""SELECT 
                        labels.id, sellers.name, products.id, products.name, products.description, labels.weight, labels.price, labels.price_kg, labels.packing_date, labels.expiry_date 
                   FROM
                        labels
                        INNER JOIN sellers ON sellers.id = labels.seller_id
                        INNER JOIN products ON products.id = labels.product_id;
                   """)
    rows = cur.fetchall()
    return rows


def get_seller(seller_id):
    cur = conn.cursor()
    seller_query = """SELECT id, name, address FROM sellers WHERE id=?"""
    cur.execute(seller_query, (seller_id,))

    row = cur.fetchone()

    seller = {"id": row[0], "name": row[1], "address": row[2], }
    return seller


def select_product(selected_value):
    global product
    products_dict = get_products_dict()
    product_id = products_dict[selected_value]
    product = get_product(product_id)


def select_seller(selected_value):
    global seller
    sellers_dict = get_sellers_dict()
    seller_id = sellers_dict[selected_value]
    seller = get_seller(seller_id)


def set_product_fields(product):
    name.value = product['name']
    description.value = product['description']
    price_kg.value = product['price_kg']
    price_fixed.value = product['price_fixed']
    expiration_days.value = product['expiration_days']


def set_product_from_fields(product):
    product['name'] = name.value
    product['description'] = description.value
    product['price_kg'] = price_kg.value
    product['price_fixed'] = price_fixed.value
    product['expiration_days'] = expiration_days.value


def update_expiry_date():
    current_date = datetime.datetime.now().date()
    packing_date.value = current_date
    expiry_date.value = current_date + datetime.timedelta(days=int(expiration_days.value))


def set_label_fields(product):
    current_date = datetime.datetime.now().date()
    packing_date.value = current_date
    expiry_date.value = current_date + datetime.timedelta(days=int(product['expiration_days']))


def set_label():
    global label
    global product
    global seller
    label = product.copy()
    label['packing_date'] = packing_date.value
    label['expiry_date'] = expiry_date.value
    label['product_id'] = label['id']
    label['seller_id'] = seller['id']
    label['seller_name'] = seller['name']
    label['seller_address'] = seller['address']


def test_print_pdf():
    product = get_product(1)
    seller = get_seller(1)
    label = product.copy()
    label['packing_date'] = '2020-08-01'
    label['expiry_date'] = '2020-08-10'
    label['product_id'] = label['id']
    label['seller_id'] = seller['id']
    label['seller_name'] = seller['name']
    label['seller_address'] = seller['address']
    label['weight'] = 0.987

    if label['price_fixed']:
        label['price_fixed'] = format_price(float(label['price_fixed']))
        label['price'] = label['price_fixed']
    else:
        label['price_kg'] = format_price(float(label['price_kg']))
        label['price'] = format_price(float(label['weight']) * label['price_kg'])
    generate_pdf_label(label)


def change_product():
    product_selection.show(wait=True)
    app.cancel(get_weight)


def button_confirm_product_selection():
    global product
    global seller
    product_selection.hide()
    set_product_fields(product)
    set_label_fields(product)
    if not seller:
        seller = get_seller(1)
    product_window.show()


def button_create_new_product():
    global product
    global seller
    product_selection.hide()
    current_date = datetime.datetime.now().date()
    packing_date.value = current_date
    product = {}
    if not seller:
        seller = get_seller(1)
    product_window.show()


def button_confirm_product():
    global product
    product_window.hide()
    set_product_from_fields(product)
    product = save_product(product)
    app.repeat(1000, get_weight)
    set_label()
    draw_label()


def generate_label():
    global label
    if not "weight" in label:
        label['weight'] = 0.0

    if label['price_fixed']:
        label['price_fixed'] = format_price(float(label['price_fixed']))
        label['price'] = label['price_fixed']
    else:
        label['price_kg'] = format_price(float(label['price_kg']))
        label['price'] = format_price(float(label['weight']) * label['price_kg'])


def format_price(price):
    base = 5
    deci, inte = math.modf(price)
    return inte + (base * round(100 * deci / base)) / 100


def draw_label():
    generate_label()
    label_preview.clear()
    label_preview.image(0, 0, "static/label.png")
    label_preview.text(20, 10, label['name'], size=30)
    label_preview.text(20, 70, label['description'], size=20)
    if not label['price_fixed']:
        label_preview.text(100, 275, 'Fr/kg', size=14)
        label_preview.text(130, 310, "{:7.2f}".format(label['price_kg']), size=24)
    label_preview.text(20, 210, label['packing_date'], size=16)
    label_preview.text(185, 210, label['expiry_date'], size=16)
    label_preview.text(345, 210, "{:5.3f} kg".format(label['weight']), size=16)
    label_preview.text(270, 280, "{:7.2f}".format(label['price']), size=50)
    label_preview.text(20, 365, label['seller_name'], size=18)
    label_preview.text(20, 395, label['seller_address'], size=12)


def start_printing():
    status_box.bg = "green"
    status_message.value = "Impression automatique des étiquettes..."


def stop_printing():
    status_box.bg = None
    status_message.value = "Arrêt de l'impression des étiquettes..."


def export_file():
    app.cancel(get_weight)
    file_name = app.select_file(filetypes=[["CSV data", "*.csv"]], save=True)
    if file_name:
        if file_name.split('.')[-1] != 'csv':
            file_name = file_name + '.csv'
        data = get_labels()
        with open(file_name, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['#ID', 'Vendeur', '#ID produit', 'Nom', 'Description', 'Poids', 'Prix', 'Prix/kg', 'Date emballage', 'Date consommation'])
            writer.writerows(data)
        app.info("Export des données", "Les données ont été exportées dans le fichier {}".format(file_name))
    app.repeat(1000, get_weight)


def generate_pdf_label(label):
    styleName = ParagraphStyle('styleName', fontName="Helvetica-Bold", fontSize=12, alignment=1, spaceAfter=5)
    styleDescription = ParagraphStyle('styleDescription', fontName="Helvetica", fontSize=9, alignment=1, spaceAfter=0)
    styleSellerName = ParagraphStyle('styleSellerName', fontName="Helvetica-Bold", fontSize=8, alignment=1, spaceAfter=0)
    styleSellerAddress = ParagraphStyle('styleSellerAddress', fontName="Helvetica", fontSize=6, alignment=1, spaceAfter=0)

    temp_pdf_file = io.BytesIO()
    c = canvas.Canvas(temp_pdf_file, pagesize=(60*mm, 50*mm))

    header = []
    header.append(Paragraph('{}'.format(label['name']), styleName))
    header.append(Paragraph('{}'.format(label['description']), styleDescription))
    f = Frame(2*mm, 32*mm, 56*mm, 16*mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
    c.setStrokeColorCMYK(0, 1, 0.98, 0.15)
    f.addFromList(header, c)

    c.setFont('Helvetica', 8)
    c.drawString(2.4 * mm, 23 * mm, label['packing_date'])
    c.drawString(21.5 * mm, 23 * mm, label['expiry_date'])
    c.drawString(40.5 * mm, 23 * mm, "{:5.3f} kg".format(label['weight']))

    if not label['price_fixed']:
        c.setFont('Helvetica', 7)
        c.drawString(9.5 * mm, 16 * mm, 'Fr/kg')
        c.setFont('Helvetica', 10)
        c.drawRightString(28 * mm, 10 * mm, "{:7.2f}".format(label['price_kg']))
    c.setFont('Helvetica-Bold', 16)
    c.drawRightString(56 * mm, 10 * mm, "{:7.2f}".format(label['price']))

    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(30 * mm, 5 * mm, "{}".format(label['seller_name']))
    c.setFont('Helvetica', 6)
    c.drawCentredString(30 * mm, 2 * mm, "{}".format(label['seller_address']))

    c.showPage()
    c.save()

    temp_pdf_file.seek(0)
    new_pdf = PdfFileReader(temp_pdf_file)
    existing_pdf = PdfFileReader(open("static/label.pdf", "rb"))
    output = PdfFileWriter()
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    outputStream = open("print.pdf", "wb")
    output.write(outputStream)
    outputStream.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    product = None
    label = None
    seller = None
    app = App(title="L'agité du bocal", width=1024, height=600)
    app.tk.iconbitmap("./static/favicon.ico")

    status_box = Box(app, width="fill", align="bottom", border=True)
    status_message = Text(status_box, text="Ready", size=10, align="left")

    options_box = Box(app, height="fill", align="right")
    Text(options_box, text="Options")
    PushButton(options_box, text="Changer le produit",
               command=change_product, width="fill")
    Text(options_box, text="")
    Text(options_box, text="Impression")
    PushButton(options_box, text="Démarrer l'impression", command=start_printing, width="fill")
    PushButton(options_box, text="Stopper l'impression", command=stop_printing, width="fill")
    Text(options_box, text="")
    Text(options_box, text="Données")
    PushButton(options_box, text="Exporter les données", command=export_file, width="fill")


    content_box = Box(app, align="top", width="fill", border=True)

    products_dict = get_products_dict()
    sellers_dict = get_sellers_dict()

    # product_selection window
    # Used to select to product at the beginning

    product_selection = Window(app, title="Sélectionner un produit à peser...", height=300, visible=False)
    product_selection.tk.iconbitmap("./static/favicon.ico")
    Text(product_selection, text="")
    Text(product_selection, text="Sélectionner le produit")
    Combo(product_selection, width="fill", options=products_dict, command=select_product)
    Text(product_selection, text="")
    Text(product_selection, text="Sélectionner le fournisseur")
    Combo(product_selection, width="fill", options=sellers_dict, command=select_seller)
    product_selection_buttons_box = Box(product_selection, width="fill", align="bottom")
    PushButton(product_selection_buttons_box, text="Créer un nouveau produit", align="right", command=button_create_new_product)
    PushButton(product_selection_buttons_box, text="OK", align="right", command=button_confirm_product_selection)


    product_window = Window(app, title="Gestion d'article", visible=False)
    product_window.tk.iconbitmap("./static/favicon.ico")
    Text(product_window, text="Données article")
    product_form_box = Box(product_window, layout="grid", width="fill", border=True)
    Text(product_form_box, text="Nom du produit", grid=[0, 0], align="left")
    name = TextBox(product_form_box, width="fill", grid=[1, 0])
    Text(product_form_box, text="Description", grid=[0, 1], align="left")
    description = TextBox(product_form_box, width="fill", grid=[1, 1])
    Text(product_form_box, text="Prix (kg)", grid=[0, 2], align="left")
    price_kg = TextBox(product_form_box, width="fill", grid=[1, 2])
    Text(product_form_box, text="Prix fixe (laisser vide si prix au kg)", grid=[0, 3], align="left")
    price_fixed = TextBox(product_form_box, width="fill", grid=[1, 3])
    Text(product_form_box, text="Péremption (jours)", grid=[0, 4], align="left")
    expiration_days = TextBox(product_form_box, width="fill", grid=[1, 4], command=update_expiry_date)
    Text(product_window, text="Données étiquette")
    label_form_box = Box(product_window, layout="grid", width="fill", border=True)
    Text(label_form_box, text="Date d'emballage", grid=[0, 0], align="left")
    packing_date = TextBox(label_form_box, width="fill", grid=[1, 0])
    Text(label_form_box, text="Date de péremption", grid=[0, 1], align="left")
    expiry_date = TextBox(label_form_box, width="fill", grid=[1, 1])
    buttons_box = Box(product_window, width="fill", align="bottom")
    PushButton(buttons_box, text="Annuler", align="right")
    PushButton(buttons_box, text="OK", align="right", command=button_confirm_product)

    label_box = Box(content_box, height="fill", width="fill", align="left", visible=False)
    label_preview = Drawing(label_box, width=510, height=426)
    label_preview.image(0, 0, "static/label.png")
    label_box.show()



    if not product:
        change_product()



    app.display()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
