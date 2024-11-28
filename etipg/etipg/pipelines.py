# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import EtipgPageContent, EtipgFile
import os
import requests
import urllib
from pdfminer.high_level import extract_text_to_fp
from io import BytesIO
from bs4 import BeautifulSoup


class EtipgPipeline:
    def process_item(self, item, spider):
        if item['dirpath'].split(os.sep)[0] not in spider.allowed_domains:
            return item
        
        os.makedirs(item['dirpath'], exist_ok=True)
        if isinstance(item, EtipgFile):
            file_path, pdf_name = self.download_file(item['link'], item['dirpath'])
            
            html_text = self.pdf_to_html(file_path)
            pdf_content = BeautifulSoup(html_text, "lxml").get_text()
            
            self.save_context(pdf_content, item['dirpath'], pdf_name.replace('.pdf', '.txt'))
        elif isinstance(item, EtipgPageContent):
            self.save_context(item['content'], item['dirpath'], "content.txt")

        return item

    def download_file(self, url, dirpath):
        filename = urllib.parse.unquote(url.split("/")[-1]).replace(" ","")[-64:]
        r = requests.get(url)
        path = os.path.join(dirpath, filename)
        open(path, 'wb').write(r.content)
        return path, filename
    
    def pdf_to_html(self, pdf_path):
        output_buffer = BytesIO()
        
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(pdf_file, output_buffer, output_type='html')

        html_content = output_buffer.getvalue().decode('utf-8')
        return html_content
    
    def save_context(self, content, dirpath, filename):
        filepath = os.path.join(dirpath, filename)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)