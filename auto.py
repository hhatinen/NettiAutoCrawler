from sets import Set
from HTMLParser import HTMLParser
import os.path
import urllib2
import re
import csv
import time
import datetime

#url = 'https://www.nettiauto.com/listAdvSearchFindAgent.php?id=152135976&tb=tmp_find_agent&PN[0]=adv_search&PL[0]=advSearch.php?qs=Y?id=152135976@tb=tmp_find_agent&id_model=954'
#print feeddata

class NettiAutoParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.previous_class = ''
        self.active_class = ''
        self.in_data_box = False
        self.data_box_lvl = 0
        self.car_data = {}
        self.curr_page = -1
        self.total_pages = -1
        self.link_read = False
        self.result = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'div' or tag == 'span':
            if not self.in_data_box:
                if any(x[0] == 'class' and x[1].startswith('listing') for x in attrs):
                    #print "Started"
                    self.data_box_lvl = 1
                    self.in_data_box = True;
                    self.car_data = {}
                    self.car_data["Dealership"] = False
                    self.link_read = False
            else:
                self.data_box_lvl += 1
        if any(x[0] == 'class' for x in attrs):
            self.previous_class = self.active_class
            self.active_class = next(x[1] for x in attrs if x[0] == 'class')
        if self.in_data_box:
            if tag == 'a' and any(x[0] == 'href' for x in attrs) and not self.link_read:
                url = next(x[1] for x in attrs if x[0] == 'href')
                self.car_data["url"] = url
                self.link_read = True
                id = ""
                n = -1
                while url[n].isdigit():
                    id = url[n] + id
                    n = n-1
                self.car_data["id"] = id
                self.car_data["last_seen"] = datetime.datetime.now().strftime('%d.%m.%Y')


    def handle_endtag(self, tag):
        if tag == 'div' or tag == 'span':
            if self.in_data_box == True:
                self.data_box_lvl -= 1
                if self.data_box_lvl == 0:
                    #print str(self.car_data)
                    if not self.car_data["id"] in self.result:
                        self.car_data["first_seen"] = datetime.datetime.now().strftime('%d.%m.%Y')
                    else:
                        self.car_data["first_seen"] = self.result[self.car_data["id"]]["first_seen"]

                    self.result[self.car_data["id"]] = self.car_data
                    self.in_data_box = False

    def handle_data(self, data):
        if self.active_class == 'totPage' and data.strip() != '' and data.isdigit():
            print data
            self.total_pages = int(data)
        elif self.active_class == 'pageOfPage' and data.isdigit() and data != '/':
            self.curr_page = int(data)
        if self.in_data_box:
            if self.active_class == "gray_text" and self.previous_class == "list_seller_info":
                text = data[:data.find("&")].strip()
                if text != "":
                    self.car_data["Location"] = text
            elif self.active_class == 'make_model_link':
                self.car_data["Make"] = data[:data.find(' ')].strip()
                self.car_data["Model"] = data[data.find(' '):].strip()
            elif self.active_class == 'eng_size' and data.strip() != '':
                self.car_data["Engine"] = data.strip()[1:-1].replace(".", ",")
            elif self.active_class == 'main_price' and data.strip() != '':
                self.car_data["Price"] = int(data.replace(' ', ''))
            elif self.active_class == "checkLnesFlat" and data.strip() != '':
                info = data.strip()
                index = 1000
                self.car_data["ModalInfo"] = info
            elif self.active_class.startswith('vehicle_other_info'):
                if 'km' in data:
                    self.car_data["Mileage"] = data.replace("km", "").replace(" ", "")
                elif data == "Diesel" or data == "Bensiini" or data == "Hybridi":
                    self.car_data["Power"] = data
                elif data == "Automaatti" or data == "Manuaali":
                    self.car_data["Gears"] = data
                elif data.strip().isdigit():
                    self.car_data["Year"] = int(data.strip())
            if "LIIKE" in data:
                self.car_data["Dealership"] = True
            #print "Data for " + self.active_class + " = \'" + data + "\'"


def append_url(url, dict):
    print "Fetching url " + url

    request = request = urllib2.Request(url);
    opener = urllib2.build_opener()
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36/')
    feeddata = opener.open(request).read()

    parser = NettiAutoParser()
    parser.result = dict
    parser.feed(feeddata)

    print "Page " + str(parser.curr_page) + " of " + str(parser.total_pages)

    return parser.result, parser.curr_page >= parser.total_pages

prev={}

if os.path.isfile('cars.csv'):
    with open('cars.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            prev[row["id"]] = row

url = 'https://www.nettiauto.com/listAdvSearchFindAgent.php?id=152135976&tb=tmp_find_agent&PN[0]=adv_search&PL[0]=advSearch.php?id=152135976@posted_by=@tb=tmp_find_agent'

last_page = False
page = 1
while not last_page:
    url0 = url + "&page=" + str(page)
    result, last_page = append_url(url0, prev)
    page = page+1
    time.sleep(2)

with open('cars.csv', 'w') as csvfile:
    fieldnames_set = Set()
    for row in result.values():
        for rowkey in row.keys():
            fieldnames_set.add(rowkey)
    fieldnames = fieldnames_set
    writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))

    writer.writeheader()
    for x in result.values():
        writer.writerow(x)


#response = urllib2.urlopen(url)
#html = response.read()
#print html
