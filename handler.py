from sanic.response import text

from bot import pyBot, slack


def _process_messages(slack_event):
    # ============== Share Message Events ============= #
    # If the user has shared the onboarding message, the event type will be
    # message. We'll also need to check that this is a message that has been
    # shared by looking into the attachments for "is_shared".
    team_id = slack_event["team_id"]
    if slack_event["event"].get("attachments"):
        user_id = slack_event["event"].get("user")
        if slack_event["event"]["attachments"][0].get("is_share"):
            # Update the onboarding message and check off "Share this Message"
            pyBot.update_share(team_id, user_id)
            return text("Welcome message updates with shared message",
                        200, )
    else:
        user_id = slack_event["event"].get("user")
        if user_id:
            slack.api_call("chat.postMessage",
                                  channel=slack_event["event"]["channel"],
                                  username="Slackbot Admin1",
                                  icon_emoji=":robot_face:",
                                  text="ololo",
                                  attachments=[]
                                  )
        return text("olololo")


def _process_team_join(slack_event):
    # ================ Team Join Events =============== #
    # When the user first joins a team, the type of event will be team_join
    team_id = slack_event["team_id"]
    user_id = slack_event["event"]["user"]["id"]
    # Send the onboarding message
    pyBot.onboarding_message(team_id, user_id)
    return text("Welcome Message Sent", 200, )


def _process_reaction_added(slack_event):
    # ============= Reaction Added Events ============= #
    # If the user has added an emoji reaction to the onboarding message
    team_id = slack_event["team_id"]
    user_id = slack_event["event"]["user"]
    # Update the onboarding message
    pyBot.update_emoji(team_id, user_id)
    return text("Welcome message updates with reactji", 200, )


def _process_pin_added(slack_event):
    # =============== Pin Added Events ================ #
    # If the user has added an emoji reaction to the onboarding message
    team_id = slack_event["team_id"]
    user_id = slack_event["event"]["user"]
    # Update the onboarding message
    pyBot.update_pin(team_id, user_id)
    return text("Welcome message updates with pin", 200, )


def event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.

    Parameters
    ----------
    event_type : str
        type of event received from Slack
    slack_event : dict
        JSON response from a Slack reaction event

    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error

    """
    mapper = {
        "message": _process_messages,
        "team_join": _process_team_join,
        "reaction_added": _process_reaction_added,
        "pin_added": _process_pin_added
    }

    handler = mapper.get(event_type)
    if handler:
        return handler(slack_event)
    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return text(message, 200, {"X-Slack-No-Retry": 1})
