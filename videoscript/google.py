import google_streetview.api
import os
import glob
from natsort import natsorted
from moviepy.editor import *
from flask import Flask
import math
import datetime
#import requests
import jsonlib
from pprint import pprint
from flask import jsonify
from flask import request
from flask_cors import CORS, cross_origin
#from url_decode import urldecode
 
pairname='undefined'
app = Flask(__name__)
cors = CORS(app, resources={r'/*': {"origins": '*'}})
base_dir = os.path.realpath("")

def calculate_initial_compass_bearing(pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing
@app.route("/")
def hello():
    return "VTA Video Creation!"
@app.route('/json', methods=['GET','POST'])
def json():
      clicked=None
      if request.method == "POST":
        if request.data != '':
            data = request.data.split('"')
            if len(data)==3 :
                global pairname
                pairname = "Route_"+data[1]
            else :
                tme=00;
                try:
                    os.makedirs(base_dir+"/"+pairname)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                video = pairname+".mp4"
                f = open(base_dir+"/"+pairname+"/"+pairname+".kml", "w")
                m=0;
                f.write("""<?xml version="1.0" encoding="UTF-8"?> <kml xmlns="http://www.opengis.net/kml/2.2">\n""")
                f.write("<Document>")
                for i in range(0,len(data)-1):
                  if i%2 == 1 :
                    try:
                        a = data[i].split(',')
                        b = data[i+2].split(',')
                        a3 = a[-1].split(' ')
                        a1 = float(a[0])
                        a2 = float(a3[-1])
                        f.write('\n <SchemaData>')
                        f.write('\n   <SimpleData name="Lat">'+a[0]+'</SimpleData>')
                        f.write('\n   <SimpleData name="Lon">'+a3[-1]+'</SimpleData>')
                        f.write('\n   <SimpleData name="UTC_Date">24/04/2018</SimpleData>')
                        f.write('\n   <SimpleData name="UTC_Time">'+str(datetime.timedelta(seconds=tme))+'</SimpleData>')
                        f.write('\n </SchemaData>')
                        tme=tme+0.495867768;
                        b1 = float(b[0])
                        b2 = float(b[-1])
                        ang=calculate_initial_compass_bearing((a1,a2),(b1,b2))
                        params = [{
                          'size': '1024x1024', # max 2048x2048 pixels
                          'location': data[i],
                          'heading': ang,
                          'pitch': '-0.76',
                          'scale': '4',
                          'key': 'AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0'
                        }]
                        results = google_streetview.api.results(params)# Download images to directory 'downloads'
                        results.download_links(base_dir+"/"+pairname+"/",str(m))    
                        m=m+1;
                    except:
                        pass
                f.write("\n</Document>")
                f.close()
                gif_name = 'pic'
                fps = 2.01666667
                file_list = glob.glob(base_dir+"/"+pairname+"/"+'*.jpg')  # Get all the pngs in the current directory
                file_list_sorted = natsorted(file_list,reverse=False)  # Sort the images
                clips = [ImageClip(m).set_duration(.495867768)
                         for m in file_list_sorted]
                concat_clip = concatenate_videoclips(clips, method="compose")
                concat_clip.write_videofile(base_dir+"/"+pairname+"/"+video, fps=fps)
                os.system('/usr/bin/ffmpeg -y -i '+base_dir+'/'+pairname+'/'+video+' -filter:v "crop=1024:800:1024:0" '+base_dir+'/'+pairname+'/cropped'+video)
            return jsonify(request.data)
