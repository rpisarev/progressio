#!/usr/bin/python
"""
Data structure:

Each task/step/ticket is an Item instance.

Each item may have one parent and several children nodes.
"""

import os
import sys
import yaml
import time
import string
import re
import sqlite3


__version__ = '0.2dev'

PROGRESS_TXT_FILE_NAME = 'progress.txt'
PROGRESS_DB_FILE_NAME = 'progress.db'

BASE_FOR_ID = 36


class Item(object):
    """
    The following fields are stored in the database:

    pk (id)     - int
    children    - str - a list of children ids, order is important (limit of 8 items!)
    title       - str - title
    added_at    - datetime
    done        - boolean
    done_at     - datetime

    TODO: Think about using materialized path (it is not necessary yet):

    path        - str - materialized path - root, subroot, ..., grandparent, parent

    It should be added if its used would seem to be required.
    """

    def __init__(self, pk, children=None, title=None, added_at=None, done=False, done_at=None):
        self.pk = int(pk)
        if children is not None:
            self.children = children.split(',')
        else:
            self.children = []
        self.title = title
        self.added_at = added_at
        self.done = done
        self.done_at = done_at

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{} - {}'.format(self.pk, self.title)

    def __cmp__(self, other):
        return cmp(int(self.pk, BASE_FOR_ID), int(other.pk, BASE_FOR_ID))


def base_encode(num, base, dd=False):
    """
    Converts a number in base 10
    to new base from 2 to 36.
    
    http://www.daniweb.com/forums/thread159163.html
    to convert back  int(string, BASE_FOR_ID)

    :param num:
    :param base:
    :param dd:

    :returns: number in `base`
    """
    if not 2 <= base <= 36:
        raise ValueError('The base number must be between 2 and 36.')
    if not dd:
        dd = dict(zip(range(36), list(string.digits + string.ascii_lowercase)))
    if num < base:
        return dd[num]
    num, rem = divmod(num, base)
    return base_encode(num, base, dd) + dd[rem]

def _create_db_if_needed():
    """
    Checks if db file exists. Creates it if it does not exist.

    :returns: False if db file did not exist, True if it existed.
    """

    if not os.path.exists(PROGRESS_DB_FILE_NAME):
        con = sqlite3.connect(PROGRESS_DB_FILE_NAME)
        cur = con.cursor()
        cur.execute("CREATE TABLE item(pk INTEGER PRIMARY KEY, children, title, added_at, done, done_at)")
        cur.execute("INSERT INTO item(pk, children, title) values(0, '', 'root')")
        con.commit()
        con.close()
        return False

    return True


def load_items():
    """
    Returns a list with Items.
    """
    con = sqlite3.connect(PROGRESS_DB_FILE_NAME)
    cur = con.cursor()
    cur.execute("SELECT * FROM item")
    items = cur.fetchall()
    item_instances = [Item(*i) for i in items]
    con.close()
    return item_instances


def save_items(items):
    stream = open('progress.yaml', 'w')
    dump_options = {
            'indent': 4,
            'default_flow_style': False, 
            }
    yaml.dump(items, stream, **dump_options)
    stream.close()


def get_info(items):
    """Get info from items.
    """
    if 'info' in items:
        return {'info': items['info']}
    else:
        return {'info': {}}


def parse_item(line):
    item_re = re.compile('(\w+) - (.+)')
    pk, title = item_re.findall(line)[0]
    return Item(pk, title)


def load_txt():
    items = []
    if not os.path.exists(PROGRESS_TXT_FILE_NAME):
        return []
    for line in open(PROGRESS_TXT_FILE_NAME, 'r'):
        items.append(parse_item(line))
    return items


def save_txt(items):
    with open(PROGRESS_TXT_FILE_NAME, 'w') as f:
        for i in items:
            f.write(' {0} - {1}'.format(
                i.pk, 
                i.title))
            f.write('\n')


def get_item(pk):
    con = sqlite3.connect(PROGRESS_DB_FILE_NAME)
    cur = con.cursor()
    cur.execute('SELECT * FROM item WHERE pk={}'.format(pk))
    item = Item(*cur.fetchone())
    con.close()
    return item


def add(item_title=None, item_pk=None, parent_pk=0):
    """
    add a step/task/goal...
    
    If no parent_pk is specified item is added to root (pk=0)
    """

    if not item_title:
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-t", "--title", dest="title")
        parser.add_option("-i", "--item", dest="type", default="step")
        (opts, args) = parser.parse_args(sys.argv[2:])
        if not getattr(opts,"title"):
            return
        item_title = opts.title

    _create_db_if_needed()

    parent = get_item(parent_pk)

    con = sqlite3.connect(PROGRESS_DB_FILE_NAME)
    cur = con.cursor()
    query = "INSERT INTO item(title) values('{title}')".format(title=item_title)
    cur.execute(query)
    con.commit()
    parent.children.append(cur.lastrowid)
    children = ','.join(map(str, parent.children))
    query = "UPDATE item SET children='{children}' WHERE pk={parent_pk}".format(
        children=children, parent_pk=parent_pk)
    cur.execute(query)
    con.commit()
    con.close()

    items = load_items()
    save_txt(items)

    """
    try:
        last_id = items['info']['last_id']
    except KeyError:
        last_id = '0'
    new_id = base_encode(int(last_id, BASE_FOR_ID) + 1, BASE_FOR_ID)
    if item_pk:
        items['items'][item_pk]['items'] = {}
        items['items'][item_pk]['items']['0'] = {
            'title': item_title,
            'added_at':  time.strftime('%a %b %d %H:%M:%S %Y %Z'),
            'id': new_id
            }
    else:
        items['items'][new_id] = {
                    'title': item_title,
                    'added_at':  time.strftime('%a %b %d %H:%M:%S %Y %Z'),
                    'id': new_id
                    }
    items['info']['last_id'] = new_id
    save_items(items)


    return
    """


def clean():
    done_list = []
    not_done_list = []
    for i in yaml.load_all(open('progress.yaml')):
        key = i.keys()[0]
        is_done = i[key].get("done",False)
        if is_done and i[key].has_key('title'):
            print "%s: %s" % (key,i[key]['title'])
            done_list.append(i)
        else:
            not_done_list.append(i)
    stream = open('progress.history.yaml','a')
    dump_options = {'indent':4,'default_flow_style':False, 'explicit_start':'---'}
    for i in done_list:
        yaml.dump(i,stream,**dump_options)
    stream.close()
    stream = open('progress.yaml','w')
    dump_options = {'indent':4,'default_flow_style':False, 'explicit_start':'---'}
    for i in not_done_list:
        yaml.dump(i,stream,**dump_options)
    stream.close()
    return

def convert():
    print "converting to new progress.txt format"
    if os.path.exists(PROGRESS_TXT_FILE_NAME):
        print '{} already exists'.format(PROGRESS_TXT_FILE_NAME)
        return
    with open(PROGRESS_TXT_FILE_NAME, 'w') as f:
        for i in load_items():
            key = i.keys()[0]
            is_done = i[key].get("done", False)
            if not is_done and i[key].has_key('title') and i[key].has_key('id'):
                f.write("%s - %s\n" % (i[key]['id'], i[key]['title']))
    return

def count():
    count_done = 0
    count_total = 0
    items = load_items()['items']
    for i in items:
        count_total += 1
        is_done = items[i].get("done", False)
        if is_done:
            count_done += 1
    print "done: ", count_done
    print "total items: ", count_total
    return

def done(id_done=None):
    "mark an item done"
    try:
        if id_done is None:
            id_done = sys.argv[2]
        print "will mark item %s done" % id_done
        data = load_items()
        items = data['items']
        for i in items:
            is_done = items[i].get("done", False)
            if not is_done and items[i].has_key('title'):
                if items[i]['id'] == id_done:
                    print " %s - %s" % (items[i]['id'], items[i]['title'])
                    items[i]['done'] = True
                    items[i]['done_at'] = time.strftime('%a %b %d %H:%M:%S %Y %Z')
                    data['items'] = items
                    save_items(data)
                    save_txt(data)
                    return
        print 'did not find this id'
    except IndexError:
        print "you need to specify an item number"
    except ValueError:
        print "you need to specify an item number as integer"
    return

def help():
    "print help"
    print "usage: p [COMMAND [ARGS]]"
    print ""
    print "  add        [-i [(step,task,issue)]] -t TITLE"
    print "  clean      clean progress.yaml, move done items to progress.yaml.history"
    print "  convert    convert to new progress.txt format"
    print "  count      count items done and to be done"
    print "  done       [n] - mark item n done"
    print "  help       print help"
    print "  html       generate progress.html"
    print "  log        [-i item_type] [-d] - log items"


def html():
    print "creating html"
    
    fields_list = ['step', 'issue', 'task', 'version', 'goal', 'other']
    fields = {'step': [], 'issue': [], 'task': [], 'version': [], 'goal': [], 'other': []}
    ignore_keys = ('added_at', 'title')

    # add to fields
    for i in yaml.load_all(open('progress.yaml')):
        key = i.keys()[0]
        if key in fields:
            fields[key].append(i[key])
        else:
            fields['other'].append(i[key])

    file = open("progress.html", "w")
    file.write("""<style> body { padding: 1em; } </style>""")
    for f in fields_list:
        file.write("""<h2>%ss</h2>""" % f)
        for i in fields[f]:
            is_done = i.get("done",False)
            if not is_done and i.has_key('title'):
                file.write("%s<br/>\n" % i['title'])
                for k in i.keys():
                    if not k in ignore_keys:
                        file.write("&nbsp;&nbsp;&nbsp;&nbsp;%s: %s<br/>\n" % (k,i[k]))
        if fields[f]:
            file.write("<br/>")


def log():
    "log [-i item_type] [-d]"
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--item", dest="type", default="all")
    parser.add_option('-d', dest='print_done', default=False, action='store_true')
    (opts, args) = parser.parse_args(sys.argv[2:])
    print "item type:", opts.type
    print "print done:", opts.print_done
    item_count = 1
    for i in load_items():
        key = i.keys()[0]
        is_done = i[key].get("done",False)
        if is_done==opts.print_done and i[key].has_key('title'):
            if opts.type=="all" or opts.type==key:
                print "%2d - %s: %s" % (item_count, key, i[key]['title'])
                item_count += 1
    load_txt()


def main():
    progress_file_name = 'progress.yaml'
    if not os.path.exists(progress_file_name):
        sys.stdout.write("progress.yaml does not exist. Create? y/n [n] ")
        choice = raw_input().lower()
        if choice == '' or choice == 'n':
            return
        f = open(progress_file_name, 'w')
        f.close()
        print 'created %s file' % progress_file_name
        return

    args = sys.argv
    command = None
    if len(args) > 1:
        command = args[1]

    if command == 'clean':
        clean()
        return

    if command == "html":
        html()
        return

    if command == "add":
        add()
        return

    if command == "done":
        done()
        return

    if command == "count":
        count()
        return

    if command == "convert":
        convert()
        return

    if command in ["help", "-h", "--help", "-help"]:
        help()
        return

    if command == "log":
        log()
        return

    item_count = 1
    items = load_items()['items']
    for i in items:
        is_done = items[i].get("done", False)
        if not is_done and items[i].has_key('title'):
            print " %s - %s" % (items[i]['id'], items[i]['title'])
            item_count += 1

if __name__ == "__main__":
    main()
