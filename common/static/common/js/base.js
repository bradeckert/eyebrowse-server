function submitFeedBack(e, d) {
    $('#submit_success').fadeIn();
    $.post('/feedback', { 
        'feedback' : $('#feedback').val()
    });
    $('#submit_success').fadeOut();
    $('#send-feedback-modal').modal('hide');
    $('#feedback').val("");
}

function submitConsent(e, d) {
	$.post('/consent_accept', {
		'consent': 'true'
	},
	function(res) {
		if (res.res === 'success') {
			window.location.replace('/live_stream/');
		} else {
			location.reload();
		}
	});
	return false;
	
}

function dropitemSelected (e, v) {
    $('#search-bar').blur();
    navToUser(v);
}

function navToUser(val){
    var username = user_dict[val];
    window.location = '/users/' + username
}

function submitForm(e, d){
    e.preventDefault();
    var $form = $(e.target);
    var id = $form.attr('id');
    var url = $form.data('url');
    $form.find('.btn[type=submit]').button('loading')
    $form.find('.alert').slideUp();
    
    $.post(url, $form.serialize(), function(res){
        if (res.success){
            var addClass = "alert-success";
            var removeClass = "alert-error";
            var text = '<p>' + res.success + '</p>';
        } else {
            var addClass = "alert-error";
            var removeClass = "alert-success";
            var text = "";
            for (var i =0, max=res.errors[id].length; i<max; i++){
                text += "<p>" + res.errors[id][i] + "</p>";
            }
        }
        $form.find('.response_text').html(text)
        $form.find('.alert').removeClass(removeClass).addClass(addClass).slideDown();
        $form.find('.btn[type=submit]').button('reset')

        $('#pic').find('.btn[type=submit]').addClass('disabled')//reset pic submit to be disabled.
        $form.trigger('formRes', res)
    });
}

function typeahead(id) {
    id = id || 'search-bar';
    id = '#' + id;
    $(id).typeahead({
        source: function (typeahead, query) {
            return $.getJSON('/api/typeahead/', {'query': query}, function(res) {
                if (res.success) {
                	var arr = [];
                    $.each(res.users, function (index, value) {
                    	var res_item = { username: value.username, fullname: value.fullname, email: value.email, gravatar: value.gravatar};
                    	arr.push(JSON.stringify(res_item));
                    });
                    return typeahead.process(arr);
                }
            });
        },
        // typeahead calls this function when a object is selected, and passes an object or string depending on what you processed, in this case a string
        onselect: function (obj) {
        	var item = JSON.parse(obj);
            $(id).blur();
            window.location = '/users/'+item.username
        },
        highlighter: function(obj) {
        	var item = JSON.parse(obj);
        	
        	var regex = new RegExp('(' + this.query + ')', 'ig')
        	var func = function ($1, match) { return '<strong>' + match + '</strong>'}
        	
        	username = item.username.replace(regex, func)
        	fullname = item.fullname.replace(regex, func)
        	html = '<a href="/users/'+item.username+'"><li>'+item.gravatar;
        	html += '<span class="fullname">'+fullname+'</span> ';
        	html += '<span class="username">'+username+'</span></li></a>';
			return html;
        },
        matcher: function (obj) {
        	var item = JSON.parse(obj);
        	return item.username.toLowerCase().indexOf(this.query.toLowerCase()) > -1 || item.fullname.toLowerCase().indexOf(this.query.toLowerCase()) > -1 || item.email.toLowerCase().indexOf(this.query.toLowerCase()) > -1;
		},
		sorter: function(items) {
		    var beginswith = []
				, caseSensitive = []
				, caseInsensitive = []
		    	, aitem;
		    	
		    while (aitem = items.shift()) {
		    	var item = JSON.parse(aitem);

        		if (!item.username.toLowerCase().indexOf(this.query.toLowerCase())) beginswith.push(aitem)
        		else if (!item.fullname.toLowerCase().indexOf(this.query.toLowerCase())) beginswith.push(aitem)
        		else if (item.username.indexOf(this.query)) caseSensitive.push(aitem)
        		else if (item.fullname.indexOf(this.query)) caseSensitive.push(aitem)
        		else caseInsensitive.push(aitem)
      		}
      		return beginswith.concat(caseSensitive, caseInsensitive)
		},
    });
}

///////// templating helpers /////

/*
template_list is a list of elments initially sent by the server
renderFunc is what these items are sent into
*/
function setupTemplateValues(template_list, renderFunc, type) {
    if (template_list != undefined) { 
        $.each(template_list, function(index, item){
            item = {
                'success': true,
                'data': item,
            }
            renderFunc(item, type);
        });
    }
}

/*
Adds a new row or creates an intial row the given type of row to add 
*/
function initTemplateTable(type) {
    var $rows = $(sprintf('.%s-row', type));
    var $toAdd, addFunc;
    if ($rows.length == 0 ){
        $toAdd = $(sprintf('.%s-body', type))
        addFunc = 'append';
    } else {
        $toAdd = $rows.filter(':last');
        addFunc = 'after'
    }
    return {
        'toAdd' : $toAdd,
        'addFunc' : addFunc,
    }
}

/*
Given a rendered template appends it to the proper row given by init template table
*/
function addTableTemplate(type, template) {
    var init = initTemplateTable(type);
    var $toAdd = init.toAdd;
    var addFunc = init.addFunc;
    $toAdd[addFunc](template);
}

/*
defaults to placing right and focus trigger if 
no values given.
*/
function makeTip(selector, title, placement, trigger) {
    placement = placement || 'right';
    trigger = trigger || 'focus'
    $(selector).tooltip({
        "placement" : placement,
        "title" : title,
        "trigger" : trigger,
    });
}

/*
Set multiple tips to a class
*/
function setTips(targetClass, position, trigger) {
    var $targets = $(targetClass);
    position = position || 'right';
    trigger = trigger || 'hover';
    $.each($targets, function(index, target) {
        $target = $(target);
        makeTip($target, $target.data('content'), position, trigger);
    });
    
}

/*
    Detects if the user is on a mobile browser. Uses helper file lib/mobile_detection.js. Changes filepicker.SERVICES to only facebook and dropbox for mobile
    */
function filepicker_services(){
    if ($.browser.mobile) {
        return [
            'FACEBOOK',
            'DROPBOX'
        ];
    }
    return [
            'WEBCAM',
            'COMPUTER',
            'FACEBOOK',
            'GMAIL',
        ];
}

/* 
filepicker image upload for registration/edit_profile page
*/
function getImg() {
    filepicker.setKey('ABDI6UIw6SzCfmtCVzEI3z');
    filepicker.pick({
    	mimetypes: ['image/*'],
    	container: 'modal',
    	services: filepicker_services(),
    },
    function(InkBlob) {
    	$('#pic').find('.btn[type=submit]').removeAttr('disabled').removeClass('disabled');
        $('#profile_pic').attr("src", InkBlob.url);
        $('#id_pic_url').attr("value", InkBlob.url);
    });
}


//helper function for fomatting numbers with commas
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function getApiURL(resource, id, params) { 
    params = params || {};
    var apiBase = '/api/v1/' + resource;
    var getParams = '';
    $.each(params, function(key, val){
        getParams += sprintf("&%s=%s", key, val);
    });
    if (id != null) {
        apiBase += '/' + id;
    } 
    return sprintf("%s?format=json%s", apiBase, getParams)
}

/*
Deletes a resource, requires data of resource type and the id of the item to be in the item triggering the event.
*/
function rmItem(e, filterset) {
    var $target = $(e.currentTarget);
    var id = $target.data('id');
    $target.closest('tr').remove()
    $.ajax({
        url: getApiURL(filterset, id),
        type: 'DELETE',
    });
}

/*
Deletes a resource, requires data of resource type and the id of the item to be in the item triggering the event.
*/
function addItem(resource, url) {
    $.ajax({
        type: 'POST',
        url: getApiURL(resource),
        data:  JSON.stringify({ "url" : url, "user" : getResourceURI()}),
        contentType:'application/json',
        dataType: 'application/json',
        processData: false,
    });
}

function follow(e) {
    var $icon = $(e.currentTarget).children();
    var type = $icon.data('type');
    $.post('/accounts/connect', $icon.data(), function(res){
        if(res.success){
            $.each($('.connection'), function(index, item){
                $item = $(item).children();
                if ($item.data('user') == $icon.data('user')){
                    swapFollowClass($item, type);
                }
            });
        }
    });
}

function swapFollowClass(icon, type) {
    var $icon = $(icon);
    if (type == 'add-follow'){
        $icon.attr('data-type', 'rm-follow');
        $icon.removeClass('icon-ok').addClass('icon-remove');
        var text = $icon.parent().html().replace('Follow', 'Following')
        $icon.parent().html(text);
        ;
    } else {
        $icon.attr('data-type', 'add-follow');
        $icon.removeClass('icon-remove').addClass('icon-ok');
        var text = $icon.parent().html().replace('Following', 'Follow')
        $icon.parent().html(text);
    }
}

function getResourceURI() { 
    return sprintf('/api/v1/user/%s/', username)
}


function urlDomain(url, cut) {
    cut = cut || true;
    var uri = new URI(url)
    var hostname = uri.hostname();
    if (cut) {
        hostname = truncate(hostname);
    }
    return hostname
}

function truncate(str, len){
    len = len || 40;
    return str.substr(0, len);
}

function date_ms(dateString) {
    dateString = dateString.replace('a.m.', 'AM').replace('p.m.', 'PM');
    return (new moment(dateString).unix())*1000
}

/*
Ajax CSRF protection
*/
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

function getURLParameter(name) {
    var res =  decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
    );
    if (res == 'null'){
        res = null
    }
    return res
}

function nullFilter(filter){
    return null
}


/*
    Apply infinite scroll to the givin selector. infiniteSel specifies what the data will be appended to.
    defalts to .live-stream-container (auto update on live stream) and .infinite-scroll (applied to all live streams)
*/
function infiniteScroll(infiniteSel, itemSel){  
    infiniteSel = infiniteSel || '.live-stream-container';
    itemSel = itemSel || '.infinite-scroll';
    // infinitescroll() is called on the element that surrounds 
    // the items you will be loading more of
    $(infiniteSel).infinitescroll({
 
        navSelector  : ".pager", // selector for the paged navigation (it will be hidden)
        nextSelector : ".pager .next .next-link", // selector for the NEXT link (to page 2)
        itemSelector : itemSel, // selector for all items you'll retrieve
    });
         
}

//generic update stats function
function updateStats(history_data) {
    $("#tot_history .content").text(numberWithCommas(history_data.num_history));
    $("#tot_online .content").text(numberWithCommas(history_data.num_online));
    if (history_data.is_online) {
        $("#is_online .content").html("<span class='green'> online now</span>");
    } else {
        $("#is_online .content").html("<span class='red'> not online </span>")
    }
}

//set tool tips for truncated data
function setHistoryTips() {
    setTips('.author-pic', 'left'); 
    setTips('.time-ago');
    setTips('.cut-content'); 
    setTips('.cut-url', 'left'); 
    setTimeAgo();
}

//generic callback for livestream ping
//this should be called by any modifed functions
function liveStreamCallback(history_data){
    setHistoryTips();
    updateStats(history_data);
}

//humanize the timestamps passed down
function calculateStats() {
    $.each($(".time-stat"), function(i, v){
        v = $(v);
        v.text(moment.humanizeDuration(v.data('time')));
    });
}

//find all objects that have a time-ago and update 
//the humanzied time from when the event occurred.
//runs on a 1 minute interval
function setTimeAgo(){
    $.each($(".time-ago"), function(i, v){
        v = $(v);
        var time = new Date(v.data('time-ago') + ' UTC');
        v.text(moment(time).fromNow());
    });
}

function submitSearch(e) {
    if (e.which !== 1 && e.which !== 13) return
    var query = $(".search-bar").val();
    var date = $(".date-search-bar").val();
    var filter = getURLParameter("filter");
    var url = sprintf("?query=%s&date=%s&filter=%s", query, date, filter);

    if (profile_username !== "") {
        url = sprintf("/users/%s%s&username=%s", profile_username, url, profile_username);
    } else {
        url = /live_stream/ + url;
    }

    document.location = url;
}

//init search listeners and tooltips
function setupSearch() {
    $('.search-btn').click(submitSearch);
    $('.date-search-bar').keypress(submitSearch);
    $('.search-bar').keypress(submitSearch);
    
    var filter = getURLParameter("filter");
    var searchTip;

    if (filter !== null) {
        searchTip = sprintf("Search with the %s filter", filter);
    } else {
        searchTip = sprintf("Search %s's history", profile_username)
    }
    
    makeTip(".search-bar", searchTip, "right", "hover");
    makeTip(".date-search-bar", "Limit search by date.", "bottom", "hover");
}


$(function(){
    var csrftoken = $.cookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    TEMPLATE_BASE = "api/js_templates/";

    $("#submit_feedback").on('click', submitFeedBack);
    
    $("#confirmation").on('click', submitConsent);
    

    typeahead();

    infiniteScroll();

    setTimeAgo(); //init
    setInterval(setTimeAgo, 3600);

    setupSearch();

});