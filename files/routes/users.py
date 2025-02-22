from typing import Literal
import qrcode
import io
import time
import math
from files.classes.leaderboard import Leaderboard
from files.classes.views import *
from files.classes.transactions import *
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.const import *
from files.helpers.sorting_and_time import *
from files.helpers.actions import *
from files.mail import *
from flask import *
from files.__main__ import app, limiter, db_session
import sqlalchemy
from sqlalchemy.orm import aliased
from sqlalchemy import desc
from collections import Counter
import gevent
from sys import stdout
import os
import json
from .login import check_for_alts

def upvoters_downvoters(v, username, uid, cls, vote_cls, vote_dir, template, standalone):
	u = get_user(username, v=v, include_shadowbanned=False)
	if not u.is_visible_to(v): abort(403)
	if not (v.id == u.id or v.admin_level >= PERMS['USER_VOTERS_VISIBLE']): abort(403)
	id = u.id
	try:
		uid = int(uid)
	except:
		abort(404)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(cls).join(vote_cls).filter(cls.ghost == False, cls.is_banned == False, cls.deleted_utc == 0, vote_cls.vote_type==vote_dir, cls.author_id==id, vote_cls.user_id==uid).order_by(cls.created_utc.desc()).offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE + 1).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > PAGE_SIZE
	listing = listing[:PAGE_SIZE]

	if cls == Submission:
		listing = get_posts(listing, v=v)
	elif cls == Comment:
		listing = get_comments(listing, v=v)
	else:
		listing = []

	return render_template(template, next_exists=next_exists, listing=listing, page=page, v=v, standalone=standalone)

@app.get("/@<username>/upvoters/<uid>/posts")
@auth_required
def upvoters_posts(v, username, uid):
	return upvoters_downvoters(v, username, uid, Submission, Vote, 1, "voted_posts.html", None)


@app.get("/@<username>/upvoters/<uid>/comments")
@auth_required
def upvoters_comments(v, username, uid):
	return upvoters_downvoters(v, username, uid, Comment, CommentVote, 1, "voted_comments.html", True)


@app.get("/@<username>/downvoters/<uid>/posts")
@auth_required
def downvoters_posts(v, username, uid):
	return upvoters_downvoters(v, username, uid, Submission, Vote, -1, "voted_posts.html", None)


@app.get("/@<username>/downvoters/<uid>/comments")
@auth_required
def downvoters_comments(v, username, uid):
	return upvoters_downvoters(v, username, uid, Comment, CommentVote, -1, "voted_comments.html", True)

def upvoting_downvoting(v, username, uid, cls, vote_cls, vote_dir, template, standalone):
	u = get_user(username, v=v, include_shadowbanned=False)
	if not u.is_visible_to(v): abort(403)
	if not (v.id == u.id or v.admin_level >= PERMS['USER_VOTERS_VISIBLE']): abort(403)
	id = u.id
	try:
		uid = int(uid)
	except:
		abort(404)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(cls).join(vote_cls).filter(cls.ghost == False, cls.is_banned == False, cls.deleted_utc == 0, vote_cls.vote_type==vote_dir, vote_cls.user_id==id, cls.author_id==uid).order_by(cls.created_utc.desc()).offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE + 1).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > PAGE_SIZE
	listing = listing[:PAGE_SIZE]
	
	if cls == Submission:
		listing = get_posts(listing, v=v)
	elif cls == Comment:
		listing = get_comments(listing, v=v)
	else:
		listing = []

	return render_template(template, next_exists=next_exists, listing=listing, page=page, v=v, standalone=standalone)

@app.get("/@<username>/upvoting/<uid>/posts")
@auth_required
def upvoting_posts(v, username, uid):
	return upvoting_downvoting(v, username, uid, Submission, Vote, 1, "voted_posts.html", None)


@app.get("/@<username>/upvoting/<uid>/comments")
@auth_required
def upvoting_comments(v, username, uid):
	return upvoting_downvoting(v, username, uid, Comment, CommentVote, 1, "voted_comments.html", True)


@app.get("/@<username>/downvoting/<uid>/posts")
@auth_required
def downvoting_posts(v, username, uid):
	return upvoting_downvoting(v, username, uid, Submission, Vote, -1, "voted_posts.html", None)


@app.get("/@<username>/downvoting/<uid>/comments")
@auth_required
def downvoting_comments(v, username, uid):
	return upvoting_downvoting(v, username, uid, Comment, CommentVote, -1, "voted_comments.html", True)

def user_voted(v, username, cls, vote_cls, vote_dir, template, standalone):
	u = get_user(username, v=v, include_shadowbanned=False)
	if not u.is_visible_to(v): abort(403)
	if not (v.id == u.id or v.admin_level >= PERMS['USER_VOTERS_VISIBLE']): abort(403)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(cls).join(vote_cls).filter(
			cls.ghost == False,
			cls.is_banned == False,
			cls.deleted_utc == 0,
			cls.author_id != u.id,
			vote_cls.user_id == u.id,
			vote_cls.vote_type == vote_dir
		).order_by(cls.created_utc.desc()).offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE + 1).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > PAGE_SIZE
	listing = listing[:PAGE_SIZE]
	if cls == Submission:
		listing = get_posts(listing, v=v)
	elif cls == Comment:
		listing = get_comments(listing, v=v)
	else:
		listing = []

	return render_template(template, next_exists=next_exists, listing=listing, page=page, v=v, standalone=standalone)

@app.get("/@<username>/upvoted/posts")
@auth_required
def user_upvoted_posts(v, username):
	return user_voted(v, username, Submission, Vote, 1, "voted_posts.html", None)


@app.get("/@<username>/upvoted/comments")
@auth_required
def user_upvoted_comments(v, username):
	return user_voted(v, username, Comment, CommentVote, 1, "voted_comments.html", True)


@app.get("/grassed")
@auth_required
def grassed(v):
	users = g.db.query(User).filter(User.ban_reason.like('grass award used by @%'))
	if not v.can_see_shadowbanned:
		users = users.filter(User.shadowbanned == None)
	users = users.all()
	return render_template("grassed.html", v=v, users=users)

@app.get("/chuds")
@auth_required
def chuds(v):
	users = g.db.query(User).filter(User.agendaposter > 0)
	if not v.can_see_shadowbanned:
		users = users.filter(User.shadowbanned == None)
	users = users.order_by(User.username).all()
	return render_template("chuds.html", v=v, users=users)

def all_upvoters_downvoters(v, username, vote_dir, is_who_simps_hates):
	vote_str = 'votes'
	simps_haters = 'voters'
	vote_name = 'Neutral'
	if vote_dir == 1:
		vote_str = 'upvotes'
		simps_haters = 'simps for' if is_who_simps_hates else 'simps'
		vote_name = 'Up'
	elif vote_dir == -1:
		vote_str = 'downvotes'
		simps_haters = 'hates' if is_who_simps_hates else 'haters'
		vote_name = 'Down'

	id = get_user(username, v=v, include_shadowbanned=False).id
	if not (v.id == id or v.admin_level >= PERMS['USER_VOTERS_VISIBLE']):
		abort(403)
	votes = []
	votes2 = []
	if is_who_simps_hates:
		votes = g.db.query(Submission.author_id, func.count(Submission.author_id)).join(Vote).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==vote_dir, Vote.user_id==id).group_by(Submission.author_id).order_by(func.count(Submission.author_id).desc()).all()
		votes2 = g.db.query(Comment.author_id, func.count(Comment.author_id)).join(CommentVote).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==vote_dir, CommentVote.user_id==id).group_by(Comment.author_id).order_by(func.count(Comment.author_id).desc()).all()
	else:
		votes = g.db.query(Vote.user_id, func.count(Vote.user_id)).join(Submission).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==vote_dir, Submission.author_id==id).group_by(Vote.user_id).order_by(func.count(Vote.user_id).desc()).all()
		votes2 = g.db.query(CommentVote.user_id, func.count(CommentVote.user_id)).join(Comment).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==vote_dir, Comment.author_id==id).group_by(CommentVote.user_id).order_by(func.count(CommentVote.user_id).desc()).all()
	votes = Counter(dict(votes)) + Counter(dict(votes2))
	total = sum(votes.values())	
	users = g.db.query(User).filter(User.id.in_(votes.keys())).all()
	users2 = []
	for user in users: 
		users2.append((user, votes[user.id]))
	users = sorted(users2, key=lambda x: x[1], reverse=True)

	try:
		pos = [x[0].id for x in users].index(v.id)
		pos = (pos+1, users[pos][1])
	except: pos = (len(users)+1, 0)

	received_given = 'given' if is_who_simps_hates else 'received'
	if total == 1: vote_str = vote_str[:-1] # we want to unpluralize if only 1 vote
	total = f'{total} {vote_str} {received_given}'

	name2 = f'Who @{username} {simps_haters}' if is_who_simps_hates else f'@{username} biggest {simps_haters}'

	return render_template("voters.html", v=v, users=users[:PAGE_SIZE], pos=pos, name=vote_name, name2=name2, total=total)

@app.get("/@<username>/upvoters")
@auth_required
def upvoters(v, username):
	return all_upvoters_downvoters(v, username, 1, False)

@app.get("/@<username>/downvoters")
@auth_required
def downvoters(v, username):
	return all_upvoters_downvoters(v, username, -1, False)

@app.get("/@<username>/upvoting")
@auth_required
def upvoting(v, username):
	return all_upvoters_downvoters(v, username, 1, True)

@app.get("/@<username>/downvoting")
@auth_required
def downvoting(v, username):
	return all_upvoters_downvoters(v, username, -1, True)

@app.post("/@<username>/suicide")
@limiter.limit("1/second;5/day")
@limiter.limit("1/second;5/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
@feature_required('USERS_SUICIDE')
def suicide(v, username):
	

	user = get_user(username)
	suicide = f"Hi there,\n\nA [concerned user](/id/{v.id}) reached out to us about you.\n\nWhen you're in the middle of something painful, it may feel like you don't have a lot of options. But whatever you're going through, you deserve help and there are people who are here for you.\n\nThere are resources available in your area that are free, confidential, and available 24/7:\n\n- Call, Text, or Chat with Canada's [Crisis Services Canada](https://www.crisisservicescanada.ca/en/)\n- Call, Email, or Visit the UK's [Samaritans](https://www.samaritans.org/)\n- Text CHAT to America's [Crisis Text Line](https://www.crisistextline.org/) at 741741.\nIf you don't see a resource in your area above, the moderators keep a comprehensive list of resources and hotlines for people organized by location. Find Someone Now\n\nIf you think you may be depressed or struggling in another way, don't ignore it or brush it aside. Take yourself and your feelings seriously, and reach out to someone.\n\nIt may not feel like it, but you have options. There are people available to listen to you, and ways to move forward.\n\nYour fellow users care about you and there are people who want to help."
	if not v.shadowbanned:
		send_notification(user.id, suicide)
	return {"message": f"Help message sent to @{user.username}"}


@app.get("/@<username>/coins")
@auth_required
def get_coins(v, username):
	user = get_user(username, v=v, include_shadowbanned=False)
	return {"coins": user.coins}

def transfer_currency(v:User, username:str, currency_name:Literal['coins', 'procoins'], apply_tax:bool):
	MIN_CURRENCY_TRANSFER = 100
	TAX_PCT = 0.03
	friendly_currency_name = 'marseybux' if currency_name == 'procoins' else 'coins'
	receiver = get_user(username, v=v, include_shadowbanned=False)
	if receiver.id == v.id: abort(400, f"You can't transfer {friendly_currency_name} to yourself!")
	amount = request.values.get("amount", "").strip()
	amount = int(amount) if amount.isdigit() else None

	if amount is None or amount <= 0: abort(400, f"Invalid number of {friendly_currency_name}")
	if amount < MIN_CURRENCY_TRANSFER: abort(400, f"You have to gift at least {MIN_CURRENCY_TRANSFER} {friendly_currency_name}")
	tax = 0
	if apply_tax and not v.patron and not receiver.patron and not v.alts_patron and not receiver.alts_patron:
		tax = math.ceil(amount*TAX_PCT)

	reason = request.values.get("reason", "").strip()
	log_message = f"@{v.username} has transferred {amount} {friendly_currency_name} to @{receiver.username}"
	notif_text = f":marseycapitalistmanlet: @{v.username} has gifted you {amount-tax} {friendly_currency_name}!"

	if reason:
		if len(reason) > TRANSFER_MESSAGE_LENGTH_LIMIT: abort(400, f"Reason is too long, max {TRANSFER_MESSAGE_LENGTH_LIMIT} characters")
		notif_text += f"\n\n> {reason}"
		log_message += f"\n\n> {reason}"

	if not v.charge_account(currency_name, amount):
		abort(400, f"You don't have enough {friendly_currency_name}")

	if not v.shadowbanned:
		if currency_name == 'procoins':
			receiver.procoins += amount - tax
		elif currency_name == 'coins':
			receiver.coins += amount - tax
		else:
			raise ValueError(f"Invalid currency '{currency_name}' got when transferring {amount} from {v.id} to {receiver.id}")
		g.db.add(receiver)
		send_repeatable_notification(GIFT_NOTIF_ID, log_message)
		send_repeatable_notification(receiver.id, notif_text)
	g.db.add(v)
	return {"message": f"{amount - tax} {friendly_currency_name} have been transferred to @{receiver.username}"}
	
@app.post("/@<username>/transfer_coins")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@is_not_permabanned
def transfer_coins(v, username):
	return transfer_currency(v, username, 'coins', True)

@app.post("/@<username>/transfer_bux")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@is_not_permabanned
@feature_required('PROCOINS')
def transfer_bux(v, username):
	return transfer_currency(v, username, 'procoins', False)

@app.get("/leaderboard")
@auth_required
def leaderboard(v):
	users = g.db.query(User)
	if not v.can_see_shadowbanned:
		users = users.filter(User.shadowbanned == None)

	coins = Leaderboard("Coins", "coins", "coins", "Coins", None, Leaderboard.get_simple_lb, User.coins, v, lambda u:u.coins, g.db, users)
	subscribers = Leaderboard("Followers", "followers", "followers", "Followers", None, Leaderboard.get_simple_lb, User.stored_subscriber_count, v, lambda u:u.stored_subscriber_count, g.db, users)
	posts = Leaderboard("Posts", "post count", "posts", "Posts", "", Leaderboard.get_simple_lb, User.post_count, v, lambda u:u.post_count, g.db, users)
	comments = Leaderboard("Comments", "comment count", "comments", "Comments", "comments", Leaderboard.get_simple_lb, User.comment_count, v, lambda u:u.comment_count, g.db, users)
	received_awards = Leaderboard("Awards", "received awards", "awards", "Awards", None, Leaderboard.get_simple_lb, User.received_award_count, v, lambda u:u.received_award_count, g.db, users)
	coins_spent = Leaderboard("Spent in shop", "coins spent in shop", "spent", "Coins", None, Leaderboard.get_simple_lb, User.coins_spent, v, lambda u:u.coins_spent, g.db, users)
	truecoins = Leaderboard("Truescore", "truescore", "truescore", "Truescore", None, Leaderboard.get_simple_lb, User.truecoins, v, lambda u:u.truecoins, g.db, users)

	badges = Leaderboard("Badges", "badges", "badges", "Badges", None, Leaderboard.get_badge_marsey_lb, Badge.user_id, v, None, g.db, None)
	marseys = Leaderboard("Marseys", "Marseys made", "marseys", "Marseys", None, Leaderboard.get_badge_marsey_lb, Marsey.author_id, v, None, g.db, None) if SITE_NAME == 'rDrama' else None

	blocks = Leaderboard("Blocked", "most blocked", "blocked", "Blocked By", "blockers", Leaderboard.get_blockers_lb, UserBlock.target_id, v, None, g.db, None)

	owned_hats = Leaderboard("Owned hats", "owned hats", "owned-hats", "Owned Hats", None, Leaderboard.get_hat_lb, User.owned_hats, v, None, g.db, None)
	designed_hats = Leaderboard("Designed hats", "designed hats", "designed-hats", "Designed Hats", None, Leaderboard.get_hat_lb, User.designed_hats, v, None, g.db, None)	

	leaderboards = [coins, coins_spent, truecoins, subscribers, posts, comments, received_awards, badges, marseys, blocks, owned_hats, designed_hats]

	return render_template("leaderboard.html", v=v, leaderboards=leaderboards)

@app.get("/<id>/css")
def get_css(id):
	try: id = int(id)
	except: abort(404)

	css = g.db.query(User.css).filter_by(id=id).one_or_none()
	if not css: abort(404)

	resp = make_response(css[0] or "")
	resp.headers["Content-Type"] = "text/css"
	return resp

@app.get("/<id>/profilecss")
def get_profilecss(id):
	try: id = int(id)
	except: abort(404)

	css = g.db.query(User.profilecss).filter_by(id=id).one_or_none()
	if not css: abort(404)

	resp = make_response(css[0] or "")
	resp.headers["Content-Type"] = "text/css"
	return resp

@app.get("/@<username>/song")
def usersong(username):
	user = get_user(username)
	if user.song: return redirect(f"/song/{user.song}.mp3")
	else: abort(404)

@app.get("/song/<song>")
@app.get("/static/song/<song>")
def song(song):
	resp = make_response(send_from_directory('/songs', song))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	return resp

@app.post("/subscribe/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def subscribe(v, post_id):
	existing = g.db.query(Subscription).filter_by(user_id=v.id, submission_id=post_id).one_or_none()
	if not existing:
		new_sub = Subscription(user_id=v.id, submission_id=post_id)
		g.db.add(new_sub)
	return {"message": "Subscribed to post successfully!"}
	
@app.post("/unsubscribe/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def unsubscribe(v, post_id):
	existing = g.db.query(Subscription).filter_by(user_id=v.id, submission_id=post_id).one_or_none()
	if existing:
		g.db.delete(existing)
	return {"message": "Unsubscribed from post successfully!"}

@app.post("/@<username>/message")
@limiter.limit("1/second;10/minute;20/hour;50/day")
@limiter.limit("1/second;10/minute;20/hour;50/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@is_not_permabanned
def message2(v, username):
	user = get_user(username, v=v, include_blocks=True, include_shadowbanned=False)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		abort(403, "You're blocking this user.")

	if v.admin_level <= PERMS['MESSAGE_BLOCKED_USERS'] and hasattr(user, 'is_blocked') and user.is_blocked:
		abort(403, "This user is blocking you.")

	message = sanitize_raw_body(request.values.get("message"), False)
	if not message: abort(400, "Message is empty!")
	if 'linkedin.com' in message: abort(403, "This domain 'linkedin.com' is banned.")
	if v.id != AEVANN_ID and ('discord.gg' in message or 'discord.com' in message or 'discordapp.com' in message):
		abort(403, "Stop grooming!")

	body_html = sanitize(message)

	if not (SITE.startswith('rdrama.') and user.id == BLACKJACKBTZ_ID):
		existing = g.db.query(Comment.id).filter(Comment.author_id == v.id,
																Comment.sentto == user.id,
																Comment.body_html == body_html,
																).first()

		if existing: abort(403, "Message already exists.")

	c = Comment(author_id=v.id,
						parent_submission=None,
						level=1,
						sentto=user.id,
						body_html=body_html
						)
	g.db.add(c)
	g.db.flush()
	execute_blackjack(v, c, c.body_html, 'message')
	c.top_comment_id = c.id

	if user.id not in bots:
		notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=user.id).one_or_none()
		if not notif:
			notif = Notification(comment_id=c.id, user_id=user.id)
			g.db.add(notif)


	if PUSHER_ID != 'blahblahblah' and not v.shadowbanned:
		interests = f'{SITE}{user.id}'

		title = f'New message from @{username}'

		if len(message) > 500: notifbody = message[:500] + '...'
		else: notifbody = message

		url = f'{SITE_FULL}/notifications/messages'

		gevent.spawn(pusher_thread, interests, title, notifbody, url)

	return {"message": "Message sent!"}


@app.post("/reply")
@limiter.limit("1/second;6/minute;50/hour;200/day")
@limiter.limit("1/second;6/minute;50/hour;200/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def messagereply(v):
	body = sanitize_raw_body(request.values.get("body"), False)
	if not body and not request.files.get("file"): abort(400, "Message is empty!")

	if 'linkedin.com' in body: abort(403, "This domain 'linkedin.com' is banned")

	if v.id != AEVANN_ID and ('discord.gg' in body or 'discord.com' in body or 'discordapp.com' in body):
		abort(403, "Stop grooming!")

	id = request.values.get("parent_id")
	parent = get_comment(id, v=v)
	user_id = parent.author.id

	if v.is_suspended_permanently and parent.sentto != 2:
		abort(400, "You are permabanned and may not reply to messages.")
	elif v.is_muted and parent.sentto == 2:
		abort(400, "You are forbidden from replying to modmail.")

	if parent.sentto == 2: user_id = None
	elif v.id == user_id: user_id = parent.sentto

	if user_id:
		user = get_account(user_id, v=v, include_blocks=True)
		if hasattr(user, 'is_blocking') and user.is_blocking:
			abort(403, "You're blocking this user.")
		elif (v.admin_level <= PERMS['MESSAGE_BLOCKED_USERS']
				and hasattr(user, 'is_blocked') and user.is_blocked):
			abort(403, "You're blocked by this user.")

	if parent.sentto == 2:
		body += process_files()

	body = body.strip()

	body_html = sanitize(body)

	c = Comment(author_id=v.id,
							parent_submission=None,
							parent_comment_id=id,
							top_comment_id=parent.top_comment_id,
							level=parent.level + 1,
							sentto=user_id,
							body_html=body_html,
							)
	g.db.add(c)
	g.db.flush()
	execute_blackjack(v, c, c.body_html, 'message')

	if user_id and user_id not in (v.id, 2, bots):
		notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=user_id).one_or_none()
		if not notif:
			notif = Notification(comment_id=c.id, user_id=user_id)
			g.db.add(notif)

		if PUSHER_ID != 'blahblahblah' and not v.shadowbanned:
			interests = f'{SITE}{user_id}'

			title = f'New message from @{v.username}'

			if len(body) > 500: notifbody = body[:500] + '...'
			else: notifbody = body

			url = f'{SITE_FULL}/notifications/messages'

			gevent.spawn(pusher_thread, interests, title, notifbody, url)



	if c.top_comment.sentto == 2:
		admins = g.db.query(User.id).filter(User.admin_level >= PERMS['NOTIFICATIONS_MODMAIL'], User.id != v.id)
		if SITE == 'watchpeopledie.tv':
			admins = admins.filter(User.id != AEVANN_ID)

		admins = [x[0] for x in admins.all()]

		if parent.author.id not in admins:
			admins.append(parent.author.id)

		for admin in admins:
			notif = Notification(comment_id=c.id, user_id=admin)
			g.db.add(notif)

		ids = [c.top_comment.id] + [x.id for x in c.top_comment.replies(sort="old", v=v)]
		notifications = g.db.query(Notification).filter(Notification.comment_id.in_(ids), Notification.user_id.in_(admins))
		for n in notifications:
			g.db.delete(n)


	return {"comment": render_template("comments.html", v=v, comments=[c])}

@app.get("/2faqr/<secret>")
@auth_required
def mfa_qr(secret, v):
	x = pyotp.TOTP(secret)
	qr = qrcode.QRCode(
		error_correction=qrcode.constants.ERROR_CORRECT_L
	)
	qr.add_data(x.provisioning_uri(v.username, issuer_name=SITE_NAME))
	img = qr.make_image(fill_color="#000000", back_color="white")

	mem = io.BytesIO()

	img.save(mem, format="PNG")
	mem.seek(0, 0)

	return send_file(mem, mimetype="image/png", as_attachment=False)


@app.get("/is_available/<name>")
@limiter.limit("100/day")
def is_available(name):

	name=name.strip()

	if len(name)<3 or len(name)>25:
		return {name:False}
		
	name2 = name.replace('\\', '').replace('_','\_').replace('%','')

	x = g.db.query(User).filter(
		or_(
			User.username.ilike(name2),
			User.original_username.ilike(name2)
			)
		).one_or_none()

	if x:
		return {name: False}
	else:
		return {name: True}

@app.get("/id/<id>")
def user_id(id):
	user = get_account(id)
	return redirect(user.url)
		
@app.get("/u/<username>")
@auth_required
def redditor_moment_redirect(username, v):
	return redirect(f"/@{username}")

@app.get("/@<username>/followers")
@auth_required
def followers(username, v):
	u = get_user(username, v=v, include_shadowbanned=False)
	if u.id == CARP_ID and SITE == 'watchpeopledie.tv': abort(403)

	if not (v.id == u.id or v.admin_level >= PERMS['USER_FOLLOWS_VISIBLE']):
		abort(403)

	users = g.db.query(Follow, User).join(Follow, Follow.target_id == u.id) \
		.filter(Follow.user_id == User.id) \
		.order_by(Follow.created_utc).all()
	return render_template("followers.html", v=v, u=u, users=users)

@app.get("/@<username>/blockers")
@auth_required
def blockers(username, v):
	u = get_user(username, v=v, include_shadowbanned=False)

	users = g.db.query(UserBlock, User).join(UserBlock, UserBlock.target_id == u.id) \
		.filter(UserBlock.user_id == User.id) \
		.order_by(UserBlock.created_utc).all()
	return render_template("blockers.html", v=v, u=u, users=users)

@app.get("/@<username>/following")
@auth_required
def following(username, v):
	u = get_user(username, v=v, include_shadowbanned=False)
	if not (v.id == u.id or v.admin_level >= PERMS['USER_FOLLOWS_VISIBLE']):
		abort(403)

	users = g.db.query(User).join(Follow, Follow.user_id == u.id) \
		.filter(Follow.target_id == User.id) \
		.order_by(Follow.created_utc).all()
	return render_template("following.html", v=v, u=u, users=users)

@app.get("/views")
@auth_required
def visitors(v):
	if not v.viewers_recorded:
		return render_template("errors/patron.html", v=v)
	viewers=sorted(v.viewers, key = lambda x: x.last_view_utc, reverse=True)
	return render_template("viewers.html", v=v, viewers=viewers)


@app.get("/@<username>")
@app.get("/@<username>.json")
@app.get("/logged_out/@<username>")
@auth_desired_with_logingate
def u_username(username, v=None):
	u = get_user(username, v=v, include_blocks=True, include_shadowbanned=False)
	if username != u.username:
		return redirect(SITE_FULL + request.full_path.replace(username, u.username))
	is_following = v and u.has_follower(v)

	if v and v.id not in (u.id, DAD_ID) and u.viewers_recorded:
		g.db.flush()
		view = g.db.query(ViewerRelationship).filter_by(viewer_id=v.id, user_id=u.id).one_or_none()

		if view: view.last_view_utc = int(time.time())
		else: view = ViewerRelationship(viewer_id=v.id, user_id=u.id)

		g.db.add(view)
		g.db.commit()

		
	if not u.is_visible_to(v):
		if g.is_api_or_xhr or request.path.endswith(".json"):
			abort(403, "This userpage is private")
		return render_template("userpage_private.html", u=u, v=v, is_following=is_following), 403

	
	if v and hasattr(u, 'is_blocking') and u.is_blocking:
		if g.is_api_or_xhr or request.path.endswith(".json"):
			abort(403, f"You are blocking @{u.username}.")
		return render_template("userpage_blocking.html", u=u, v=v), 403


	sort = request.values.get("sort", "new")
	t = request.values.get("t", "all")
	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	ids = u.userpagelisting(site=SITE, v=v, page=page, sort=sort, t=t)

	next_exists = (len(ids) > PAGE_SIZE)
	ids = ids[:PAGE_SIZE]

	if page == 1:
		sticky = []
		sticky = g.db.query(Submission).filter_by(is_pinned=True, author_id=u.id, is_banned=False).all()
		if sticky:
			for p in sticky:
				ids = [p.id] + ids

	listing = get_posts(ids, v=v)

	if u.unban_utc:
		if (v and v.client) or request.path.endswith(".json"):
			return {"data": [x.json for x in listing]}
		
		return render_template("userpage.html",
												unban=u.unban_string,
												u=u,
												v=v,
												listing=listing,
												page=page,
												sort=sort,
												t=t,
												next_exists=next_exists,
												is_following=is_following)

	if (v and v.client) or request.path.endswith(".json"):
		return {"data": [x.json for x in listing]}
	
	return render_template("userpage.html",
									u=u,
									v=v,
									listing=listing,
									page=page,
									sort=sort,
									t=t,
									next_exists=next_exists,
									is_following=is_following)


@app.get("/@<username>/comments")
@app.get("/@<username>/comments.json")
@app.get("/logged_out/@<username>/comments")
@auth_desired_with_logingate
def u_username_comments(username, v=None):
	u = get_user(username, v=v, include_blocks=True, include_shadowbanned=False)
	if username != u.username:
		return redirect(f"/@{u.username}/comments")
	is_following = v and u.has_follower(v)

	if not u.is_visible_to(v):
		if g.is_api_or_xhr or request.path.endswith(".json"):
			abort(403, "This userpage is private")
		return render_template("userpage_private.html", u=u, v=v, is_following=is_following), 403

	if v and hasattr(u, 'is_blocking') and u.is_blocking:
		if g.is_api_or_xhr or request.path.endswith(".json"):
			abort(403, f"You are blocking @{u.username}.")
		return render_template("userpage_blocking.html", u=u, v=v), 403

	try: page = max(int(request.values.get("page", "1")), 1)
	except: page = 1
	
	sort=request.values.get("sort","new")
	t=request.values.get("t","all")

	comment_post_author = aliased(User)
	comments = g.db.query(Comment.id) \
				.join(Comment.post) \
				.join(comment_post_author, Submission.author) \
				.filter(
					Comment.author_id == u.id,
					Comment.parent_submission != None
				)

	if not v or (v.id != u.id and v.admin_level < PERMS['POST_COMMENT_MODERATION']):
		comments = comments.filter(
			Comment.is_banned == False,
			Comment.ghost == False,
			Comment.deleted_utc == 0
		)

	comments = apply_time_filter(t, comments, Comment)

	comments = sort_objects(sort, comments, Comment,
		include_shadowbanned=(v and v.can_see_shadowbanned))

	comments = comments.offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE+1).all()
	ids = [x.id for x in comments]

	next_exists = (len(ids) > PAGE_SIZE)
	ids = ids[:PAGE_SIZE]

	listing = get_comments(ids, v=v)

	if (v and v.client) or request.path.endswith(".json"):
		return {"data": [c.json for c in listing]}
	
	return render_template("userpage_comments.html", u=u, v=v, listing=listing, page=page, sort=sort, t=t,next_exists=next_exists, is_following=is_following, standalone=True)


@app.get("/@<username>/info")
@auth_required
def u_username_info(username, v=None):

	user=get_user(username, v=v, include_blocks=True, include_shadowbanned=False)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		abort(401, "You're blocking this user.")
	elif hasattr(user, 'is_blocked') and user.is_blocked:
		abort(403, "This user is blocking you.")

	return user.json

@app.get("/<id>/info")
@auth_required
def u_user_id_info(id, v=None):

	user=get_account(id, v=v, include_blocks=True, include_shadowbanned=False)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		abort(403, "You're blocking this user.")
	elif hasattr(user, 'is_blocked') and user.is_blocked:
		abort(403, "This user is blocking you.")

	return user.json

@app.post("/follow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def follow_user(username, v):

	target = get_user(username, v=v, include_shadowbanned=False)

	if target.id==v.id:
		abort(400, "You can't follow yourself!")

	if target.is_nofollow:
		abort(403, "This user has disallowed other users from following them!")

	if g.db.query(Follow).filter_by(user_id=v.id, target_id=target.id).one_or_none():
		return {"message": f"@{target.username} has been followed!"}

	new_follow = Follow(user_id=v.id, target_id=target.id)
	g.db.add(new_follow)

	g.db.flush()
	target.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=target.id).count()
	g.db.add(target)

	if not v.shadowbanned:
		send_notification(target.id, f"@{v.username} has followed you!")


	return {"message": f"@{target.username} has been followed!"}

@app.post("/unfollow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def unfollow_user(username, v):

	target = get_user(username)

	if target.fish:
		if not v.shadowbanned:
			send_notification(target.id, f"@{v.username} has tried to unfollow you and failed because of your fish award!")
		abort(400, "You can't unfollow this user!")

	follow = g.db.query(Follow).filter_by(user_id=v.id, target_id=target.id).one_or_none()

	if follow:
		g.db.delete(follow)
		
		g.db.flush()
		target.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=target.id).count()
		g.db.add(target)

		if not v.shadowbanned:
			send_notification(target.id, f"@{v.username} has unfollowed you!")


	return {"message": f"@{target.username} has been unfollowed!"}

@app.post("/remove_follow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{SITE}-{session.get("lo_user")}')
@auth_required
def remove_follow(username, v):
	target = get_user(username)

	follow = g.db.query(Follow).filter_by(user_id=target.id, target_id=v.id).one_or_none()

	if not follow: return {"message": f"@{target.username} has been removed as a follower!"}

	g.db.delete(follow)
	
	g.db.flush()
	v.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=v.id).count()
	g.db.add(v)

	send_repeatable_notification(target.id, f"@{v.username} has removed your follow!")


	return {"message": f"@{target.username} has been removed as a follower!"}

@app.get("/pp/<id>")
@app.get("/uid/<id>/pic")
@app.get("/uid/<id>/pic/profile")
@app.get("/logged_out/pp/<id>")
@app.get("/logged_out/uid/<id>/pic")
@app.get("/logged_out/uid/<id>/pic/profile")
@cache.memoize(timeout=86400)
@limiter.exempt
def user_profile_uid(id):
	try: id = int(id)
	except:
		try: id = int(id, 36)
		except: abort(404)

	x=get_account(id)
	return redirect(x.profile_url)

@app.get("/@<username>/pic")
@cache.memoize(timeout=86400)
@limiter.exempt
def user_profile_name(username):
	x = get_user(username)
	return redirect(x.profile_url)

def get_saves_and_subscribes(v, template, relationship_cls, page:int, standalone=False):
	PAGE_SIZE = 25
	if relationship_cls in [SaveRelationship, Subscription]:
		query = relationship_cls.submission_id
		join = relationship_cls.post
		cls = Submission
	elif relationship_cls is CommentSaveRelationship:
		query = relationship_cls.comment_id
		join = relationship_cls.comment
		cls = Comment
	else:
		raise TypeError("Relationships supported is SaveRelationship, Subscription, CommentSaveRelationship")
	ids = [x[0] for x in g.db.query(query).join(join).filter(relationship_cls.user_id == v.id).order_by(cls.created_utc.desc()).offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE + 1).all()]
	next_exists = len(ids) > PAGE_SIZE
	ids = ids[:PAGE_SIZE]
	if cls is Submission:
		listing = get_posts(ids, v=v)
	elif cls is Comment:
		listing = get_comments(ids, v=v)
	else:
		raise TypeError("Only supports Submissions and Comments. This is probably the result of a bug with *this* function")
	if v.client: return {"data": [x.json for x in listing]}
	return render_template(template, u=v, v=v, listing=listing, page=page, next_exists=next_exists, standalone=standalone)

@app.get("/@<username>/saved/posts")
@auth_required
def saved_posts(v, username):
	page = max(1, int(request.values.get("page", 1)))
	return get_saves_and_subscribes(v, "userpage.html", SaveRelationship, page, False)

@app.get("/@<username>/saved/comments")
@auth_required
def saved_comments(v, username):
	page = max(1, int(request.values.get("page", 1)))
	return get_saves_and_subscribes(v, "userpage_comments.html", CommentSaveRelationship, page, True)

@app.get("/@<username>/subscribed/posts")
@auth_required
def subscribed_posts(v, username):
	page = max(1, int(request.values.get("page", 1)))
	return get_saves_and_subscribes(v, "userpage.html", Subscription, page, False)

@app.post("/fp/<fp>")
@auth_required
def fp(v, fp):
	v.fp = fp
	users = g.db.query(User).filter(User.fp == fp, User.id != v.id).all()
	if users: print(f'{v.username}: fp', flush=True)
	if v.email and v.is_activated:
		alts = g.db.query(User).filter(User.email == v.email, User.is_activated, User.id != v.id).all()
		if alts:
			print(f'{v.username}: email', flush=True)
			users += alts
	for u in users:
		li = [v.id, u.id]
		existing = g.db.query(Alt).filter(Alt.user1.in_(li), Alt.user2.in_(li)).one_or_none()
		if existing: continue
		new_alt = Alt(user1=v.id, user2=u.id)
		g.db.add(new_alt)
		g.db.flush()
		print(v.username + ' + ' + u.username, flush=True)
		check_for_alts(v)
	g.db.add(v)
	return '', 204

@app.get("/toggle_pins/<sort>")
def toggle_pins(sort):
	if sort == 'hot': default = True
	else: default = False

	pins = session.get(sort, default)
	session[sort] = not pins

	if is_site_url(request.referrer):
		return redirect(request.referrer)
	return redirect('/')


@app.get("/badge_owners/<bid>")
@auth_required
def bid_list(v, bid):

	try: bid = int(bid)
	except: abort(400)

	try: page = int(request.values.get("page", 1))
	except: page = 1

	users = g.db.query(User).join(User.badges).filter(Badge.badge_id==bid).offset(PAGE_SIZE * (page - 1)).limit(PAGE_SIZE + 1).all()

	next_exists = (len(users) > PAGE_SIZE)
	users = users[:PAGE_SIZE]

	return render_template("user_cards.html",
						v=v,
						users=users,
						next_exists=next_exists,
						page=page,
						)


@app.post("/kofi")
def kofi():
	data = json.loads(request.values['data'])
	verification_token = data['verification_token']
	if verification_token != KOFI_TOKEN: abort(400)

	id = data['kofi_transaction_id']
	created_utc = int(time.mktime(time.strptime(data['timestamp'].split('.')[0], "%Y-%m-%dT%H:%M:%SZ")))
	type = data['type']
	amount = 0
	try:
		amount = int(float(data['amount']))
	except:
		abort(400, 'invalid amount')
	email = data['email']

	transaction = Transaction(
		id=id,
		created_utc=created_utc,
		type=type,
		amount=amount,
		email=email
	)

	g.db.add(transaction)
	return ''

kofi_tiers={
	5: 1,
	10: 2,
	20: 3,
	50: 4,
	100: 5,
	200: 6
	}

@app.post("/settings/kofi")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def settings_kofi(v):
	if not (v.email and v.is_activated):
		abort(400, f"You must have a verified email to verify {patron} status and claim your rewards!")

	transaction = g.db.query(Transaction).filter_by(email=v.email).order_by(Transaction.created_utc.desc()).first()

	if not transaction:
		abort(404, "Email not found")

	if transaction.claimed:
		abort(400, f"{patron} rewards already claimed")

	tier = kofi_tiers[transaction.amount]

	v.patron = tier

	procoins = procoins_li[tier]

	v.procoins += procoins
	send_repeatable_notification(v.id, f"You have received {procoins} Marseybux! You can use them to buy awards in the [shop](/shop).")

	g.db.add(v)

	badge_grant(badge_id=20+tier, user=v)

	transaction.claimed = True

	g.db.add(transaction)

	return {"message": f"{patron} rewards claimed!"}
