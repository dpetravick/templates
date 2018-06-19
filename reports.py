#!/usr/bin/env python
from __future__ import print_function
import shlog
import argparse
import sqlite3
import collections
# do not worry yet about rows that are composite.

def q(args, sql):
    con = sqlite3.connect(args.dbfile)
    cur = con.cursor()
    shlog.verbose(sql)
    result  = cur.execute (sql)
    con.commit()
    return result

def qtranspose(args, sql):
    shlog.verbose(sql)
    results = []
    rets = q(args,sql).fetchall()
    if not rets:
        return [[],[]]
    for result in rets :
        results.append(result)
    return zip(*results)


class Workspace:
    """ Provde an in-memory workslae that can be rendered into excel, etc..."""
    def __init__(self):
        # one-based index beacause you know, excel...:
        self.row = 0
        self.col = 0
        self.col_max = 0
        #self.content = collections.defaultdict(lambda x : "Empty")
        self.content={}
    def next_row(self):
        self.row = self.row+1
        #self.content[self.row] = collections.defaultdict(lambda x : "Empty")
        self.content[self.row] = {}
        self.col = 1
    def max_chars(self, colno):
        #return the max characters in any cell witing a column, 0 for empty column 
        max_chars = 0
        for rowno in range(self.row):
            if rowno in self.content.keys() and colno in self.content[rowno].keys():
                #use python string as a proxy for numeric columns.
                max_chars = max(max_chars,len("%s" % self.content[rowno][colno]))
        shlog.normal("XXX %s %s" %  (colno, max_chars*2)) 
        return max_chars
    def add_element(self, content_element):
        #add populate the curent celle on the current row.
        self.content[self.row][self.col] = content_element
        shlog.verbose("content: (%s,%s):%s" % (self.row, self.col, self.content[self.row][self.col]))
        self.col_max = max(self.col_max, self.col)
        self.col += 1
    def catenate_workspace(self, workspace_to_catenate):
        for n in range(1, workspace_to_catenate.row):
            self.row +=1
            shlog.verbose("catenting row %s" % self.row)
            columns_from_other = workspace_to_catenate.content[n]
            self.content[self.row] = columns_from_other
            self.col_max = max(self.col_max,workspace_to_catenate.col_max)
    def dump(self):
        #provide a crude dump of the workspace
        for r in range(1,self.row):print (self.content[r])
    def excel(self):
        #write the output to an excel file.  @ optionally pop up execl to see ot
        import xlsxwriter
        import os
        workbook = xlsxwriter.Workbook('dog.xlsx')
        worksheet = workbook.add_worksheet()
        #have to say bold to work to make wrap to work, hmm
        x = workbook.add_format({"text_wrap" : True,  "bold" : True })
        for r in range(1,self.row):
            keys = self.content[r].keys()
            for c in keys:
                worksheet.write(r, c, self.content[r][c], x)

        for c in range(self.col_max):
                maxc = min(self.max_chars(c), 60)
                maxc = max(maxc, 1) # at least one char
                worksheet.set_column(c,c, maxc)
                       
        if args.show : os.system('open -a "Microsoft Excel" dog.xlsx')

class Header:
    def __init__(self, args, header_list):
        self.args = args
        self.header_list = header_list
    def report (self, _dummy):
        pass


        
class QueryContext:
    # a query contest is an array of dicitionary that provides
    # addional informaition to a query.  The keys in teh dictionary
    # are teh names in the select statement
    # e.g Deleac a, b...dog from,,,,   a and dog would be keys
    # a distinct dictionary is made for every line returned.
    # the primary internal data structure is a list of these
    # dictionaries.
    #
    # All of this supports a stanxa repeating itsels on a row,
    # Each time using a line from the SQL query to generate new
    # outputs.
    #
    # Capitalization Names capitalised as known to the database.

    def __init__(self, args, sql):
        self.context_list = []
        if sql== None:  #shim to support no context... Fix afer getting the chain to work.
            self.context_list= [{}]
            return
        con = sqlite3.connect(args.dbfile)
        cur = con.cursor()
        shlog.verbose(sql)
        self.results = [r for r in  cur.execute (sql)]
        self.names = [d[0] for d in cur.description]
        shlog.debug("context list generated with names %s" % self.names)
        for row in self.results: 
            d = {}
            for (key, item) in zip(self.names, row):
                 d[key] = item
            self.context_list.append(d)
        shlog.verbose("new query context: %s", self.context_list)
    
class SegmentSQL:
        def __init__(self, segment_sql, many_to_many=True, context=QueryContext(None,None)):
            self.segment_sql = segment_sql
            self.many_to_many = many_to_many
            self.context = context  # an object

class StanzaFactory:
   # recipe for 0...n terminal rows
    def __init__(self, args, element_sql):
        self.args = args
        # The element  query yields information on identifying
        # things on rows. e.g list the elementsid asscociated
        # with a folder id.
        # e.g. SELECT node_id from ELEMENT_FOLDER where  folder_id = '%s"
        self.element_sql = element_sql
        # the report sql tells what to print on a report line
        # for an element, e.g. report on an element.
        # e.g. SELECT * from element where id = `%s`
        self.report_segments = []
        # the substanza object is called to make sub stanza after each report line.
        # e.g self.substanza.report(element_id)
        self.workspace = Workspace()
        self.substanza = None

    def add_report_segment(self, segment_sql):
        self.report_segments.append(segment_sql)

    def set_substanza(self, substanza):
        self.substanza = substanza
        
    def report(self, element_sql_params):
        #Outer loop -- this query givee query paremater to ideniify the subject of a row
        for row_query_sql_params in q(args, self.element_sql % element_sql_params) :
            self.workspace.next_row()
            for segment in self.report_segments:
                unformatted_row_query_sql = segment.segment_sql
                contexts = segment.context.context_list
                for context in contexts:
                    row_query_sql = unformatted_row_query_sql % row_query_sql_params
                    row_query_sql = row_query_sql.format(**context)
                    if segment.many_to_many:
                        self.generate_many_to_many_segment(row_query_sql)
                    else:
                        self.generate_one_to_many_segment(row_query_sql)
                    #done bulding this row, now build any substanza
            if self.substanza:
                self.substanza.workspace = self.workspace
                self.substanza.report(row_query_sql_params)
        return self.workspace
    
    def generate_many_to_many_segment(self,segment_sql):
        #perform query and then populate successive cells in the
        #workspace row with the result
        segment_result = q(self.args, segment_sql).fetchone()
        for s in segment_result:
            self.workspace.add_element(s)
            
    def generate_one_to_many_segment(self,segment_sql):
        #perform query and then catenate the list of results
        #insert into rightmost cell of the workspace
        answer = []
        segment_result = q(self.args, segment_sql).fetchall()
        for result in segment_result:
            #make a string from each returned row.
            s = ' '.join(result)  
            answer.append(s)
        #separate the data from each row wiht a delimiter
        #put data in the next column of the row.
        delimiter = ':::'
        delimiter = '\n'
        self.workspace.add_element(delimiter.join(answer))
        
def report(args):


    #folder factory
    #master  stanza -- loop over folders.
    Folders  = StanzaFactory(args,
                             "SELECT Id from folders order by DEPTH"
    )
    Contents = StanzaFactory(args,
                             "SELECT id from Contents where FolderId= '%s'"
    )
    # find parmeters from the parent stanza
    Parameters = StanzaFactory(args,
                               "SELECT  '%s'  FROM DUAL"
    )


    Parameters.add_report_segment(
        SegmentSQL("SELECT 'PARAMETERS',* from PARAMETERS Where id = '%s'", many_to_many=False)
    )
     
    Contents.add_report_segment(
         SegmentSQL("SELECT 'CONTENTS:', * from Contents where Id='%s'")
    )
    #    Contents.set_substanza(Parameters)
    Folders.set_substanza (Contents)

    Folders.add_report_segment(
        SegmentSQL("SELECT 'FOLDER:', id,depth,name  from Folders where id = '%s'")
    )
    Folders.add_report_segment(
        SegmentSQL("SELECT ' FOLDER SUPRISED ' from Folders where id = '%s'")
    )

    Folders.add_report_segment(
        SegmentSQL("select count(*) from DUAL where dummy = '{PID}' and dummy = '%s'",
                   context = QueryContext(args,"select ID PID from Parameters")
        )
    )


    Folders.report([])        # now go make the report
    #Folders.workspace.dump()
    if args.show: Folders.workspace.excel()



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
    

    #Subcommand  to  make a report 
    report_parser = subparsers.add_parser('report', help=report.__doc__)
    report_parser.set_defaults(func=report )  
    report_parser.add_argument("--force", "-f", help="remove existing db file of the same name", default=False, action='store_true')
    report_parser.add_argument("--show" , "-s", help="show result in excel", default=False, action='store_true')

  
    args = main_parser.parse_args()


    # translate text arguement to log level.
    # least to most verbose FATAL WARN INFO DEBUG
    # level also printst things to the left of it. 
    loglevel=shlog.__dict__[args.loglevel]
    assert type(loglevel) == type(1)
    shlog.basicConfig(level=shlog.__dict__[args.loglevel])
    shlog.normal("Database is %s" % args.dbfile)
    if not args.func:  # there are no subfunctions
        main_parser.print_help()
        exit(1)
    args.func(args)
