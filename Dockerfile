FROM python:3.9

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update
RUN apt install zip
EXPOSE 8888
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"
CMD ["jupyter", "lab","--no-browser","--allow-root","--ip=0.0.0.0"]
#CMD ["/bin/bash"]
