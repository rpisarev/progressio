#!/usr/bin/python
import sys, os
import yaml

def load_items():
    return [i for i in yaml.load_all(open('progress.yaml'))]

def save_items(items):
    stream = open('progress.yaml','w')
    dump_options = {'indent':4,'default_flow_style':False, 'explicit_start':'---'}
    for i in items:
        yaml.dump(i,stream,**dump_options)
    stream.close()

def add():
    "add a step/task/goal..."
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--title", dest="title")
    parser.add_option("-i", "--item", dest="type")
    (opts, args) = parser.parse_args(sys.argv[2:])
    if not getattr(opts,"title"):
        print "specify title with option -t"
        return
    print "title:", opts.title
    print "item type:", opts.type
    items_list = load_items()
    # prepend new item in the beginning
    if not opts.type:
        opts.type = 'step'
    items_list = [{opts.type:{'title':opts.title}}] + items_list
    save_items(items_list)
    return

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

def done():
    "mark an item done"
    try:
        print "will mark item %d done" % int(sys.argv[2])
        count_done = int(sys.argv[2])
        count = 1
        items = load_items()
        for i in items:
            key = i.keys()[0]
            is_done = i[key].get("done",False)
            if not is_done and i[key].has_key('title'):
                if count == count_done:
                    print "%2d - %s: %s" % (count, key, i[key]['title'])
                    i[key]['done'] = True
                    save_items(items)
                    return
                count += 1
    except IndexError:
        print "you need to specify an item number"
    except ValueError:
        print "you need to specify an item number as integer"
    return

def html():
    print "creating html"
    
    fields_list = ['step', 'issue', 'task', 'version', 'goal', 'other']
    fields = {'step': [], 'issue': [], 'task': [], 'version': [], 'goal': [], 'other': []}

    # add to fields
    for i in yaml.load_all(open('progress.yaml')):
        key = i.keys()[0]
        if key in fields:
            fields[key].append(i[key])
        else:
            fields['other'].append(i[key])

    file = open("progress.html", "w")
    for f in fields_list:
        for i in fields[f]:
            is_done = i.get("done",False)
            if not is_done and i.has_key('title'):
                file.write("%s: %s<br/>\n" % (f,i['title']))
                for k in i.keys():
                    if not k == 'title':
                        file.write("&nbsp;&nbsp;&nbsp;&nbsp;%s: %s<br/>\n" % (k,i[k]))
        if fields[f]:
            file.write("<br/>")

def main():
    progress_file_name = 'progress.yaml'
    if not os.path.exists(progress_file_name):
        f = open(progress_file_name, 'w')
        f.close()
        print 'created %s file' % progress_file_name
        return

    args = sys.argv
    command = None
    if len(args) > 1:
        command = args[1]
        print command

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

    count = 1
    for i in load_items():
        key = i.keys()[0]
        is_done = i[key].get("done",False)
        if not is_done and i[key].has_key('title'):
            print "%2d - %s: %s" % (count, key, i[key]['title'])
            count += 1

if __name__ == "__main__":
    main()
