<html>
<head>
<title></title>
<body>

<?php
if(isset($_POST['save'])){
	require "config.php";
	$dbconn = new mysqli($dbhost,$dbuser,$dbpass,$dbname);
		if ($dbconn->connect_error) {
			die("Connection failed: " . $dbconn->connect_error);
		}
	$emp_id = mysqli_real_escape_string($dbconn, $_REQUEST['emp_id']);
	$emp_name = mysqli_real_escape_string($dbconn, $_REQUEST['emp_name']);

	$sql = "INSERT INTO employee_data (employee_id, employee_name) VALUES ('$emp_id', '$emp_name')";
	if($dbconn->query($sql)){
		echo "Records added successfully.";
	} else{
		echo "ERROR: Could not able to execute $sql. " . $dbconn->connect_error;
	}
	$dbconn->close();
}
?>
<form method="post">
    <p>
        <label for="empId">Employee ID:</label>
        <input type="text" name="emp_id" id="empId">
    </p>
    <p>
        <label for="empName">Employee Name:</label>
        <input type="text" name="emp_name" id="empName">
    </p>
    <input type="submit" name="save" value="Submit">
</form>
<br>
<a href="index.php">Home Page</a>
</body>
</html>