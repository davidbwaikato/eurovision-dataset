import pandas as pd
import os


def read_csv(fp):
    return pd.read_csv(fp)


def to_csv(contest, votes_ofilename="votes.csv", contestants_ofilename="contestants.csv"):
    
    # all_votes = [votes for c in contests for votes in c.votes_to_list()]
    all_votes = contest.votes_to_list()
    df = pd.DataFrame(all_votes, columns=[
                      'year', 'round', 'from_country_id', 'to_country_id', 'from_country', 'to_country', 'total_points', 'tele_points', 'jury_points'])

    if not os.path.exists(votes_ofilename):
        df.to_csv(votes_ofilename, index=False)
    else:
        df.to_csv(votes_ofilename, mode='a', header=False, index=False)

    all_contestants = contest.contestants_to_list()
    df = pd.DataFrame(all_contestants,
                      columns=['year', 'to_country_id', 'to_country', 'performer', 'song', 'country_year_disambiguation', 'place_contest', 'sf_num',
                               'running_final', 'running_sf',
                               'place_final', 'points_final', 'place_sf', 'points_sf',
                               'points_tele_final', 'points_jury_final', 'points_tele_sf', 'points_jury_sf',
                               'composers', 'lyricists',
                               'lyrics', 'youtube_url'])

    if not os.path.exists(contestants_ofilename):
        df.to_csv(contestants_ofilename, index=False)
    else:
        df.to_csv(contestants_ofilename, mode='a', header=False, index=False)

def cast_int(i):
    if i is not None and i.isdigit():
        return int(i)
    return None
