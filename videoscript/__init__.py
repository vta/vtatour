import os
import sys
import math
import json
import urllib2
import datetime
import psycopg2
import commands
import subprocess
import numpy as np
import google_streetview.api
from math import cos, sin, atan2, sqrt, radians, degrees, asin, modf
from flask import Flask,request, render_template
from flask_cors import CORS, cross_origin
from flask import request

global base_dir,pdir,pairname,routename,dirname,video,newpano,data,sdata
pairname='undefined'
app = Flask(__name__)
cors = CORS(app, resources={r'/*': {"origins": '*'}})

data=list(); 
sdata=list();
snapts=list();
pdb=list();
newpano='init_0'

fps='4.02'
base_dir = "/home/crowdplat"
pdir='/vtatour/videoscript/' # Project directory

def getPathLength(lat1,lng1,lat2,lng2):
    '''calculates the distance between two lat, long coordinate pairs'''
    R = 6371000 # radius of earth in m
    lat1rads = math.radians(lat1)
    lat2rads = math.radians(lat2)
    deltaLat = math.radians((lat2-lat1))
    deltaLng = math.radians((lng2-lng1))
    a = math.sin(deltaLat/2) * math.sin(deltaLat/2) + math.cos(lat1rads) * math.cos(lat2rads) * math.sin(deltaLng/2) * math.sin(deltaLng/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d
def getDestinationLatLong(lat,lng,azimuth,distance):
    '''returns the lat an long of destination point 
    given the start lat, long, aziuth, and distance'''
    R = 6378.1 #Radius of the Earth in km
    brng = math.radians(azimuth) #Bearing is degrees converted to radians.
    d = distance/1000 #Distance m converted to km
    lat1 = math.radians(lat) #Current dd lat point converted to radians
    lon1 = math.radians(lng) #Current dd long point converted to radians
    lat2 = math.asin(math.sin(lat1) * math.cos(d/R) + math.cos(lat1)* math.sin(d/R)* math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d/R)* math.cos(lat1), math.cos(d/R)- math.sin(lat1)* math.sin(lat2))
    #convert back to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    return[lat2, lon2]

def geocords(interval,azimuth,lat1,lng1,lat2,lng2):
    '''returns every coordinate pair inbetween two coordinate 
    pairs given the desired interval'''
    coords = []
    d = getPathLength(lat1,lng1,lat2,lng2)
    remainder, dist = modf((d / interval))
    counter = 1.0
    coords.append([lat1,lng1])
    for distance in xrange(1,int(dist)):
        c = getDestinationLatLong(lat1,lng1,azimuth,counter)
        counter += 1.0
        coords.append(c)
    counter +=1
    coords.append([lat2,lng2])
    return coords

def rmspams(base_dir,pdir,dirname):
    path, dirs, files = next(os.walk(base_dir+pdir+dirname+"/original/forward/"))
    file_count = len(files)
    print file_count
    n=0
    m=0
    i=0
    b=1
    tmp=0;
    flag=0
    while i<(file_count-2):
        a = commands.getstatusoutput('compare -metric RMSE '+base_dir+pdir+dirname+'/original/forward/'+str(i)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(i+b)+'.jpg NULL:')
        val = a[1].split(" ")
        print i
        try:
            if flag==1 or float(val[0])<14000:
                os.system('ffmpeg -y -i '+base_dir+pdir+dirname+'/original/forward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+base_dir+pdir+dirname+'/cropped/forward/'+str(n)+'_cropped.jpg')
                os.system('ffmpeg -y -i '+base_dir+pdir+dirname+'/original/backward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+base_dir+pdir+dirname+'/cropped/backward/'+str(n)+'_cropped.jpg')
                os.system('ffmpeg -y -i '+base_dir+pdir+dirname+'/original/left/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+base_dir+pdir+dirname+'/cropped/left/'+str(n)+'_cropped.jpg')
                os.system('ffmpeg -y -i '+base_dir+pdir+dirname+'/original/right/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+base_dir+pdir+dirname+'/cropped/right/'+str(n)+'_cropped.jpg')
                n=n+1
                i=i+b
                flag=0
                b=1
                tmp=val[0]
            else:
                if val[0]<tmp:
                    flag=1
                    pass
                tmp=val[0]
                b=b+1
        except:
            pass

def rmframes(data):
    global newpano
    import json
    oldpano = newpano
    result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+data.replace(" ","")+'&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
    htmletxt = result.read()
    snap = json.loads(htmletxt)
    newpano = snap['pano_id']
    if (oldpano!=newpano) or (oldpano == 'init_0'):
        return 1
    else:
        return 0
def postgreSQL(rId,dId):
    global sdata,pdb
    import json
    del pdb[:]
    del sdata[:]
    del data[:]
    o=0
    d=0
  
    try:
        con = psycopg2.connect("host='52.37.122.170' dbname='gtfs' user='sal_s' password='hsoras6'")   
        cur = con.cursor()
        cur.execute("SELECT routeshape FROM current.routes_v WHERE route_id ='"+str(rId)+"' AND direction_id ='"+str(dId)+"'")
        
        while True:
            arr = cur.fetchone()
        
            if arr == None:
                break
            a1 = arr[0].split('},{')
            for i in range(1,len(a1)):
                a2 = a1[i].split(',')
                a3 = a2[1].split(':')
                a4 = a2[0].split(':')
                pdb.append(str(a4[1]+','+a3[1]))
        
    except psycopg2.DatabaseError, e:
        if con:
            con.rollback()
     
        print 'Error %s' % e    
        sys.exit(1)
     
    finally:   
        if con:
            con.close()
    
    for i in range(0,(len(pdb)-2)):
        a = pdb[i].split(',')
        a1 = float(a[0])
        a2 = float(a[-1].replace(" ",""))
        b = pdb[i+1].split(',')
        b1 = float(b[0])
        b2 = float(b[-1])
        ang=calculate_initial_compass_bearing((a1,a2),(b1,b2))
        sdata.append(geocords(1,ang,a1,a2,b1,b2))
    
    for x in sdata:
        for y in x:
            data.append(str(y[0])+','+str(y[1]))

    return data
        
def grabimage(data,angle,resln,base_dir,pdir,dirname,path,fno):
    params = [{
      'size': resln, # max 2048x2048 pixels
      'location': data,
      'heading': angle,
      'pitch': '0',
      'key': 'AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0'
    }]
    results = google_streetview.api.results(params)# Download images to directory 'downloads'
    results.download_links(base_dir+pdir+dirname+"/original/"+path+"/",str(fno))    

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
	
def createkml(timeinmsec,data,base_dir,pdir,dirname,video):
    print "Creating KML"
    time=0;
    time=((float(timeinmsec)/1000)/(len(data)/2))
    print time
    f = open(base_dir+pdir+dirname+"/"+video+".kml", "w")
    f.write("""<?xml version="1.0" encoding="UTF-8"?> <kml xmlns="http://www.opengis.net/kml/2.2">\n""")
    f.write("<Document>")
    tme=00;
    for i in range(1,len(data)):
    	if 1==1 :
    		try:
    		    a = data[i].split(',')
    		    a3 = a[-1].split(' ')
    		    f.write('\n <SchemaData>')
    		    f.write('\n   <SimpleData name="Lat">'+a[0]+'</SimpleData>')
    		    f.write('\n   <SimpleData name="Lon">'+a3[-1]+'</SimpleData>')
    		    f.write('\n   <SimpleData name="UTC_Date">24/04/2018</SimpleData>')
    		    f.write('\n   <SimpleData name="UTC_Time">'+str(datetime.timedelta(seconds=int(tme)))+'</SimpleData>')
    		    f.write('\n </SchemaData>')
    		    tme=tme+time
    		except:
    		    print "Error writing to kml"
    		    pass

    f.write("\n</Document>")
    f.close()
    print "KML file created!"
    return 1
@app.route("/")
def hello():
    # web = base_dir+'/'+'index.html'
    return render_template('index.html')
@app.route('/json', methods=['GET','POST'])
def json():
      clicked=None
      if request.method == "POST":
        if request.data != '':
            global data
            print request.data
            if len(data)>0:
                del data[:]
            data = request.data.split('"')
            print data
            if len(data)==7 :
                if data[1]=='rid':
                    global routename,dirid,video,dirname
                    routename = data[3]
                    dirid = data[5]
            	    dirname = routename +'/'+ dirid
            	    video = routename+"_"+dirid
                    print "Route_ID : ",routename
                    print "Direction : ",dirid
                    print "> "+base_dir+pdir+"static/"+routename+"_"+dirid+".txt"
                    os.system("> "+base_dir+pdir+"static/"+routename+"_"+dirid+".txt")#path........
                    sdata = postgreSQL(routename,dirid)
                    print "No of Cordinates : ",len(sdata)
                    global f,dir_stats
                    try:
                        os.makedirs(base_dir+pdir+dirname)
                        os.makedirs(base_dir+pdir+dirname+'/original')
                        os.makedirs(base_dir+pdir+dirname+'/original/left')
                        os.makedirs(base_dir+pdir+dirname+'/original/right')
                        os.makedirs(base_dir+pdir+dirname+'/original/forward')
                        os.makedirs(base_dir+pdir+dirname+'/original/backward')
                        os.makedirs(base_dir+pdir+dirname+'/cropped')
                        os.makedirs(base_dir+pdir+dirname+'/cropped/left')
                        os.makedirs(base_dir+pdir+dirname+'/cropped/right')
                        os.makedirs(base_dir+pdir+dirname+'/cropped/forward')
                        os.makedirs(base_dir+pdir+dirname+'/cropped/backward')
                        dir_stats='Successfully created video directory'

                        
                    except:
                        dir_stats='Faild to create video directory'
                        print "Failed to create Directories!"
                        pass
                    open(base_dir+pdir+"static/"+routename+"_"+dirid+".txt", "w").close()
                    open(base_dir+pdir+dirname+"/"+video+".json", 'w').close()
                    f = open(base_dir+pdir+dirname+"/"+video+".json", "a+")
                    f.write('{\n    "route": [{\n            "id": "'+routename+'"\n        },\n        {\n            "direction": "'+dirid+'"\n        }\n    ],\n    "download": [')
                    f.close()
                    m=0;
                    for i in range(0,len(sdata)):
                        if(rmframes(sdata[i])==1):
                            try:
                                try:
                                    a = sdata[i].split(',')
                                    b = sdata[i+4].split(',')
                                    a3 = a[-1].split(' ')
                                    a1 = float(a[0])
                                    a2 = float(a3[-1])
                                    b1 = float(b[0])
                                    b2 = float(b[-1])
                                except:
                                    pass
                                ang=int(calculate_initial_compass_bearing((a1,a2),(b1,b2)))
                                print "angle",ang
                                global kml
                                
                                kml='forward'
                                grabimage(sdata[i],ang+0,'2048x2048',base_dir,pdir,dirname,'forward',m)
                                grabimage(sdata[i],ang+90,'2048x2048',base_dir,pdir,dirname,'right',m)
                                grabimage(sdata[i],ang+180,'2048x2048',base_dir,pdir,dirname,'backward',m)
                                grabimage(sdata[i],ang+270,'2048x2048',base_dir,pdir,dirname,'left',m)
                                
                                prog=(float(i)/(len(sdata)))*100
                                print "Progress : ",int(prog),"% Downloading Image ",str(m)," Status : OK"
                                f = open(base_dir+pdir+"static/"+routename+"_"+dirid+".txt", "w")#path........
                                f.write(str(int(prog)))
                                f.close()
                                m=m+1;
                            except:
                                prog=(float(i)/(len(sdata)))*100
                                print "Progress : ",int(prog),"% Status : Error! No image found! at :",sdata[i]
                                f = open(base_dir+pdir+"static/"+routename+"_"+dirid+".txt", "w")#path........
                                f.write(str(int(prog)))
                                f.close()
                                pass
                    f = open(base_dir+pdir+dirname+"/"+video+".json", "a+")
                    f.write('\n ],\n  "url": [')
                    f.close()
                    
                    
                    rmspams(base_dir,pdir,dirname)
                    
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -c:v libx264 -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_forward.mp4')
                    os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_forward.mp4 s3://vta-tour-rtmp/'+routename+'/')
                    
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -c:v libx264 -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_right.mp4')
                    os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_right.mp4 s3://vta-tour-rtmp/'+routename+'/')
                    
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -c:v libx264 -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_backward.mp4')
                    os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_backward.mp4 s3://vta-tour-rtmp/'+routename+'/')
                    
                    
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg -c:v libx264 -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_left.mp4')
                    os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_left.mp4 s3://vta-tour-rtmp/'+routename+'/')
                    
                    a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_'+kml+'.mp4').read()
                    if createkml(a,sdata,base_dir,pdir,dirname,video)==1 :
                        print "Kml ok"
                        os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'.kml s3://vta-tour-rtmp/'+routename+'/')
                    else:
                        print "Kml bad"
                    f = open(base_dir+pdir+dirname+"/"+video+".json", "a+")
                    f.write('{\n            "forward": "https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/'+routename+'/'+video+'_forward.mp4"\n        },\n')
                    f.write('{\n            "backward": "https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/'+routename+'/'+video+'_backward.mp4"\n        },\n')
                    f.write('{\n            "left": "https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/'+routename+'/'+video+'_left.mp4"\n        },\n')
                    f.write('{\n            "right": "https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/'+routename+'/'+video+'_right.mp4"\n        },\n')
                    f.write('{\n            "kml": "https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/'+routename+'/'+video+'.kml"\n        }\n')
                    
                    f.write('   ]\n}')
                   
                    f.close()    
                    
                    f = open("/var/www/vta_tour/videoscript/static/"+routename+"_"+dirid+".txt", "wb")
                    f.write('101')
                    f.close()                
                return request.data




                
