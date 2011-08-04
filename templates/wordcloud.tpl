<ul>
%for word in wordcloud:
<li>{{word['word']}} : {{word['count']}} </li>
%end
</ul>

<a href="/rebuildwordcloud">Rebuild cloud (May take a LONG time)</a>