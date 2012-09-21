<!-- Allows us to edit a source -->

<div class='content newentry'>
<form action="/refetchsource" method="POST">
Refetch source <input type="text" name="query" size='30' title="Enter pubmed query and hit enter to refetch the bibliographic data">
<input type="hidden" name="id" value={{source['id']}}>
</form>
<form action="/refetchsourcebibtex" method="POST">
Parse from BibTeX
<textarea class="filldiv" name="query" rows="5" title="Enter bibtex and hit enter to populate the bibliographic data"></textarea>
<input type="hidden" name="id" value={{source['id']}}>
</form>
</div>

<form action="/savesource" method="POST">
<input type="hidden" name="id" value={{source['id']}}>
citekey <input type="text" name="citekey" title="citekey" value="{{source['citekey']}}"><br/> 
Title <input type="text" name="title" class="filldiv" title="title" value="{{source['title']}}"><br/>
Abstract
<textarea rows="10" wrap="virtual" name="abstract" class="filldiv" title="abstract">{{source['abstract']}}</textarea><br/>
Type <input type="text" name="source_type" class="entry" title="source type" value="{{source['source_type']}}"><br/>
Journal <input type="text" name="journal" class="entry" title="journal" value="{{source['journal']}}"><br/>
<br/>
    Vol <input type="text" size=4 name="volume" class="entry" title="volume" value="{{source['volume']}}">
    No <input type="text" size=4 name="number" class="entry" title="number" value="{{source['number']}}">
		Year <input type="text" size=4 name="year" class="entry" title="year" value="{{source['year']}}">
    Month <input type="text" size=4 name="month" class="entry" title="month" value="{{source['month']}}">
		Pages <input type="text" size=8 name="pages" class="entry" title="pages" value="{{source['pages']}}">
<br/>
<br/>Authors
<textarea size="40x5" wrap="virtual" name="author" class="entry" title="Enter authors on separate lines. Last Name, First Name M.I">{{source['author']}}</textarea><br/>
		
<div id='book-source'>
booktitle <input type="text" size=50 name="booktitle" title="book title" value="{{source['booktitle']}}">
<br/>chapter<input type="text" size=3 name="chapter" title="chapter" value="{{source['chapter']}}">
edition<input type="text" size=4 name="edition" title="edition" value="{{source['edition']}}">
series<input type="text" size=50 name="series" title="series" value="{{source['series']}}">
<br/>Editors <textarea size="40x5" wrap="virtual" name="editor" title="Enter names on separate lines. Last Name, First Name M.I">{{source['editor']}}</textarea><br/>
<br/>publisher <input type="text" size=50 name="publisher" title="publisher" value="{{source['publisher']}}">
<br/>address
<br/><textarea size="20x4" wrap="virtual" name="address" title="Address">{{source['address']}}</textarea>
</div>

<div id='thesis-source'>howpublished <input type="text" size=5 name="howpublished" title="How published" value="{{source['howpublished']}}">
institution <input type="text" size=20 name="institution" title="institution" value="{{source['institution']}}"><br/>
organization <input type="text" size=20 name="organization" title="organization" value="{{source['organization']}}">
school <input type="text" size=20 name="school" title="School" value="{{source['school']}}"><br/>
doi <input type="text" size=20 name="doi" title="doi" value="{{source['doi']}}">
</div>

<input type="submit" name="save" value="save">
</form>