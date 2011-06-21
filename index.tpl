<html>
<head>
<title>Chotha (চোথা) {{title}}</title>

<style type="text/css">

body {
	font-family:"Century Gothic";
	font-size: 12pt;
  background-color: #fff; 
	color: #333;
	text-align:center;
	}

.year {
	text-align: center;
  font-size: 6em;
	font-weight: bold;
	font-family:"Century Gothic";
	color: black;
}

.year-pane {
	position:absolute;
	top:10px;
	left:5%;
	width:20%;
	border:solid;
	padding:5px;
	-moz-border-radius: 1em;
	text-align: left;
}

.year-pane a:link {text-decoration: none; color: black;}
.year-pane a:visited {text-decoration: none; color: black;}
.year-pane a:hover {text-decoration: underline overline; color: red;}


.entry {
  width: 100%; /*dynamic with div size*/
}

.content {
	left:37%;
  font-family:"Century Gothic";	
	font-size: 11pt;
	padding-left:2em;
	padding-right:2em;
	padding-top:.1em;
	padding-bottom:.1em;
	margin: 1em auto;	
  width: 12cm;
  text-align: left;
	}

.title {
	width: 100%;
	font-size:large;
	font-weight: bold;
	border-bottom: 1px dotted #ba0000;
}

.date {
  font-weight: normal;
	font-size: .8em;
}

.lastupdated {
	text-align:right;
  font-weight: bold;
	font-size: .6em;
}
.lastupdated a:link {color: black;}
.lastupdated a:visited {color: black;}

</style>
</head>   
<body>
%import urllib

<div class='year-pane'>
<a href="/">Home</a>
%if view=='list': #In the traditional list view we see the keyword list

%query = [('cskeyword_list', cskeyword_list), \
%         ('page',0), ('perpage',perpage)]
<form action="/?{{urllib.urlencode(query)}}" method="GET">
<input class="entry" type="text" size=20 name="search_text" title="Search" value={{search_text}}>
<input type="hidden" name="cskeyword_list" value={{cskeyword_list}}>
<input type="hidden" name="perpage" value={{perpage}}>
</form>
%if cskeyword_list != '':
{{'+' + cskeyword_list}}
%end
<hr/>

%pre = cskeyword_list + ',' if cskeyword_list != '' else ''
%for keyword in candidate_keywords:
%query = [('cskeyword_list',pre + keyword['name']), \
%         ('search_text', search_text), \
%         ('perpage',perpage)]
<a href="/?{{urllib.urlencode(query)}}">{{keyword['name']}}</a></br>
%end
%end #If view=='list'
</div> <!-- keywords pane -->

%if view=='list': #In the traditional list view we get the new item box 
<div class='content'>
<form action="/new" method="POST">
<p><input type="text" name="title" class="entry" title="Note title">
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
%if row['source_id'] == None:  
  <div class='title'>{{row['title']}}</div>
%else:
  <div class='sourcetitle'>
  <a href="/source/{{row['source_id']}}">{{row['title']}}</a>
  </div>
%end  
  <p>{{!row['html']}}</p>
  <p>{{row['key_list']}}</p>
  <div class='lastupdated'>
  <a href="/edit/{{row['id']}}" title="click to edit">edit</a>
  </div>
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
   <p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note">{{note['body']}}</textarea></p>
	 <p><input type="text" name="key_list" class="entry" title="Keyword list" value="{{note['key_list']}}"></p>
   <input type="submit" name="save" value="save">
  </form>
</div>

%elif view=='note': #Show us the edited note only
<div class="content">
%if note != None:
  <div class='date'>{{note['date']}}</div>
  <div class='title'>{{note['title']}}</div>
  <p>{{!note['body']}}</p>
  <p>{{note['key_list']}}</p>  
  <div align="right"><a href="/edit/{{note['id']}}">edit</a></div>
%else:
No such note
%end
</div>

%elif view=='editsource': #Allow us to edit a single source
<div class="content">
<form action="/savesource/{{source['id']}}" method="POST">
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