import argparse

from contest import Contest
from scraper import Scraper
from utils import to_csv


def get_contest(y, rounds):
    contest = Contest(y)
    for r in rounds:
        print('Scraping: Eurovision Song Contest {} {}'.format(y, r))
        contest = scraper.scrape_year(contest, r)
    
    contest = scraper.scrape_misc(contest)
    return contest

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Eurovision Data Scraper')
    parser.add_argument('--start', type=int, default=1956,
                        help='Start year range of the Eurovision Song Contest')
    parser.add_argument('--end', type=int, default=2021,
                        help='End year range of the Eurovision Song Contest')

    args = parser.parse_args()

    ofilename_suffix = None
    if (args.start == args.end):
        ofilename_suffix = f"-{args.start}"
    else:
        ofilename_suffix = f"-{args.start}-to-{args.end}"

    votes_ofilename = f"votes{ofilename_suffix}.csv"
    contestants_ofilename = f"contestants{ofilename_suffix}.csv"
    
    scraper = Scraper()
    
    for y in range(args.start, args.end+1):
        if y < 2004:
            rounds = ['final']
        elif y >= 2004 and y < 2008:
            rounds = ['final', 'semi-final']
        else:
            rounds = ['final', 'semi-final-1', 'semi-final-2']

        # Avoid 2020 as there was no contest run that year due to Covid-19
        # While countries progressed as far as selecting their entry,
        # as there was no contest, there is no voting/placement data
        # on that year's web page at eurovisionworld.com
        # As currently written, scraper.py terminates with an error
        if y != 2020:            
            contest = get_contest(y, rounds)
            to_csv(contest, votes_ofilename, contestants_ofilename)
        else:
            print("Skipping year 2020 as contest was cancelled. No votes to tabulate")
            
    
    scraper.driver.quit()
