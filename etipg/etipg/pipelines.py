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
import mimetypes
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
import shutil


class EtipgPipeline:
    def process_item(self, item, spider):
        if item['dirpath'].split(os.sep)[0] not in spider.allowed_domains:
            return item
        
        os.makedirs(item['dirpath'], exist_ok=True)
        if isinstance(item, EtipgFile):
            self.process_file_item(item)
        elif isinstance(item, EtipgPageContent):
            self.process_page_item(item)
            
        return item
    
    def process_file_item(self, item):
        link = item["link"]
        dirpath = item['dirpath']
        try:
            pdf_name = urllib.parse.unquote(link.split("/")[-1]).replace(" ","")[-64:]
            file_path = os.path.join(dirpath, pdf_name)
            
            self.download_file(link, file_path)

            self.extract_pdf_text(file_path, dirpath)
            # html_text = self.pdf_to_html(file_path)
            # pdf_content = BeautifulSoup(html_text, "lxml").get_text()
            # self.save_context(pdf_content, dirpath, pdf_name.replace('.pdf', '.txt'))
        except Exception as err:
            err_msg = str(err)
            if mimetypes.guess_type(file_path)[0] != 'application/pdf':
                err_msg += "\nDownloaded file is not a PDF!"
            
            self.save_context(self.format_error_log(item, err_msg), "/home/nukeemann/github/scrapper_mgr/etipg/errors", pdf_name+".error.txt")
        
    def process_page_item(self, item):
        try:
            self.save_context(item['content'], item['dirpath'], "content.txt")
        except Exception as err: 
            #print(self.format_error_log(item, str(err)))
            self.save_context(self.format_error_log(item, str(err)), "/home/nukeemann/github/scrapper_mgr/etipg/errors", "error.txt")


    def download_file(self, url, path):
        r = requests.get(url)
        open(path, 'wb').write(r.content)
    
    def pdf_to_html(self, pdf_path):
        output_buffer = BytesIO()
        
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(pdf_file, output_buffer, output_type='html')

        html_content = output_buffer.getvalue().decode('utf-8')
        return html_content
    
    def save_context(self, content, dirpath, filename):
        filepath = os.path.join(dirpath, filename)
        content_stripped = os.linesep.join([s for s in content.splitlines() if s])
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content_stripped)
    
    def format_error_log(self, item, err_msg):
        return f"""
                ###########################################
                ITEM: {str(item)}
                EXCEPT: {err_msg}
                ###########################################
                """
    
    def extract_pdf_text(self, pdf_path, dirpath):
        # Create paths and writers
        pdf_name = pdf_path.split("/")[-1]
        local_image_dir, local_md_dir = os.path.join(dirpath, "images"), dirpath
        os.makedirs(local_image_dir, exist_ok=True)
        image_save_dir = str(os.path.basename(local_image_dir))

        # if File already exists, skip
        x = os.path.join(local_md_dir, f"{pdf_name}.txt")
        print(f"Try downloading {x}")
        if os.path.exists(str(os.path.join(local_md_dir, f"{pdf_name}.txt"))):
            print(f"{x} file already exists!")
            return

        image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

        # Read the PDF content
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(pdf_path)

        # Create dataset instance
        ds = PymuDocDataset(pdf_bytes, lang="pl")

        # Inference
        infer_result = ds.apply(doc_analyze, ocr=False, lang="pl")
        pipe_result = infer_result.pipe_txt_mode(image_writer)

        # Save extracted content
        pipe_result.dump_md(md_writer, f"{pdf_name}.txt", image_save_dir)

        # Remove images directory
        shutil.rmtree(local_image_dir, ignore_errors=True)