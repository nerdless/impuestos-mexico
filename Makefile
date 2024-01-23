#python src/main.py OOME871219PL5 2019 --type anual
build:
	docker build -t impuestos .

jupyter:
	docker run --rm -it -p 8888:8888 -v $(shell pwd):/usr/src/app --env-file=.env impuestos

bash:
	docker run --rm -it -v $(shell pwd):/usr/src/app --env-file=.env impuestos /bin/bash

ipython:
	docker run --rm -it -v $(shell pwd):/usr/src/app --env-file=.env impuestos ipython

install-crawler-env:
	pip install -r crawlers/requirements.txt

crawl:
	export $(cat .env | xargs)
	ipython
