<?php

	$action = $_GET['q'];
	
	if($action == "set_project_detail"){
		$project_name = $_POST['project_name'];
		$password = $_POST['password'];
		$description = $_POST['description'];
		
		$data = array(array('project_name' => $project_name,
				 'password' => $password,
				 'description' => $description));
		$result = shell_exec('python SoMeToolkit/__main__.py db setup ' . escapeshellarg(json_encode($data)));
		
		
		echo $result;
	}
	else if($action == "set_network_detail"){
		$project_id = $_POST['project_id'];
		$preprocessor_status = $_POST['preprocessor_status'];
		$inserter_status = $_POST['inserter_status'];
		$network = strtolower($_POST['network']);
		
		if($preprocessor_status == 1){
			$result = shell_exec('python SoMeToolkit/__main__.py controller process start ' . $project_id . ' ' . $network);
		}
		else{
			$result = shell_exec('python SoMeToolkit/__main__.py controller process stop ' . $project_id . ' ' . $network);
		}
		
		if($inserter_status == 1){
			$result = shell_exec('python SoMeToolkit/__main__.py controller insert start ' . $project_id . ' ' . $network);
		}
		else{
			$result = shell_exec('python SoMeToolkit/__main__.py controller insert stop ' . $project_id . ' ' . $network);
		}
		
		echo $result;
	}
	
	else if($action == "set_collector_detail"){
		$project_id = $_POST['project_id'];
		$network = strtolower($_POST['network']);
		$api = $_POST['api'];
		$oauth = $_POST['oauth'];
		$collector_name = $_POST['collector_name'];
		$collector_id = $_POST['collector_id'];
		$consumer_key = $_POST['consumer_key'];
		$consumer_secret = $_POST['consumer_secret'];
		$access_token = $_POST['access_token'];
		$access_token_secret = $_POST['access_token_secret'];
		$terms_list = $_POST['terms_list'];
		
		$collector_status = $_POST['collector_status'];

		$api_credentials = array(array('consumer_key' => $consumer_key,
				 'consumer_secret' => $consumer_secret,
				 'access_token' => $access_token,
				 'access_token_secret' => $access_token_secret));
				 
		$terms = explode(',', $terms_list);
		
		$result = shell_exec('python SoMeToolkit/__main__.py db set_collector_detail ' . $project_id . ' ' . $network . ' ' . $api . ' \'' . $collector_name . '\' ' . escapeshellarg(json_encode($api_credentials)) . ' ' . escapeshellarg(json_encode($terms)));
		
		if($collector_id != -1){
			if($collector_status == 1){
				$result = shell_exec('python SoMeToolkit/__main__.py controller collect start ' . $project_id . ' ' . $collector_id);
				echo 'python SoMeToolkit/__main__.py controller collect start ' . $project_id . ' ' . $collector_id;
			}
			else{
				$result = shell_exec('python SoMeToolkit/__main__.py controller collect stop ' . $project_id . ' ' . $collector_id);
			}
		}
		
		echo $result;
	}
	
	else if($action == "get_project_detail"){
		$project_id = $_POST['project_id'];
		$result = shell_exec('python SoMeToolkit/__main__.py db get_project_detail ' . $project_id);
		echo $result;
	}
	else if($action == "get_collector_detail"){
		$project_id = $_POST['project_id'];
		$collector_id = $_POST['collector_id'];
		$result = shell_exec('python SoMeToolkit/__main__.py db get_collector_detail ' . $project_id .' '.$collector_id);
		echo $result;
	}
	else if($action == "get_network_detail"){
		$project_id = $_POST['project_id'];
		$network = strtolower($_POST['network']);
		$result = shell_exec('python SoMeToolkit/__main__.py db get_network_detail ' . $project_id .' '.$network);
		echo $result;
	}
	
	
	
	
	
	
?>