<html>
<head>
<title>{{title}} - চোথা</title>
<link rel="shortcut icon" href="/static/shortcut_icon.png" />
<script type="text/javascript" src="/static/asciiMathML.js"></script>
<!--<script type="text/javascript" src="/static/LaTeXMathML.js"></script>-->
<script>mathcolor="Black"</script>
<link rel="stylesheet" href="/static/screen.css" type="text/css" />
<link rel="stylesheet" href="/static/print.css" type="text/css" media="print" />
</head>
<body>
%import urllib, datetime

<div class='pane control-pane'>
%query = [('cskeyword_list',desktop_cskeyword_list)]
<a href="/?{{urllib.urlencode(query)}}" title="Go to the desktop">Desktop</a> 
<br/><a href="/">Home</a> 

%if view=='list': #In the traditional list view we see the search box and keyword list

%filter_data = {'total_found': total_found, 'total_shown': len(rows), 'candidate_keywords': candidate_keywords, 'cskeyword_list': cskeyword_list, 'search_text': search_text, 'limit': limit, 'offset': offset}
%include templates/filter_controls filter_data=filter_data 

%end #If view=='list'
</div> <!-- control pane -->

<div class='pane content-pane'>

%if view=='list': #In the traditional list view we get the new item box 
<div class='content newentry'>
<div> <!-- for the hover -->
+Entry
<form action="/new" method="POST">
<p><input type="text" name="title" class="filldiv" title="Note title or pubmed query">
<input type="checkbox" name="ispaper" value='yes' />This is a paper</p>
<p><textarea rows="10" wrap="virtual" name="body" class="filldiv" title="Text of note"></textarea></p>
<p><input type="text" name="key_list" class="filldiv" title="Keyword list" value="{{cskeyword_list}}"></p>
<input type="submit" name="create" value="create">
</form>
</div> <!-- For the hover -->
</div>
%end #If view=='list'

%if view=='list': #Show us the traditional list view
%for row in rows:
<div class="content">
  <div class='date'>{{row['nicedate']}}</div>

%if row['source_id'] != None:  
  <div class='itemid-box'>
  <div>Source 
  <span>
  <br/><a href="/note/{{row['id']}}" title="Go to note">Show note</a>
  <br/><a href="/source/{{row['source_id']}}" title="Go to citation">Show source</a>
  <br/><a href="/edit/{{row['id']}}" title="Go to citation">Edit note</a>
  <br/><a href="/editsource/{{row['source_id']}}" title="Go to citation">Edit source</a>
  </span>
	</div>
  </div>
  <div class='sourcetitle'>{{row['title']}}</div>
%else:
  <div class='itemid-box'>
  <div>{{'note:%d' %row['id']}}
  <span>
  <br/><a href="/note/{{row['id']}}" title="Go to note">show</a>
  <br/><a href="/edit/{{row['id']}}" title="Go to note">edit</a>
  </span>
  </div>
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
%include templates/edit_note note=note
</div>

%elif view=='note': #Show us the edited note only
<div class="content">
%include templates/show_note note=note
</div>

%elif view=='editsource': #Allow us to edit a single source
<div class="content">
%include templates/edit_source source=source
</div>

%elif view=='source': #Show us the edited source only
<div class="content">
%include templates/show_source source=source  
</div>

%end

%if view=='list':
<div class='pane paging-pane'> 
%filter_data = {'total_found': total_found,'cskeyword_list': cskeyword_list, 'search_text': search_text, 'limit': limit, 'offset': offset}
%include templates/page_controls filter_data=filter_data 
</div> <!-- paging-pane -->
%end

</div> <!-- content-pane -->

<div class='pane control-pane'><!-- other navigation -->
<a href="/static/abouthelp.html">Help/About</a>
<br/><a href="/config">Config</a>
</div>

</body>
</html>