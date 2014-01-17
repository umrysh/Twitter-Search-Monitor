#!/usr/bin/env python
#
import twitter
from smtplib import SMTP
import datetime
import sys


def format_status(result):
    userUrl = "http://twitter.com/%s" % result.user.screen_name
    return {
        'id': result.id,
        'user': '<a href="%s">@%s</a>' % (userUrl, result.user.screen_name),
        'message': result.text,
        'detailsUrl': '<a href="%s/status/%s">link to tweet</a>' % (
            userUrl, result.id)
    }


def messages_to_string(messages, sep="\n<br/><br/>\n"):
    template = "%(user)s: %(message)s [%(detailsUrl)s]"
    body = sep.join([template % msg for msg in messages])
    return body


class MailNotifier(object):
    """
        SL Twitter Monitor
        Set default values for search term, mail server/port/user/password, from
        and to addresses here. These defaults can be overloaded below when creating
        an instance of this class
    """
    def __init__(self, search="softlayer", server="smtp.gmail.com",
                 to="SET ME",
                 port=587, user=None, password=None, from_=None, logfilename=None):
        self.search_term = search
        self.server = server
        self.port = port
        self.user = user or ''
        self.passwd = password or ''
        self.from_ = from_ or "SLitter Monitor <twitter@softlayer.com>"
        self.to = to
        self._log_value = None
        self.logfile = logfilename or 'tweet.id'

        self.date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.subject = "%s twitter mentions %s " % ('%d', self.date)
        self.smtp_message = "\n".join([
            "From: %s",
            "To: %s",
            "Content-type: text/html",
            "Subject: %s",
            "Date: %s",
            "\n%s",
        ])

    @property
    def log_value(self):
        if self._log_value is None:
            try:
                with open(self.logfile, 'r') as f:
                    self._log_value = int(f.read())
            except IOError:
                with open(self.logfile, 'w+') as f:
                    f.write("0")
                self._log_value = 0
        return self._log_value

    @log_value.setter  # NOQA
    def log_value(self, value):
        self._log_value = value
        with open(self.logfile, 'w+') as f:
            f.write(str(value))

    def _format_message(self, subject, body, count):
        return self.smtp_message % (
            self.from_, self.to,
            subject % count,
            self.date,
            body.encode('utf8')
        )

    def send_mail(self, message, count):
        try:
            smtp = SMTP()
            smtp.connect(self.server, self.port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.user, self.passwd)
            smtp.sendmail(self.from_, self.to, self._format_message(self.subject,
                message, count))
            smtp.quit()

        except Exception, exc:
            sys.exit("mail failed; %s" % str(exc))

    def new_tweets(self, results):
        max_result = max(result.id for result in results)
        if self.log_value < max_result:
            self.log_value = max_result
            return True

    def status_by_search(self, search):
        statuses = api.GetSearch(term=search, count=100)
        results = filter(lambda x: x.id > self.log_value, statuses)
        returns = []
        if len(results) > 0:
            for result in results:
                returns.append(format_status(result))

            self.new_tweets(results)
            return returns, len(returns)
        else:
            exit()


if __name__ == "__main__":
    """
        Enter twitter API information here
    """
    api = twitter.Api(consumer_key='SET ME',
        consumer_secret='SET ME',
        access_token_key='SET ME',
        access_token_secret='SET ME')

    """
        Enter email authentication, search term, and to email address here. If not set here the default values
        above will be used. Mail server infromation defaults to gmail
    """
    notifier = MailNotifier(user='SET ME', password='SET ME', to='SET ME',
        search='SET ME')
    unformatted_body, count = notifier.status_by_search(notifier.search_term)
    body = messages_to_string(unformatted_body)

    notifier.send_mail(body, count)
