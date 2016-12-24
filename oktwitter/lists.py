import logging
import datetime

import twitter

from oktwitter import settings
from parliament.models import Parliament
from government.models import Government

logger = logging.getLogger(__name__)


api = twitter.Api(
    consumer_key=settings.TWITTER_CONSUMER_KEY,
    consumer_secret=settings.TWITTER_CONSUMER_SECRET,
    access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
)


def update_current_parliament_members_list():
    logger.info('BEGIN')
    current_pms = Parliament.get_or_create_tweede_kamer().get_members_at_date(datetime.date.today())
    update_members_list(list_name='tweedekamerleden', members=current_pms)
    logger.info('END')


def update_current_government_members_list():
    logger.info('BEGIN')
    current_gov = Government.current()
    members = current_gov.members_latest
    update_members_list(list_name='kabinetsleden', members=members)
    logger.info('END')


def update_members_list(list_name, members):
    list_members = api.GetListMembers(
        slug=list_name,
        owner_screen_name='openkamer',
    )

    list_screen_names = []
    for list_member in list_members:
        list_screen_names.append(list_member.screen_name.lower())

    # add new members
    twitter_usernames_lower = []
    for member in members:
        if not member.person.twitter_username:
            logger.info(str(member.person.fullname()) + ' has no twitter username defined')
            continue
        twitter_usernames_lower.append(member.person.twitter_username.lower())
        if member.person.twitter_username.lower() in list_screen_names:
            logger.info(member.person.twitter_username + ' already in list')
            continue
        logger.info('adding ' + member.person.twitter_username + ' to ' + list_name + ' twitter list')
        try:
            api.CreateListsMember(
                slug=list_name,
                owner_screen_name='openkamer',
                screen_name=member.person.twitter_username
            )
        except twitter.error.TwitterError as e:
            logger.exception(e)

    # remove members
    for username in list_screen_names:
        if username.lower() not in twitter_usernames_lower:
            logger.info('removing ' + username + ' from ' + list_name + ' twitter list')
            api.DestroyListsMember(
                slug=list_name,
                owner_id='802459284646850560',
                screen_name=username
            )
