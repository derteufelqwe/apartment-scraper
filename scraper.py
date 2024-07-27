from argparse import ArgumentParser
import hashlib
import json
import re
import struct
import time
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from fake_useragent import UserAgent
import undetected_chromedriver as uc

import selenium
import yaml
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


USER_AGENT = UserAgent()


class SmallEntry:

    def __init__(self, provider: str, title: str, url: str, price: float, size: float, rooms: float,
                 address: Optional[str], image: Optional[str]):
        self.provider = provider
        self.title = title
        self.url = url
        self.price = price
        self.size = size
        self.rooms = rooms
        self.address = address
        self.image = image

    @property
    def uid(self):
        m = hashlib.md5()
        m.update(self.provider.encode())
        if self.price:
            m.update(struct.pack('f', self.price))
        if self.rooms:
            m.update(struct.pack('f', self.rooms))
        if self.size:
            m.update(struct.pack('f', self.size))
        if self.address:
            m.update(self.address.encode())
        return m.hexdigest()

    def to_json(self):
        return {
            'provider': self.provider,
            'id': self.uid,
            'title': self.title,
            'url': self.url,
            'price': self.price,
            'size': self.size,
            'rooms': self.rooms,
            'address': self.address,
            'image': self.image,
        }

    def __repr__(self):
        return f'SmallEntry({self.price}€, {self.size}m2, {self.rooms})'


class BaseSeleniumProvider(ABC):
    PROVIDER_NAME = ''
    MUST_FORMAT_PAGENUM = True

    def __init__(self, browser: WebDriver, options: dict):
        self.browser = browser
        self.options = options
        self.page_number = 1
        self.wait = WebDriverWait(browser, 5)

    @property
    @abstractmethod
    def url(self):
        pass

    @abstractmethod
    def page_is_empty(self) -> bool:
        pass

    @abstractmethod
    def await_page_loaded(self) -> bool:
        pass

    @abstractmethod
    def find_entries(self) -> List[SmallEntry]:
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    # --- Utility methods ---

    def find_if_available(self, element: WebElement, xpath: str) -> Optional[str]:
        try:
            return element.find_element(By.XPATH, xpath).text.strip()
        except NoSuchElementException:
            pass


class BaseAPIProvider(ABC):
    PROVIDER_NAME = ''

    def __init__(self, options):
        self.options = options

    @abstractmethod
    def find_entries(self) -> List[SmallEntry]:
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}()'


class HuGSeleniumProvider(BaseSeleniumProvider):
    PROVIDER_NAME = 'HausUndGrund'

    @property
    def url(self):
        return f"https://haus-und-grund-ostsee.de/luebeck/fuer-mieter/immobilien-mieten/#/list{self.page_number}"


    def page_is_empty(self) -> bool:
        return len(self.browser.find_elements(By.CSS_SELECTOR, 'div.hm_listbox')) == 0

    def await_page_loaded(self) -> bool:
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.hm_listbox')))
            return True
        except selenium.common.exceptions.TimeoutException:
            pass

        return False

    def find_entries(self) -> List[SmallEntry]:
        res = list()
        elements = self.browser.find_elements(By.CSS_SELECTOR, 'div.hm_listbox')

        for element in elements:
            url_id = element.find_element(By.XPATH, ".//a").get_attribute("href")
            url_id = url_id.split('ToExpose("')[1].split('")')[0]
            title = element.find_element(By.XPATH, ".//a").get_attribute("title")
            if rent := self.find_if_available(element, ".//strong[contains(text(), '€')]"):
                rent = rent.strip(' €\t').replace('.', '').replace(',', '.')
            if size := self.find_if_available(element, ".//strong[contains(text(), 'm²')]"):
                size = size.strip(' m²\t').replace('.', '').replace(',', '.')
            if rooms := self.find_if_available(element,
                                               "//span[contains(text(), 'Zimmer')]/preceding-sibling::strong[1]"):
                rooms = rooms.strip().replace(',', '.')
            if image := element.find_elements(By.XPATH, './/img'):
                image = image[0].get_attribute('src').rsplit('/', 1)[0] + '/800x600'
            if address := element.find_elements(By.XPATH, './/div[@class="hm_listaddress"]'):
                address = address[0].text.strip()

            res.append(SmallEntry(
                provider=self.PROVIDER_NAME,
                title=title,
                url=f'https://haus-und-grund-ostsee.de/luebeck/fuer-mieter/immobilien-mieten/#/expose{url_id}',
                price=float(rent) if rent else None,
                size=float(size) if size else None,
                rooms=float(rooms) if rooms else None,
                address=address,
                image=image,
            ))

        return res


class SOSeleniumProvider(BaseSeleniumProvider):
    PROVIDER_NAME = 'SvenOldoerp'

    @property
    def url(self):
        location = self.options['location']
        location_filter = ''
        if location:
            location_filter = f'#filter=.geo-ort-{location}'

        return f"https://www.oldoerp-immobilien.de/mietangebotetest.html{location_filter}"

    def page_is_empty(self) -> bool:
        return self.page_number > 1

    def await_page_loaded(self) -> bool:
        """ Results are only on one page """

        if self.page_number > 1:
            return True
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="estate_list"]/a')))
            return True
        except selenium.common.exceptions.TimeoutException:
            pass

        return False

    def find_entries(self) -> List[SmallEntry]:
        res = list()
        elements = self.browser.find_elements(By.XPATH, '//*[@id="estate_list"]/a')

        for element in elements:
            if len(element.find_elements(By.XPATH,
                                         'div/img[@src="files/cto_layout/img/headbalken_vermietet.jpg"]')) > 0:
                continue  # Inactive
            insert_type = self.find_if_available(element,
                                                 "div[@class='content objectDescr']//li[div[@class='label' and text()='Nutzungsart']]/div[@class='value']")
            if insert_type != 'Wohnen':
                continue

            title = self.find_if_available(element, "div[@class='content objectDescr']/h2")
            url = element.get_attribute('href')
            if rent := self.find_if_available(element,
                                              "div[@class='content objectDescr']//li[div[@class='label' and text()='Kaltmiete']]/div[@class='value']"):
                rent = re.findall(r'(\d+(?:\.\d+)?)', rent.replace('.', '').replace(',', '.'))[0]
            if size := self.find_if_available(element,
                                              "div[@class='content objectDescr']//li[div[@class='label' and text()='Wohnfläche']]/div[@class='value']"):
                size = re.findall(r'(\d+(?:\.\d+)?)', size.replace('.', '').replace(',', '.'))[0]
            address = self.find_if_available(element,
                                             "div[@class='content objectDescr']//li[div[@class='label' and text()='Lage']]/div[@class='value']")
            rooms = None
            if rooms_search := re.findall(r'(\d+)[- ](?:Zimmer|Zi)', title):
                rooms = rooms_search[0]
            if image := element.find_elements(By.XPATH, './/img[2]'):
                image = image[0].get_attribute('src')

            res.append(SmallEntry(
                provider=self.PROVIDER_NAME,
                title=title,
                url=url,
                price=float(rent) if rent else None,
                size=float(size) if size else None,
                rooms=float(rooms) if rooms else None,
                address=address,
                image=image,
            ))

        return res


class ImmoweltSeleniumProvider(BaseSeleniumProvider):
    PROVIDER_NAME = 'Immowelt'
    ELEMENTS_XPATH = "//div[@class[starts-with(., 'SearchList-')]]/div[@class[starts-with(., 'EstateItem-')]]"

    def __init__(self, browser: WebDriver, options: dict):
        super().__init__(browser, options)
        self._is_empty = False

    @property
    def url(self):
        location = self.options['location']
        search_radius = self.options['search_radius']
        price_min = self.options['price_min']
        price_max = self.options['price_max']
        size_min = self.options['size_min']
        size_max = self.options['size_max']
        rooms_min = self.options['rooms_min']
        rooms_max = self.options['rooms_max']

        parameters = [
            f'r={search_radius}' if search_radius is not None else None,
            f'pmi={price_min}' if price_min is not None else None,
            f'pma={price_max}' if price_max is not None else None,
            f'ami={size_min}' if size_min is not None else None,
            f'ama={size_max}' if size_max is not None else None,
            f'rmi={rooms_min}' if rooms_min is not None else None,
            f'rma={rooms_max}' if rooms_max is not None else None,
        ]

        query_str = '&'.join([p for p in parameters if p is not None]) + f'&sd=DESC&sf=RELEVANCE&sp={self.page_number}'

        return f'https://www.immowelt.de/suche/{location}/wohnungen/mieten?{query_str}'

    def page_is_empty(self) -> bool:
        if not self._is_empty:
            self._is_empty = len(self.browser.find_elements(By.XPATH,self.ELEMENTS_XPATH)) > 0
            return False

        return True

    def await_page_loaded(self) -> bool:
        """ Results are only on one page """
        if self._is_empty:
            return True

        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, self.ELEMENTS_XPATH)))

            if shadow_parent := self.browser.find_elements(By.XPATH, '//div[@id="usercentrics-root"]'):
                shadow_parent = shadow_parent[0]
                outer = self.browser.execute_script('return arguments[0].shadowRoot', shadow_parent)
                if buttons := outer.find_elements(By.CSS_SELECTOR, "button[data-testid='uc-accept-all-button']"):
                    buttons[0].click()
                    time.sleep(1)

            return True
        except selenium.common.exceptions.TimeoutException:
            pass

        return False

    def find_entries(self) -> List[SmallEntry]:
        res = list()
        elements = self.browser.find_elements(By.XPATH,self.ELEMENTS_XPATH)

        for element in elements:
            # Scroll the element into the view, so its images get loaded
            self.browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",element)
            time.sleep(0.25)

            title = self.find_if_available(element, ".//div[@class[starts-with(., 'FactsMain-')]]/*/h2")
            if price := self.find_if_available(element, ".//div[@class[starts-with(., 'FactsMain-')]]/div[@class[starts-with(., 'KeyFacts-')]]/div[@data-test='price']"):
                price = price.strip(' \t€').replace('.', '').replace(',', '.')
            if rooms := self.find_if_available(element, ".//div[@class[starts-with(., 'FactsMain-')]]/div[@class[starts-with(., 'KeyFacts-')]]/div[@data-test='rooms']"):
                rooms = re.findall(r'(\d+(?:\.\d+)?)', rooms)[0]
            if size := self.find_if_available(element, ".//div[@class[starts-with(., 'FactsMain-')]]/div[@class[starts-with(., 'KeyFacts-')]]/div[@data-test='area']"):
                size = size.strip(' \tm²').replace(',', '.').strip()
            address = self.find_if_available(element, ".//div[@class[starts-with(., 'FactsMain-')]]//span")
            if image := element.find_elements(By.XPATH, ".//div[@class[starts-with(., 'VisualSection-')]]//picture/img"):
                image = image[0].get_attribute('src')
            url = element.find_element(By.XPATH, './/a').get_attribute('href')

            res.append(SmallEntry(
                provider=self.PROVIDER_NAME,
                title=title,
                url=url,
                price=float(price) if price else None,
                size=float(size) if size else None,
                rooms=float(rooms) if rooms else None,
                address=address,
                image=image,
            ))

        return res


class ImmonetSeleniumProvider(BaseSeleniumProvider):
    PROVIDER_NAME = 'Immonet'

    def __init__(self, browser: WebDriver, options: dict):
        super().__init__(browser, options)
        self._is_empty = False

    @property
    def url(self):
        location = self.options['location']
        price_min = self.options['price_min']
        price_max = self.options['price_max']
        size_min = self.options['size_min']
        size_max = self.options['size_max']
        rooms_min = self.options['rooms_min']
        rooms_max = self.options['rooms_max']

        parameters = [
            f'locations={location}' if location is not None else None,
            f'priceMin={price_min}' if price_min is not None else None,
            f'priceMax={price_max}' if price_max is not None else None,
            f'spaceMin={size_min}' if size_min is not None else None,
            f'spaceMax={size_max}' if size_max is not None else None,
            f'numberOfRoomsMin={rooms_min}' if rooms_min is not None else None,
            f'numberOfRoomsMax={rooms_max}' if rooms_max is not None else None,
        ]

        query_str = '&'.join([p for p in parameters if p is not None]) + f'&page={self.page_number}'

        return f'https://www.immonet.de/classified-search?{query_str}'

    def page_is_empty(self) -> bool:
        if not self._is_empty:
            self._is_empty = len(self.browser.find_elements(By.XPATH,
                                                            '//div[@data-testid="serp-enlargementlist-testid"]/div/div[contains(text(), "Weitere Ergebnisse in der Nähe")]')) > 0
            return False

        return True

    def await_page_loaded(self) -> bool:
        """ Results are only on one page """
        if self._is_empty:
            return True

        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//div/div[@data-testid="serp-card-testid"]')))

            if shadow_parent := self.browser.find_elements(By.XPATH, '//div[@id="usercentrics-root"]'):
                shadow_parent = shadow_parent[0]
                outer = self.browser.execute_script('return arguments[0].shadowRoot', shadow_parent)
                if buttons := outer.find_elements(By.CSS_SELECTOR, "button[data-testid='uc-accept-all-button']"):
                    buttons[0].click()
                    time.sleep(1)

            return True
        except selenium.common.exceptions.TimeoutException:
            pass

        return False

    def find_entries(self) -> List[SmallEntry]:
        res = list()
        elements = self.browser.find_elements(By.XPATH,
                                              '//div[@data-testid="serp-scrollablelist-testid"]/div/div[@data-testid="serp-card-testid"]/div')

        for element in elements:
            if rent := self.find_if_available(element, ".//div[@data-testid='cardmfe-price-testid']"):
                rent = rent.strip(' \t€').replace('.', '').replace(',', '.')
            if rooms := self.find_if_available(element, ".//div[@data-testid='cardmfe-keyfacts-testid']/div[1]"):
                rooms = re.findall(r'(\d+(?:\.\d+)?)', rooms)[0]
            if size := self.find_if_available(element, ".//div[@data-testid='cardmfe-keyfacts-testid']/div[3]"):
                size = size.strip(' \tm²').replace('.', '').replace(',', '.').strip()
            address = self.find_if_available(element, ".//div[@class='css-162g046']")
            if image := element.find_elements(By.XPATH, ".//div[@aria-roledescription='slide'][1]/img"):
                image = image[0].get_attribute('src')
            url = element.find_element(By.XPATH, './/a').get_attribute('href')

            res.append(SmallEntry(
                provider=self.PROVIDER_NAME,
                title="Wohnung zur Miete",
                url=url,
                price=float(rent) if rent else None,
                size=float(size) if size else None,
                rooms=float(rooms) if rooms else None,
                address=address,
                image=image,
            ))

        return res


class MeineStadtAPIProvider(BaseAPIProvider):
    PROVIDER_NAME = 'MeineStadt'

    def __init__(self, options):
        super().__init__(options)
        self._headers1 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'trailers',
        }
        self._headers2 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.meinestadt.de/luebeck/immobilien/wohnungen',
            'Content-Type': 'application/json',
            'Content-Length': '200',
            'Origin': 'https://www.meinestadt.de',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'trailers',
        }

    def find_entries(self) -> List[SmallEntry]:
        with requests.Session() as session:
            r1 = session.get('https://www.meinestadt.de/luebeck/immobilien/wohnungen', headers=self._headers1,
                             allow_redirects=True)

            if r1.status_code != 200:
                raise RuntimeError(f'Got API response code {r1.status_code} for r1')

            r2 = session.post('https://www.meinestadt.de/_re-service/get-items', headers=self._headers2,
                              allow_redirects=True,
                              json={
                                  "location": "empty",
                                  "lat": self.options['latitude'],
                                  "lng": self.options['longitude'],
                                  "page": 1,
                                  "pageSize": 200,
                                  "sr": self.options['search_radius'],
                                  "sort": "distance",
                                  "etype": 1,
                                  "esr": self.options['min_rooms'],
                                  "eqid": [],
                                  "furnid": 0,
                                  "epos": [],
                                  "ecat": [],
                                  "primi": 0,
                                  "prima": self.options['max_price'],
                                  "flmi": self.options['min_size'],
                                  "flma": 0
                              }
                              )

            if r2.status_code != 200:
                raise RuntimeError(f'Got API response code {r2.status_code} for r2')

            data = json.loads(r2.text)

        res = list()

        for item in data['items']:
            if image := item.get('smallImageUrl'):
                if image.startswith('https://image-resize.meinestadt.de/image-resize/v2'):
                    image = re.sub(r'([&?])w=\d+', r'\1w=800', image)
                    image = re.sub(r'([&?])h=\d+', r'\1h=800', image)

            res.append(SmallEntry(
                provider=self.PROVIDER_NAME,
                title=item['title'],
                url=item['detailUrl'],
                price=float(item['priceRaw']),
                size=float(item['livingAreaRaw']),
                rooms=float(item['rooms']),
                address=(item.get('street', '') or '') + ' ' + (item.get('postcode', '') or '') + " " + (
                        item.get('city', '') or ''),
                image=image,
            ))

        return res


def process_provider(browser: WebDriver, provider: BaseSeleniumProvider) -> List[SmallEntry]:
    results = list()

    while True:
        browser.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": USER_AGENT.random})
        print(f'Opening page {provider.page_number} for {provider.PROVIDER_NAME}')
        browser.get(provider.url)
        time.sleep(1)  # Wait for browser to change

        if not provider.await_page_loaded():
            print('Page didnt load')
            break
        if provider.page_is_empty():
            break

        time.sleep(0.5)  # Prevent stale-element-reference-exception
        results.extend(provider.find_entries())
        provider.page_number += 1

    return results


def run_scrapers(browser: WebDriver, output_file: str, selenium_providers: list, api_providers: list):
    results = list()

    # Run scrapers
    for provider_class, skip, options_list in selenium_providers:
        if skip:
            print(f'Skipping provider {provider_class.__name__}...')
            continue

        for i, options in enumerate(options_list):
            print(f'Running provider {provider_class.__name__} with settings {i + 1}/{len(options_list)}...')

            results.extend(process_provider(browser, provider_class(browser, options)))

    # Run API fetchers
    for provider_class, skip, options_list in api_providers:
        if skip:
            print(f'Skipping API provider {provider_class.__name__}...')
            continue

        for i, options in enumerate(options_list):
            print(f'Running provider {provider_class.__name__} with settings {i + 1}/{len(options_list)}...')
            results.extend(provider_class(options).find_entries())

    with open(output_file, 'w', encoding='UTF-8') as file:
        json.dump([r.to_json() for r in results], file, indent=2, ensure_ascii=False)


def main(args):
    service = Service()
    options = webdriver.ChromeOptions()
    # Selenium detection prevention: https://stackoverflow.com/questions/53039551/selenium-webdriver-modifying-navigator-webdriver-flag-to-prevent-selenium-detec/53040904#53040904
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # browser = uc.Chrome(options=options, headless=not args.no_headless, use_subprocess=False)
    browser = webdriver.Chrome(service=service, options=options)
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    with open(args.config, 'r', encoding='UTF-8') as file:
        config = yaml.safe_load(file)

    selenium_providers = [
        (HuGSeleniumProvider, args.no_hug, config['scrapers']['haus_und_grund']),
        (SOSeleniumProvider, args.no_sod, config['scrapers']['sven_oldoerp']),
        (ImmoweltSeleniumProvider, args.no_iw, config['scrapers']['immowelt']),
        (ImmonetSeleniumProvider, args.no_in, config['scrapers']['immonet']),
    ]
    api_providers = [
        (MeineStadtAPIProvider, args.no_ms, config['apis']['meine_stadt']),
    ]

    try:
        run_scrapers(browser, args.output, selenium_providers, api_providers)
    finally:
        browser.quit()


if __name__ == '__main__':
    parser = ArgumentParser('Configure the website scraper')
    parser.add_argument('--output', '-o', type=str, default='app/client/results.json', help='The output json file')
    parser.add_argument('--config', '-c', type=str, default='scraper-config.yaml', help='The scraper config file')
    parser.add_argument('--no-headless', action='store_true', default=False, help='Disable headless mode')

    parser.add_argument('--no-hug', action='store_true', default=False, help='Disable "Haus und Grund" parser')
    parser.add_argument('--no-sod', action='store_true', default=False, help='Disable "Sven Oldörp" parser')
    parser.add_argument('--no-iw', action='store_true', default=False, help='Disable "Immowelt" parser')
    parser.add_argument('--no-in', action='store_true', default=False, help='Disable "Immonet" parser')
    parser.add_argument('--no-ms', action='store_true', default=False, help='Disable "meinestadt" parser')

    args = parser.parse_args()

    main(args)

    print('Done.')
