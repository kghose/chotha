<!-- Show us a single note -->

%if note != None:
  <div class='date'>{{note['date']}}</div>
%if note['source_id'] == None:
  <div class='itemid-box'>
  <div>note:{{note['id']}}
  <span>
  <br/><a href="/edit/{{note['id']}}" title="Go to citation">Edit note</a>
  <br/><a href="/notesourceexport/{{note['id']}}" title="Export citations in this note">Export sources</a>
  </span>
	</div>
  </div>
  <div class='title'>{{note['title']}}</div>
%else:
  <div class='itemid-box'>
  <div>Source 
  <span>
  <br/><a href="/source/{{note['source_id']}}" title="Go to citation">Show source</a>
  <br/><a href="/edit/{{note['id']}}" title="Go to citation">Edit note</a>
  <br/><a href="/editsource/{{note['source_id']}}" title="Go to citation">Edit source</a>
  </span>
	</div>
  </div>
  <div class='sourcetitle'>{{note['title']}}</div>
%end  
  
  <p>{{!note['html']}}</p>
  <p><div class='key_list'>{{note['key_list']}}</div></p>  
%else:
No such note
%end
