# COVID-19 Statistics Telegram BOT

A Telegram BOT that listens to users messages and provides country wise update based on user input. The BOT will also push out update of Bangladesh COVID stats when the data updates for the day.

## Link to BOT

```http
  https://t.me/COVID19_Statsbot
```

## Visuals

#### Splash Screen

![Splash Screen](https://i.ibb.co/rQynQMm/Splash-Screen.png)

#### Main Screen

![Main Screen](https://i.ibb.co/g3W0ZP5/Main-Screen.png)

#### Commands Screen

![Commands Screen](https://i.ibb.co/M8TycvK/Commands.png)

#### Country Keyboard Selection

![Country Keyboard Selection](https://i.ibb.co/10RW2z4/Country-Update.png)

#### Bangladesh Notification

![Bangladesh Notification](https://i.ibb.co/nffkmd3/Notification.png)

## Tech Stack

**BOT:** Python, Flask

**Database:** PostgreSQL

**Hosting:** Heroku

## Features

- BOT regularly updates COVID statistics from [Worldometers](https://www.worldometers.info/coronavirus/) and [Disease SH](https://disease.sh/v3/covid-19/countries/bangladesh).
- Important COVID Statistics available for all countries of the world.
- BOT will send out notification when updated Bangladesh COVID statistics is available.
- BOT uses PostgreSQL solution from Heroku to keep track of which users to send out the notification to.
- Few additional data points are provided for Bangladesh such as `Positivity Rate` and `Test Count`.

## Installation

- For development, make sure to set up either a local .env file with the appropriate information or add the environment variables in the hosting of your choice.
- A BOT needs to be set up through BotFather in Telegram to get your unique BOT token.

## Environment Variables

To run this project, you will need to add the following environment variables or add it directly to your python script _(not recommended!)_.

`TOKEN` - Your Telegram BOT token

`HEROKU_URL` - Your Heroku URL here if using Heroku

## Notes

This BOT depends on scraping data from a website and therefore it is suggested to use it at your own risk. Always check if the website that is going to be scraped on has any guidelines on scraping and ensure very frequent attemps are not made to scrape.

## License

[ISC](https://choosealicense.com/licenses/isc/)

## Authors

- [@Ishmam156](https://github.com/Ishmam156)

## Contributing

Contributions are always welcome!

Kindly generate a `pull request` with your contribution.

## Feedback

If you have any feedback, please reach out to me at ishmam156@gmail.com
