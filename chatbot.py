from flask import Flask, request, Response # web server for hooks
from twilio.rest import Client # twilio client to send messages
from twilio.twiml.messaging_response import MessagingResponse # twilio response to send back to user
import ollama # llm management
import os # environment variables
from dotenv import load_dotenv # load environment variables from .env file

load_dotenv() # load environment variables from .env file
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID') # twilio account sid
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN') # twilio auth token
twilio_client = Client(twilio_account_sid, twilio_auth_token) # twilio client to send messages

model = 'qwen2.5:1.5b'

system_prompt = """
    You are a helpful assistant that answers questions and provides information.
"""

conversation_context = {}
conversation_context_limit = 6 # limit the number of messages in the conversation context

flask_app = Flask(__name__) # create flask app

def store_chat(number, message, role):
    for number in conversation_context:
        curr_chat = conversation_context[number]

        if len(curr_chat) >= conversation_context_limit:
            curr_chat.pop(0) # remove the oldest message if the limit is reached

        curr_chat.append({'role': role, 'content': message}) # store the message in the conversation context

    else:
        conversation_context[number] = [{'role': role, 'content': message}] # create a new conversation context for the number

def get_chat(number):
    return conversation_context[number]

@flask_app.route('/whatsapp', methods=['POST'])
def whatsapp_response_route():

    reply_number = request.form.get('From') # get the number of the user
    message = request.form.get('Body') # get the message from the user

    store_chat(reply_number, message, 'user') # store the user's message in the conversation context

    try:
        response = ollama.chat(
            model = model,
            messages = [{'role': 'system', 'content': system_prompt}] + get_chat(reply_number)
        )
    except ollama.ResponseError as e:
        print("Ollama API Error:", e.error) # print the error message
        print("Status Code:", e.status_code) # print the status code

    resp = MessagingResponse() # create a twilio response
    resp.message(response.message.content) # send the response back to the user
    return str(resp)

flask_app.run(host='0.0.0.0', port=5000) # run the flask app 