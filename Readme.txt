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

Some notes on design choices
----------------------------
* Quantity limits instead of date limits 
	- the display slowdown depends on the # of entries, not date range
	- if we do a search, and there are no results in the date range set up it can
	  get annoying and misleading to then click through different date ranges to
	  find if there are any hits at all

* html (from markdown) is not cached (currently) - want to keep code and db as
  simple as possible. Also, don't want to bloat db size.


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
* Create a new chotha database
* Copy over all the notes as is, dropping the created_at and updated_at columns
* Copy over all the sources as is, dropping the created_at, updated_at and url columns
* For each source, create a new note and fill in the source_id appropriately,
set the note date as the source created_at date and the note title as the paper
title + citekey
=> note and source ids remain the same, but now we have a bunch of extra notes at the end
* For each note, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
   * Associate each keyword with note
* For each source, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
	 * Find the note that goes with the source (source ids are conserved) and associate the keywords with that note


keywords handling in Chotha:
----------------------------
The keywords_notes and keywords_sources are defined as:

create table "a" ("x" integer, "y" integer, primary key (x,y));

such that we can now use:

insert or replace into a (x,y) values (1,2);

and not have annoying duplicate entries in the table


Todo:

* Change paging system to a date from latest hit + some time frame + offset
  This will require two fetches, one for id and date, another for fetching the
  complete subset of entries based on date then using the date, time frame and
  offset to select from the subset of entries. The second fetch will not require
  reuse of the query and so will not tax the db so much.
  Needs a rewrite of fetch_notes_by_criterion
  
* add an export page that will export to different formats (currently just exports to word)
* Break up index.tpl into sub templates - pass data using dicts
* (not doing) Add a 'window' parameter to date selector, and have fwd,bkwd buttons? 
* (done) Restrict returned notes by date (have two columns, start and end date)
* About should show some db stats and db location etc.
* (done) Desktop feature, that allows us to store a keyword conjunction that opens when
  we go 'home'. Store it in config. Basically a way to collect all our current notes
  together as we work on it.
* Add table + directory to store svg sketches that can be inserted into notes
* Integrate svg-edit with the app so we can create SVGs on the fly.
* (done - apsw apparently has this activated) Enable FTS in sqlite install
* Modify db to use FTS
* (done in a way) Search (notes and papers) just retrieves basic information, clicking on
  items pulls up full info (could speed things up for large notes + papers)
* Use snippets for text search
* (done) No more fancy AJAX crap - make it stateless, so I can open and edit in new 
  tabs and use the browser backbutton : worked well in pylog. (done)
* (done) Implement keyword conjunction UI -> need to be able to generate url links properly (urllib.encode)
* (done) Rewrite for new database format
* (done) Test new database format using dummy database
* (done) Convert rriki db to chotha format
* (done) Implement sensible paging, based on date/year for eg
* (done) make the jumping between note and citation data cleaner
* (done) On sources edit page make a "refetch" button where you can put a query in and
  refetch the citation data

Some useful SQL queries:
------------------------
select keywords.name from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id = 667;

select keywords.name from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id = 667 limit 10;

select notes.id, group_concat(keywords.name) from notes inner join keywords_notes on keywords_notes.note_id = notes.id inner join keywords on keywords_notes.keyword_id = keywords.id where notes.id in (564,667) group by notes.id;
 
 
UPDATE notes SET notes.key_list=kwd WHERE notes.id=nid  (SELECT notes.id AS nid, group_concat(keywords.name) AS kwd FROM notes,keywords,keywords_notes WHERE keywords_notes.keyword_id = keywords.id AND keywords_notes.note_id = notes.id GROUP BY notes.id LIMIT 10) 