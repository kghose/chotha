<html>
<head>
<title>Chotha (চোথা) {{title}}</title>
<link rel="shortcut icon" href="/static/shortcut_icon.png" />
<script type="text/javascript" src="/static/asciiMathML.js"></script>
<!--<script type="text/javascript" src="/static/LaTeXMathML.js"></script>-->
<script>mathcolor="Black"</script>
<link rel="stylesheet" href="/static/screen.css" type="text/css" />
<link rel="stylesheet" href="/static/print.css" type="text/css" media="print" />
</head>
<body>
%import urllib

%if view=='list': #In the traditional list view we see the keyword list
<div class='keywords-pane'>
%query = [('cskeyword_list', cskeyword_list), \
%         ('page',0), ('perpage',perpage)]
<form action="/?{{urllib.urlencode(query)}}" method="GET">
<input class="entry" type="text" size=20 name="search_text" title="Search" value="{{search_text}}">
<input type="hidden" name="cskeyword_list" value="{{cskeyword_list}}">
<input type="hidden" name="perpage" value={{perpage}}>
</form>
%if cskeyword_list != '':
{{'+' + cskeyword_list}}
<hr/>
%end

%pre = cskeyword_list + ',' if cskeyword_list != '' else ''
%for keyword in candidate_keywords:
%query = [('cskeyword_list',pre.encode('utf-8') + keyword['name'].encode('utf-8')), \
%         ('search_text', search_text.encode('utf-8')), \
%         ('perpage',perpage)]
<a href="/?{{urllib.urlencode(query)}}">{{keyword['name']}}</a> 
%end
</div> <!-- keywords pane -->
%end #If view=='list'

<div class='nav-pane'>
<a href="/">Home</a> <a href="/static/abouthelp.html">Help/About</a>
</div> <!-- 'nav-pane' -->


%if view=='list': #In the traditional list view we get the new item box 
<div class='content noprint'>
<form action="/new" method="POST">
<p><input type="text" name="title" class="entry" title="Note title or pubmed query">
<input type="checkbox" name="ispaper" value='yes' />This is a paper</p>
<p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note"></textarea></p>
<p><input type="text" name="key_list" class="entry" title="Keyword list" value="{{cskeyword_list}}"></p>
<input type="submit" name="save" value="save">
</form>
</div>
%end #If view=='list'

%if view=='list': #Show us the traditional list view
%for row in rows:
<div class="content">
  <div class='date'>{{row['nicedate']}}</div>

%if row['source_id'] != None:  
  <div class='itemid-box'>
  <span class="itemid"><a href="/note/{{row['id']}}" title="Go to note">{{'note:%d' %row['id']}}</a></span>
  <span class="itemid"><a href="/source/{{row['source_id']}}" title="Go to citation">{{'s%04d' %row['source_id']}}</a></span>
  </div>
  <div class='sourcetitle'>{{row['title']}}</div>
%else:
  <div class='itemid-box'>
  <span class="itemid"><a href="/note/{{row['id']}}" title="Go to note">{{'note:%d' %row['id']}}</a></span>
  </div>
  <div class='title'>{{row['title']}}</div>
%end
  <p>{{!row['html']}}</p>
  <div class='key_list'>{{row['key_list']}}</div>
<!--  <div class='lastupdated'>
  <a href="/edit/{{row['id']}}" title="click to edit">edit</a>
  </div> -->
</div>
%end

%elif view=='edit': #Allow us to edit a single note
<div class="content">
Editing <b>{{note['title']}}</b>
</div>
<div class="content">
  <form action="/save/{{note['id']}}" method="POST">
   <p><input type="text" name="date" class="entry" title="Note date" value="{{note['date']}}"></p>  
%if note['source_id'] == None:   
   <p><input type="text" name="title" class="entry" title="Note title" value="{{note['title']}}"></p>
%else:
   <input type="hidden" name="title" value="{{note['title']}}">   
%end
   <p><textarea rows="30" wrap="virtual" name="body" class="entry" title="Text of note">{{note['body']}}</textarea></p>
	 <p><input type="text" name="key_list" class="entry" title="Keyword list" value="{{note['key_list']}}"></p>
   <input type="submit" name="save" value="save">
  </form>
</div>

%elif view=='note': #Show us the edited note only
<div class="content">
%if note != None:
  <div class='date'>{{note['date']}}</div>
  <div class='title'>{{note['title']}}</div>
  <p>{{!note['html']}}</p>
  <p><div class='key_list'>{{note['key_list']}}</div></p>  
  <div align="right"><a href="/edit/{{note['id']}}">edit</a></div>
  <div align="right"><a href="/notesourceexport/{{note['id']}}">
  export sources</a></div>
%else:
No such note
%end
</div>

%elif view=='editsource': #Allow us to edit a single source
<div class="content">
<form action="/refetchsource" method="POST">
Refetch source <input type="text" name="query" size='20' title="Enter pubmed query and hit enter to refetch the bibliographic data">
<input type="hidden" name="id" value={{source['id']}}>
</form>

<form action="/savesource" method="POST">
<input type="hidden" name="id" value={{source['id']}}>
citekey <input type="text" name="citekey" class="source_edit" title="citekey" value="{{source['citekey']}}"><br/> 
Title <input type="text" name="title" class="entry" title="title" value="{{source['title']}}"><br/>
Abstract
<textarea rows="10" wrap="virtual" name="abstract" class="entry" title="abstract">{{source['abstract']}}</textarea><br/>
Type <input type="text" name="source_type" class="entry" title="source type" value="{{source['source_type']}}"><br/>
Journal <input type="text" name="journal" class="entry" title="journal" value="{{source['journal']}}"><br/>
<br/>
    Vol <input type="text" size=4 name="volume" class="entry" title="volume" value="{{source['volume']}}">
    No <input type="text" size=4 name="number" class="entry" title="number" value="{{source['number']}}">
		Year <input type="text" size=4 name="year" class="entry" title="year" value="{{source['year']}}">
    Month <input type="text" size=4 name="month" class="entry" title="month" value="{{source['month']}}">
		Pages <input type="text" size=8 name="pages" class="entry" title="pages" value="{{source['pages']}}">
<br/>
<br/>Authors<br/>
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
doi <input type="text" size=20 name="doi" title="doi" value="{{source['doi']}}"
</div>	

<input type="submit" name="save" value="save">
</form>
</div>

%elif view=='source': #Show us the edited source only
<div class="content">
  <div class='title'><a href="/editsource/{{source['id']}}" title="Click to edit">{{source['title']}}</a></div>
  <p>{{source['abstract']}}</p>
</div>
%end

</body>
</html>