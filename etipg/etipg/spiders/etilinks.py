import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.http.response.html
from scrapy.spiders import CrawlSpider, Rule, Spider
from scrapy.linkextractors import LinkExtractor
from ..items import EtipgPageContent, EtipgFile

import os
import requests
import urllib.parse
from bs4 import BeautifulSoup


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
    title_text = soup.find('div', {"id":'block-tytulstrony'})
    if not title_text:
        title_text = ""
    else:
        title_text = title_text.get_text()

    content = soup.find(tag)
    if content != None:
        content = title_text + content.get_text()
    return content

def read_pdf_links(response):
    soup = BeautifulSoup(response.text, "lxml")

    contents = soup.find_all('a', href=True)
    a_links = [ x["href"] for x in contents if x["href"].endswith('.pdf')]

    return a_links

class EtilinksSpider(Spider):
    name = "etilinks"
    default_domain = "eti.pg.edu.pl"
    allowed_domains = ["eti.pg.edu.pl", "files.pg.edu.pl"]
    start_urls = ["https://eti.pg.edu.pl"]

    def parse(self, response):
        result = EtipgPageContent()
        dirpath = url_to_dir(response.url)
        result["dirpath"] = dirpath

        main_content = read_tag(response, "main")
        article_content = read_tag(response, "article")

        content_text = None

        #article tag has higher priority as it is more narrow
        if article_content != None and main_content != None:
            content_text = article_content
        else:
            content_text = main_content or article_content
        
        result["content"] = content_text
        yield result
        
        links_to_pdf = read_pdf_links(response)
        
        for link in links_to_pdf:
            item = EtipgFile(dirpath = dirpath, link = link)
            yield item
        
        le = LinkExtractor(allow_domains = [self.default_domain], deny=(r"/documents/.*",r"/en/.*",r"/.*/....-../.*")) # Dokumenty, ENglish, aktualnosci
        links = le.extract_links(response)
        
        for link in links:
            yield scrapy.Request(link.url, callback=self.parse)
