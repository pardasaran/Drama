from files.helpers.const import SITE

if SITE in ('pcmemes.net', 'localhost'):
	import time
	from files.helpers.wrappers import auth_required
	from files.helpers.sanitize import sanitize
	from datetime import datetime
	from flask_socketio import SocketIO, emit
	from files.__main__ import app, limiter
	from flask import render_template
	import sys

	socketio = SocketIO(app, async_mode='gevent')
	typing = []
	online = []

	@app.get("/chat")
	@auth_required
	def chat( v):
		return render_template("chat.html", v=v)

	@socketio.on('speak')
	@limiter.limit("5/second;30/minute")
	@auth_required
	def speak(data, v):
		if not data: abort(403)

		data={
			"avatar": v.profile_url,
			"username":v.username,
			"namecolor":v.namecolor,
			"text":sanitize(data[:1000].strip()),
			"time": time.strftime("%d %b %Y at %H:%M:%S", time.gmtime(int(time.time())))
		}

		emit('speak', data, broadcast=True)
		return '', 204

	@socketio.on('connect')
	@auth_required
	def connect(v):
		if v.username not in online:
			online.append(v.username)
			emit("online", online, broadcast=True)

		emit('typing', typing)
		return '', 204

	@socketio.on('disconnect')
	@auth_required
	def disconnect(v):
		if v.username in online:
			online.remove(v.username)
			emit("online", online, broadcast=True)

		if v.username in typing: typing.remove(v.username)
		emit('typing', typing, broadcast=True)
		return '', 204

	@socketio.on('typing')
	@auth_required
	def typing_indicator(data, v):

		if data and v.username not in typing: typing.append(v.username)
		elif not data and v.username in typing: typing.remove(v.username)

		emit('typing', typing, broadcast=True)
		return '', 204