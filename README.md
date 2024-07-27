# Apartment Scraper
This is a small utility, which helps you find new apartments in your area.
It scrapes various websites for their entries, aggregates them and presents them on a small SvelteKit website.

Currently, the following websites are supported:
- [Haus und Grund](https://haus-und-grund-ostsee.de/luebeck/fuer-mieter/immobilien-mieten/#/list1)
- [Sven Oldörp](https://www.oldoerp-immobilien.de/mietangebotetest.html#filter=.page1)
- [Immowelt](https://www.immowelt.de)
- [Immonet](https://www.immonet.de)
- [MeineStadt](https://www.meinestadt.de/luebeck/immobilien/wohnungen)


## Run locally
1. Download the latest build artifact and unzip it
2. (Optional) Create a python venv using ``python -m venv venv`` and activate it using `.\venv\Scripts\activate.ps1`
3. Install the python requirements: ``pip install -r requirements.txt``
4. Install pnpm: ``npm install -g pnpm``
5. Install nodejs dependencies: ``pnpm install --prod``
6. Modify the ``scraper-config.yaml`` config file to your needs
7. Run the scraper: ``python scraper.py``
8. Run the webapp: ``node app``
9. Visit ``http://localhost:3000``


## Modify for your location


## Add new scraper
