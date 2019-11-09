from imutils.video import VideoStream
from flask import Response
from flask import Flask, render_template, flash, request
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
from fer import FER
import cv2
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField


# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)
vs = VideoStream(src=0).start()
time.sleep(2.0)


DEBUG = True
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

class ReusableForm(Form):
    fname = TextField('Name:', validators=[validators.required()])
    lname = TextField('Name:', validators=[validators.required()])
    dob = TextField('Name:', validators=[validators.required()])
    email = TextField('Name:', validators=[validators.required()])
    phone = TextField('Name:', validators=[validators.required()])
    gender = TextField('Name:', validators=[validators.required()])
	
	
    
    @app.route("/register", methods=['GET', 'POST'])
    def register():
        form = ReusableForm(request.form)
        
        print(form.errors)
        if request.method == 'POST':
            fname=request.form['fname']
            lname=request.form['lname']
            dob=request.form['dob']
            email=request.form['email']
            phone=request.form['phone']
            gender=request.form['gender']
            text=fname+" "+lname+" "+dob+" "+email+" "+phone+" "+gender
            with open('output.txt', 'w') as file:
                file.write(text)
            return render_template('landing.html', form=form)
        
        return render_template('index.html', form=form)




@app.route("/home")
def home():
	# return the rendered template
	return render_template("home.html")


@app.route("/")
def index1():
     return render_template('index1.html')



def detect_motion(frameCount):
	# grab global references to the video stream, output frame, and
	# lock variables
	global vs, outputFrame, lock
	while True:
		# read the next frame from the video stream, resize it,
		# convert the frame to grayscale, and blur it
		frame = vs.read()
		frame = imutils.resize(frame,600,800)

		# grab the current timestamp and draw it on the frame
		timestamp = datetime.datetime.now()
		detector = FER()
		try:
			emotion, score = detector.top_emotion(frame)
		except:
			emotion,score ="finding...",0
		cv2.putText(frame, emotion, (10, frame.shape[0] - 10),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		with lock:
			outputFrame = frame.copy()
		
def generate():
	# grab global references to the output frame and lock variables
	global outputFrame, lock

	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame is None:
				continue

			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

			# ensure the frame was successfully encoded
			if not flag:
				continue

		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	# start a thread that will perform motion detection
	t = threading.Thread(target=detect_motion, args=(32,))
	t.daemon = True
	t.start()

	# start the flask app
	app.run(host="0.0.0.0", port="8000", debug=True,threaded=True, use_reloader=False)

# release the video stream pointer
vs.stop()
