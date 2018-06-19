# templates
templates and for short shell-commands I tend to use while prototyping various stuff.  BasincallI write small scripts (<2000 lines) to understand the fasiblity of making human driven workflows, or to explore a domain with small shell tools.  The files I have in here are ones I use on various computers.  Perhas they are usefil for you as well, but I do not represent that these tools are bug-free or good for any particular purpose. 

# Heirarchical Report Generator
This is a tool I use to generate more elaborate CSV and other reports from a data I've put into an sqllite database. It is  motivated by several use cases I've run into.  I usualy use it  to fill a gap while I hunt for usually better integrated tools, or a data integration programmer. 

## Theory of operations.

### StanzaFactory
A stanza defines a line in a report. A stanzaFactory is an object tha creates many stanzas base on SQL queries. In fact, A stanza is defined by three types of SQL queries.  All of these queries relate to a single subject.  A line about a particular subject may optionally be followed by a substanza  where each line contains inforamation about a different sort of subject.   

The idea directories and files is an intuitive example that illustrates the concept.  the tool can generte a report about each folder in a directory tree.  Each Stanza of the report would contain a line about some particular directory,after that lines, there would be additional lines about the files in each folder.  The high-level stanzas are about the subject of *folders*, each report line about a folder containes a report line about a *file* in a directory.

#### Subject Query
A subject query defines an ordered list of subjects that are to be reported on. The Quaery yield parameters needed to identify a subject for each line in a report. The subjet Query is passed to a contructor of a StanzaFactory object in its constructor.


```python
	Folders = StanzaFactory("SELECT id FROM Folders ORDER BY folder_number")
```

In the above example, The StanzaFactory eventually generates a report where there is a line for each folder.  Evidently the returned *id* will be sufficient to locate the particular folder for a particular line in a report. 

#### Queries to Generate a Report about a Specifc Subject
Reports about a specifc subect are realized in a row of a report. It may take more than one SQL query to generate the information needed in a report of a specfic subject. The results of each such query is called a segment. These ideas are implemented in the following way: Each Stanzafacory object reports about a given row.  The rows are composed by one of more segments. Each segment is defined by the output of a segment query. The segment queries use the sql parameters emitted by the subject query, discussed above, to identify the specifc subject for the row current being generated.

Segment queries are stored in a list. Segments are generated in left to right order, with the first added report segment being the left-most segement of the report. Each returned item frem the select statement is rendered as its own internal cell.  I.e each slected itme would be in its own cell in a report rendered as a spreadsheet.

```python
	Folders.add_report_segment(
           SegmentSQL("SELECT id, depth from Folders where id = '%s'")
	 )
```
in the above example, the internal database ID, depth of folder in a heirarcy, and name of folder are reported. To generate a specifinc line the %s is replaces wth the id produced by the Subject query, describe in the previous section.

### Additional Context for a Segment Query.

Often an SQL query to generate a report needs more information that that the parameters taht  describe the subject of a row. an Additional context is needed. A query suporting additional context is can be supplied the the *SegmentSQL* object constructor.
```python
Folders.add_report_segment(
        SegmentSQL("select count(*) from DUAL where dummy = '{PID}' and dummy = '%s'",
                   context = QueryContext(args,"select ID PID from Parameters")
        )
```
MOre later...

# Shell LOog
