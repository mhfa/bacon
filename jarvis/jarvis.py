import os
from slackclient import SlackClient
import boto3
import arrow
import random
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
TIMEZONE = 'Australia/Melbourne'


class Jarvis:
    def __init__(self, token):
        self.token = token
        self.slack = SlackClient(token)

    def hello_sunny(self):
        self.send('hello,world', '@sunnyy')

    def recycling_reminder(self, except_users=['jarvis']):
        names = self.__pick(except_users=except_users)
        names_prefixed = ['@' + name for name in names]
        names_joined = ' '.join(names_prefixed)
        self.send(f'Hi {names_joined}! Please check recycling today. :) cc @here', 'dev')
        return names

    def __pick(self, channel='dev', count=2, except_users=['jarvis']):
        names = self.get_group_member_names(channel)
        names_reduced = [name for name in names if (name not in except_users)]
        if len(names_reduced) != count:
            names_picked = random.sample(names_reduced, count)
        else:
            names_picked = names_reduced
        return names_picked

    def timesheet(self):
        self.send('Hi @here! Just a reminder to submit your timesheet today. :)', 'dev')

    def whatsup(self):
        msgs = [
            "People @here what have you been up to?",
            "What's everyone up to this at the moment/how is everyone's workload? @here",
            "How's and what is everyone doing? Busy days? @here",
        ]
        self.send(random.choice(msgs), '#whatsupbot')

    def send(self, text, to='@sunnyy'):
        self.slack.api_call(
            'chat.postMessage',
            parse='full',
            text=text,
            as_user=True,
            channel=to)

    def get_channel_name_id_dict(self):
        channels = self.list_channels()
        return {c['name']: c['id'] for c in channels}

    def get_group_member_names(self, group='dev'):
        channel_id = self.get_group_id_by_name(group)
        response = self.slack.api_call(
            'groups.info',
            channel=channel_id)
        if response['ok']:
            return [self.get_member_name(user_id) for user_id in response['group']['members']]
        else:
            return False

    def get_member_name(self, id):
        response = self.slack.api_call(
            'users.info',
            user=id)
        if response['ok']:
            return response['user']['name']
        else:
            return False

    def get_group_id_by_name(self, name):
        name_id = self.get_group_name_id_dict()
        return name_id[name]

    def get_group_name_id_dict(self):
        groups = self.list_groups()
        return {g['name']: g['id'] for g in groups}

    def list_channels(self):
        result = self.slack.api_call('channels.list')
        return result['channels']

    def list_groups(self):
        result = self.slack.api_call('groups.list')
        return result['groups']

    def latest_message(self, channel='whatsupbot'):
        channel_id = self.get_channel_name_id_dict()[channel]
        response = self.slack.api_call(
            'channels.history',
            ts='latest',
            inclusive='true',
            count=1,
            channel=channel_id)
        return response['messages'][0]


class DataSerivce:
    def __init__(self, aws_id, aws_key):
        self.data = {}
        self.aws_id = aws_id
        self.aws_key = aws_key
        self.region = 'us-east-1'
        self.dynamodb = boto3.resource(
            service_name='dynamodb',
            region_name=self.region,
            aws_access_key_id=self.aws_id,
            aws_secret_access_key=self.aws_key)
        self.appdata = self.dynamodb.Table('appdata')
        self.__init_data()

    def __init_data(self):
        response = self.appdata.get_item(Key={
            'appname': 'jarvis',
        })
        self.data = response['Item']['data']

    def get_data(self, key, value=None):
        if key not in self.data:
            return value
        return self.data[key]

    def set_data(self, key, value):
        self.data[key] = value

    def commit(self):
        self.appdata.put_item(Item={
            'appname': 'jarvis',
            'data': self.data,
        })

    def debug(self):
        print(
            boto3.client(
                'dynamodb',
                region_name=self.region,
                aws_access_key_id=self.aws_id,
                aws_secret_access_key=self.aws_key).list_tables())


def main():
    now = arrow.now(TIMEZONE)
    weekday = now.isoweekday()
    is_workday = weekday in [1, 2, 3, 4, 5]

    # fire up Jarvis.
    j = Jarvis(os.environ.get('SLACK_TOKEN'))

    # pre-check with current time.
    if not is_work_hour(now):
        logger.info(f'{now.hour} is not working hour, skipping')
        return 'jarvis early exit.'

    # check with datetime from DataSerivce.
    appdata = DataSerivce(os.environ.get('AWS_ID'), os.environ.get('AWS_KEY'))
    last_run_timestamp = appdata.get_data('last_run_timestamp')
    if is_workday:
        "j.send(f'last time this ran was {last_run_timestamp}')"
    last = arrow.get(last_run_timestamp).to(TIMEZONE)

    # has this ran in the past 1 hour?
    if not (now.timestamp > last.shift(hours=+1).timestamp):
        if is_workday:
            j.send(f'{now.hour} is less an hour from the last run, skipping')
        return 'jarvis early exit.'

    # passed all checks, update datetime.
    appdata.set_data('last_run_timestamp', now.timestamp)

    # run the following only once per day.
    if not (now.day == last.day):
        # recyling runs only on certain weekdays.
        if weekday in [2, 4]:
            except_users = ['jarvis', 'mark']
            # add last recyclers to except_users' list so they don't get picked
            # again.
            last_recyclers = appdata.get_data('last_recyclers', [])
            if len(last_recyclers) > 0:
                except_users = except_users + last_recyclers
                j.recycling_reminder(except_users=except_users)
                j.send('recyling reminder sent.')
                # clear last_recyclers list now they are skipped them this time.
                appdata.set_data('last_recyclers', [])
            else:
                names = j.recycling_reminder(except_users=except_users)
                j.send('recyling reminder sent.')
                # add the picked recyclers so they are skipped next time.
                appdata.set_data('last_recyclers', names)
        # timesheet on every second monday.
        if weekday is 1:
            # week number is odd.
            week_number = now.isocalendar()[1]
            if (week_number % 2) is 1:
                j.timesheet()
        # walk reminder on weekdays between 2pm and 2:30pm.
        if (is_workday) and (now.hour == 14) and (now.minute <= 30):
            msg = 'Hey @here let\'s go for a walk!' \
                  ' Anyone not walking, please stand up!'
            j.send(msg, '#random')
        # post whatsupbot channel on certain weekdays but not all the time.
        if (is_workday) and (random.random() < 0.4):
            # has it been long enough since latest message in the channel.
            latest_message = j.latest_message(channel='whatsupbot')
            latest_arrow = arrow.get(latest_message['ts'])
            check_ts = latest_arrow.shift(days=+5).timestamp
            j.send(f'check_ts: {check_ts}, now.timestamp: {now.timestamp}')
            if now.timestamp >= check_ts:
                if random.random() <= 0.5:
                    j.whatsup()
                else:
                    msgs = [
                        '@here stand up NOW! (like literally) :parrot:',
                        'hey you @here, I have been looking at you, '
                        'you have been sitting all this time!!! RISE '
                        'NOW! (like literally standing up) :parrot:',
                        'Test complete and begin diagnostics... blood '
                        'toxicity, 24%. It appears that the continued use of '
                        'the chair is accelerating your condition. I have run '
                        'simulations on every known sitting position, and '
                        'none can serve as a viable replacement for standing '
                        'up.\nYour only option is to stand up. :stark:',
                    ]
                    j.send(random.choice(msgs), '#random')
                j.send('whatsup reminder sent.')
    else:
        if is_workday:
            "j.send('daily task already done for the day.')"

    appdata.commit()
    msg = 'jarvis function completed.'
    if is_workday:
        "j.send(msg)"
    return msg


def is_work_hour(time):
    return ((time.hour >= 10) and (time.hour < 16))


def default_handler(event, context):
    return main()


if __name__ == '__main__':
    main()
