import sqlite3
from datetime import datetime, timedelta
import subprocess
from selenium import webdriver
from urllib.parse import urlencode, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pdfkit
from urllib import request
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import utils
from os import path, getcwd
from datetime import datetime
from slugify import slugify

timeout = 2
document_types_list = [
    ['Ato de Diretor', 'Ato Normativo Conjunto', 'Ato do Presidente', 'Comunicado', 'Comunicado Conjunto', 'Decisão Conjunta',
        'Instrução Normativa Conjunta', 'Portaria Conjunta', 'Instrução Normativa Conjunta', 'Portaria Conjunta'],
    ['Carta Circular', 'Circular'],
    ['Instrução Normativa BCB', 'Resolução BCB', 'Resolução CMN',
        'Resolução Conjunta', 'Resolução Coremec']
]
subject = "Novo(s) documento(s) Normativo(s)"
mail_server = "smtp.gmail.com"
mail_port = 465
mail_username = "shaiennyfrezende@gmail.com"
mail_password = "gbfdcwoohpvfkwwh"
sender = mail_username


def search(search_data):

    if search_data['number'] is None:
        search_data['number'] = ''

    if search_data['content'] is None:
        search_data['content'] = ''

    start_date = (datetime.now().date() -
                  timedelta(days=search_data['frequency'])).strftime('%d/%m/%Y')
    end_date = datetime.now().date().strftime('%d/%m/%Y')

    data = {
        'tipoDocumento': search_data['document_type'],
        'numero': search_data['number'],
        'conteudo': search_data['content'],
        'dataInicioBusca': start_date,
        'dataFimBusca': end_date
    }

    # subprocess.Popen(
    #    '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 -incognito', shell = True)
    options = webdriver.ChromeOptions()

    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    # driver = webdriver.Chrome(options=options)
    driver = webdriver.Chrome('C:\\chromedriver\chromedriver.exe')
    start_row = 0
    links = []

    while True:

        driver.get('https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?' +
                   urlencode(data) + '&startRow=' + str(start_row))

        results_selector = '.resultado-item a[href]'
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, results_selector)))
        except TimeoutException:
            break
        results = driver.find_elements(By.CSS_SELECTOR, results_selector)
        for result in results:
            links.append(result.get_attribute('href'))
        start_row += 15

    files = []

    for link in links:

        driver.get(link)
        url_data = parse_qs(link.split('?')[1])
        document_type = url_data['tipo'][0]
        number = url_data['numero'][0]
        filename = getcwd() + '\\site\\flaskblog\\pdf\\' + \
            slugify(document_type + ' nº ' + number) + '.pdf'
        files.append(filename)

        document_content_selector = ''
        element_to_wait_selector = ''
        if document_type in document_types_list[0]:
            document_content_selector = 'main'
            element_to_wait_selector = 'main exibenormativo #conteudoTexto'
        elif document_type in document_types_list[1]:
            document_content_selector = 'main exibenormativo a'
            element_to_wait_selector = document_content_selector
        elif document_type in document_types_list[2]:
            document_content_selector = 'main exibenormativo .corpoNormativo, main exibenormativo #conteudoTexto'
            element_to_wait_selector = document_content_selector
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, element_to_wait_selector)))
        except TimeoutException:
            continue
        document_content = driver.find_elements(
            By.CSS_SELECTOR, document_content_selector)[0]

        if document_type in document_types_list[0] or document_type in document_types_list[2]:

            stylesheets_selector = 'link[rel="stylesheet"]'
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, stylesheets_selector)))
            except TimeoutException:
                continue
            # css = list(map(lambda css: css.get_attribute('href'), driver.find_elements(By.CSS_SELECTOR, stylesheets_selector)))
            # css = [getcwd() + '\\flaskblog\\static\\css\\styles.50e7fffa09cac58b.css']

            document_content_html = document_content.get_attribute('outerHTML')

            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
            """
            # html += stylesheets
            html += """
            </head>
            <body>
            """
            html += document_content_html
            html += """
            </body>
            </html>
            """
            config = pdfkit.configuration(
                wkhtmltopdf='D:/wkhtmltopdf/bin/wkhtmltopdf.exe')
            pdfkit.from_string(
                html, filename, configuration=config, verbose=True)

        elif document_type in document_types_list[1]:

            document_content_href = document_content.get_attribute('href')

            request.urlretrieve(document_content_href, filename)

    driver.close()

    body = """Segue novo(s) documento(s) em anexo, de acordo com pesquisa cadastrada
    
    Tipo de Documento: """ + search_data['document_type'] + """
    Número: """ + (search_data['number'] if search_data['number'] != '' else '-') + """
    Conteúdo: """ + (search_data['content'] if search_data['content'] != '' else '-') + """
    Período: """ + start_date + " a " + end_date

    receiver = search_data['email']
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = subject
    message['Message-id'] = utils.make_msgid()
    message['Date'] = utils.formatdate()
    message.attach(MIMEText(body, "plain"))
    for file in files:
        if path.exists(file):
            with open(file, "rb") as attachment:
                part = MIMEBase("application", "pdf")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment; filename=\"" + str(path.basename(file)) + "\"",
            )
            message.attach(part)
        else:
            print('Arquivo ' + file + ' não existe')
    text = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
        server.login(mail_username, mail_password)
        server.sendmail(sender, receiver, text.encode('utf-8'))

    conn = sqlite3.connect('../site/flaskblog/site.db')
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO search_history(
            search_id,
            created_at)
        VALUES(
            """ + str(search_data['id']) + """,
            '""" + str(datetime.now()) + """'
        )"""
    )
    conn.commit()
    conn.close()
