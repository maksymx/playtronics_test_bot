# -*- coding: utf-8 -*-
"""
A routing layer for the onboarding bot tutorial built using
[Slack's Events API](https://api.slack.com/events-api) in Python
"""
import os
import requests
import jinja2
import jinja2_sanic
from sanic import Sanic
from sanic.response import json, text

from bot import pyBot
from handler import event_handler

app = Sanic()

jinja2_sanic.setup(
    app,
    loader=jinja2.FileSystemLoader(searchpath="templates")
)


@app.listener('before_server_start')
async def start(app, loop):
    users = requests.get("https://slack.com/api/users.list", params={"token": os.environ.get("SLACK_BOT_TOKEN")}).json()
    if "members" in users:
        app.users = {member.pop("id"): member for member in users.get("members", [])}


@app.route("/")
async def test(request):
    return json({"hello": "world"})


@app.route("/stats", methods=["POST"])
def stats(request):
    return


@app.route("/moveuser", methods=["POST"])
def moveuser(request):
    form = request.form
    username = form.get("user_name")
    return json({"hello": "world"})


@app.route("/ban", methods=["POST"])
def moveuser(request):
    form = request.form
    return json({"hello": "world"})


@app.route("/install", methods=["GET"])
async def pre_install(request):
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = pyBot.oauth["client_id"]
    scope = pyBot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return jinja2_sanic.render_template("install.html", request, dict(client_id=client_id, scope=scope))


@app.route("/thanks", methods=["GET", "POST"])
async def thanks(request):
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    pyBot.auth(code_arg)
    return jinja2_sanic.render_template("thanks.html", request, {})


@app.route("/listening", methods=["GET", "POST"])
async def hears(request):
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    slack_event = request.json

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if "challenge" in slack_event:
        return json(slack_event["challenge"], 200)

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if pyBot.verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], pyBot.verification)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        text(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subscribed to
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        return event_handler(request, event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return text("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        workers=int(os.environ.get('WEB_CONCURRENCY', 1)),
        debug=bool(os.environ.get('DEBUG', ''))
    )
