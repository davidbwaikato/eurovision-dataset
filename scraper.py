from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common import keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import re
import time
from collections import defaultdict

from country import Country
from contestant import Contestant
from votes import Votes


class Scraper():

    def __init__(self):
        print("Searching for WebDriver module")
        
        try:
            options = webdriver.ChromeOptions()
            # The following is the original github project code, but as docker image installs
            #   latest version of chrome-driver, it was found to be insufficient and caused
            #   scraper.py to hang for a long time, and then eventually timeout, having never
            #   downloaded anything
            
            #options.add_argument("headless")
            #options.add_argument("no-sandbox")
            #options.add_argument("disable-dev-shm-usage")

            # Based on:
            #   https://stackoverflow.com/questions/48450594/selenium-timed-out-receiving-message-from-renderer
            #
            # ChromeDriver is just AWFUL because every version or two it breaks unless you pass cryptic arguments
            # AGRESSIVE: options.setPageLoadStrategy(PageLoadStrategy.NONE); // https://www.skptricks.com/2018/08/timed-out-receiving-message-from-renderer-selenium.html
            options.add_argument("start-maximized");                   # https://stackoverflow.com/a/26283818/1689770
            options.add_argument("enable-automation");                 # https://stackoverflow.com/a/43840128/1689770
            options.add_argument("--headless");                        # only if you are ACTUALLY running headless
            options.add_argument("--no-sandbox");                      # https://stackoverflow.com/a/50725918/1689770
            options.add_argument("--disable-infobars");                # https://stackoverflow.com/a/43840128/1689770
            options.add_argument("--disable-dev-shm-usage");           # https://stackoverflow.com/a/50725918/1689770
            options.add_argument("--disable-browser-side-navigation"); # https://stackoverflow.com/a/49123152/1689770
            options.add_argument("--disable-gpu");                     # https://stackoverflow.com/questions/51959986/how-to-solve-selenium-chromedriver-timed-out-
            
            self.driver = webdriver.Chrome(chrome_options=options)
            print('  Found Chrome WebDriver')
            return
        except Exception as e:
            print('  Did not detect Chrome WebDriver')
            print(e)
            pass

        
        try:
            options = webdriver.firefox.options.Options()
            options.add_argument('--headless')
            self.driver = webdriver.Firefox(options=options)
            print('  Found Firefox WebDriver')
            return
        except Exception as e:
            print('  Did not detect Firefox WebDriver')
            print(e)
            pass

        try:
            self.driver = webdriver.Safari()
            print('  Found Safari WebDriver')
            return
        except:
            print('  Did not detect Safari WebDriver')
            pass

        print("Failed to find any WebDriver Python modules.  Exiting ...")
        exit(1)
        
              
    def get_sf_num(self, sf):
        if sf == 'semi-final':
            return str(0)
        if sf == 'semi-final-1':
            return str(1)
        if sf == 'semi-final-2':
            return str(2)

    def get_from_to_country_in_dict(self, from_country, to_country, d):
        if not d:
            return None

        for k, v in d.items():
            for _k, points in v.items():
                if k == from_country and _k == to_country:
                    return points 
        return None 


    def scrape_votes(self, contest, table_data_attrib=None):
        votes_dict = defaultdict(lambda: defaultdict(int))

        time.sleep(3)

        # Create the voting table for the contest
        voting_grid = self.soup.find('table', {'class': 'scoreboard_table'})
        with open("output1.html", "w") as file:
            file.write(str(self.soup))

        if voting_grid is None:
            return votes_dict

        if not voting_grid.contents:
            return votes_dict

        # Switch to other table for tele/jury voting
        if table_data_attrib:
            btn = self.driver.find_element_by_xpath('//button[@data-button="{}"]'.format(table_data_attrib))
            btn.send_keys(keys.Keys.SPACE)

            soup = BeautifulSoup(self.driver.page_source, features='html.parser')

            # It looks like the eurovisionworld.com website has made some HTML syntax changes
            #   to their site (based on a comparison of the current pages and those from 2 years ago
            #   accessed via the WayBack Machine on archive.org
            #
            # There is nolonger a 'voting_grid' id in the HTML for find() to latch on to
            
            # voting_grid = soup.find('div', {'id': 'voting_grid'})
            voting_grid = self.soup.find('table', {'class': 'scoreboard_table'})

        if len(voting_grid.text) > 0:

            # Create country id/value pairs, since voting countries can be different than participating
            # countries (e.g. San Marino in 2007)
            countries = {}
            for row in voting_grid.find('thead').findAll('tr'):
                cols = row.find_all('td')
                for c in cols:
                    img = c.find('img')
                    if img:
                        countries[c['tdid']] = img['alt']
                    
                    if 'data-from' in c.attrs:
                        countries[c['data-from']] = c['data-from']

            for row in voting_grid.find('tbody').findAll('tr'):
                cols = row.find_all('td')
                country_name = cols[2].text
                country_id = cols[2]['data-to']
                # total_points = cols[3].text

                points_cols = cols[4:]
                for p in points_cols:
                    from_country_id = p['data-from']
                    to_country_id = p['data-to']
                    if not p.text:
                        votes_dict[from_country_id][to_country_id] = 0
                    else:
                        votes_dict[from_country_id][to_country_id] = int(p.text)

                    from_country_name = countries[from_country_id]
                    to_country_name = countries[to_country_id]
                    contest.countries[from_country_id] = Country(from_country_name, from_country_id)
                    contest.countries[to_country_id] = Country(to_country_name, to_country_id)

        return votes_dict

    def get_contestants(self, contest, contest_round, rows, qualified=True):
        for row in rows:
            cols = row.find_all('td')

            # Tele/jury votes were implemented in 2016
            televotes = None
            juryvotes = None

            if len(cols) == 5:
                place_flag, country, song_artist, points, running = cols
            if len(cols) == 7:
                place_flag, country, song_artist, points, televotes, juryvotes, running = cols

            place = place_flag.find("b").text.rstrip()
            country_name = country.text.rstrip('.')
            country_id = None
            song = song_artist.find('a').text
            artist = song_artist.find('span').text.rstrip()
            song = song.replace(artist, '').rstrip()
            points = points.text.rstrip()
            running = running.text.rstrip()

            if not place.isdigit():
                place = None

            if not points.isdigit():
                points = None
            
            if not running.isdigit():
                running = None

            if country_name == "United KingdomUK":
                country_name = "United Kingdom"

            if country_name == "North MacedoniaNorth MacedoniaN.Macedonia":
                country_name = "North Macedonia"
                           
            page_url = song_artist.find('a')['href']

            if televotes and juryvotes:
                televotes = televotes['data-sort'].rstrip()
                juryvotes = juryvotes.text.rstrip()

            # Add country to country dictionary
            country = Country(country_name, country_id)
            contest.countries[country_id] = country

            # Add contestant to contestant dictionary
            contestant_key = '{}_{}_{}'.format(contest.year, country.name, artist)

            if contestant_key in contest.contestants.keys():
                c = contest.contestants[contestant_key]
            else:
                c = Contestant(contest.year, country, artist, song, page_url)
                contest.contestants[contestant_key] = c

            if qualified:
                if contest_round == 'final':
                    c.running_final = running
                    c.place_contest = place # place in contest = place in final
                    c.place_final = place
                    c.points_final = points
                    c.points_tele_final = televotes
                    c.points_jury_final = juryvotes 
                else:
                    c.sf_num = self.get_sf_num(contest_round)
                    c.running_sf = running
                    c.place_sf = place
                    c.points_sf = points
                    c.points_tele_sf = televotes
                    c.points_jury_sf = juryvotes
            else:
                c.place_contest = place

            print("  ", contest.year, c.country.name, contest_round if qualified else f"{contest_round} Non qualified")
        return contest

    def scrape_year(self, contest, contest_round):


        if contest_round == 'final':
            url = 'https://eurovisionworld.com/eurovision/{}'.format(contest.year)
        else:
            url = 'https://eurovisionworld.com/eurovision/{}/{}'.format(contest.year, contest_round)

        print("  Scraping year: " + url)
        
        self.driver.get(url)

        # While driver.get() waits on a web pages resources to load in, it does not (is not able to) wait on
        # subsequent JS operatations, as as AJAX calls -- as happen in the loaded pages, where the voting data
        # is dynamically loaded in
        
        # Loosely based on:
        #  https://stackoverflow.com/questions/26566799/wait-until-page-is-loaded-with-selenium-webdriver-for-python
        delay = 10
        # WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.ID, 'voting_table')))
        WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.XPATH, "//div[@id='voting_table']/table")))        
        
        self.soup = BeautifulSoup(self.driver.page_source, features='html.parser')

            
        voting_table = self.soup.find('div', {'id': 'voting_table'})
        if not voting_table:
            return None
               
        # Qualified countries 
        rows = voting_table.findAll('table')[0].find('tbody').findAll('tr')
        contest = self.get_contestants(contest, contest_round, rows)
        
        # Non-qualified countries, only for final ranking (place in contest)
        if len(voting_table.findAll("table")) > 1:
            rows = voting_table.findAll('table')[1].find('tbody').findAll('tr')
            contest = self.get_contestants(contest, contest_round, rows, qualified=False)


        # Tele/jury votes were implemented in 2016
        tele_votes = None
        jury_votes = None
        total_votes = self.scrape_votes(contest)
        if contest.year >= 2016:
            tele_votes = self.scrape_votes(contest, 'tele') 
            jury_votes = self.scrape_votes(contest, 'jury') 
        
        # Merge dictionaries:
        for k, v in total_votes.items():
            for _k, _v in v.items():
                tele_points = self.get_from_to_country_in_dict(k, _k, tele_votes)
                jury_points = self.get_from_to_country_in_dict(k, _k, jury_votes)
                total_votes[k][_k] = (_v, tele_points, jury_points)


        votes = Votes(contest.year, contest_round, total_votes)
        contest.votes[contest_round] = votes
        return contest

    def scrape_misc(self, contest):
        for _, contestant in contest.contestants.items():

            # Get contestant's page url
            url = 'https://eurovisionworld.com' + contestant.page_url

            print("  Scraping misc: " + url)

            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, features='html.parser')

            # Get lyrics
            lyrics = soup.find('div', class_='lyrics_div').findAll('p')
            lyrics = '\\n\\n'.join([p.get_text(separator='\\n') for p in lyrics])
            contestant.lyrics = lyrics


            # Get video URL 
            video_src = soup.find('div', class_='lyrics_video_wrap').find('iframe')['src']
            video_id = video_src.split('/')[-1].split('?')[0]
            youtube_url = 'https://youtube.com/watch?v=' + video_id
            contestant.youtube_url = youtube_url


            # Get composers (rewrite this...)
            tmp = []
            composers = soup.find('h4', class_='label', text=re.compile("COMPOSERS?"))
            if composers is None:
                composers = soup.find('h4', class_='label', text=re.compile("SONGWRITERS?"))
            if composers:
                composers = composers.parent.find('ul').find_all('li', recursive=False)
                tmp = []
                for c in composers:
                    tmp.append(c.find('b').text)
            contestant.composers = tmp
            
            lyricists = soup.find('h4', class_='label', text=re.compile("LYRICISTS?"))
            tmp = []
            if lyricists:
                lyricists = lyricists.parent.find('ul').find_all('li', recursive=False)
                tmp = []
                for c in lyricists:
                    tmp.append(c.find('b').text)
            contestant.lyricists = tmp

        return contest
