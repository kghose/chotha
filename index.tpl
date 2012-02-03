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

<div class='pane filter-pane'>
%query = [('cskeyword_list',desktop_cskeyword_list)]
<a href="/?{{urllib.urlencode(query)}}" title="Go to the desktop">Desktop</a> 
<br/><a href="/">Home</a> 
%filter_data = {'total_found': total_found, 'total_shown': len(rows), 'candidate_keywords': candidate_keywords, 'cskeyword_list': cskeyword_list, 'search_text': search_text, 'limit': limit, 'offset': offset}
%include templates/filter_controls filter_data=filter_data 
</div> <!-- filter pane -->

<div class='pane content-pane'>

%if view != 'new':
%query = [('cskeyword_list',cskeyword_list)]
<div class="content newentry">
<a href="/new?{{urllib.urlencode(query)}}">New</a>
</div>
%end

%if 'message' in locals():
<div class="content, message">
{{!message}}
</div>
%end

%if view == 'new':
<div class="content">
<form action="/new" method="POST">

%if 'ntitle' not in locals():
% ntitle = ''
%end
%if 'ispaper' not in locals():
% ispaper = ''
%end

<p><input type="text" name="title" class="filldiv" title="Note title or pubmed query" value="{{ntitle}}">
<input type="checkbox" name="ispaper" value="yes" {{ispaper}} />This is a paper</p>
<p><textarea rows="10" wrap="virtual" name="body" class="filldiv" title="Text of note"></textarea></p>
<p><input type="text" name="key_list" class="filldiv" title="Keyword list" value="{{cskeyword_list}}"></p>
<input type="submit" name="create" value="create">
</form>
</div>

%elif view=='list': #Show us the traditional list view

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

%elif view=='note': #Show us the note only
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

</div> <!-- content-pane -->


%if view=='list':
<div class='paging-pane'>
%filter_data = {'total_found': total_found,'cskeyword_list': cskeyword_list, 'search_text': search_text, 'limit': limit, 'offset': offset}
%include templates/page_controls filter_data=filter_data
</div> <!-- paging-pane -->
%end

<div class='pane misc-pane'><!-- other navigation -->
<a href="/wordcloud">Word cloud</a>
<br/><a href="/static/abouthelp.html">Help/About</a>
<br/><a href="/config">Config</a>
</div>

</body>
</html>