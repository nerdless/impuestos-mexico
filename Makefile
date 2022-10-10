build:
	docker build -t impuestos .

jupyter:
	docker run --rm -it -p 8888:8888 -v $(shell pwd):/usr/src/app --env-file=.env impuestos

bash:
	docker run --rm -it -v $(shell pwd):/usr/src/app --env-file=.env impuestos /bin/bash

ipython:
	docker run --rm -it -v $(shell pwd):/usr/src/app --env-file=.env impuestos ipython
