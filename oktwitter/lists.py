import datetime

import twitter

from oktwitter import settings

from parliament.models import Parliament
from parliament.models import ParliamentMember


def update_current_parliament_members_list():
    api = twitter.Api(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )

    current_pms = Parliament.get_or_create_tweede_kamer().get_members_at_date(datetime.date.today())
    current_pm_usernames = []
    for member in current_pms:
        if member.person.twitter_username:
            current_pm_usernames.append(member.person.twitter_username)
            if len(current_pm_usernames) == 100:
                api.CreateListsMember(slug='tweedekamerleden', owner_screen_name='openkamer', screen_name=current_pm_usernames)
                current_pm_usernames = []
    api.CreateListsMember(slug='tweedekamerleden', owner_screen_name='openkamer', screen_name=current_pm_usernames)

    # lists = api.GetLists(screen_name='openkamer')
    members = api.GetListMembers(slug='tweedekamerleden', owner_screen_name='openkamer')
    return members
