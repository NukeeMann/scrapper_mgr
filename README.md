# scrapper_mgr

python3 -m pip install beautifulsoup4 scrapy

scrapy startproject etipg  
cd etipg
scrapy genspider etilinks eti.pg.edu.pl
scrapy crawl etilinks
