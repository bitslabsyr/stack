// JavaScript Document
var un = '';
var pw = '';
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
	var research = [{'records': 30000000, 'name':'Name AAA', 'desc': 'blah blaah blaaah'}];
	var researches = [];
	researches.push(research);
	researches.push(research);
	researches.push(research);
	researches.push(research);
	researches.push(research);
	
	
	var row = Math.ceil(researches.length / 2);
	console.log(researches.length+" "+row);
	for(var j=0; j<row; j++){
		if(j>0){
			var new_row_html = '<tr id="row-research-project-'+j+'">'+template+'</tr>';
			$('#tbl-research-project').append(new_row_html);
		}
		
		var k = 0;
		for(var i=(j*2); (i< ((j*2)+2)) && (i < researches.length); i++){
			
			$('#row-research-project-'+(j)+'').find('#col-'+k+' i').text('12345678');
			$('#row-research-project-'+(j)+'').find('#col-'+k+' h3').text('Project ABC');
			$('#row-research-project-'+(j)+'').find('#col-'+k+' p').text('Blah blaah blaah');
			k++;
		}
	}
	for(var i = researches.length; (i< ((row*2))); i++){
		var col = Math.floor(i % 2);		
		$('#row-research-project-'+(row-1)+'').find('#col-'+col+'').hide();
	}
	
	
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
	//login_pass();
	// authenticated
	if(status == 0){
		$('#dialog-login').dialog('close');
		window.location = 'project.html?proj_id=3';
	}
	else{
		// unauthenticated
		$('#sp_login_status').text('Invalid Username/Password');
	}

}


function login_pass(){
	$('#login h2').text('Welcome, '+un);
	$('#login-unauth').hide();
	$('#login-auth').show();
	
	set_network_page();	
}