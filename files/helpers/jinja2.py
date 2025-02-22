from files.__main__ import app, cache
from jinja2 import pass_context
from .get import *
from os import listdir, environ
from .const import * 
import time
from files.helpers.assetcache import assetcache_path
from files.helpers.wrappers import calc_users

@app.template_filter("post_embed")
def post_embed(id, v):
	p = get_post(id, v, graceful=True)
	
	if p: return render_template("submission_listing.html", listing=[p], v=v)
	return ''


@app.template_filter("asset")
@pass_context
def template_asset(ctx, asset_path):
	return assetcache_path(asset_path)


@app.template_filter("asset_siteimg")
def template_asset_siteimg(asset_path):
	# TODO: Add hashing for these using files.helpers.assetcache
	return f'/i/{SITE_NAME}/{asset_path}?v=3010'


@app.template_filter("timestamp")
def timestamp(timestamp):
	return make_age_string(timestamp)

@app.context_processor
def inject_constants():
	return {"environ":environ, "SITE":SITE, "SITE_NAME":SITE_NAME, "SITE_FULL":SITE_FULL,
			"AUTOJANNY_ID":AUTOJANNY_ID, "PUSHER_ID":PUSHER_ID, 
			"CC":CC, "CC_TITLE":CC_TITLE, "listdir":listdir, "AEVANN_ID":AEVANN_ID, 
			"PIZZASHILL_ID":PIZZASHILL_ID, "DEFAULT_COLOR":DEFAULT_COLOR, 
			"COLORS":COLORS, "time":time, "PERMS":PERMS, "FEATURES":FEATURES,
			"HOLE_NAME":HOLE_NAME, "HOLE_STYLE_FLAIR":HOLE_STYLE_FLAIR, "HOLE_REQUIRED":HOLE_REQUIRED,
			"GUMROAD_LINK":GUMROAD_LINK, "DEFAULT_THEME":DEFAULT_THEME, "DESCRIPTION":DESCRIPTION,
			"has_sidebar":has_sidebar, "has_logo":has_logo, "has_app":has_app,
			"FP":FP, "NOTIF_MODACTION_JL_MIN":NOTIF_MODACTION_JL_MIN, "cache":cache,
			"ONLINE_STR":ONLINE_STR, "patron":patron, "DUES":DUES,
			"SIDEBAR_THREAD":SIDEBAR_THREAD, "BANNER_THREAD":BANNER_THREAD,
			"BADGE_THREAD":BADGE_THREAD, "SNAPPY_THREAD":SNAPPY_THREAD,
			"KOFI_TOKEN":KOFI_TOKEN, "KOFI_LINK":KOFI_LINK,
			"approved_embed_hosts":approved_embed_hosts,
			"site_settings":app.config['SETTINGS'],
			"EMAIL":EMAIL, "calc_users":calc_users, "TELEGRAM_LINK":TELEGRAM_LINK,
			"EMAIL_REGEX_PATTERN":EMAIL_REGEX_PATTERN,
			"CONTENT_SECURITY_POLICY_DEFAULT":CONTENT_SECURITY_POLICY_DEFAULT,
			"CONTENT_SECURITY_POLICY_HOME":CONTENT_SECURITY_POLICY_HOME,
			"TRUESCORE_DONATE_LIMIT":TRUESCORE_DONATE_LIMIT,
			"BAN_EVASION_DOMAIN":BAN_EVASION_DOMAIN, "HOUSE_JOIN_COST":HOUSE_JOIN_COST, "HOUSE_SWITCH_COST":HOUSE_SWITCH_COST, "IMAGE_FORMATS":IMAGE_FORMATS
			}
