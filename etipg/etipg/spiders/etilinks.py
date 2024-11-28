import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.http.response.html
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

def download_file(url, filename, dirpath):
    r = requests.get(url)
    path = os.path.join(dirpath, filename)
    open(path, 'wb').write(r.content)
    return path

def remove_https(url):
    result = url.replace("https://","")
    return result.replace("http://","")

def url_to_dir(url):
    url = remove_https(url)
    first_split = url.split("?")
    second_split = first_split[0].split("/")
    if len(first_split) > 1:
        first_split = first_split[1:]
    else:
        first_split = []
    dirpath = os.path.join(*(second_split + first_split))
    return dirpath

def read_tag(response, tag):
    soup = BeautifulSoup(response.text, "lxml")

    #remove navigation bars
    for s in soup.find_all('div', {"class": ['sidebar','side-menu']}):
        s.decompose()

    # select only specific tag and remove all non-text elements like <tags> </tags>
    content = soup.find(tag)
    if content != None:
        content = content.get_text()
    return content

class EtilinksSpider(CrawlSpider):
    name = "etilinks"
    allowed_domains = ["eti.pg.edu.pl", "files.pg.edu.pl"]
    start_urls = ["https://eti.pg.edu.pl"]
    rules = [
            Rule(LinkExtractor(allow_domains = ["eti.pg.edu.pl"], deny=(r"/documents/.*",r"/en/.*",r"/.*/....-../.*")), callback='parse_page', follow=True),
            Rule(LinkExtractor(allow_domains = ["files.pg.edu.pl"],), process_request="parse_file", follow=False)
            ]
    file_hash = dict()

    def parse_page(self, response):
        dirpath = url_to_dir(response.url)
        os.makedirs(dirpath, exist_ok=True)

        main_content = read_tag(response, "main")
        article_content = read_tag(response, "article")

        content_text = None

        #article tag has higher priority as it is more narrow
        if article_content != None and main_content != None:
            content_text = article_content
        else:
            content_text = main_content or article_content

        if content_text:
            filepath = os.path.join(dirpath, "content.txt")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(content_text)

    def parse_file(self, request, response):
        filename = urllib.parse.unquote(request.url.split("/")[-1]).replace(" ","")
        if not filename.endswith("pdf"):
            filename = filename[-64:]
            self.file_hash[request.url] = filename[-64:]
            self.logger.info("Using alternative name %s %s!", request.url, filename)            
        path = download_file(request.url, filename, url_to_dir(response.url))
        self.logger.info("Downloaded %s", path)
        return None
