// JavaScript Document
var project_id = '-1';
var network = 'Twitter';

$(document).ready(init);

function init(){
	//$('#sel-nw-list').selectmenu();
	/*$('#tabs-1 #sel-terms-list').multiselectable({
                selectableLabel: 'Active Terms (double-click to remove)',
                selectedLabel: 'Inactive Terms',
                moveRightText: 'Remove',
                moveLeftText: 'Add'
    });
	$('tabs-1 #btn-collector-term-add').bind('click', collector_add_term);
	//var data = [[""]];
	/*$('#tabs-1 #dt-terms-list').handsontable({
	  data: data,
	  minSpareRows: 1//,
	 // contextMenu: ['remove_row']
	});
	*/
	/*$('tabs-1 .network').bind('click', function(){
		$('tabs-1 .network').addClass('alt');
		$('tabs-1 .network').removeClass('selected_btn');
		$(this).removeClass('alt');
		$(this).addClass('selected_btn');
		network = $(this).text();
	});
	
	$('#btn-collector-tw').click();*/
	set_multi('1');
	$('#tabs-1 #btn-collector-term-add').bind('click', collector_add_term);
	var project_id = get_url_value('proj_id');
	
	if(project_id != -1){
		set_project();
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
	
	set_collectors();
	/*$('#sel-nw-list').selectmenu();
	$('#sel-terms-list').multiselectable({
                selectableLabel: 'Active Terms',
                selectedLabel: 'Inactive Terms',
                moveRightText: '>',
                moveLeftText: '<'
    });
	$('button').addClass('button alt');*/
	
	
	/*$('#tabs-1').children().each(function(index, element) {
        $(this).data('collector_id', -1);
    });*/
	
	
}

function set_project(){
	// get project info.
	
	var projects = [];
	projects.loginname = 'Aaaa';
	projects.password = 'Aaaa';
	
	projects.name = 'Aaaa';
	projects.desc = 'Blah blah blah';
	projects.id = '123456'
	
	$('#project-loginname').val(projects.loginname);
	$('#project-password').val(projects.password);
	$('#project-repassword').val(projects.password);
	$('#project-name').val(projects.name);
	$('#project-desc').val(projects.desc);
	
	$('#sp-project-name').text(projects.name);
	$('#sp-project-desc').text(projects.desc);
	$('#btn-project-create').text('update');
}
function set_collectors(){
	
	// get list of process
	var collectors = ['A', 'B', 'C'];
	var html = '';
	
	for(var i=0; i<collectors.length; i++){
		html += '<li><a href="#tabs-'+(i+2)+'">'+collectors[i]+'</a></li>';
		set_collector_detail(collectors[i], (i+2));
	}
	
	$('#tabs-collector ul:first').append(html);
	
	$('#tabs-collector').tabs();
	
}

function set_collector_detail(id, tab_index){
	var template = $('#tabs-1').html();
	var tab_id = '#tabs-'+tab_index;
	
	var html = '<div id="tabs-'+tab_index+'">'+template+'</div>';
	$('#tabs-collector').append(html);
	
	// get collector detail
	var collector_name = 'Name '+id;
	var oauth = 'OAuth '+id;
	var terms = ['Aaaa', 'Bbbb', 'Cccc'];
	
	$(tab_id+' #tab-name').val(collector_name);
	$(tab_id+' #tab-oauth').val(oauth);
	$(tab_id+' #btn-project-create').text("Update");
	
	$(tab_id+'').children().each(function() {
        $(this).data('collector_id', id);
		$(this).data('tab_index', tab_index);
    });
	
	
	for(var i=0; i<terms.length; i++){
		$(tab_id+' #sel-terms-list').append('<option value=0>'+terms[i]+'</option>');
	}
	
	set_multi(tab_index);
	$(tab_id+' #btn-collector-term-add').bind('click', collector_add_term);
	
	
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
}

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