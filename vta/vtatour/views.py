import os
import sys
import math
import json
import urllib2
import commands
import datetime
import subprocess
import numpy as np
import google_streetview.api
from firebase import firebase
from math import cos, sin, atan2, sqrt, radians, degrees, asin, modf
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
import json



#firebase = firebase.FirebaseApplication('https://vtavirtualtransit-7c904.firebaseio.com', None)

class Google(object):
    
    # global newpano
            
    # newpano='init_0'
    global fps
    fps='4.02'
    
    global firebase
    firebase = firebase.FirebaseApplication('https://vtavirtualtransit-7c904.firebaseio.com', None)

    def download(self,data):
        #print data
        if len(data)==7 :
            if data[1]=='rid':
                m=0
                routename = data[3]
                dirid = data[5]
                dirname = routename +'/'+ dirid
                video = routename+"_"+dirid
                print "Route_ID : ",routename
                print "Direction : ",dirid
                base_dir = os.path.realpath("")
                pdir='/' # Project directory
                sdata=list();
                del sdata[:]
                sdata = self.firedata(routename,dirid)
                print "No of Cordinates : ",len(sdata)
                
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
                except:
                    print "Dir exists!"
                    pass
                
                for i in range(0,50):#len(sdata)):
                    import json
                    if(i==0):
                        newpano = 'init_0'
                    oldpano=newpano
                    result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+sdata[i].replace(" ","")+'&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
                    htmletxt = result.read()
                    snap = json.loads(htmletxt)
                    newpano = snap['pano_id']
                    if (oldpano!=newpano):
                        rm=1
                    else:
                        rm=0
                    if(rm==1):
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
                            ang=int(self.calculate_initial_compass_bearing((a1,a2),(b1,b2)))
                            self.grabimage(sdata[i],ang+0,'640x640',base_dir,pdir,dirname,'forward',m)
                            #self.grabimage(sdata[i],ang+90,'2048x2048',base_dir,pdir,dirname,'right',m)
                            #self.grabimage(sdata[i],ang+180,'2048x2048',base_dir,pdir,dirname,'backward',m)
                            #self.grabimage(sdata[i],ang+270,'2048x2048',base_dir,pdir,dirname,'left',m)
                            
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
               
                self.rmspams(base_dir,pdir,dirname)
                print "Creating and uploading videos to s3"
                os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_forward.mp4')
                os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_forward.mp4 s3://vta-tour-rtmp/'+routename+'/')
                
                #os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_right.mp4')
                #os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_right.mp4 s3://vta-tour-rtmp/'+routename+'/')
                
                #os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_backward.mp4')
                #os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_backward.mp4 s3://vta-tour-rtmp/'+routename+'/')
                
                
                #os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg-crf 0 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_left.mp4')
                #os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_left.mp4 s3://vta-tour-rtmp/'+routename+'/')
                print "Done uploading videos!"
                a = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_'+'forward'+'.mp4').read()
                try:
                    if self.createkml(a,sdata,base_dir,pdir,dirname,video)==1 :
                        print "Uploading Kml"
                        os.system('aws s3 cp '+base_dir+pdir+dirname+'/'+video+'.kml s3://vta-tour-rtmp/'+routename+'/')
                        print "Done uploading Kml!"
                    else:
                        print "Kml bad"
                except:
                    print "No Cords received!"
                
                os.system('rm -r '+base_dir+pdir+routename+'/')
                print "Removed directory :",base_dir+pdir+routename,"/ !"
                f = open(base_dir+pdir+"static/"+routename+"_"+dirid+".txt", "w")
                f.write('101')
                f.close() 
                         
        
    def getPathLength(self,lat1,lng1,lat2,lng2):
        try:
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
        except:
            print "Error - Get Path Length"
    def getDestinationLatLong(self,lat,lng,azimuth,distance):
        try:
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
        except:
            print "Error - Destination lat lng calc"
    def geocords(self,interval,azimuth,lat1,lng1,lat2,lng2):
        try:
            '''returns every coordinate pair inbetween two coordinate 
            pairs given the desired interval'''
            coords = []
            d = self.getPathLength(lat1,lng1,lat2,lng2)
            remainder, dist = modf((d / interval))
            counter = 1.0
            coords.append([lat1,lng1])
            for distance in xrange(1,int(dist)):
                c = self.getDestinationLatLong(lat1,lng1,azimuth,counter)
                counter += 1.0
                coords.append(c)
            counter +=1
            coords.append([lat2,lng2])
            return coords
        except:
            print "Error - Geocords"
    def rmspams(self,bd,pd,dnme):
        try:
            path, dirs, files = next(os.walk(bd+pd+dnme+"/original/forward/"))
            file_count = len(files)
            n=0
            m=0
            i=0
            b=1
            tmp=0;
            flag=0
            while i<(file_count-2):
                a = commands.getstatusoutput('compare -metric RMSE '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg '+bd+pd+dnme+'/original/forward/'+str(i+b)+'.jpg NULL:')
                val = a[1].split(" ")
                try:
                    if flag==1 or float(val[0])<14000:
                        os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-10" -loglevel quiet '+bd+pd+dnme+'/cropped/forward/'+str(n)+'_cropped.jpg')
                        os.system('rm '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg')
                        #os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/backward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+bd+pd+dnme+'/cropped/backward/'+str(n)+'_cropped.jpg')
                        #os.system('rm '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg')
                        #os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/left/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+bd+pd+dnme+'/cropped/left/'+str(n)+'_cropped.jpg')
                        #os.system('rm '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg')
                        #os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/right/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-800" -loglevel quiet '+bd+pd+dnme+'/cropped/right/'+str(n)+'_cropped.jpg')
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
                    i=i+1
                    pass
        except:
            print "Error - Spam frame removal" 

    def rmframes(self,data,k):
        if(k==0):
            newpano = 'init_0'
            oldpano=newpano
        import json
        
        print oldpano,newpano
        result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+data.replace(" ","")+'&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
        htmletxt = result.read()
        snap = json.loads(htmletxt)
        newpano = snap['pano_id']
        if (oldpano!=newpano):
            oldpano=newpano
            return 1
        else:
            oldpano=newpano
            return 0


    def firedata(self,rId,dId):
        import json
        data=list(); 
        
        fdata=list();
        print "rId : ",rId
        print "dId : ",dId
        
        geopts=0
        del data[:]
        del fdata[:]

        
        #firebase = firebase.FirebaseApplication('https://vtavirtualtransit-7c904.firebaseio.com', None)
        geopts = firebase.get('/route-details/'+rId+'/'+dId+'/videoGeoPoints', None)
        print geopts
        print "Rid :",rId,"Length : ",len(geopts)
        for k in range(0,len(geopts)):
            try:
                angll=self.calculate_initial_compass_bearing((geopts[k]['lat'],geopts[k]['lng']),(geopts[k+1]['lat'],geopts[k+1]['lng']))
                #print 'ang',ang
                fdata.append(self.geocords(1,angll,geopts[k]['lat'],geopts[k]['lng'],geopts[k+1]['lat'],geopts[k+1]['lng']))
            except:
                print "Error Null value"
        
        #print sdata
        for x in fdata:
            for y in x:
                data.append(str(y[0])+','+str(y[1]))

        return data
            
    def grabimage(self,data,angle,resln,br,pr,dr,path,fno):
        import urllib
        try:
            urllib.urlretrieve("https://maps.googleapis.com/maps/api/streetview?size=640x640&location="+data.replace(" ","")+"&heading="+str(angle)+"&pitch=0.0" ,br+pr+dr+"/original/"+path+"/"+str(fno)+".jpg")
        except:
            print "Error - grabimage"
    def calculate_initial_compass_bearing(self,pointA, pointB):
        try:
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
        except:
            print "Error - Bearing Calculation"
    def createkml(self,timeinmsec,data,base,pi,di,video):
        try:
            print "Creating KML"
            time=0;
            time=((float(timeinmsec)/1000)/(len(data)/2))
            print time
            f = open(base+pi+di+"/"+video+".kml", "w")
            f.write("""<?xml version="1.0" encoding="UTF-8"?> <kml xmlns="http://www.opengis.net/kml/2.2">\n""")
            f.write("<Document>")
            tme=0;
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
        except:
            print "Error - Kml Creation"

# Create your views here.


class index(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)
    def post(self, request):
        if request.body != '':
            rdata =list();
            print request.body
            if len(rdata)>0:
                del rdata[:]
            rdata = request.body.split('"')
            google = Google()
            
            try:
                google.download(rdata)  
            except ValueError as valerr:
                print valerr   
            return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')

