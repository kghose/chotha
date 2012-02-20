<html>
<head>
<title>{{title}} - চোথা</title>
<link rel="shortcut icon" href="/static/shortcut_icon.png" />

<style type="text/css">
body {
    font-family: Helvetica;
    font-size: 10pt;
}
.header {
    width: 50%;
    margin-left: auto;
    margin-right: auto;
    background: limegreen;
    text-align: center;
    margin-top: 5px;
    padding: 5px;
    margin-bottom: 5px;
}
.content {
    width: 50%;
    margin-left: auto;
    margin-right: auto;
}
.keyword {
    float:left;
    width: 50%;
    text-align: right;
    border-bottom: thin solid white;/* To match that of the bar */
}
.keyword a:link {
    text-decoration: none;
    color: gray;
}
.keyword a:visited {
    text-decoration: none;
    color: gray;
}
.keyword a:hover {
    text-decoration: none;
    color: black;
    font-weight: bold;
}

.bardiv {
    float: right;
    width: 50%;
}
#bar {
    background: yellow;
    border-right: thin solid black;
    border-bottom: thin solid black;
    margin-left: 5px;
}
</style>

</head>
<body>

%import urllib

<div class='header'>
{{len(keyf)}} keywords
</div>

<div class='content'>

%for k in keyf:
%query = [('cskeyword_list', k['name'].encode('utf-8')),
%         ('limit',limit), ('offset',0)]

<div>
<div class='bardiv'>
<div id='bar' style="width: {{k['count(kn.rowid)']}}px;">&nbsp;</div>
</div>
<div class='keyword'>
<a href="/?{{urllib.urlencode(query)}}" title="{{k['count(kn.rowid)']}}">
{{k['name']}}</a>
</div>
</div>

%end
</div>

</body>
</html>