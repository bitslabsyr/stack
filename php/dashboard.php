<?php
	$action = $_GET['q'];

	if($action == "login"){
		$project_name = $_POST['project_name'];
		$password = $_POST['password'];

		$result = shell_exec('python SoMeToolkit/__main__.py db auth ' . $project_name . ' '. $password);

		echo $result;
	}
	else if($action == "get_project_list"){
		$result = shell_exec('python SoMeToolkit/__main__.py db get_project_list');

		echo $result;
	}


?>
