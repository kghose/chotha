<html>
<head>
<title>Configuration - চোথা</title>
</head>
<body>
<h1>Database</h1>
%for key in dbinfo.keys():
{{key}}: {{dbinfo[key]}}<br/>
%end

<h1>Configuration</h1>
%for sec in config.sections():
<h3>{{sec}}</h3>
%for key in config.options(sec):
{{key}}: {{config.get(sec,key)}}<br/>
%end
%end
</body>
</html>