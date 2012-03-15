import time
import re
import json

from datetime import datetime, timedelta
from decimal import Decimal

from basebank import BaseBank


class NBG(BaseBank):

    base_url = "https://www.nbg.gr/"
    data_re = re.compile("data = (?P<data>\[\[.*\]\])")

    def __init__(self, user=None, passw=None, acnt=None, name="NBG"):
        super(NBG, self).__init__(name)
        if user!=None: self.load(user, passw, acnt)

    def _load(self, user, passw=None, account=None, date_from=None, days_delta=60):
        user, passw, account = self.manage_up(user, passw, account)

        # read login response to identify the login form action url
        source, tree = self.openUrl("%swps/portal/LoginPageMap" % self.base_url)
        action = tree.xpath("//form[@id='formara']/@action")[0]

        # do login and get the contents to find the statements url in menu
        params = { 'userId': user, 'password': passw }
        source, index_tree = self.openUrl('%s%s' \
                % (self.base_url, action.lstrip('/')), params)

        # extract the amount of the account
        # TODO: it might be a good place to exit out if account given does not exist
        js_data_match = self.data_re.search(source)
        amounts = json.loads(js_data_match.groupdict()['data'])
        amount = None
        for m in amounts:
            if m[1] == account:
                amount = m[3]

        st_link = index_tree.xpath('//*[@id="ss1.3.inner2"]/div[4]/a/@href')[0]

        # open the statement page and find the action to post the data
        source, tree = self.openUrl('%s%s' % (self.base_url, st_link.lstrip("/")))
        st_action = tree.xpath('//form[@id="nbgIbForm"]/@action')[0];

        # date params
        now = datetime.now()
        if not date_from:
            date_from = now - timedelta(days=days_delta)
        # helper lambda to format dates
        date_fmt = lambda d: d.strftime("%d/%m/%Y")

        # sample post data (decoded)
        # inputData={'jspLocale':'en',"account": "<account>","from":
        # "22/06/2011","to": "10/07/2011"}
        data = {'account': account, 'from': date_fmt(date_from), 'to': date_fmt(now)}
        input_data = ("{'jspLocale':'en',\r\n\t\"account\": \"%(account)s\","
                '\r\n\t "from": "%(from)s", \r\n\t"to": "%(to)s"\r\n}') % data
        params = { 'inputData': input_data }

        # get the statement response, data will be in a <script> tag formated
        # in javascript array
        source, tree = self.openUrl('%s%s' %
                (self.base_url, st_action.lstrip("/")), params)

        js_data_match = self.data_re.search(source)
        data = json.loads(js_data_match.groupdict()['data'])

        norm_data = map(lambda row: (time.strptime(row[1],'%Y/%m/%d'),
                                    self.name + "/" + account, # FIXME: is this ok??
                                    -Decimal(str(row[4])) if row[5] == 'D' else \
                                            Decimal(str(row[4])),
                                    row[7]),
                        data)

        return Decimal(str(amount)), norm_data
