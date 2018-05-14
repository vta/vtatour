import os
import sys
import math
import json
import urllib2
import datetime
import subprocess
import google_streetview.api
from flask import Flask,request, render_template
from flask_cors import CORS, cross_origin
from flask import request

global base_dir,pdir,pairname,routename,dirname,video,newpano,data
pairname='undefined'
app = Flask(__name__)
cors = CORS(app, resources={r'/*': {"origins": '*'}})
#base_dir = os.path.realpath("")
base_dir = '/home/crowdplat'
data=list(); 
newpano='init_0'
fps='2.01'
pdir='/vtatour/videoscript/' # Project directory




def rmframes(resln,angle,lat,lng):
    global newpano,f
    import json
    oldpano = newpano
    result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?size='+resln+'&location='+str(lat)+','+str(lng)+'&heading='+str(angle)+'&pitch=0&fov=120&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
    htmletxt = result.read()
    snap = json.loads(htmletxt)
    newpano = snap['pano_id']
    if (oldpano!=newpano) or (oldpano == 'init_0'):
        f.write('\nPano_ID : '+newpano)
        return 1
    else:
        return 0
        
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
    os.system('ffmpeg -y -i '+base_dir+pdir+dirname+'/original/'+path+'/'+str(fno)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+base_dir+pdir+dirname+'/cropped/'+path+'/'+str(fno)+'_cropped.jpg')

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
    	if i%2!=0 :
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
            if len(data)>0:
                del data[:]
            data = request.data.split('"')
            print "No of cordinates : ",len(data)/2
            if len(data)==9 :
                if data[1]=='rid':
            		global routename,dirid,video,dirname,camangle
            		routename = data[3]
            		dirid = data[5]
            		camangle = data[7]
            		print camangle
            		dirname = routename +'/'+ dirid
            		video = routename+"_"+dirid
            else :
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
            	    pass
            	f = open(base_dir+pdir+dirname+"/"+video+"output.log", "w")
            	now = datetime.datetime.now()
            	f.write('Start Time : '+str(now))
                f.write('\nRoute_ID : '+routename+'\nDirection : '+dirid+'\nCamera angle : '+camangle)
            	f.write('\n'+dir_stats)
            	m=0;
            	for i in range(1,len(data)):
                	if i%2!=0:
                		try:
                		    try:
                		        a = data[i].split(',')
                		        b = data[i+4].split(',')
                		        a3 = a[-1].split(' ')
                		        a1 = float(a[0])
                		        a2 = float(a3[-1])
                		        b1 = float(b[0])
                		        b2 = float(b[-1])
                		    except:
                		        pass
                                    ang=int(calculate_initial_compass_bearing((a1,a2),(b1,b2)))
            	                    if rmframes('2048x2048',ang,a1,a2)==1 :
                                    	global kml
                                        if camangle=='Forward':
                                        	grabimage(data[i],ang+0,'2048x2048',base_dir,pdir,dirname,'forward',m)
            	                                f.write('\nImage : '+camangle+'_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+0))
                                        	kml='forward'
                                        if camangle=='Right':
                                        	grabimage(data[i],ang+90,'2048x2048',base_dir,pdir,dirname,'right',m)
            	                                f.write('\nImage : '+camangle+'_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+90))
                                        	kml='right'
                                        if camangle=='Backward':
                                        	grabimage(data[i],ang+180,'2048x2048',base_dir,pdir,dirname,'backward',m)
            	                                f.write('\nImage : '+camangle+'_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+180))
                                        	kml='backward'
                                        if camangle=='Left':
                                        	grabimage(data[i],ang+270,'2048x2048',base_dir,pdir,dirname,'left',m)
            	                                f.write('\nImage : '+camangle+'_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+270))
                                        	kml='left'
                                        if camangle=='All':
                                        	kml='forward'
                                        	grabimage(data[i],ang+0,'2048x2048',base_dir,dirname,'forward',m)
            	                                f.write('\nImage : Forward_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+0))
                                        	grabimage(data[i],ang+90,'2048x2048',base_dir,dirname,'right',m)
            	                                f.write('\nImage : Right_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+90))
                                        	grabimage(data[i],ang+180,'2048x2048',base_dir,dirname,'backward',m)
            	                                f.write('\nImage : Backward_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+180))
                                        	grabimage(data[i],ang+270,'2048x2048',base_dir,dirname,'left',m)
            	                                f.write('\nImage : Left_'+str(m)+' Cordinates : '+data[i]+' Angle : '+str(ang+270))
                                        prog=(float(i)/(len(data)-2))*100
                                        print "Progress : ",int(prog),"% Downloading Image ",m," Status : OK"
                                        m=m+1;
                		except:
                		    prog=(float(i)/(len(data)-2))*100
                		    print "Progress : ",int(prog),"% Status : Error! No image found! at :",data[i]
            	                    f.write('\nFailed to download image '+m+' Cordinates : '+data[i])
                		    pass
            	now = datetime.datetime.now()
                f.write('\n'+str(now)+' : Finished downloading images')
                f.write('\n'+str(now)+' : Creating '+video+'_forward.mp4')
                os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_forward.mp4')
                try:
                    a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_forward.mp4').read()
                    time = str(datetime.timedelta(seconds=int(a)))
            	except:
            	    time='0,No video created!'
            	now = datetime.datetime.now()
                f.write('\n'+str(now)+' : Successfully created '+video+'_forward.mp4 Duration : '+time)
                
                f.write('\n'+str(now)+' : Creating '+video+'_right.mp4')
                os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_right.mp4')
                try:
                    a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_right.mp4').read()
                    time = str(datetime.timedelta(seconds=int(a)))
                except:
            	    time='0,No video created!'
            	now = datetime.datetime.now()
                f.write('\n'+str(now)+' : Successfully created '+video+'_right.mp4 Duration : '+time)
                
                f.write('\n'+str(now)+' : Creating '+video+'_backward.mp4')
                os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_backward.mp4')
                try:
                    a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_backward.mp4').read()
                    time = str(datetime.timedelta(seconds=int(a)))
                except:
            	    time='0,No video created!'
                now = datetime.datetime.now()
                f.write('\n'+str(now)+' : Successfully created '+video+'_backward.mp4 Duration : '+time)
                
                f.write('\n'+str(now)+' : Creating '+video+'_left.mp4')
                os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_left.mp4')
                try:
                    a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_left.mp4').read()
                    time = str(datetime.timedelta(seconds=int(a)))
                except:
            	    time='0,No video created!'
                now = datetime.datetime.now()
                f.write('\n'+str(now)+' : Successfully created '+video+'_left.mp4 Duration : '+time)
                a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_'+kml+'.mp4').read()
                if createkml(a,data,base_dir,pdir,dirname,video)==1 :
                    f.write("\nSuccessfully created KML file")
                else:
                    f.write("\nFailed to create KML file")
                now = datetime.datetime.now()
                f.write("\nEnd time : "+str(now))
                f.close()    
            return request.data



