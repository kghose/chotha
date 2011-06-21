Chotha is a rewrite of RRiki using Python and Bottle. 

Usage
-----
1. Quickly type in a note (research idea, meeting notes) and file it using
keywords
2. Grab a citation info for a paper from pubmed you are reading and type in
notes about it
3. Manually enter citation info for a book that you are reading and/or will be
referencing in a paper
4. Search for a paper/note by keyword intersection and text search on multiple

UI Design
---------
1. Two "panel" paged design 
2. Left has a search box and a keyword list, arranged vertically
3. Right contains the results of the search paged. Full text of the items
is displayed (which inclines us to making shorter notes)
4. Clicking on 'edit' takes us to an edit page for that item.
5. Saving an item takes us to the conjunction page - search page with the same
keyword conjunction as that item
6. Clicking new note or new sourc on a search page (i.e. other than the
opening page) will populate the keywords with the current conjunction
7. Creating a new note/source will present it on a search page having the
same conjunction of keywords as it has


Changes from RRiki database structure
-------------------------------------
* Diary subapp has been dropped and moved into a new app
* Hierarchical keywords discarded for a keyword intersection model
* After some debate I changed the structure such that every thing is a note.
A citation is basically a note (our notes about the paper) with a source
object attached to it. The source object has a one-one relationship with Rriki's
source table except that the 'body' (notes) is not present. Each note has a
source_id pointer, that is NULL for most notes, except those that are citations
The title of the note is not editable by us and is a short citation form that
is generated when the source attributes are modified (using a trigger)

Conversion of RRiki database to Chotha:
--------------------------------------
Keep track of all ids

sources: 
Change the 'url' field to 'doi'
Ignore the last_updated_at field
Create a new note with date as the created_at field, title as some function of
paper title, citekey and year and link it to the paper



notes:
Ignore the last_updated_at and created_at fields

keywords handling:
-----------------
The keywords_notes and keywords_sources are defined as:

create table "a" ("x" integer, "y" integer, primary key (x,y));

such that we can now use:

insert or replace into a (x,y) values (1,2);

and not have annoying duplicate entries in the table

Converting keywords
-------------------
for each item, read in the path_text for each linked keyword, split each path
component into keywords and use those as the keywords.


Todo:

1. Enable FTS in sqlite install
2. Search (notes and papers) just retrieves basic information, clicking on
items pulls up full info (could speed things up for large notes + papers)
3. Use snippets for text search
4. No more fancy AJAX crap - make it stateless, so I can open and edit in new 
tabs and use the browser backbutton : worked well in pylog.

Some useful SQL queries:
------------------------
select keywords.name from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id = 667;

select keywords.name from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id = 667 limit 10;

select notes.id, group_concat(keywords.name) from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id in (564,667) group by notes.id;
 