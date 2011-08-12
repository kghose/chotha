%if source is None:
	<p>Source not in database</p>

%else:

	<br/> <!-- Need this for proper spacing -->
  <div class='itemid-box'>
  <div>{{source['citekey']}} 
  <span>
  <br/><a href="/note/{{source['nid']}}" title="Go to note">Show note</a>
  <br/><a href="/edit/{{source['nid']}}" title="Go to citation">Edit note</a>
  <br/><a href="/editsource/{{source['id']}}" title="Go to citation">Edit source</a>
  </span>
	</div>
  </div>
	<div class='sourcetitle'>{{source['title']}}</div>

%if source['source_type'] == 'article':
	<span class='sourcejournal'>
	{{source['journal']}} {{source['month']}} {{source['year']}}, 
	n<b>{{source['number']}}</b>
	v<b>{{source['volume']}}</b> pp{{source['pages']}}
	</span>
%elif source['source_type'] == 'book':
	<span class='sourcejournal'>
	{{source['booktitle']}} {{source['publisher']}}, {{source['address']}}, {{source['year']}}
	</span>
%end

	<span class='sourceauthors'>
%aul = [au for au in source['author'].split('\n') if au != ''] 
%for n,au in enumerate(aul):
% nm = au.split(',')

% if len(nm) > 1:
{{nm[1]}} {{nm[0]}}
%elif len(nm) > 0:
{{nm[0]}}
%end

%if len(aul) > 1 and n < len(aul) - 1:
%if n == len(aul) -2:
 and 
%else:
,
%end
%end

%end
	</span>

%if source['source_type'] == 'inbook':
	in <span class='sourcejournal'>{{source['booktitle']}}</span>
	Eds.
	<span class='sourceauthors'>
	{{source['editors']}}
	</span>
%end

%if source['source_type'] == 'article':
  <h2>Abstract</h2>
  <p>{{source['abstract']}}</p>
%end

%end #If source is None