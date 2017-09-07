### This program :
# 1. Opens a web browser
# 2. Reads the webapp data using screenshots.
# 3. Sends the screenshots to the neural network and gets instructions.
# 4. Sends commands to the webapp using javascript.

### Libraries
from selenium import webdriver #for changing web browser
from selenium.webdriver.chrome.options import Options #for opening chrome in the right mode
import time #for waiting for pages to load
import json #for sending the json data in post requests from the webapp
from PIL import Image #can't remember
import pyscreenshot as ImageGrab #grab screenshots

def nn(data):
	### This function represents the neural network
	# INPUT image numpy array (120x120x3)
	# OUTPUT tuple (throttle, left, right)
	return (0.5,1.0,0.0)

def nn2(data):
	### If the top half of the image is brighter than the bottom turn left.
	#this function is used to test that the image is being understood in the right way.
	if (len(data)==2 and len(data[0])==2):
		if sum(data[0][0])+sum(data[0][1])>sum(data[1][0])+sum(data[1][1]):
			return (1,1,0) #top half greater than bottom = left
		else:
			return (1,0,1) #bottom greater = right
	else:
		print("invalid image size")
		return (0.5,1.0,0.0) #placeholder

def convert_image(image, size):
	### Splits a list into a list of list representing rows.
	#image[0] is top left, then it goes across the top row of pixels, final element in array is bottom right of image
	formatted_array=[]
	for y in range(size[1]):
		formatted_array.append(image[size[0]*y:size[0]*(y+1)])
	return formatted_array

def connect(ip):
	#CONSTANTS
	throttle_limit = 0.3
	image_size=(120,120)
	web_address="http://"+ip+":8887/drive"
	loop_duration=200
	browser_header_height=40 #magic number. Represents the height of the top of the chrome browser

	#establish a browser connection to the webapp
	chromeOptions = Options()
	chromeOptions.add_argument("--kiosk")
	driver = webdriver.Chrome(chrome_options=chromeOptions) #driver is the webdriver which controls the browser
	driver.get(web_address)

	#find the location of the image within the window
	img_window=driver.find_element_by_xpath("//img[@id='mpeg-image']")
	img_location=img_window.location
	img_size=img_window.size
	img_location["y"]+=browser_header_height # this is a magic number which represents the height of the browser window header.

	#set the format for the POST command
	commmand_format = '''$.post("{0}",'{1}')'''
	instructions = {"angle":0,"throttle":0,"drive_mode":"user","recording":False}

	try: #using a try/finally block to make sure that the car is stopped when the script finishes.
		for i in range(loop_duration):
			# Take the screenshot
			screenshot=ImageGrab.grab(bbox=(
				img_location["x"],img_location["y"],
				img_location["x"]+img_size["width"],img_location["y"]+img_size["height"]
			)) # X1,Y1,X2,Y2

			# Save the image
			# screenshot.save("capture/grab{0}.bmp".format(i))

			#resize the image to the desired size
			screenshot=screenshot.resize(image_size) #argument is (width,height)
			image_array=list(screenshot.getdata()) #convert the image to an array
			image_array=convert_image(image_array,image_size) #convert the array to a

			#send the image to the neural network to be processed
			nn_output=nn(np.asarray(image_array))
			# nn_output=nn2(image)

			#construct the javascript command
			#set turning (from -1 to 1) and throttle (from -1 to 1)
			instructions["angle"]=nn_output[1]-nn_output[2] # TODO figure out how to combine left and right
			instructions["throttle"]=nn_output[0]*throttle_limit #throttle is limited to prevent car driving too fast to control

			#construct the command to send to the webserver
			full_command=commmand_format.format(web_address,json.dumps(instructions))
			# print(full_command)

			# run the javascript command from the browser window (will be immediately executed on the car)
			driver.execute_script(full_command)
	finally:
		# Try to stop the car
		instructions["angle"]=0
		instructions["throttle"]=0
		full_command=commmand_format.format(web_address,json.dumps(instructions))
		driver.execute_script(full_command)

#Ip address of raspberry pi
connect("192.168.43.14")