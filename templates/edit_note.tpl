
Editing <b>{{note['title']}}</b>
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
