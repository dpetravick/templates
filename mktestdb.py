#!/usr/bin/env python
from __future__ import print_function
"""
acquire tmobile useage CSVs by default from the downloads area
into the csv_valt area.  Remake a databse and ingest the CSV's
RUn a variet of reports, 

or

Log backback women for me phone numbers,


"""
import argparse
import sqlite3
import shlog
import uuid
import csv
import operator
import itertools
import fnmatch
import tabulate
import os
import datetime
import glob
import sys

def q(args, sql):
    con = sqlite3.connect(args.dbfile)
    cur = con.cursor()
    shlog.verbose(sql)
    result  = cur.execute (sql)
    con.commit()
    return result

def qr(args, sql, row):
    con = sqlite3.connect(args.dbfile)
    cur = con.cursor()
    shlog.verbose("SQl: %s first row: %s" % (sql, row))
    result  = cur.execute (sql, row)
    con.commit()
    return result

def t(x):return x
def i(x):return int(x)
def r(x):return float(x)

class SQLTable:
    def __init__(self, args):
        self.columns   = None  #list of Header keywords as if in  line 1 of CSV
        self.hfn       = None  #List of ascii converter functions eg t, i f)
        self.hdt       = None  #list of SQL types for each keyword
        self.tableName = None # name of the SQL table 
        self.args = args
        
    def check(self):
        # Check that the required data items are set up consisentlu
        #shlog.normal("self.columns: %s" % self.columns)
        #shlog.normal("self.hfn: %s" % self.hfn)
        #shlog.normal("self.hdt: %s" % self.hdt)
        #shlog.normal("self.tableName %s" % self.tableName)
        assert len(self.columns) == len(self.hfm)
        assert len(self.columns) == len(self.hdt) # Bail if we have made typoss
        assert self.tableName
        
    def mkTable (self):
        #make the schemas for the main database tables
        # the schema can be loaded with data from subsequent calls of this program.
        columns = ["%s %s" % (name, dbtype) for (name, dbtype) in zip (self.columns, self.hdt)]
        columns = (',').join(columns)
        create_statement = "create table "+ self.tableName + " (" + columns + ')'
        q(self.args, create_statement)
        return

    def insert(self, rows):
        #insert rows of Ascii into the databse table
        #after applying conversion funcitons.
        insert_statement = (',').join(["?" for name in self.columns])
        insert_statement = "insert into " + self.tableName + "  values (" + insert_statement + ")"
        for row in  rows:
            #apply convertion functions
            shlog.debug("insert sql: %s" % (insert_statement))
            r= ([f(item) for (item, f) in zip(row, self.hfm)])
            qr(self.args, insert_statement, r ) 



###################################################################
#
#  functions to make database state,  make tables, and ingest, DB info.
#
##################################################################

def mkdb (args):
    """Provide an empty database loaded with all schema""" 
    #make the schemas for the main database tables
    # the schema can be loaded with data from subsequent calls of this program.
    try:
        os.remove(args.dbfile)
        shlog.normal ("removed old database : %s" ,args.dbfile)
    except:
        pass
    # folders
    foldersTable = SQLTable(args)
    foldersTable.tableName = "Folders"
    foldersTable.columns = [  'id', 'DEPTH', 'NAME']
    foldersTable.hfm =     [     t,       t,       t]
    foldersTable.hdt =     ['text',  'text', 'text']
    foldersTable.check()

    # folder content 
    contentsTable = SQLTable(args)
    contentsTable.tableName = 'Contents'
    contentsTable.columns   =[  'id','folderId','Name']
    contentsTable.hfm       =[     t,         t,     t]
    contentsTable.hdt       =['text',    'text','text']
    contentsTable.check()


    # parameters content
    parametersTable = SQLTable(args)
    parametersTable.tableName = 'Parameters'
    parametersTable.columns   =[  'id','Name','Number']
    parametersTable.hfm       =[     t,     t,       t]
    parametersTable.hdt       =['text','text',  'text']
    parametersTable.check()

    # plataeu content
    plateausTable = SQLTable(args)
    plateausTable.tableName = 'Plateaus'
    plateausTable.columns   =[  'id','targetID', 'Name']
    plateausTable.hfm       =[     t,         t,      t]
    plateausTable.hdt       =['text',    'text', 'text']
    plateausTable.check()

    # DUAL,the famous little table used for SQL tricks
    dualTable = SQLTable(args)
    dualTable.tableName = 'Dual'
    dualTable.columns   =['Dummy']
    dualTable.hfm       =[      t]
    dualTable.hdt       =[ 'text']
    dualTable.check()

    dualTable.mkTable()
    foldersTable.mkTable()
    contentsTable.mkTable()
    parametersTable.mkTable()
    plateausTable.mkTable()
    
    q(args, "insert into Dual values ('X')")
    import uuid
    x =uuid.uuid1()
    """ Ingest items in the CVS_vault into databse tables """
    folderlist = [
        ["%s" % uuid.uuid1(), "1"  ,"folder 1"  ],
        ["%s" % uuid.uuid1(), "1.1","folder 1.1"],
        ["%s" % uuid.uuid1(), "2"  ,"folder 2"  ]
    ]
    contentslist = []
    parameterslist = []
    n = 0 
    for (fid, fdepth, fname)  in folderlist:
        for cname in ["%s Content1", "%s Content2" ]:
            n += 1
            contentuuid = "%s" % uuid.uuid1()
            contentslist.append([contentuuid, fid,cname % fname])
            commonparameter = [contentuuid, "commonParameter", '1']
            parameterslist.append(commonparameter)
            uniqueparameter = [contentuuid, "uniqueParameter: %s" % (n), '2']
            parameterslist.append(uniqueparameter)
    foldersTable.insert(folderlist)
    contentsTable.insert(contentslist)
    parametersTable.insert(parameterslist)

    plateauslist = []
    n = 0
    for (fuuid, _dummy1, _dummy2) in folderlist:
        plateauslist.append(
            [ "%s" % uuid.uuid1(),
              fuuid,
              "P%s" % n
            ]
            )
        n = n+1
    plateausTable.insert(plateauslist)
    
###################################################################
#
#  reports
#
##################################################################

def dbinfo(args):
    """Print summary information about database content"""
    shlog.normal ("about to open %s",args.dbfile)
    l = []
    earliest_text = "SELECT  Time FROM TEXTS ORDER BY Time ASC  LIMIT 1"
    l.append (["Earliest Text", q(args, earliest_text).fetchone()[0]])

    latest_text   = "SELECT  Time FROM TEXTS ORDER BY Time DESC LIMIT 1"
    l.append (["Latest Text",   q(args, latest_text  ).fetchone()[0]])

    n_texts   = "SELECT  count(*) FROM TEXTS"
    l.append (["Number of Texts",   q(args, n_texts  ).fetchone()[0]])
    
    n_text_ingest   = "SELECT  count(*) FROM INGESTS where IngestType = 'TEXTS'"
    l.append (["Number of Text Ingests",   q(args, n_text_ingest).fetchone()[0]])

    earliest_call = "SELECT  Time FROM CALLS ORDER BY Time ASC  LIMIT 1"
    l.append (["Earliest Call", q(args, earliest_call).fetchone()[0]])

    latest_call   = "SELECT  Time FROM CALLS ORDER BY Time DESC LIMIT 1"
    l.append (["Latest Call",   q(args, latest_call  ).fetchone()[0]])

    n_calls   = "SELECT  count(*) FROM CALLS"
    l.append (["Number of Calls",   q(args, n_calls  ).fetchone()[0]])

    n_allcalls   = "SELECT  count(*) FROM ALLCALLS"
    l.append (["Number of text + Voice records",   q(args, n_allcalls).fetchone()[0]])

    n_call_ingest   = "SELECT  count(*) FROM INGESTS where IngestType = 'CALLS'"
    l.append (["Number of Call Ingests",   q(args, n_call_ingest).fetchone()[0]])

    n_call_escorts   = "SELECT  count(*) FROM SHADY where escort = 'true'"
    l.append (["Number shady escort observations",   q(args, n_call_escorts).fetchone()[0]])

    n_contacts   = "SELECT  count(*) FROM CONTACTS"
    l.append (["Number of contact ",   q(args, n_contacts).fetchone()[0]])

    print (tabulate.tabulate(l,["Item","Value"]))
    
def list(args):
    """Dump a list of all TEXTS and CALLS Sorted by time """
    pass
    con = sqlite3.connect(args.dbfile)
    cur = con.cursor()
    q = "select * from ALLCALLS order by time"
    q = "select *  from (Select * from TEXTS  UNION select * from CALLS) order by time DESC"
    shlog.normal(q)
    rows=[]
    for c in cur.execute (q): rows.append(c)
    print (tabulate.tabulate(rows))

        
if __name__ == "__main__":

    #main_parser = argparse.ArgumentParser(add_help=False)
    main_parser = argparse.ArgumentParser(
     description=__doc__,
     formatter_class=argparse.RawDescriptionHelpFormatter)
    main_parser.add_argument('--loglevel','-l',
                             help=shlog.LOGHELP,
                             default="NORMAL")
    
    main_parser.add_argument("--dbfile", "-d", default="test.db")
    main_parser.set_defaults(func=None) #if none then there are  subfunctions    
    subparsers = main_parser.add_subparsers(title="subcommands",
                       description='valid subcommands',
                       help='additional help')
    

    #Subcommand  to ingest csv to sqlite3 db file 
    mkdb_parser = subparsers.add_parser('mkdb', help=mkdb.__doc__)
    mkdb_parser.set_defaults(func=mkdb)
    mkdb_parser.add_argument("--force", "-f", help="remove existing db file of the same name", default=False, action='store_true')

    
    list_parser = subparsers.add_parser('list', help=list.__doc__)
    list_parser.set_defaults(func=list)
    list_parser.add_argument(   "--chr", "-c", help='Chromosome Numbers' , default='1')

    dbinfo_parser = subparsers.add_parser('dbinfo', help=dbinfo.__doc__)
    dbinfo_parser.set_defaults(func=dbinfo)


    args = main_parser.parse_args()


    # translate text arguement to log level.
    # least to most verbose FATAL WARN INFO DEBUG
    # level also printst things to the left of it. 
    loglevel=shlog.__dict__[args.loglevel]
    assert type(loglevel) == type(1)
    shlog.basicConfig(level=shlog.__dict__[args.loglevel])


    if not args.func:  # there are no subfunctions
        main_parser.print_help()
        exit(1)
    args.func(args)
