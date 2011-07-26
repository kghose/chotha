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

.column input {border-radius:10px; padding: 3px;}

</style>
</head>
<body>

<div class='column'>
<p>Sqlite version: {{cfg['dbinfo']['sqlite version']}}</p>

<p>{{cfg['dbinfo']['note count']}} notes<br/>
{{cfg['dbinfo']['source count']}} sources</p>

<p><form action="/selectdb" method="POST">
<input type="submit" name="select" value="Set as new db file" style="width: 150px;">
<input type="text" name="newdbname" size="60" value="{{cfg['cfg file'].get('Basic','dbname')}}">
</form></p>

<p><form action="/backup" method="POST">
<input type="submit" name="Backup to" value="Backup to" style="width: 150px;">
<input type="text" name="newdbname" size="60" value="backup.sqlite3">
</form></p>

</div>

</body>
</html>