var params = { allowScriptAccess: "always", bgcolor: "#cccccc" };
var atts = { id: "myytplayer" };
swfobject.embedSWF("http://www.youtube.com/apiplayer?enablejsapi=1&playerapiid=ytplayer", 
		   "ytapiplayer", "400", "300", "8", null, null, params, atts);
var captions=0;
$("#slider").slider({slide:function(event,ui){seek_slide('slide',event.originalEvent,ui.value);},
                     stop:function(event,ui){seek_slide('stop',event.originalEvent,ui.value);}});

function good() {
    	window['console'].log(ytplayer.getCurrentTime());
}

ajax_video=good;

loadNewVideo('${id}', ${ video_time });

