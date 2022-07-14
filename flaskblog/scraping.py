from urllib.request import urlopen
from bs4 import BeautifulSoup

html = urlopen("https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?tipoDocumento=Todos")
bsObj = BeautifulSoup(html.read(), "html.parser")

teste = bsObj.findAll("", {"class":"resultado-item"})
for a in teste:
    print(a)

comunicados = bsObj.findAll(text="Comunicado")
for a in comunicados:
    print(a)