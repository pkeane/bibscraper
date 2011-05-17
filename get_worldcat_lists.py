#!/usr/bin/env python


from BeautifulSoup import BeautifulSoup
import base64
import codecs
import datetime
import feedparser
import fnmatch
import httplib
import json
import md5
import mimetypes
import os
import random
import re
#import simplejson as json
import string
import sys
import urllib
import urllib2

#necessary for printing to file
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#wcname = 'zdoleshal'
wcname = 'utphilosophy'
wcname = 'pkeane'

lists_directory = 'user_lists_'+wcname
json_directory = 'json_items_'+wcname

def dirify(str):
    str = re.sub('\&amp\;|\&', ' and ', str) 
    str = re.sub('[-\s]+', '_', str)
    return re.sub('[^\w\s-]', '', str).strip().lower()

def add_meta(item,key,val):
    if key not in item['metadata']:
        item['metadata'][key] = []
    item['metadata'][key].append(val)
    return item

def get_lists():
    if not os.path.exists(lists_directory):
        os.mkdir(lists_directory)
    url = "http://utexas.worldcat.org/profiles/"+wcname+"/lists"
    soup = BeautifulSoup(urllib.urlopen(url).read())
    #lists = open('lists')
    #soup = BeautifulSoup(lists.read())
    for list in soup('td','list'):
        list_url = 'http://www.worldcat.org'+list.contents[1]['href']+'/rss?count=500'
        list_name = dirify(list.contents[1].contents[0].contents[0])
        data = urllib.urlopen(list_url).read()
        FILE = open(lists_directory+'/'+list_name+'.rss',"w")
        FILE.write(data)
        print list_name

def create_json():
    if not os.path.exists(json_directory):
        os.mkdir(json_directory)
    for f in os.listdir(lists_directory):
        records_directory = f.replace('.rss','')
        records_path = lists_directory+'/'+records_directory
        if not os.path.exists(records_path):
            os.mkdir(records_path)
        d = feedparser.parse(records_path+'.rss')
        section = d.feed['title']
        for entry in d.entries:
            item = {}
            item['metadata'] = {}
            book_url = entry['link']
            add_meta(item,'book_url',book_url)
            book_url = book_url.replace('www.world','utexas.world')
            book_filename = book_url.split('/').pop()
            add_meta(item,'oclc_number',book_filename)
            print 'oclc_num: '+book_filename
            add_meta(item,'section',section)
            book_record_path = records_path+'/'+book_filename+'.html'
            #stats = os.stat(book_record_path)
            #print 'filesize: '+str(stats[6])
            #if 1485 == stats[6]:
            if not os.path.exists(book_record_path):
                book_data = urllib.urlopen(book_url).read()
                FILE = open(book_record_path,"w")
                FILE.write(book_data)
                print "wrote "+book_filename

                try:
                    soup = BeautifulSoup(open(book_record_path).read())
                    #if soup.find('img','cover'):
                    #    enc = soup.find('img','cover')['src']
                    #    item['enclosure']  = enc
                    if soup.find('h1','title'):
                        title = soup.find('h1','title').contents[0].split(':')
                        if len(title):
                            ti = title[0]
                            add_meta(item,'title',ti)
                        if len(title) > 1:
                            subti = title[1]
                            add_meta(item,'subtitle',subti)
                    auth = soup.find('th',text='Author:')
                    if auth:
                        for a in auth.parent.findNextSibling('td').findAll('a'):
                            author = a.contents[0]
                            add_meta(item,'author',author)
                    format = soup.find('th',text='Edition/Format:')
                    if format:
                        fmt = format.parent.findNextSibling('td').find('span','bks')
                        if fmt and len(fmt.contents):
                            format = fmt.contents[0].strip()
                            add_meta(item,'format',format)
                    series = soup.find('th',text='Series:')
                    if series:
                        for a in series.parent.findNextSibling('td').findAll('a'):
                            if len(a.contents):
                                series = a.contents[0]
                                add_meta(item,'series',series)
                    pub = soup.find('th',text='Publisher:')
                    if pub:
                        publisher = pub.parent.findNextSibling('td').contents[0]
                        add_meta(item,'publisher',publisher)
                    subjects = soup.find('h3',text='Subjects')
                    if subjects:
                        for subj in subjects.parent.findNextSibling('ul').findAll('a'):
                            if len(subj.contents):
                                if 'View all s' not in subj.contents[0]:
                                   subject = subj.contents[0]
                                   add_meta(item,'subject',subject)
                    print item
                    FILE = open(json_directory+'/'+book_filename+'.json',"w")
                    FILE.write(json.dumps(item))
                except:
                    print 'could NOT parse '+book_filename

def post_item(item_json,sernum,dase_collection,user,passwd):
    DASE_HOST = 'daseupload.laits.utexas.edu'
    h = httplib.HTTPSConnection(DASE_HOST,443)
    auth = 'Basic ' + string.strip(base64.encodestring(user+':'+passwd))
    body = item_json                                   
    headers = {
        "Content-Type":'application/json',
        "Content-Length":str(len(body)),
        "Authorization":auth,
        "Slug":sernum
    };
    h.request("POST",'/collection/'+dase_collection+'?auth=service',body,headers)
    r = h.getresponse()
    return r.status

def post_json_to_dase(dase_collection,user,passwd):
    for f in os.listdir(json_directory):
        if not fnmatch.fnmatch(f,'.*'):
            sernum = f.replace('.json','')
            f = file(json_directory+'/'+f, "rb")
            item_json = f.read()                                                                     
            pydata = json.loads(item_json)
            if 'title' not in pydata['metadata']:
                pydata['metadata']['title'] = ['missing']
                print sernum 
            else:
                print 'OK'
            print post_item(item_json,sernum,dase_collection,user,passwd)

if __name__=='__main__':
    dase_collection = 'pkeane'
    user = 'pkeane'
    passwd = 'pubsub8'
    get_lists()
    create_json()
    post_json_to_dase(dase_collection,user,passwd)
