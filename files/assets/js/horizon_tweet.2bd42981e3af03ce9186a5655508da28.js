(window.__twttrll=window.__twttrll||[]).push([[8],{168:function(t,e,r){var i=r(39),a=r(170),n=r(7);(i=Object.create(i)).build=n(i.build,null,a),t.exports=i},169:function(t,e,r){var i=r(42),a=r(37),n=r(38),s=r(0),o=r(7),d=r(33),c=r(5),u=r(174);t.exports=function(t){t.params({partner:{fallback:o(d.val,d,"partner")}}),t.define("scribeItems",function(){return{}}),t.define("scribeNamespace",function(){return{client:"tfw"}}),t.define("scribeData",function(){return{widget_origin:n.rootDocumentLocation(),widget_frame:n.isFramed()&&n.currentDocumentLocation(),widget_partner:this.params.partner,widget_site_screen_name:u(d.val("site")),widget_site_user_id:c.asNumber(d.val("site:id")),widget_creator_screen_name:u(d.val("creator")),widget_creator_user_id:c.asNumber(d.val("creator:id"))}}),t.define("scribe",function(t,e,r){t=s.aug(this.scribeNamespace(),t||{}),e=s.aug(this.scribeData(),e||{}),i.scribe(t,e,!1,r)}),t.define("scribeInteraction",function(t,e,r){var i=a.extractTermsFromDOM(t.target);i.action=t.type,"url"===i.element&&(i.element=a.clickEventElement(t.target)),this.scribe(i,e,r)})}},170:function(t,e,r){var i=r(40),a=r(0),n=r(171);function s(){i.apply(this,arguments),this.Widget=this.Component}s.prototype=Object.create(i.prototype),a.aug(s.prototype,{factory:n,build:function(){return i.prototype.build.apply(this,arguments)},selectors:function(t){var e=this.Widget.prototype.selectors;t=t||{},this.Widget.prototype.selectors=a.aug({},t,e)}}),t.exports=s},171:function(t,e,r){var i=r(6),a=r(35),n=r(41),s=r(0),o=r(7),d=r(172),c="twitter-widget-";t.exports=function(){var t=n();function e(e,r){t.apply(this,arguments),this.id=c+d(),this.sandbox=r}return e.prototype=Object.create(t.prototype),s.aug(e.prototype,{selectors:{},hydrate:function(){return i.resolve()},prepForInsertion:function(){},render:function(){return i.resolve()},show:function(){return i.resolve()},resize:function(){return i.resolve()},select:function(t,e){return 1===arguments.length&&(e=t,t=this.el),t?(e=this.selectors[e]||e,s.toRealArray(t.querySelectorAll(e))):[]},selectOne:function(){return this.select.apply(this,arguments)[0]},selectLast:function(){return this.select.apply(this,arguments).pop()},on:function(t,e,r){var i,n=this.el;this.el&&(t=(t||"").split(/\s+/),2===arguments.length?r=e:i=e,i=this.selectors[i]||i,r=o(r,this),t.forEach(i?function(t){a.delegate(n,t,i,r)}:function(t){n.addEventListener(t,r,!1)}))}}),e}},172:function(t,e){var r=0;t.exports=function(){return String(r++)}},173:function(t,e,r){var i=r(5),a=r(0);t.exports=function(t){t.define("widgetDataAttributes",function(){return{}}),t.define("setDataAttributes",function(){var t=this.sandbox.sandboxEl;a.forIn(this.widgetDataAttributes(),function(e,r){i.hasValue(r)&&t.setAttribute("data-"+e,r)})}),t.after("render",function(){this.setDataAttributes()})}},174:function(t,e){t.exports=function(t){return t&&"@"===t[0]?t.substr(1):t}},175:function(t,e,r){var i=r(0);t.exports=function(t){return i.isType("string",t)}},179:function(t,e,r){var i=r(4),a=r(5),n=i.createElement("div");t.exports=function(t){return a.isNumber(t)&&(t+="px"),n.style.width="",n.style.width=t,n.style.width||null}},182:function(t,e){var r=/^(dark|light)$/;t.exports=function(t){return r.test(t)}},236:function(t,e,r){var i=r(6),a=r(46),n=r(20),s=r(168),o=r(18),d=r(19),c=r(0),u=r(11),l=r(37),f=r(36),p=r(237),h=r(238),m="Twitter Tweet",g=a.version;t.exports=s.couple(r(169),r(173),function(t){t.params(p),t.define("getUrlParams",function(t,e){var r=this.scribeData();return c.compact({dnt:d.enabled(),features:f.encodeFeatures(t),hideCard:this.params.hideCard,hideThread:this.params.hideThread,id:this.params.tweetId,lang:this.params.lang,embedId:this.id,theme:this.params.theme,partner:this.params.partner,widgetsVersion:g,width:this.params.width,origin:r.widget_origin,frame:r.widget_frame,sessionId:e,siteScreenName:r.widget_site_screen_name,siteUserId:r.widget_site_user_id,creatorScreenName:r.widget_creator_screen_name,creatorUserId:r.widget_creator_user_id})}),t.around("scribeItems",function(t){return c.aug(t(),l.formatHorizonTweetData(this.params.tweetId))}),t.around("scribeNamespace",function(t){return c.aug(t(),{page:"tweet"})}),t.around("scribeData",function(t){return c.aug(t(),{context:"horizon",widget_iframe_version:this.sandbox.iframeVersion})}),t.around("widgetDataAttributes",function(t){return c.aug({"tweet-id":this.params.tweetId},t())}),t.define("styleSandboxWrapper",function(t){var e=this;return o.write(function(){c.forIn(t,function(t,r){e._sandboxWrapperEl.style[t]=r})})}),t.override("render",function(){var t=this;return f.getHorizonSettings().then(function(e){var r=t.getUrlParams(e.features,e.sessionId),a=n.embedIframe(["Tweet"],e.features),s=u.url(a,r);return h(e.features,t.params.tweetId,e.sessionId),t.sandbox.setWaitToSwapUntilRendered(!0),i.all([t.sandbox.setTitle(m),t.styleSandboxWrapper({display:"flex",maxWidth:t.params.width,width:"100%",marginTop:"10px",marginBottom:"10px"}),t.sandbox.styleSelf({display:"block",flexGrow:"1"}),t.sandbox.loadDocument(s)])})}),t.after("render",function(){var t=this.sandbox;return t.getResultsPromise().then(function(){t.makeVisible()}).then(function(){return t.getRenderedPromise()})})})},237:function(t,e,r){var i=r(179),a=r(7),n=r(71),s=r(175),o=r(182),d=r(33),c=r(5),u={tweetId:{required:!0,validate:s},id:{validate:s},lang:{required:!0,transform:n.matchLanguage,fallback:"en"},width:{required:!0,fallback:"550px",validate:i,transform:i},theme:{fallback:[a(d.val,d,"widgets:theme"),"light"],validate:o},hideCard:{fallback:!1,transform:c.asBoolean},hideThread:{fallback:!1,transform:c.asBoolean},partner:{fallback:a(d.val,d,"partner")}};t.exports=u},238:function(t,e,r){var i=r(239),a=r(37),n="tfw_team_holdback_11929";t.exports=function(t,e,r){var s;t&&(s=t[n])&&s.bucket&&i(n,s.bucket,s.version,a.formatHorizonTweetData(e),r)}},239:function(t,e,r){var i=r(76);t.exports=function(t,e,r,a,n){var s={client:"tfw",page:"ddg",section:t,action:"experiment"},o={experiment_key:t,bucket:e,version:r,data:a},d={session_id:n};i.clientEvent(s,o,void 0,void 0,d)}},240:function(t,e,r){var i=r(175);t.exports=function(t){t.params({align:{required:!1},width:{required:!1},floatedWidth:{fallback:"350px",validate:i},centeredWidth:{fallback:"70%",validate:i}}),t.before("render",function(){var t,e,r,i,a=this.params.align;switch(a&&a.toLowerCase()){case"center":t=this.params.width||this.params.centeredWidth,e="auto",r="auto";break;case"left":t=this.params.width||this.params.floatedWidth,r="10px",i="left";break;case"right":t=this.params.width||this.params.floatedWidth,e="10px",i="right";break;default:return}return this.styleSandboxWrapper&&this._sandboxWrapperEl?this.styleSandboxWrapper({width:t,marginLeft:e,marginRight:r,cssFloat:i}):this.sandbox.styleSelf({width:t,marginLeft:e,marginRight:r,cssFloat:i})})}},89:function(t,e,r){var i=r(168);t.exports=i.build([r(236),r(240)])}}]);