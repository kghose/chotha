<html>
<head>
<title>Tika (টীকা)</title>

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

%if view=='list': #In the traditional list view we see the keyword list
<div class='year-pane'>
<a href="/">Home</a>

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
</div>
%end

%if view=='list': #In the traditional list view we get the new note box 
<div class='content'>
<form action="/new" method="POST">
<p><input type="text" name="title" class="entry" title="Note title" autocomplete="off">
<input type="checkbox" name="ispaper" value='yes' />This is a paper</p>
<p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note"></textarea></p>
<p><input type="text" name="key_list" class="entry" title="Keyword list" value="{{cskeyword_list}}"></p>
<input type="submit" name="save" value="save">
</form>
</div>
%end

%if view=='list' or view=='searchlist': #Show us the traditional list view
%for row in rows:
<div class="content">
  <div class='date'>{{row['nicedate']}}</div>
  <div class='title'>{{row['title']}}</div>
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
%end
   <p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note">{{note['body']}}</textarea></p>
	 <p><input type="text" name="key_list" class="entry" title="Keyword list" value="{{note['key_list']}}"></p>
   <input type="submit" name="save" value="save">
  </form>
</div>
%elif view=='saved': #Show us the edited note only
<div class="content">
Saved <b>{{note['title']}}</b>
</div>
<div class="content">
  <div class='date'>{{note['date']}}</div>
  <div class='title'>{{note['title']}}</div>
  <p>{{!note['body']}}</p>
  <p>{{note['key_list']}}</p>  
  <div align="right"><a href="/edit/{{note['id']}}">edit</a></div>
</div>
%end

</body>
</html>