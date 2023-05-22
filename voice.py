from google.oauth2 import service_account
from googleapiclient.discovery import build
SERVICE_ACCOUNT_FILE = 'soai-voice-assistant.json'
import datetime
import speech_recognition as sr
import os
import pyttsx3 
import pyaudio
import spacy
import pygame
import pyjokes


def play_music(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

API_NAME = 'calendar'
API_VERSION = 'v3'

def initialize_account_service():
	"""Initializes the Google Account Service that is linked with the project credentials."""
	creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/calendar'])
	service = build(API_NAME, API_VERSION, credentials=creds)
	return service

def initialize_nlp():
	"""Initializes the Natural Language Processing library."""
	nlp = spacy.load('en_core_web_md')
	return nlp

def get_calendars_id(service, calendar_name):
	"""Gets the calendar ID of the course calendar and TD calendar providing a calendar name."""
	result = []
	calendar_list = service.calendarList().list().execute()
	calendars = calendar_list.get('items', [])
	#get td calendar id
	for calendar in calendars:
		if calendar_name in calendar['summary']:
			result.append(calendar['id'])
	#get course calendar id
	#split the calendar_name using space as delimiter
	calendar_name = calendar_name.split(' ')

	#getting the only two first elements of the list and joining them with a space
	calendar_name = ' '.join(calendar_name[:2])

	for calendar in calendars:
		if calendar_name == calendar['summary']:
			result.append(calendar['id'])



	if not result:
		return 'No calendar found.'
	else:
		return result

def get_next_event(service, calendar_id):
	#get the next event within  from now
	now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	events_result = service.events().list(calendarId=calendar_id, timeMin=now,
					                                      maxResults=1, singleEvents=True,
										orderBy='startTime').execute()
	event = events_result.get('items', [])
	if not event:
		return 'No upcoming events found.'
	else:
		return event[0]

	
def parse_event(event):
	# get the date of the event 
	date = event['start']['dateTime'].split('T')[0]
	# get the time of the event
	time = event['start']['dateTime'].split('T')[1].split('+')[0]


	"""Parses the event and returns a string with the event details."""
	result = 'You will have ' + event['summary'] + ' on ' + date  + 'at'+ time + ' in ' +event['location'] + '.'
	print(result)
	return result



def detect_speech(audio,r):
	text = r.recognize_google(audio)
	return text

def speak(text):
	engine = pyttsx3.init()
	voices = engine.getProperty('voices')
	engine.setProperty('voice', voices[1].id)
	engine.setProperty('rate', 120)
	engine.say(text)
	engine.runAndWait()

def process_year_group(nlp,text):
	doc = nlp(text)
	result = []
	for token in doc:
		if token.dep_ == 'amod':
			if token.text == 'first':
				result.append('1CP')
			elif token.text == 'second':
				result.append('2CP')
			elif token.text == 'third':
				result.append('1CS')
			elif token.text == 'fourth':
				if 'data science' in doc.text:
					result.append('2SD')
				if 'computer systems' in doc.text:
					result.append('2SQ')
				if 'software engineering' in doc.text:
					result.append('2SL')
				if 'information systems' in doc.text:
					result.append('2SD')
			else: 
				return None
		if token.pos_ == 'NUM':
			if int(token.text) >= 1 or int(token.text) < 4:
				result.append('A')
				result.append('G0'+str(token.text))
			elif int(token.text) >= 4 or int(token.text) < 7:
				result.append('B')
				result.append('G0'+str(token.text))
			elif int(token.text) >= 7 or int(token.text) < 10:
				result.append('C')
				result.append('G0'+str(token))
			elif int(token.text) >= 10 or int(token.text) < 13:
				result.append('D')
				result.append('G0'+str(token.text))
	return ' '.join(result)



def execute_command(command,r,m,nlp):
	if 'schedule' in command:
		speak('I will give you your schedule, just give me your year, and your group.')
		service = initialize_account_service()
		with m as source:
			r.adjust_for_ambient_noise(source, duration=2)
			print("Say something!")
			audio = r.listen(source, phrase_time_limit=10)
			try:
				text = detect_speech(audio,r)
				print("Google Speech Recognition thinks you said " + text)
				processed_text = process_year_group(nlp,text)
				calendars = get_calendars_id(service, processed_text)
				event_course = get_next_event(service, calendars[0])
				event_td = get_next_event(service, calendars[1])
				parsed_event = parse_event(min(event_course, event_td, key=lambda x: x['start']['dateTime']))
				speak(parsed_event)
			except sr.UnknownValueError:
				print("Google Speech Recognition could not understand audio")
				speak('I did not understand what you said. Please try again.')
			except TypeError():
				print("Google Speech Recognition could not understand audio")
				speak('You didnt give a valid year and group. Please try again.')

	elif 'goodbye' in command:
		speak('Goodbye!')
		exit()
	elif 'hello' in command:
		speak('Hello! How can I help you?')
	elif 'weather' in command:
		weather_api = api.API()

		# Get the location ID for New York
		location_id = weather_api.get_location_id('Algiers')

		# Get the weather data for New York
		weather_data = weather_api.get_weather_data(location_id)
		current_condition = weather_data['current_condition']
		print(f"Current weather in {weather_data['city']} is {current_condition['weatherDesc'][0]['value'].lower()} with a temperature of {current_condition['temp_C']}°C")
		speak("Current weather in {weather_data['city']} is {current_condition['weatherDesc'][0]['value'].lower()} with a temperature of {current_condition['temp_C']}°C")

	elif 'joke' in command:
		# get a joke from the pyjokes library
		speak(pyjokes.get_joke())


		

	

def parse_commande(text,nlp):
	doc = nlp(text)
	command = []
	# detect the dobj tags and append them to the command list
	for token in doc:
		if token.dep_ == 'dobj' or token.dep_ == 'INTJ':
			command.append(token.text)
	if 'hello' in text:
		command.append('hello')
	if 'goodbye' in text:
		command.append('goodbye')
	return command


def main():
	r = sr.Recognizer()
	m = sr.Microphone()
	service = initialize_account_service()
	nlp = initialize_nlp()

	# keep listening until the program is closed
	while True:
		with m as source:
			play_music('calibrating.mp3')
			r.adjust_for_ambient_noise(source, duration=2)
			print("Say something!")
			audio = r.listen(source)
		try:
			text = detect_speech(audio,r)
			print("Google Speech Recognition thinks you said: -- " + text,'--')
			command = parse_commande(text,nlp)
			print(command)
			if command:
				execute_command(command,r,m,nlp)
			else:
				speak('It seems that you didn\'t enter a valid command. Please try again.')
		except sr.UnknownValueError:
			print("Google Speech Recognition could not understand audio")
			speak('I did not understand what you said. Please try again.')
		except sr.RequestError as e:
			print("Could not request results from Google Speech Recognition service; {0}".format(e))
			speak('There was an error, please try again.')






			



if __name__ == '__main__':

	main()

	






