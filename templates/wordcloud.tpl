<html>
<head>
<title>{{title}} - চোথা</title>
<link rel="shortcut icon" href="/static/shortcut_icon.png" />
<link rel="stylesheet" href="/static/screen.css" type="text/css" />
<link rel="stylesheet" href="/static/print.css" type="text/css" media="print" />
</head>
<body>

{{len(wordcloud)}} words
<hr/>

<div class="wordcloud">
%for n,word in enumerate(wordcloud):
%if n%10 == 0:
</br>
%end
<a href="/?search_text=+{{word['word']}}+"><font size={{word['count']}}>{{word['word']}}</font></a>
%end
</div>

<hr/>

<a href="/rebuildwordcloud">Rebuild cloud (May take a LONG time)</a>

</body>
</html>