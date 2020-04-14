import io
import sys
import json
import time
import requests
import threading
import subprocess
from bs4 import BeautifulSoup as bs
from subprocess import PIPE, DEVNULL

ID = ""
PASSWD = ""
LOGINURL = "https://account.nicovideo.jp/login/redirector"
CONNECTURL = "https://www.nicovideo.jp/watch/sm28242091"

def heartbeat(session, api_uri, data, killevent, interval = 40):
	headers = {"Content-Type": "application/json"}
	uri = api_uri + "/" + data['session']['id'] + "?_format=json&_method=PUT"
	while True:
		print("Sending Heartbeat...")
		res = session.post(uri, headers = headers, data = json.dumps(data))
		if res.status_code != 200:
			raise RuntimeError("Heartbeat Failed. returned value:" + res.text)
		data = res.json()['data']
		print("Heartbeat sent succesfully. ")
		if killevent.wait(timeout = interval):
			print("Got killevent. stopping heartbeat.")
			return

if __name__ == "__main__":
	print("Creating Session...")
	session = requests.session()
	if ID and PASSWD:
		print("Logging In...")
		session.post(LOGINURL, data = {"mail_tel": ID, "password": PASSWD})
		print("Login Successful. Cookies:")
		print(session.cookies.get_dict())
	else:
		print("No ID and PASSWD present. proceed without login...")
	
	print("Connecting to video page...")
	r = session.get(CONNECTURL)
	print("Parsing datas...")
	soup = bs(r.text)
	info = json.loads(soup.find(id="js-initial-watch-data")['data-api-data'])
	if info['video']['dmcInfo']:
		print("DMC video detected.")
		api_url = info['video']['dmcInfo']['session_api']['urls'][0]['url']
		# get all the things from data-api-data, but I will change things a bit in video/audio source to get lowest quality on video and highest quality on audio.
		data = {
			"session": {
        		"recipe_id": info['video']['dmcInfo']['session_api']['recipe_id'],
        		"content_id": info['video']['dmcInfo']['session_api']['content_id'],
        		"content_type": "movie",
        		"content_src_id_sets": [
		            {
                		"content_src_ids": [
		                    {
                        		"src_id_to_mux": {
		                            # Get lowest setting of video, highest setting of audio
                            		"video_src_ids": [info['video']['dmcInfo']['session_api']['videos'][-1]],
                            		"audio_src_ids": [info['video']['dmcInfo']['session_api']['audios'][0]]
                        		}
                    		}
                		]
            		}
        		],
        		"timing_constraint": "unlimited",
        		"keep_method": {
		            "heartbeat": {
                		"lifetime": info['video']['dmcInfo']['session_api']['heartbeat_lifetime']
            		}
        		},
        		"protocol": {
		            "name": info['video']['dmcInfo']['session_api']['protocols'][0],
            		"parameters": {
		                "http_parameters": {
                    		"parameters": {
		                        "hls_parameters": {
                            		"use_well_known_port": "yes",
                            		"use_ssl": "yes",
                            		"transfer_preset": "",
                            		"segment_duration": 6000
                        		}
                    		}
                		}
            		}
        		},
        		"content_uri": "",
        		"session_operation_auth": {
		            "session_operation_auth_by_signature": {
                		"token": info['video']['dmcInfo']['session_api']['token'],
                		"signature": info['video']['dmcInfo']['session_api']['signature']
            		}
        		},
        		"content_auth": {
		            "auth_type": info['video']['dmcInfo']['session_api']['auth_types'][info['video']['dmcInfo']['session_api']['protocols'][0]],
            		"content_key_timeout": info['video']['dmcInfo']['session_api']['content_key_timeout'],
            		"service_id": "nicovideo",
            		"service_user_id": info['video']['dmcInfo']['session_api']['service_user_id']
        		},
        		"client_info": {
		            "player_id": info['video']['dmcInfo']['session_api']['player_id']
        		},
        		"priority": info['video']['dmcInfo']['session_api']['priority']
    		}
		}
		headers = {"Content-Type": "application-json"}
		print("Sending API request...")
		r = session.post(api_url + "?_format=json", headers = headers, data = json.dumps(data))
		r.raise_for_status()
		print("Success.")
		api_result = r.json()
		killevent = threading.Event()
		thread = threading.Thread(target = heartbeat, args = (session, api_url, api_result['data'], killevent))
		thread.start()
		
		print("Getting m3u8 list...")
		# Get m3u8 fron nicovideo, add baseurl
		m3u8_baseurl = api_result['data']['session']['content_uri'].split("master.m3u8")[0]
		m3u8_pre = session.get(api_result['data']['session']['content_uri']).text.split("\n")[-2]
		m3u8_url = m3u8_baseurl + m3u8_pre
		m3u8_baseurl = m3u8_url.split("playlist.m3u8")[0]
		m3u8 = session.get(m3u8_url).text
		ts_list = [m3u8_baseurl + entry for entry in m3u8.split("\n") if entry and entry[0] != "#"]
	
		print("Amount of ts file to be downloaded: " + str(len(ts_list)) + " files")
		print("Generate BytesIO and start downloading Files...")
		songbytes = io.BytesIO()
		
		for index in range(len(ts_list)):
			print(f"Processing {index}/{len(ts_list)}...")
			print("Downloading...")
			url = ts_list[index]
			ts = session.get(url)
			ts.raise_for_status()
			print("Done. Encoding...")
			process = subprocess.run(["ffmpeg", "-i", "-", "-vn", "-f", "opus", "-"], input = ts.content, stdout = PIPE, stderr = DEVNULL)
			print("Succesfully Encoded to opus. adding to BytesIO...")
			print(songbytes.write(process.stdout))
	
		print("Finished Downloading. Stop heartbeat and Saving...")
		killevent.set()
		songbytes.seek(0)
		with open("nicotest.opus", "wb") as f:
			f.write(songbytes.read())
		print("Finished.")
	else:
		# https://www.nicovideo.jp/watch/sm14746821
		print("SmileVideo Detected.")
		url = info['video']['smileInfo']['url']
		print("Generate BytesIO...")
		songbytes = io.BytesIO()
		print("Downloading video...")
		video = session.get(url)
		print("Encoding video")
		process = subprocess.run(["ffmpeg", "-i", "-", "-vn", "-f", "opus", "-"], input = video.content, stdout = PIPE, stderr = DEVNULL)
		print("Finished Downloading. Saving...")
		songbytes.seek(0)
		with open("nicotest.opus", "wb") as f:
			f.write(songbytes.read())
		print("Finished.")