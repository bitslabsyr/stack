// JavaScript Document

$(document).ready(init);

function init(){
	// initital elements
	$('#btn-login').bind('click', login_click);
	$('#btn-create-project').bind('click', create_project_click);
	$('#dialog-login').dialog({
		autoOpen: false,
		show: {
			effect: "blind",
			duration: 1000
		},
		hide: {
			effect: "explode",
			duration: 1000
		},
		resizable: true,
		width: 500,
		//height:140,
		modal: true,
		buttons: {
			"Submit": function() {
				login_submit_click();
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		}
	});

	get_research_project();
	
	//draw_graph();
}

function get_research_project(){
	var template = $('#row-research-project-0').html();
	
	// get data
	var my_data = '';
	
	$.ajax({
  		type: "POST",
  		url: server_url + "dashboard.php?q=get_project_list",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				for(var i=0; i<data.project_count; i++){
					var researches = data.project_list;
					
					var row = Math.ceil(researches.length / 2);
					for(var j=0; j<row; j++){
						if(j>0){
							var new_row_html = '<tr id="row-research-project-'+j+'">'+template+'</tr>';
							$('#tbl-research-project').append(new_row_html);
						}
						
						var k = 0;
						for(var i=(j*2); (i< ((j*2)+2)) && (i < researches.length); i++){
							
							$('#row-research-project-'+(j)+'').find('#col-'+k+' i').text(researches[i].record_count);
							$('#row-research-project-'+(j)+'').find('#col-'+k+' h3').text(researches[i].project_name);
							$('#row-research-project-'+(j)+'').find('#col-'+k+' p').text(researches[i].description);
							$('#row-research-project-'+(j)+' td').width('50%');
							k++;
						}
					}
					for(var i = researches.length; (i< ((row*2))); i++){
						var col = Math.floor(i % 2);		
						$('#row-research-project-'+(row-1)+'').find('#col-'+col+'').hide();
					}
				}
				/*var research = [{'records': 30000000, 'name':'Name AAA', 'desc': 'blah blaah blaaah'}];
				var researches = [];
				researches.push(research);
				researches.push(research);
				researches.push(research);
				researches.push(research);
				researches.push(research);*/
				
				
				
			}
			else{
				alert("Please try again");
			}
			
		},
		error: function(err){console.log(err);
			alert("Please try again");
		}
	});
	
	
	
	
}


// Draw Bar Graph
function draw_graph(){
	  var s1 = [2, 6, 7, 10];
	  var s2 = [7, 5, 3, 4];
	  var s3 = [14, 9, 3, 8];
	  plot3 = $.jqplot('chart3', [s1, s2, s3], {
		// Tell the plot to stack the bars.
		stackSeries: true,
		captureRightClick: true,
		seriesDefaults:{
		  renderer:$.jqplot.BarRenderer,
		  rendererOptions: {
			  // Put a 30 pixel margin between bars.
			  barMargin: 30,
			  // Highlight bars when mouse button pressed.
			  // Disables default highlighting on mouse over.
			  highlightMouseDown: true   
		  },
		  pointLabels: {show: true}
		},
		axes: {
		  xaxis: {
			  renderer: $.jqplot.CategoryAxisRenderer
		  },
		  yaxis: {
			// Don't pad out the bottom of the data range.  By default,
			// axes scaled as if data extended 10% above and below the
			// actual range to prevent data points right on grid boundaries.
			// Don't want to do that here.
			padMin: 0
		  }
		},
		legend: {
		  show: true,
		  location: 'e',
		  placement: 'outside'
		}      
	  });
	  // Bind a listener to the "jqplotDataClick" event.  Here, simply change
	  // the text of the info3 element to show what series and ponit were
	  // clicked along with the data for that point.
	  $('#chart3').bind('jqplotDataClick', 
		function (ev, seriesIndex, pointIndex, data) {
		  $('#info3').html('series: '+seriesIndex+', point: '+pointIndex+', data: '+data);
		}
	  ); 
}

function login_click(){
	$('#sp_login_status').text('');
	$('#dialog-login').dialog('open');
}

function create_project_click(){
	window.location = 'project.html';
}

function login_submit_click(){
	un = $('#login-un').val();
	pw = $('#login-pw').val();
	
	// authentication
	var my_data = 'project_name='+$('#login-un').val();
	my_data += '&password='+$('#login-pw').val();
	
	$.ajax({
  		type: "POST",
  		url: server_url + "dashboard.php?q=login",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				$('#dialog-login').dialog('close');
				window.location = 'project.html?proj_id='+data.project_id;
			}
			else{
				$('#sp_login_status').text('Invalid Username/Password');
			}
			
		},
		error: function(err){
			alert("error "+err);
			//console.log(err);	
		}
	});

}


function login_pass(){
	$('#login h2').text('Welcome, '+un);
	$('#login-unauth').hide();
	$('#login-auth').show();
	
	set_network_page();	
}