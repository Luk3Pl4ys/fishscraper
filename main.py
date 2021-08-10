import datetime as dt
import os
import smtplib
import time
from email.message import EmailMessage

import requests
import schedule
from bs4 import BeautifulSoup


# get date and rearange it to a human readable format
def get_date():
    now = dt.datetime.now()
    day = str(now.day)
    month = str(now.month)
    year = str(now.year)
    clock = f'[{day}.{month}.{year}]'
    return clock


# scrape information from the website and store it in lists, decide wheter it is the standard text or not,
# call the function to send an email if it's not the standard text
def scrape_table():
    print(get_date())
    print('getting information...')
    source = requests.get('http://fischvomkutter.de/moeltenort.html').text

    soup = BeautifulSoup(source, 'lxml')

    titles = []
    messages = []

    for entry in soup.find('table', id='Tabelle1').find_all('tr'):
        raw_title = entry.find('td', width="252")
        if raw_title is not None:
            title = raw_title.font.text
            title = title.strip()
            title = title.replace("Ã¶", "ö")
            title = title.replace(':', '')
            titles.append(title)

        else:
            message_url = entry.td.font.script.attrs['src']
            message_source = requests.get('http:' + message_url).text
            message_soup = BeautifulSoup(message_source, 'lxml')
            raw_message = message_soup.find_all('p')
            message = raw_message[1].text
            messages.append(message)

    print(titles)
    print(messages)

    fishnumbers = []

    for idx, message in enumerate(messages):
        text = message[21:]

        if text == 'Zurzeit kein Fischverkauf, bitte schauen Sie später wieder herein.':
            continue
        else:
            fishnumbers.append(idx)

    fishmessages = []

    for number in fishnumbers:
        title = titles[number]
        message = messages[number]
        fishmessages.append(title + ':  \n' + message + '\n\n')

    if not fishmessages == []:
        send_email(fishmessages)
    else:
        print('no new information found! waiting for next day...')


# input: list of pre formated messages to be sent
# creates an encrypted connection to my gmail adress, sends an email to my main email adress
# containing the previously scraped messages
def send_email(fishmessages):
    print('new information found! preparing email...')

    gmail_address = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_PASS')
    email_address = os.environ.get('EMAIL_USER')
    dad_email_adress = os.environ.get('DADMAIL_USER')

    msg = EmailMessage()
    msg['Subject'] = 'FISCHVERKAUF!!!'
    msg['From'] = gmail_address
    msg['To'] = [email_address, dad_email_adress]
    raw_body = 'Es wird aktuell folgender Fisch verkauft: \n\n'
    for message in fishmessages:
        raw_body += message
    body = raw_body
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(gmail_address, gmail_password)

        print('sending e-mail! waiting for next day...')

        smtp.send_message(msg)


# schedule the function to run every day at 7:30 AM
schedule.every().day.at('07:30').do(scrape_table)

# execution of the code on startup, check the time every minute
print('script running...')
get_date()
scrape_table()
while True:
    schedule.run_pending()
    time.sleep(59)
