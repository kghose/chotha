<html>
<head>
<title>Configuration - চোথা</title>
<style>

.column {
	float: left;
	padding: 10px;
	border-radius: 10px;
	background-color: lightgreen;
}

.column input {border-radius:10px;}

.config-pane {
	background-color: aqua;
	border-radius: 10px;
	padding-left:5px;
	padding-right:5px;	
}
.config-pane input {border-radius:10px}
.config-pane-button {width: 75px}

.config-pane div span {display:none}
.config-pane div:hover span {display:inline}


</style>
</head>
<body>

<div class='column'>

<p>{{cfg['dbinfo']['note count']}} notes<br/>
{{cfg['dbinfo']['source count']}} sources</p>

<p><form action="/selectdb" method="POST">
<input type="submit" name="select" value="Select new db file" style="width: 150px;">
<input type="text" name="newdbname" size="60" value="{{cfg['cfg file'].get('Basic','dbname')}}">
</form></p>

<p><form action="/backup" method="POST">
<input type="submit" name="Backup to" value="Backup to" style="width: 150px;">
<input type="text" name="newdbname" size="60" value="backup.sqlite3">
</form></p>

<p>Sqlite version: {{cfg['dbinfo']['sqlite version']}}</p>
</div>




</body>
</html>