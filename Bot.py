import os
import requests
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask, request
from telebot import types
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

## Telegram Bot Starter
# API Token for Telegram BOT from BOTFather
TOKEN = "TELEGRAM_BOT_TOKEN"
HEROKU_URL = "HEROKU_URL"

# Initializing the bot and server
bot = telebot.TeleBot(token=TOKEN)
server = Flask(__name__)

# Bot's Functionalities
def sendMessage(message, text):
    bot.send_message(message.chat.id, text)


# Initializing database connection
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Initializing world list
world = []

# Initializing time
updt_time = ""

# Initializing data list
data = []

# Creating sorted list for custom keyboard use
country_sort = None

# Creating country key value pair for results
countries = {}

# chat_ids for sending notification
chat_id = []

# Function to run every 15 minutes to update world and country stats with latest time mentioned
def WorldData():

    # URL for scraping world data
    url = "https://www.worldometers.info/coronavirus/"
    html = requests.get(url)
    raw_data = BeautifulSoup(html.text, "html.parser")

    # Initializing global variables
    global world, updt_time, data, country_sort, countries, chat_id

    # Checking if BD stats is present and saving the current total cases
    check_bd = countries.get("bangladesh")

    if check_bd:
        temp_bd = int(
            "".join(i for i in data[countries["bangladesh"]]["Total Cases"] if i != ",")
        )
        cases_bd = int(
            "".join(i for i in data[countries["bangladesh"]]["Total Tests"] if i != ",")
        )
        bd_new_test = int(
            "".join(i for i in data[countries["bangladesh"]]["New Tests"] if i != ",")
        )
        positivity_rate = data[countries["bangladesh"]]["Positivity Rate"][:-1]
    else:
        temp_bd = False

    # Initiliazing sending BD update
    send_bd_update = False

    # Clearing saved data for updating with new one
    data = []
    world = []
    country_sort = None
    updt_time = ""

    # Getting the data update time
    init_time = raw_data.find_all(class_="label-counter")
    time_string = init_time[0].find_next_sibling().get_text()
    dt = datetime.strptime(time_string[14:-4], "%B %d, %Y, %H:%M") + timedelta(hours=6)
    updt_time = dt.strftime("%I %M %p, %A %d %B %Y")

    # Getting the global data
    temp = raw_data.find_all(class_="body_world")
    for i in temp:
        total_case_count = i.find("td").find_next_sibling().find_next_sibling()
        total_new_cases = total_case_count.find_next_sibling()
        total_deaths = total_new_cases.find_next_sibling()
        rev_total_deaths = total_deaths.get_text().split()
        new_deaths = total_deaths.find_next_sibling()
        total_recovered = new_deaths.find_next_sibling()
        active_cases = total_recovered.find_next_sibling().find_next_sibling()
        world.append(
            {
                "Country": "World",
                "Total Cases": total_case_count.get_text(),
                "New Cases": total_new_cases.get_text(),
                "Total Deaths": rev_total_deaths[0],
                "New Deaths": new_deaths.get_text(),
                "Total Recovered": total_recovered.get_text(),
                "Active Cases": active_cases.get_text(),
            }
        )
        break

    # Getting country wise data
    source_code = raw_data.find_all(class_="mt_a")
    count = 0
    for i in source_code:
        if count == 213:
            break
        name = i.get_text()
        total_case_count = i.find_parent().find_next_sibling()
        total_new_cases = total_case_count.find_next_sibling()
        total_deaths = total_new_cases.find_next_sibling()
        rev_total_deaths = total_deaths.get_text().split()
        if len(rev_total_deaths) == 0:
            rev_total_deaths.append("0")
        new_deaths = total_deaths.find_next_sibling()
        total_recovered = new_deaths.find_next_sibling()
        active_cases = total_recovered.find_next_sibling().find_next_sibling()
        # Check if country is Bangladesh
        if name.lower() == "bangladesh":

            # Getting data from Covid API
            url_2 = "https://disease.sh/v3/covid-19/countries/bangladesh"
            html_2 = requests.get(url_2)

            # Coverting to JSON
            bd_data = html_2.json()

            # Measuring out current active cases
            active_cases = bd_data["cases"] - bd_data["deaths"] - bd_data["recovered"]

            # Check if BD status available
            if temp_bd:
                # Check if today's case has updated
                if int(bd_data["cases"]) > temp_bd:
                    # Get ready to send update
                    send_bd_update = True
                    # Update New Test and % Rate
                    bd_new_test = bd_data["tests"] - cases_bd
                    positivity_rate = round(
                        ((bd_data["todayCases"] / bd_new_test) * 100), 2
                    )
                else:
                    print("No new update for BD")
            else:
                print("No temp bd")
                bd_new_test = 0
                positivity_rate = "0.00"

            # Append all data from DGHS website
            data.append(
                {
                    "Country": name,
                    "Total Cases": f'{bd_data["cases"]:,}',
                    "New Cases": f'+{bd_data["todayCases"]:,}',
                    "Total Deaths": f'{bd_data["deaths"]:,}',
                    "New Deaths": f'+{bd_data["todayDeaths"]:,}',
                    "Total Recovered": f'{bd_data["recovered"]:,}',
                    "Active Cases": f"{active_cases:,}",
                    "Positivity Rate": f"{positivity_rate}%",
                    "New Tests": f"+{bd_new_test:,}",
                    "Total Tests": f'{bd_data["tests"]:,}',
                }
            )
        else:
            data.append(
                {
                    "Country": name,
                    "Total Cases": total_case_count.get_text(),
                    "New Cases": total_new_cases.get_text(),
                    "Total Deaths": rev_total_deaths[0],
                    "New Deaths": new_deaths.get_text(),
                    "Total Recovered": total_recovered.get_text(),
                    "Active Cases": active_cases.get_text(),
                }
            )
        # Keeping count of countries checked
        count += 1

    # Preparing the reply keyboard with country names
    country_sort = sorted([i["Country"] for i in data])

    countries = {}
    for idx, i in enumerate(data):
        countries[i["Country"].lower()] = idx

    # Populating latest list of ids who have requested notification
    chat_id = []

    query = db.execute("SELECT chat_id FROM chat").fetchall()
    for i in query:
        chat_id.append(i[0])

        print(chat_id)

    # If BD stats has been updated, send notification
    if send_bd_update:
        text1 = f"Update for Bangladesh.\n\nAs of:\n{updt_time}.\n\nNew Case(s):        {data[countries['bangladesh']]['New Cases']}\nTotal Cases:           {data[countries['bangladesh']]['Total Cases']}\nNew Death(s):       {data[countries['bangladesh']]['New Deaths']}\nTotal Deaths:          {data[countries['bangladesh']]['Total Deaths']}\nTotal Recovered:    {data[countries['bangladesh']]['Total Recovered']}\nActive Cases:         {data[countries['bangladesh']]['Active Cases']}\nPositivity Rate:         {data[countries['bangladesh']]['Positivity Rate']}\nNew Tests:           {data[countries['bangladesh']]['New Tests']}\nTotal Tests:          {data[countries['bangladesh']]['Total Tests']}"
        for i in chat_id:
            try:
                bot.send_message(i, text1, parse_mode="HTML")
            except:
                print("problem with this chat_id")
                print(i)

    return None


# Running first instance
WorldData()

# Custom Keyboard for Country list
markup = types.ReplyKeyboardMarkup(row_width=3)
markup.add("/global")
for i in range(0, len(country_sort), 3):
    try:
        markup.add(country_sort[i], country_sort[i + 1], country_sort[i + 2])
    except:
        break

# Background task for getting update every 10 minutes
sched = BackgroundScheduler(daemon=True)
sched.add_job(WorldData, "interval", minutes=5, max_instances=2)
sched.start()

## Bot usage
# This method will send a message formatted in HTML to the user whenever it starts the bot with the /start command
@bot.message_handler(commands=["start"])
def send_info(message):
    text1 = (
        "<b>Welcome to COVID-19 Worldwide Statistics</b>\n"
        "\nDirections:\n\n1. You can type /global for worldwide summary.\n\n2. You can type /about for details about the bot.\n\n3. You can type /notify for getting daily updates of Bangladesh Statistics.\n\n4. In case the list of countries is gone from the view, you can tap on the icon with 4 circles in it to bring it back.\n\nStay indoors and maintain hygiene during these trying times!"
    )
    bot.send_message(message.chat.id, text1, parse_mode="HTML")
    bot.send_message(
        message.from_user.id,
        f"Which country's COVID-19 statistics do you want to know, {message.from_user.first_name}?",
        reply_markup=markup,
    )


# This method will send bot usage directions when called using /usage
@bot.message_handler(commands=["usage"])
def send_info(message):

    text1 = "<b>Directions:</b>\n\n1. You can type /global for worldwide summary.\n\n2. You can type /about for details about the bot.\n\n3. You can type /notify for getting daily updates of Bangladesh Statistics.\n\n4. In case the list of countries is gone from the view, you can tap on the icon with 4 circles in it to bring it back.\n\n5. Empty data fields maybe present when the country hasn't updated their information for that field\n\nStay indoors and maintain hygiene during these trying times!"
    bot.send_message(message.chat.id, text1, parse_mode="HTML")
    bot.send_message(
        message.from_user.id,
        f"Which country's COVID-19 statistics do you want to know, {message.from_user.first_name}?",
        reply_markup=markup,
    )


# This method will send global statistic when called with /global
@bot.message_handler(commands=["global"])
def send_info(message):
    text1 = (
        f"Summary of COVID-19 Worldwide.\n\nStats Updated as of:\n{updt_time}.\n"
        f"\nNew Case(s):        {world[0]['New Cases']}\nTotal Cases:           {world[0]['Total Cases']}\nNew Death(s):       {world[0]['New Deaths']}\nTotal Deaths:          {world[0]['Total Deaths']}\nTotal Recovered:    {world[0]['Total Recovered']}\nActive Cases:         {world[0]['Active Cases']}"
    )
    bot.send_message(message.chat.id, text1, parse_mode="HTML")
    bot.send_message(
        message.from_user.id,
        f"Do you want statistics on any other country, {message.from_user.first_name}? If needed, you can type /usage for directions.",
        reply_markup=markup,
    )


# This method will provide information about the app when called with /about
@bot.message_handler(commands=["about"])
def send_info(message):
    text1 = (
        "<b>Data Source:</b>\n www.worldometers.info/coronavirus/ \n\n"
        "<b>About Me:</b>\n @IshmamChowdhury \n\n"
        "<b>Source Code for bot:</b>\n www.github.com/Ishmam156/covid-19-telegrambot/ \n\n"
        f"Kindly reach out via telegram in case you've found any bug, {message.from_user.first_name}!\n"
    )
    bot.send_message(message.chat.id, text1, parse_mode="HTML")
    bot.send_message(
        message.from_user.id,
        f"Which country's COVID-19 statistics do you want to know, {message.from_user.first_name}?",
        reply_markup=markup,
    )


# This method will provide confirmation when user has opted in for notification using /notify
@bot.message_handler(commands=["notify"])
def send_info(message):
    if message.chat.id not in chat_id:
        text1 = (
            f"You have been added to the notification list for Bangladesh COVID-19 Statistics, {message.from_user.first_name}.\n\n"
            "You will be provided daily update when the data updates.\n\n"
        )
        bot.send_message(message.chat.id, text1, parse_mode="HTML")
        bot.send_message(
            message.from_user.id,
            f"Which country's COVID-19 statistics do you want to know, {message.from_user.first_name}?",
            reply_markup=markup,
        )

        db.execute("INSERT INTO chat (chat_id) VALUES (:val)", {"val": message.chat.id})
        db.commit()
    else:
        text1 = (
            f"You are already added to the notification list for Bangladesh COVID-19 Statistics, {message.from_user.first_name}.\n\n"
            "You will be provided daily update when the data updates.\n\n"
        )
        bot.send_message(message.chat.id, text1, parse_mode="HTML")
        bot.send_message(
            message.from_user.id,
            f"Which country's COVID-19 statistics do you want to know, {message.from_user.first_name}?",
            reply_markup=markup,
        )


# This method checks the message a user puts in and if not blank, it will check in the countries
@bot.message_handler(func=lambda msg: msg.text is not None)
def reply_to_message(message):
    if message.text.lower() == "bangladesh":
        sendMessage(
            message,
            f"Summary for {message.text}.\n\nStats Updated as of:\n{updt_time}.\n\nNew Case(s):        {data[countries[message.text.lower()]]['New Cases']}\nTotal Cases:           {data[countries[message.text.lower()]]['Total Cases']}\nNew Death(s):       {data[countries[message.text.lower()]]['New Deaths']}\nTotal Deaths:          {data[countries[message.text.lower()]]['Total Deaths']}\nTotal Recovered:    {data[countries[message.text.lower()]]['Total Recovered']}\nActive Cases:         {data[countries[message.text.lower()]]['Active Cases']}\nPositivity Rate:         {data[countries[message.text.lower()]]['Positivity Rate']}\nNew Tests:              {data[countries[message.text.lower()]]['New Tests']}\nTotal Tests:             {data[countries[message.text.lower()]]['Total Tests']}",
        )
        sendMessage(
            message,
            f"Do you want statistics on any other country, {message.from_user.first_name}?  If needed, you can type /usage for directions.",
        )
    elif message.text.lower() in countries:
        sendMessage(
            message,
            f"Summary for {message.text}.\n\nStats Updated as of:\n{updt_time}.\n\nNew Case(s):        {data[countries[message.text.lower()]]['New Cases']}\nTotal Cases:           {data[countries[message.text.lower()]]['Total Cases']}\nNew Death(s):       {data[countries[message.text.lower()]]['New Deaths']}\nTotal Deaths:          {data[countries[message.text.lower()]]['Total Deaths']}\nTotal Recovered:    {data[countries[message.text.lower()]]['Total Recovered']}\nActive Cases:         {data[countries[message.text.lower()]]['Active Cases']}",
        )
        sendMessage(
            message,
            f"Do you want statistics on any other country, {message.from_user.first_name}?  If needed, you can type /usage for directions.",
        )
    else:
        sendMessage(message, "Please double check the name of the country!")
        sendMessage(
            message,
            f"What country's COVID-19 statistics do you want to know, {message.from_user.first_name}? If needed, you can type /usage for directions.",
        )


## Server
# Listening turned on for server
@server.route("/" + TOKEN, methods=["POST"])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]
    )
    return "!", 200


# Server basic route
@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=HEROKU_URL + TOKEN)
    return "!", 200


# Initate server
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))