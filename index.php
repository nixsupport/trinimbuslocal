<html>
<head>
<title>Employee Record</title>
</head>
<body>
<h3>Employee Record</h3>
<table border=1>
<tr><th>Employee ID</th><th>Employee Name</th></tr>
<?php
	require "config.php";
	$dbconn = new mysqli($dbhost,$dbuser,$dbpass,$dbname);
	if ($dbconn->connect_error) {
		die("Connection failed: " . $dbconn->connect_error);
	}
	//echo 'Connection OK';
	$sql = "select employee_id,employee_name from employee_data;";
	$result = $dbconn->query($sql);
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()) {
			echo "<tr>";
			echo "<td>" . $row["employee_id"] . "</td>";
			echo "<td>" . $row["employee_name"] . "</td";
			echo "</tr>";
			
		}
	} else {
		echo "0 results";
	}
	
	$dbconn->close();
?>
</table>
<a href="create.php">Insert Record</a>
</body>
</html>