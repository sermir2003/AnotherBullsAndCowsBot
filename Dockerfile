FROM python:3.8

ADD bot.py .

RUN pip install pytelegrambotapi

# EXPOSE 8888

CMD ["python", "./bot.py"]
