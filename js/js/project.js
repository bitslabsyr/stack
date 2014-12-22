// JavaScript Document

$(document).ready(init);

function init(){
	$("input[type=checkbox]").switchButton({
	  on_label: 'START',
	  off_label: 'STOP',
	  labels_placement: "left",
	  width: 100,
	  height: 30,
	  button_width: 50,
	  checked: false
	});
	
	$('#btn-preprocessor').bind('change', function(){
		$(this).val() == 0 ? $(this).val(1): $(this).val(0);
		set_network_detail();
	});
	
	$('#btn-inserter').bind('change', function(){
		$(this).val() == 0 ? $(this).val(1): $(this).val(0);
		set_network_detail();
	});
	$('#tabs-1 #btn-collector').bind('change', function(){
		$(this).val() == 0 ? $(this).val(1): $(this).val(0);
	});
	
	set_multi('1');
	$('#tabs-1 #btn-collector-term-add').bind('click', collector_add_term);
	project_id = get_url_value('proj_id'); 
	
	if(project_id != -1){
		get_project_detail();
	}
	
	$('.network').bind('click', function(){
		$('.network').addClass('alt');
		$('.network').removeClass('selected_btn');
		$(this).removeClass('alt');
		$(this).addClass('selected_btn');
		network = $(this).text();
	});
	
	$('#btn-collector-tw').click();
	
	$('#tabs-1').children().each(function(index, element) {
        $(this).data('collector_id', -1);
		$(this).data('tab_index', 1);
    });
	
	
	$('#tabs-collector').tabs();
	
	// Bind events to buttons
	$('#btn-project-create').bind('click', set_project_detail);
	$('#btn-collector-create').bind('click', set_collector_detail);	
	
}

function get_project_detail(){
	
	var my_data = 'project_id='+project_id;
	
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=get_project_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
							
				$('#project-loginname').val(data.project_name);
				$('#project-password').val("xxxxxxx");
				$('#project-repassword').val("xxxxxxx");
				$('#project-name').val(data.project_name);
				$('#project-desc').val(data.project_description);
				
				$('#sp-project-name').text(data.project_name);
				$('#sp-project-desc').text(data.project_description);
				$('#btn-project-create').text('update');
				
				get_network_detail();
				
				var collectors = data.collectors;
				var html = '';
				
				for(var i=0; i<collectors.length; i++){
					html += '<li><a href="#tabs-'+(i+2)+'">'+collectors[i].collector_name+'</a></li>';
					
					var template = $('#tabs-1').html();
					var div_html = '<div id="tabs-'+(i+2)+'">'+template+'</div>';
					
					$('#tabs-collector').append(div_html);
					
					$('#tabs-'+(i+2)+' #tab-name').val(collectors[i].collector_name);
					$('#tabs-'+(i+2)+' #tab-oauth').val(collectors[i].oauth);
					$('#tabs-'+(i+2)+' #tab-ckey').val(collectors[i].api_auth[0].consumer_key);
					$('#tabs-'+(i+2)+' #tab-ckeysecret').val(collectors[i].api_auth[0].consumer_secret);
					$('#tabs-'+(i+2)+' #tab-atoken').val(collectors[i].api_auth[0].access_token);
					$('#tabs-'+(i+2)+' #tab-atokensecret').val(collectors[i].api_auth[0].access_token_secret);
					
					if(collectors[i].api == 'Track'){
						$('#tabs-'+(i+2)+' #tab-api').val(1);
					}
					else{
						$('#tabs-'+(i+2)+' #tab-api').val(2);
					}
					
					
					for(var k=0; k < (collectors[i].terms_list).length; k++){
						$('#tabs-'+(i+2)+' #sel-terms-list').append('<option>'+collectors[i].terms_list[k].term+'</option>');
					}
					
					$('#tabs-'+(i+2)+'').children().each(function() {
						$(this).data('collector_id', collectors[i]._id);
						$(this).data('tab_index', (i+2));
					});
					$('#tabs-'+(i+2)+' #btn-collector-create').text('UPDATE');
					$('#tabs-'+(i+2)+' #btn-collector-create').bind('click', set_collector_detail);
					$('#tabs-'+(i+2)+' #btn-collector-reset').bind('click', set_collector_detail);
					
					set_multi((i+2));
					$('#tabs-'+ (i+2) +' #btn-collector-term-add').bind('click', collector_add_term);
					
					$('#tabs-'+(i+2)+' .sw').remove();
					$('#tabs-'+(i+2)+' #btn-collector').switchButton({
						  on_label: 'START',
						  off_label: 'STOP',
						  labels_placement: "left",
						  width: 100,
						  height: 30,
						  button_width: 50,
						  checked: false
					});
					
					$('#tabs-'+(i+2)+' #btn-collector').bind('change', function(){
						$(this).val() == 0 ? $(this).val(1): $(this).val(0);
					});
					
					if(collectors[i].collector.collect == 1){
						$('#tabs-'+ (i+2) +' #btn-collector').switchButton({			  
						  checked: true
						});
						$('#tabs-'+ (i+2) +' #btn-collector').val(1);
					}
					else{
						$('#tabs-'+ (i+2) +' #btn-collector').switchButton({			  
						  checked: false
						});
						$('#tabs-'+ (i+2) +' #btn-collector').val(0);	
					}
					
					
				}
				
				$('#tabs-collector ul:first').append(html);
				$('#tabs-collector').tabs('refresh');
				
			}
			
		},
		error: function(err){
			alert(error_message);			
			console.log(err);	
		}
	});
}
function get_network_detail(){
	
	var my_data = 'project_id='+project_id;
	my_data += '&network='+network;
	
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=get_network_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				if(data.network.processor.run == 1){
					$('#btn-preprocessor').switchButton({			  
					  checked: true
					});
					$('#btn-preprocessor').val(1);
				}
				else{
					$('#btn-preprocessor').switchButton({			  
					  checked: false
					});
					$('#btn-preprocessor').val(0);	
				}
				
				if(data.network.inserter.run == 1){
					$('#btn-inserter').switchButton({			  
					  checked: true
					});
					$('#btn-inserter').val(1);
				}
				else{
					$('#btn-inserter').switchButton({			  
					  checked: false
					});
					$('#btn-inserter').val(0);	
				}
				
				
			}
			else{
				alert(error_message + ' '+data.message);	
			}
			
		},
		error: function(err){
			alert(error_message + ' '+err);	
		}
	});
	
	
}

/*function set_collector_detail(id, tab_index){
	var template = $('#tabs-1').html();
	var tab_id = '#tabs-'+tab_index;
	
	var html = '<div id="tabs-'+tab_index+'">'+template+'</div>';
	$('#tabs-collector').append(html);
	
	
	var my_data = 'project_id='+project_id;
	my_data += '&collector_id='+id;
	
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=get_collector_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				// get collector detail
				
				
				
				
				
			}
			else{
				alert(data.message);	
			}
			
		},
		error: function(err){
			alert("Please try again.");
			console.log(err);	
		}
	});
	
	
	
	//$('#tabs-'+index+'').find('div .htContainer').remove();
	//$('#tabs-'+index+' .multiselectable').remove();
	
/*	var html = '';
	var data = [];
	var data_item = [];
	
	for(var i=0; i<terms.length; i++){
		data_item = [];
		data_item.push(terms[i]);
		data.push(data_item);
	}
	$('#tabs-'+index+' #dt-terms-list').handsontable({
	  data: data,
	  minSpareRows: 1//,
	  //contextMenu: ['remove_row']
	});//.handsontable('loadData', data);
	
	$('#tabs-'+index+'').children().each(function(index, element) {
        $(this).data('collector_id', id);
    });*/
//}

function set_multi(tab_index){
	var tab_id = '#tabs-'+tab_index;
	
	$(tab_id+' .multiselectable').remove();
	$(tab_id+' #sel-terms-list').multiselectable({
                selectableLabel: 'Active Collection Terms (double-click to remove)',
                selectedLabel: 'Inactive Terms',
                moveRightText: 'Remove',
                moveLeftText: 'Add'
    });
	
	
	
}

function collector_add_term(){
	var tab_index = $(this).parent().parent().data('tab_index');
	var tab_id = '#tabs-'+tab_index;
	if($(tab_id+' #tab-term').val() != ''){		
		$(tab_id+' #sel-terms-list').append('<option value=0>'+$(tab_id+' #tab-term').val()+'</option>');
		
		set_multi(tab_index);
		$(tab_id+' #tab-term').val('');
	}
}
	
function set_project_detail(){
	
	var my_data = 'project_name='+$('#project-loginname').val();
	my_data += '&password='+$('#project-password').val();
	my_data += '&readable_name='+$('#project-name').val();
	my_data += '&description='+$('#project-desc').val();
		
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=set_project_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				alert(success_message);
			}
			else{
				alert(error_message + ' '+data.message);	
			}
			
		},
		error: function(err){
			alert(error_message+' '+err);
			console.log(err);	
		}
	});
	
}

function set_network_detail(){
	var 	my_data = 'project_id='+project_id;
	my_data += '&preprocessor_status='+$('#btn-preprocessor').val();
	my_data += '&inserter_status='+$('#btn-inserter').val();
	my_data += '&network='+network;
		
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=set_network_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				//alert(success_message);
			}
			else{
				//alert(error_message + ' '+data.message);	
			}
			
		},
		error: function(err){
			//alert(error_message+' '+err);
			console.log(err);	
		}
	});
	
}

function set_collector_detail(){
	
	var tab_id = $(this).parent().parent().data('tab_index');
	var collector_id = $(this).parent().parent().data('collector_id');
	var term = [];
	$('#tabs-'+tab_id+' .m-selectable-from select option').each(function(index, element) {
        term.push($(this).text());
	});
	
	var my_data = 'project_id='+project_id;
	my_data += '&network='+network;
	my_data += '&api='+$('#tabs-'+tab_id+' #tab-api option:selected').text();
	my_data += '&oauth='+$('#tabs-'+tab_id+' #tab-oauth').val();
	my_data += '&collector_name='+$('#tabs-'+tab_id+' #tab-name').val();
	my_data += '&collector_id='+collector_id;
	my_data += '&consumer_key='+$('#tabs-'+tab_id+' #tab-ckey').val();
	my_data += '&consumer_secret='+$('#tabs-'+tab_id+' #tab-ckeysecret').val();
	my_data += '&access_token='+$('#tabs-'+tab_id+' #tab-atoken').val();
	my_data += '&access_token_secret='+$('#tabs-'+tab_id+' #tab-atokensecret').val();
	my_data += '&terms_list='+term;
	my_data += '&collector_status='+$('#tabs-'+tab_id+' #btn-collector').val();;
	
	$.ajax({
  		type: "POST",
  		url: server_url + "project.php?q=set_collector_detail",
  		data: my_data, 
		dataType : 'json',
	    success: function(data) {
			if(data.status == 1){
				alert(success_message);
			}else{
				alert(error_message +' '+data.message)	
			}
			
		},
		error: function(err){
			alert(error_message +' '+err);
			console.log(err);	
		}
	});
	
}

function get_url_value(VarSearch){
    var SearchString = window.location.search.substring(1);
    var VariableArray = SearchString.split('&');
    for(var i = 0; i < VariableArray.length; i++){
        var KeyValuePair = VariableArray[i].split('=');
        if(KeyValuePair[0] == VarSearch){
            return KeyValuePair[1];
        }
		else{
			return -1;
		}
    }
}