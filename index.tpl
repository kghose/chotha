%if view=='list': #In the traditional list view we see the keyword list
%for keyword in candidate_keywords:
{{keyword['name']}}</br>
%end
%end


%if view=='list': #In the traditional list view we get the new note box 
<div class='content'>
<form action="/new" method="POST">
<p><input type="text" name="title" class="entry" title="Note title" autocomplete="off"></p>
<p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note"></textarea></p>
<input type="submit" name="save" value="save">
</form>
</div>
%end

%if view=='list' or view=='searchlist': #Show us the traditional list view
%for row in rows:
<div class="content">
  <div class='date'>{{row['nicedate']}}</div>
  <div class='title'>{{row['title']}}</div>
  <p>{{!row['body']}}</p>
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
   <p><input type="text" name="title" class="entry" title="Note title" value="{{note['title']}}"></p>
   <p><textarea rows="10" wrap="virtual" name="body" class="entry" title="Text of note">{{note['markup text']}}</textarea></p>
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
  <div align="right"><a href="/edit/{{note['id']}}">edit</a></div>
</div>
%end
