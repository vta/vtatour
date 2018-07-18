#+RESOLUTION
#+ENVIRONMENT
#+TURNING IDENTIFICATION
#+ALL IMAGE DOWNLOAD / NO COMPARISON
#- INTERPOLATION

import os
import sys
import time
import math
import json
#import cv2
import hmac
import base64
import urllib2
import hashlib
import urlparse
import datetime
import commands
import requests
import threading
import subprocess
import numpy as np
import mysql.connector
import google_streetview.api
from firebase import firebase
from django.conf import settings
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from math import cos, sin, atan2, sqrt, radians, degrees, asin, modf

global mydb,fps,firebase,my_host,my_user,my_password,my_db,google_key,api_key
my_host = getattr(settings, "DB_HOST", None)
my_user = getattr(settings, "DB_USER", None)
my_password = getattr(settings, "DB_PASSWORD", None)
my_db = getattr(settings, "DB_DB", None)
fps='2' # Set video frame rate (frames per second)
api_url =  getattr(settings, "API_URL", None)

google_key = getattr(settings, "G_KEY", None)


class Google(object):
    
    def mse(self,imageA, imageB):
        # the 'Mean Squared Error' between the two images is the
        # sum of the squared difference between the two images;
        # NOTE: the two images must have the same dimension
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
    
        # return the MSE, the lower the error, the more "similar"
        # the two images are
        return err


    def download(self,data):
        if 1==1: # checks if data has 4 elements
            if data[0]=='rid': #checks if the first element is 'rid'
                m=0 #Sets file number to 0
                routename = data[1] # Stores route id into routename
                dirid = data[2] # Stores direction into dirid
                camangle = data[3] # Stores view into camangle
                ores=data[4] # original resolution
                env = data[5]
                dirname = routename +'/'+ dirid+'_'+ores+'_'+env #Stores base path of video directories
                video = routename+"_"+dirid+'_'+ores+'_'+env #Base name of the video
                sqldir=dirid
                if ores=="High":
                    resln=1280 
                if ores=="Low":
                    resln=640 


                mydb = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor = mydb.cursor()

                sql = 'SELECT EXISTS(SELECT * FROM routes_progress WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'");'
                mycursor.execute(sql)
                stats = mycursor.fetchall()
                mycursor.close()
                mydb.close()
                if(stats[0][0]==0):
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb1 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor1 = mydb1.cursor()
                    sql1 = 'INSERT INTO routes_progress (route_id,direction,view,min,resolution,environment) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+currentmin+'","'+ores+'","'+env+'")'
                    mycursor1.execute(sql1)
                    mydb1.commit()
                    mycursor1.close()
                    mydb1.close()
                
                sql2 = 'UPDATE routes_progress SET gen_status=0 WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                mydb2 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor2 = mydb2.cursor()
                sql2 = 'UPDATE routes_progress SET gen_status=0,min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mycursor2.execute(sql2)
                mydb2.commit()
                mycursor2.close()
                mydb2.close()
                
                #Prints route id and direction in terminal
                print "Route_ID : ",routename  
                print "Direction : ",dirid
                 
                base_dir = '/var/www/html/vta2' #Base directory
                pdir='/' # Project directory
                sdata=list();
                fkmlcords=list();
                lkmlcords=list();
                rkmlcords=list();
                bkmlcords=list();
                fkml=list();
                del fkml[:]
                del fkmlcords[:]
                del rkmlcords[:]
                del lkmlcords[:]
                del bkmlcords[:]
                del sdata[:]
                m1=0
                m2=0
                m3=0
                m4=0
                eletmp=0.0
                total=11000
                avg=0
                npy=0
                '''
                Status is set to zero if coordinates are fetched from firebase
                Status is set to one if coordinates are fetched from kml
                '''
           
                sdata = self.firedata(routename,dirid,base_dir,pdir,sqldir,camangle,env) # Gets coordinates from firebase

                # If no coordinates are present in firebase ,execution will stop here                
                if sdata==0:
                    try:
                        #If View is Left, Right or Backward Overwrites 405 to progress file (UI will display create forward first)
                        
                        currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                        mydb5 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                        mycursor5 = mydb5.cursor()
                        sql5 = 'UPDATE routes_progress SET progress="No coordinates found in database." , min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                        mycursor5.execute(sql5)
                        mydb5.commit()
                        mycursor5.close()
                        mydb5.close()
                    except Exception as x:
                        mydb6 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                        mycursor6 = mydb6.cursor()
                        sql6 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                        mycursor6.execute(sql6)
                        mydb6.commit()
                        mycursor6.close()
                        mydb6.close()
                    return 0
                
                # Creates video directories
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
                except Exception as x:
                    mydb7 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor7 = mydb7.cursor()
                    sql7 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                    mycursor7.execute(sql7)
                    mydb7.commit()
                    mycursor7.close()
                    mydb7.close()
                    print "Directory exists!"
                    pass
                tang= 0
                vtemp=0
                #print sdata[0]
                for i in range(0,len(sdata)): #Loop to download all street view images
                    import json

                    '''
                    oldpano : Panorama id of the current coordinate
                    newpano : Panorama id of the adjacent coordinate

                    newpano and oldpano are used to compare adjacent coordinates 
                    with their pano id to avoid downloading duplicate images.

                    Each street view image has a unique Panorama id
                    
                    If Panorama ids are same the the images will be same too
                    
                    If value of oldpano is same as newpano then download will skip 
                    and next two coordinates are compared  

                    '''

                    if(i==0): 
                        newpano = 'init_0' # Define newpano ,value doesn't matter
                        oldpano = newpano # Define oldpano
                        ocord = sdata[0] # ocord is used to store the current coordinate 
                    
                    if i<len(sdata)-1:
                        rcord=sdata[i+1].replace(" ","") # rcord is used to store the adjacent coordinate

                    try:
                        # Compares adjacent coordinates to avoid downloading duplicate images
                        # Stores the metadata response(JSON) of rcord into htmltext
                        result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+rcord+'&key='+google_key)
                        htmletxt = result.read()
                        # Converts it into JSON format and stores it into snap
                        snap = json.loads(htmletxt)
                        if snap['status'] == 'ZERO_RESULTS':
                            continue   
                    
                        # Panorama id of rcord is stored into newpano
                        newpano = snap['pano_id'] 

                        '''
                        Checks if both panorama ids are same,if not set rm=1 
                        If rm=1 image is downloaded with the coordinates present in ocord

                        '''
                        if (oldpano!=newpano):  
                            oldpano=newpano
                            rm=1
                        else:
                            rm=0
                    except:
                        # rm=0
                        pass
                    

                    if(rm==1): # If rm is 1 download the images
                        try:    
                            try:
                                   # Splits ocord into latitude and longitude
                                a = ocord.split(',') 
                                # Splits rcord into latitude and longitude 
                                b = rcord.split(',') 
                                
                                a1 = float(a[0]) #lat of ocord
                                a2 = float(a[1]) #lng of ocord
                                b1 = float(b[0]) #lat of rcord
                                b2 = float(b[1]) #lng of rcord

                            except Exception as x:
                                mydb8 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                                mycursor8 = mydb8.cursor()
                                sql8 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                                mycursor8.execute(sql8)
                                mydb8.commit()
                                mycursor8.close()
                                mydb8.close()
                                pass 
                            ang=int(self.calculate_initial_compass_bearing((a1,a2),(b1,b2))) # Calculate the Heading angle (Bearing angle)
                            
                            prog=(float(i)/(len(sdata)))*100 # Calculate the progress
                            
                            '''
                            Creates threads to download each Street view image
                            All threads are set to daemon (daemon thread closes automatically)
                            
                            Images are downloaded using grabimage() 

                            grabimage(coordinates,angle,resolution,basedirectory,projectdirectory,videodirectory,view,filenumber)
                                   
                            '''
                            currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                            mydb9 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                            mycursor9 = mydb9.cursor()
                            sql9 = 'UPDATE routes_progress SET progress="Downloading images : '+str(int(prog))+'% Completed",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                            mycursor9.execute(sql9)
                            mydb9.commit()
                            mycursor9.close()
                            mydb9.close()
                            if (camangle=='Forward') or (camangle=='All'):
                                fwd=threading.Thread(target=self.grabimage,args=(ocord,ang+0,resln,base_dir,pdir,dirname,'forward',m1,))
                                fwd.setDaemon(True)
                                fwd.start()
                            if (camangle=='Backward') or (camangle=='All'):
                                bck=threading.Thread(target=self.grabimage,args=(ocord,ang+180,resln,base_dir,pdir,dirname,'backward',m2,))
                                bck.setDaemon(True)
                                bck.start()
                                
                            if (camangle=='Left') or (camangle=='All'):
                                lft=threading.Thread(target=self.grabimage,args=(ocord,ang+270,resln,base_dir,pdir,dirname,'left',m3,))
                                lft.setDaemon(True)
                                lft.start()
                               
                            if (camangle=='Right') or (camangle=='All'):
                                rgt=threading.Thread(target=self.grabimage,args=(ocord,ang+90,resln,base_dir,pdir,dirname,'right',m4,))
                                rgt.setDaemon(True)
                                rgt.start()
                               
                            
                            
                            try:

                                if (camangle=='Forward') or (camangle=='All'):
                                    # Checks if all images are downloaded
                                    try:
                                        fwd.join()
                                        if ((float(os.stat(base_dir+pdir+dirname+"/original/forward/"+str(m1)+".jpg").st_size)/1000)>10):
                                            if tang < ang-15 or tang > ang+15:
                                                #print "Turning"
                                                m1=m1+1
                                                fkmlcords.append(ocord) #ocord is added to kml array for kml creation
                                            else:
                                                d = commands.getstatusoutput('compare -metric FUZZ '+base_dir+pdir+dirname+'/original/forward/'+str(m1)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(m1-1)+'.jpg NULL:')
                                                val2 = d[1].split(" ")
                                                if (float(val2[0])!=0):
                                                    m1=m1+1
                                                    fkmlcords.append(ocord)
                                                    #print "Going Stright"
                                    except Exception as x:
                                        print x
                                        pass
                                    tang = ang 
                                if (camangle=='Right') or (camangle=='All'):
                                        try:
                                            rgt.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/right/"+str(m4)+".jpg").st_size)/1000)>10):
                                                rkmlcords.append(ocord)
                                                m4=m4+1
                                        except:
                                            pass
                                if (camangle=='Backward') or (camangle=='All'):
                                        try:
                                            bck.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/backward/"+str(m2)+".jpg").st_size)/1000)>10):
                                                bkmlcords.append(ocord)
                                                m2=m2+1
                                        except:
                                            pass
                                if (camangle=='Left') or (camangle=='All'):
                                        try:
                                            lft.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/left/"+str(m3)+".jpg").st_size)/1000)>10):
                                                lkmlcords.append(ocord)
                                                m3=m3+1 # Increment file number
                                        except:
                                            pass
                                    
                                ocord=rcord                  
                            except Exception as x:
                                
                                ocord = rcord # To download next image
                                mydb10 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                                mycursor10 = mydb10.cursor()
                                sql10 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                                mycursor10.execute(sql10)
                                mydb10.commit()
                                mycursor10.close()
                                mydb10.close()
                                pass
                            
                           
                            
                        except Exception as x:
                            mydb11 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                            mycursor11 = mydb11.cursor()
                            sql11 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                            mycursor11.execute(sql11)
                            mydb11.commit()
                            mycursor11.close()
                            mydb11.close()
                            pass
                
               
                if (camangle=='Forward') or (camangle=='All'):
                    self.cropfunc(base_dir,pdir,dirname,'Forward',resln)
                if (camangle=='Backward') or (camangle=='All'):
                    self.cropfunc(base_dir,pdir,dirname,'Backward',resln)
                if (camangle=='Left') or (camangle=='All'):
                    self.cropfunc(base_dir,pdir,dirname,'Left',resln)
                if (camangle=='Right') or (camangle=='All'):
                    self.cropfunc(base_dir,pdir,dirname,'Right',resln)

                
                #retrive aws credentials from django
                aws_key = getattr(settings, "AWS_"+env.upper()+"_KEY", None)
                aws_secret = getattr(settings, "AWS_"+env.upper()+"_SECRET", None)
                current_date = str(os.popen('date').read()).replace(" ","_").replace("\n","")
                if (camangle=='Forward') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb12 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor12 = mydb12.cursor()
                    sql12 = 'UPDATE routes_progress SET progress="99% Completed ( Generating forward video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor12.execute(sql12)
                    mydb12.commit()
                    mycursor12.close()
                    mydb12.close()

                    #Creates forward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb13 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor13 = mydb13.cursor()
                    sql13 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading forward video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor13.execute(sql13)
                    mydb13.commit()
                    mycursor13.close()
                    mydb13.close()
                    #Uploads forward video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                                       
                
                if (camangle=='Backward') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb14 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor14 = mydb14.cursor()
                    sql14 = 'UPDATE routes_progress SET progress="99% Completed ( Generating backward video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor14.execute(sql14)
                    mydb14.commit()
                    mycursor14.close()
                    mydb14.close()
                    #Creates backward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb15 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor15 = mydb15.cursor()
                    sql15 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading backward video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor15.execute(sql15)
                    mydb15.commit()
                    mycursor15.close()
                    mydb15.close()
                    #Upload backward video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    
                
                if (camangle=='Left') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb16 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor16 = mydb16.cursor()
                    sql16 = 'UPDATE routes_progress SET progress="99% Completed ( Generating left video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor16.execute(sql16)
                    mydb16.commit()
                    mycursor16.close()
                    mydb16.close()
                    #Create Left video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb17 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor17 = mydb17.cursor()
                    sql17 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading left video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor17.execute(sql17)
                    mydb17.commit()
                    mycursor17.close()
                    mydb17.close()
                    #Upload left video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    

                if (camangle=='Right') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb18 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor18 = mydb18.cursor()
                    sql18 = 'UPDATE routes_progress SET progress="99% Completed ( Generating right video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor18.execute(sql18)
                    mydb18.commit()
                    mycursor18.close()
                    mydb18.close()

                    #Create right video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4')
                    #Upload right video to s3
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    mydb19 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor19 = mydb19.cursor()
                    sql19 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading right video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mycursor19.execute(sql19)
                    mydb19.commit()
                    mycursor19.close()
                    mydb19.close()
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    
                
                fb_url=getattr(settings, "FB_"+env.upper()+"", None)
                pm_token=getattr(settings, "PM_"+env.upper()+"", None)
                
                url = fb_url+routename+"/"+dirid+""

                url_forward=routename+'/'+current_date+'_'+video+'_forward.mp4'
                url_backward=routename+'/'+current_date+'_'+video+'_backward.mp4'
                url_right=routename+'/'+current_date+'_'+video+'_right.mp4'
                url_left=routename+'/'+current_date+'_'+video+'_left.mp4'
                url_kml=routename+'/'+current_date+'_'+video+'.kml'
                url_fkml=routename+'/'+current_date+'_'+video+'_forward.kml'
                url_lkml=routename+'/'+current_date+'_'+video+'_left.kml'
                url_rkml=routename+'/'+current_date+'_'+video+'_right.kml'
                url_bkml=routename+'/'+current_date+'_'+video+'_backward.kml'

                api_key=getattr(settings,"API_KEY",None)
                api_token=getattr(settings,"API_TOKEN",None)

                
                if (camangle=='Forward') or (camangle=='All'):
                    payload = '{\n  \"videoUrl\":\"'+url_forward+'\",\n  \"KmlUrl\":\"'+url_fkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/front", data=payload, headers=headers)
                    #print  fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/front"
                    #print  payload
                    #print  headers
                    #print  response.text
                    #print response 
                    mydb20 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor20 = mydb20.cursor()
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Forward_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mycursor20.execute(sql20)
                    mydb20.commit()
                    mycursor20.close()
                    mydb20.close()

                    mydb21 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor21 = mydb21.cursor()
                    sql21 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Forward","'+url_forward+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor21.execute(sql21)
                    mydb21.commit()
                    mycursor21.close()
                    mydb21.close()

                    mydb25 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor25 = mydb25.cursor()
                    sql25 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Forward","'+url_fkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor25.execute(sql25)
                    mydb25.commit()
                    mycursor25.close()
                    mydb25.close()

                if (camangle=='Backward') or (camangle=='All'):
                    payload = '{\n  \"videoBackUrl\":\"'+url_backward+'\",\n  \"KmlUrlBack\":\"'+url_bkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/back", data=payload, headers=headers)

                 
                                    
                    mydb20 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor20 = mydb20.cursor()
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Backward_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mycursor20.execute(sql20)
                    mydb20.commit()
                    mycursor20.close()
                    mydb20.close()

                    mydb22 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor22 = mydb22.cursor()
                    sql22 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Backward","'+url_backward+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor22.execute(sql22)
                    mydb22.commit()
                    mycursor22.close()
                    mydb22.close()

                    mydb325 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor325 = mydb325.cursor()
                    sql325 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Backward","'+url_bkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor325.execute(sql325)
                    mydb325.commit()
                    mycursor325.close()
                    mydb325.close()

                
                if (camangle=='Left') or (camangle=='All'):
                    payload = '{\n  \"videoLeftUrl\":\"'+url_left+'\",\n  \"KmlUrlLeft\":\"'+url_lkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/left", data=payload, headers=headers)

                   
                    
                    mydb20 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor20 = mydb20.cursor()
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Left_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mycursor20.execute(sql20)
                    mydb20.commit()
                    mycursor20.close()
                    mydb20.close()

                    mydb23 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor23 = mydb23.cursor()
                    sql23 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Left","'+url_left+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor23.execute(sql23)
                    mydb23.commit()
                    mycursor23.close()
                    mydb23.close()

                    mydb125 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor125 = mydb125.cursor()
                    sql125 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Left","'+url_lkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor125.execute(sql125)
                    mydb125.commit()
                    mycursor125.close()
                    mydb125.close()



                if (camangle=='Right') or (camangle=='All'):
                    payload = '{\n  \"videoRightUrl\":\"'+url_right+'\",\n  \"KmlUrlRight\":\"'+url_rkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/right", data=payload, headers=headers)

                    mydb20 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor20 = mydb20.cursor()
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Right_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mycursor20.execute(sql20)
                    mydb20.commit()
                    mycursor20.close()
                    mydb20.close()

                    mydb24 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor24 = mydb24.cursor()
                    sql24 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Right","'+url_right+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor24.execute(sql24)
                    mydb24.commit()
                    mycursor24.close()
                    mydb24.close()

                    mydb225 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor225 = mydb225.cursor()
                    sql225 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Right","'+url_rkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mycursor225.execute(sql225)
                    mydb225.commit()
                    mycursor225.close()
                    mydb225.close()


       
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                mydb26 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor26 = mydb26.cursor()
                sql26 = 'UPDATE routes_progress SET progress="99% Completed ( Done uploading videos ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mycursor26.execute(sql26)
                mydb26.commit()
                mycursor26.close()
                mydb26.close()

                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                mydb27 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor27 = mydb27.cursor()
                sql27 = 'UPDATE routes_progress SET progress="99% Completed ( Generating KML ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mycursor27.execute(sql27)
                mydb27.commit()
                mycursor27.close()
                mydb27.close()
     
                
                if (camangle=='Forward') or (camangle=='All'):
                    try:
                        
                        #stores the duration of forward video to dutn 
                        dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'forward'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn,fkmlcords,base_dir,pdir,dirname,current_date,video,'forward')==1 :
     
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords Received!"
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4')
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.kml')

                        
                
                if (camangle=='Backward') or (camangle=='All'):
                    try:
                        

                        #stores the duration of forward video to dutn 
                        dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'backward'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn,bkmlcords,base_dir,pdir,dirname,current_date,video,'backward')==1 :
                            
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"

                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4')
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.kml')

                if (camangle=='Left') or (camangle=='All'):
                    try:
                            
                            
                        #stores the duration of forward video to dutn 
                        dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'left'+'.mp4').read()
                            
                        #Creates KML file
                        if self.createkml(dutn,lkmlcords,base_dir,pdir,dirname,current_date,video,'left')==1 :
                         
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4')
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.kml')


                if (camangle=='Right') or (camangle=='All'):
                    try:
                            
                        #stores the duration of forward video to dutn 
                        dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'right'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn,rkmlcords,base_dir,pdir,dirname,current_date,video,'right')==1 :
                                

                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4')
                    os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.kml')

                    
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                mydb28 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor28 = mydb28.cursor()
                sql28 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading KML to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mycursor28.execute(sql28)
                mydb28.commit()
                mycursor28.close()
                mydb28.close()
                
                # Remove current video directory and files from server
                os.system('rm -r '+base_dir+pdir+dirname+'/original/'+str(camangle.lower))
                os.system('rm -r '+base_dir+pdir+dirname+'/cropped/'+str(camangle.lower))
                
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                mydb29 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor29 = mydb29.cursor()
                sql29 = 'UPDATE routes_progress SET progress="Generation completed.",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mycursor29.execute(sql29)
                mydb29.commit()
                mycursor29.close()
                mydb29.close()
                
                return routename

                         
        
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
            print "Error - getPathLength"

    def getDestinationLatLong(self,lat,lng,azimuth,distance):
        try:
            '''
            returns the lat an long of destination point 
            given the start lat, long, aziuth, and distance
            '''
            R = 6378.1 #Radius of the Earth in km
            brng = math.radians(azimuth) #Bearing is degrees converted to radians.
            d = float(distance)/1000 #Distance m converted to km
            lat1 = math.radians(lat) #Current dd lat point converted to radians
            lon1 = math.radians(lng) #Current dd long point converted to radians
            lat2 = math.asin(math.sin(lat1) * math.cos(d/R) + math.cos(lat1)* math.sin(d/R)* math.cos(brng))
            lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d/R)* math.cos(lat1), math.cos(d/R)- math.sin(lat1)* math.sin(lat2))
            #convert back to degrees
            lat2 = math.degrees(lat2)
            lon2 = math.degrees(lon2)
            return[lat2, lon2]
        except:
            print "Error - getDestinationLatLong"

    def geocords(self,interval,azimuth,lat1,lng1,lat2,lng2):
        try:
            '''
            returns every coordinate pair inbetween two coordinate 
            pairs given the desired interval
            '''
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
            print "Error - geocords"
    def missingimage(self,data,angle,resln,br,pr,dr,path,fno,rc,pg,rd,sqlid,viewid):
        ''' 
        Increments the coordinates in heading direction 
        until an image is obtained 
        
        data : coordinates
        angle : heading angle
        resln : resolution
        br : base directory 
        pr : project directory
        dr : video directory
        path : view
        fno : file number
        rc : temp coordinate

        '''
        path1=path.lower() # Converts all characters of the string to lowercase

        tmp=0
        times=0
        while(1):
            try:
                tmp=(float(os.stat(br+pr+dr+"/original/"+path1+"/"+str(fno)+".jpg").st_size)/1000)
                break          
            except:
                
                if (rc==0):
                    rc=data
            
                k=int(angle)
                #To keep angle under 360
                if k>360: 
                    k=k-360
                #print k
            
                wsc=rc # Assign rc to a temp varriable wsc
                kc=wsc.split(',') # Split wsc to lat and lng
            
                # Lat is assigned to k1 & lng is assigned to k2
                k1,k2=float(kc[0]),float(kc[1])  
            
             
            
                # Increments the coordinate in the heading direction
                if ((k>=338) and (k<=360)) or ((k>=0) and (k<=23)): #Heading N
                    rc=str(k1+0.00001)+','+str(k2)
                if (k>=24) and (k<=68): #Heading NE
                    rc=str(k1+0.00001)+','+str(k2+0.00001)
                if (k>=69) and (k<=113): #Heading E
                    rc=str(k1)+','+str(k2+0.000001)
                if (k>=114) and (k<=158): #Heading SE
                    rc=str(k1-0.00001)+','+str(k2+0.00001)
                if (k>=159) and (k<=203): #Heading S 
                    rc=str(k1-0.00001)+','+str(k2)
                if (k>=204) and (k<=248): #Heading SW
                    rc=str(k1-0.00001)+','+str(k2-0.00001)
                if (k>=249) and (k<=293): #Heading W
                    rc=str(k1)+','+str(k2-0.00001)
                if (k>=294) and (k<=337): #Heading NW
                    rc=str(k1+0.00001)+','+str(k2-0.00001)
                

                
                #Downloads the image with the incremented coordinate pair
                params = [{
                'size': resln, # max 2048x2048 pixels
                'location': rc,
                'heading': k,
                'pitch': '0.0',
                'fov':'50',

                'key': google_key
                }]
                results = google_streetview.api.results(params)
                results.download_links(br+pr+dr+"/original/"+path1+"/",str(fno))
                
                if(times>100):
                    break
                times=times+1;
                #If an image is downloaded, the loop will exit else it will repeat until an image is obtained
                
            
    def cropfunc(self,b1,p1,d1,c1,res):
        """
        Crops the images present in original folder and stores it in cropped folder
    
        b1 : Base directory
        p1 : Project directory
        d1 : Video directory
        c1 : View
        """
        try:
            cam = c1.lower() # Converts all the characters of a string into lowercase
            
            #Gets the number of files present in the original folder
            path, dirs, files = next(os.walk(b1+p1+d1+"/original/"+cam+"/"))
            file_count = len(files)
            
            i=0
            cropval = (res*280)/1280
            while (i!=file_count):
                try:
                    # Crops the images and stores it in cropped folder using ffmpeg
                    os.system('/usr/bin/ffmpeg -y -i '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-'+str(cropval)+'" -loglevel quiet '+b1+p1+d1+'/cropped/'+cam+'/'+str(i)+'_cropped.jpg')
                    #os.system('/usr/bin/ffmpeg -y -i '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-'+cropval+'" -loglevel quiet '+b1+p1+d1+'/cropped/'+cam+'/'+str(i)+'_cropped.jpg')
                    # Removes the image in original folder to save storage space
                    os.system('rm '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg')
                    i=i+1 #Increments the file number
                    
                except:
                    pass                        
                
        except:
            print "Error - cropfunc" 
        
    def rmspams(self,bd,pd,dnme,ckml):
        '''
        Removes unwanted or spam images from forward folder 
        and crops the images into cropped directory

        All other images are cropped wrt forward images
        If a spam image in forward folder is skipped 
        then images in other views will also get skipped 
        to maintain same video duration 
    
        bd : Base directory
        pd : Project directory
        dnme : Video directory
        ckml : Kml array
    
        returns kml array which contains the coordinates for kml creation
        '''
        try:
            #Gets the file count in forward folder
            path, dirs, files = next(os.walk(bd+pd+dnme+"/original/forward/"))
            file_count = len(files)
            
            w=0 # File number for forward image in cropped folder
            x=0 # File number for backward image in cropped folder
            y=0 # File number for left image in cropped folder
            z=0 # File number for right image in cropped folder
            i=0 # File number for forward image in original folder
            b=1 # File number for adjacent forward image in original folder 
            
            tmp=0
            flag=0
            avg=0.0
            kmlarr=list(); # Kml coordinates are stored into this array and is returned when cropping is finished
            del kmlarr[:] # Empties the kml array

            while i<(file_count-2):
                # Compares adjacent images to check their similarity  
                a = commands.getstatusoutput('compare -metric RMSE '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg '+bd+pd+dnme+'/original/forward/'+str(i+b)+'.jpg NULL:')
                c = commands.getstatusoutput('compare -metric PSNR '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg '+bd+pd+dnme+'/original/forward/'+str(i+b)+'.jpg NULL:')
                d = commands.getstatusoutput('compare -metric FUZZ '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg '+bd+pd+dnme+'/original/forward/'+str(i+b)+'.jpg NULL:')
                val = a[1].split(" ")
                val2 = d[1].split(" ")
                avg = avg+float(val[0])
                cavg = (avg/(i+1))+1000

                try:
                    #if ((float(val[0])<cavg) and (float(c[1])>11) and float(val2[0])<19000) or flag==1: # If compare value is less than 14000 then the images are similar
                    if 1==1: 
                        '''Crops and removes the original image'''
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/forward/'+str(w)+'_cropped.jpg')
                            w=w+1
                            # os.system('rm '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg')
                        except:
                            pass                        
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/backward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/backward/'+str(x)+'_cropped.jpg')
                            x=x+1
                            # os.system('rm '+bd+pd+dnme+'/original/backward/'+str(i)+'.jpg')
                        except:
                            pass
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/left/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/left/'+str(y)+'_cropped.jpg')
                            y=y+1
                            # os.system('rm '+bd+pd+dnme+'/original/left/'+str(i)+'.jpg')
                        except:
                            pass
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/right/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/right/'+str(z)+'_cropped.jpg')
                            z=z+1
                            # os.system('rm '+bd+pd+dnme+'/original/right/'+str(i)+'.jpg')
                        except:
                            pass
                        kmlarr.append(ckml[i]) # Appends the coordinates of the cropped images into the array discards the coordinates of spam images
                        flag=0
                        tmp=val[0]
                        i=i+b
                        b=1 
                    else:
                        i=i+1
                   
                except:
                    i=i+1
                    pass
        except:
            print "Error - Spam frame removal" 
        return kmlarr

    
    
    def firedata(self,rId,dId,br,pr,sqlid,camid,ev):
        '''
        Gets coordinates from firebase,interpolates them 
        using geocords() and will then be passed through Snap To Roads
        Interpolation disabled in this version
        rId : Route id
        dId : Direction
        br : Base directory
        pr : Project directory
         
        returns a list of snapped coordinates
        '''
        if dId == 'Northbound' or dId == 'Westbound':
            dId='a'
        elif dId == 'Southbound' or dId == 'Eastbound':
            dId='b'
        import json
        geopts=0
        fb_creds = getattr(settings, "FBC_"+ev.upper()+"", None)
        fb = firebase.FirebaseApplication(fb_creds, None) # Configure firebase
        
        data=list(); 
        fdata=list();
        del data[:]
        del fdata[:]

        #Sotres coordinates from firebase into geopts
        geopts = fb.get('/route-details-original/'+rId+'/'+dId+'/videoGeoPoints', None)
        
        if(geopts==None):
            #print "No coordinates for : "+str(rId)+" Direction : "+str(dId)
            print threading.current_thread()
            return 0
        if(len(geopts)>0):
            print "Successfully received coordinates of route : "+str(rId)+" Direction : "+str(dId)
        
        for k in range(0,len(geopts)-1):
            try:
                g1=str(geopts[k]).replace(" ","").replace("{","").replace("}","").replace("u'","").split(",")
                lt = g1[0].split(":")
                ln = g1[1].split(":")
                data.append(str(lt[1])+','+str(ln[1]))
            except:
                print "Error: Null value"

        return data

    def interpolate(self,idata):
        
        fdata=list(); 
        del fdata[:]
        
        data=list(); 
        del data[:]


        for k in range(0,len(idata)-1):
            try:
                g1=str(idata[k]).replace(" ","").replace("{","").replace("}","").replace("u'","").split(",")
                lt = g1[0].split(":")
                ln = g1[1].split(":")
                g2=str(idata[k+1]).replace(" ","").replace("{","").replace("}","").replace("u'","").split(",")
                lt1 = g2[0].split(":")
                ln1 = g2[1].split(":")
                angll=self.calculate_initial_compass_bearing((float(str(lt[1])),float(str(ln[1]))),(float(str(lt1[1])),float(str(ln1[1]))))
                fdata.append(self.geocords(1,angll,float(str(lt[1])),float(str(ln[1])),float(str(lt1[1])),float(str(ln1[1]))))
            except:
                print "Error: Null value"
        for x in fdata:
            for y in x:
                data.append(str(y[0])+','+str(y[1]))

        return data

    def interaftersnap(self,gdata):
        
        fdata=list(); 
        del fdata[:]
        
        data=list(); 
        del data[:]


        for k in range(0,len(gdata)-1):
            try:
                g1=str(gdata[k]).split(",")
                g2=str(gdata[k+1]).split(",")
                angll=self.calculate_initial_compass_bearing((float(str(g1[0])),float(str(g1[1]))),(float(str(g2[0])),float(str(g2[1]))))
                fdata.append(self.geocords(5,angll,float(str(g1[0])),float(str(g1[1])),float(str(g2[0])),float(str(g2[1]))))
            except:
                print "Error: Null value"
        for x in fdata:
            for y in x:
                data.append(str(y[0])+','+str(y[1]))

        return data

    def snaptoroads(self,snapdata):
        #---------------------------------------------------------------SNAP TO ROADS : DISABLED--------------------------------------------------------
        
        data=list(); 
        del data[:]

        sndata=list(); 
        del sndata[:]

        for k in range(0,len(snapdata)-1):
            try:
                g1=str(snapdata[k]).replace(" ","").replace("{","").replace("}","").replace("u'","").split(",")
                lt = g1[0].split(":")
                ln = g1[1].split(":")
                data.append(str(lt[1])+','+str(ln[1]))
            except:
                print "Error: Null value"
        
        string=""
        sndata=list();
        fcords=list();
        del sndata[:]
        del fcords[:]
        
        
            
        #Passing interpolated coordinates to snap to roads
        for k in range(1,(len(data)/90)+1):
            
            #Creates a string with 90 coordinates to be passed into snap to roads request
            string =""
            for i in range((k-1)*90,k*90+1):
                string+=data[i]
                if i<k*90:
                    string+="|"
            
            # Prints Progress
            #print "Snapping Progress : "+str(i)+"/"+str(len(data))
            
            
            
            #Requests for snapped coordinates and will store the result into sndata
            result = urllib2.urlopen('https://roads.googleapis.com/v1/snapToRoads?path='+string+'&interpolate=true&key='+google_key)
            htmletxt = result.read()
            snap = json.loads(htmletxt)
            for j in range(0,len(snap['snappedPoints'])):
                try:
                    sndata.append(str(snap['snappedPoints'][j]['location']['latitude'])+','+str(snap['snappedPoints'][j]['location']['longitude']))
                except:
                    print "Out of range"
        
        #Snaps the remaining coordinates  
        string =""
        for a in range(int(len(data)/90)*90,len(data)):
            string+=data[a]
            if a<len(data)-1:
                string+="|"

        #print "Snapping Progress : "+str(a)+"/"+str(len(data))
        
        
        
        result = urllib2.urlopen('https://roads.googleapis.com/v1/snapToRoads?path='+string+'&interpolate=true&key='+google_key)
        htmletxt = result.read()
        snap = json.loads(htmletxt)
        for j in range(0,len(snap['snappedPoints'])):
            try:
                sndata.append(str(snap['snappedPoints'][j]['location']['latitude'])+','+str(snap['snappedPoints'][j]['location']['longitude']))
            except:
                print "Out of range"
        
        
        return sndata

        #---------------------------------------------------------------------------------------------------------------------------------------------


    def grabimage(self,data,angle,res,br,pr,dr,path,fno):
        ''' 
        Downloads the image using google street view api
         
        data : coordinates
        angle : heading angle
        resln : resolution
        br : base directory 
        pr : project directory
        dr : video directory
        path : view
        fno : file number

        '''
        try:
            if angle>360:
                angle=angle-360
            resval = (res*720)/1280
            cropval = (res-resval)/2
            params = [{
              'size': str(res)+'x'+str(resval+cropval), # max 2048x2048 pixels
              'location': data,
              'heading': angle,
              'pitch': '0.0',
              'fov':'70',
              'source':'outdoor',
              'radius' : 50,
              'key': google_key
            }]
            results = google_streetview.api.results(params)
            results.download_links(br+pr+dr+"/original/"+path+"/",str(fno))
                
        except:
            print "Error - grab image"
        
    def calculate_initial_compass_bearing(self,pointA, pointB):
        '''Calculate bearing/heading angle'''
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
            print "Error - calculate_initial_compass_bearing"

    def createkml(self,timeinmsec,data,base,pi,di,cd,video,angname):
        '''
        Creates kml wrt video duration
        
        timeinsec : video duration
        data : kml coordinates 
        base : Base directory
        pi : Project directory
        di : Video directory
        video : view
        
        *Number of coordinates = Number of frames

        returns 1 if kml is successfully created
        
        '''
        try:
            time=0;
            tme=0;

            #Gets current date and time
            now = datetime.datetime.now()
            
            #time= (video duration in seconds) / (number of coordinates)
            time=(float(timeinmsec)/1000)/(len(data))
            
            f = open(base+pi+di+"/"+cd+"_"+video+"_"+angname+".kml", "w+")
            f.write("""<?xml version="1.0" encoding="UTF-8"?> <kml xmlns="http://www.opengis.net/kml/2.2">\n""")
            f.write("<Document>")
            for i in range(0,len(data)):
                try:
                    a = data[i].split(',')
                    a3 = a[-1].split(' ')
                    f.write('\n <SchemaData>')
                    f.write('\n   <SimpleData name="Lat">'+a[0]+'</SimpleData>')
                    f.write('\n   <SimpleData name="Lon">'+a3[-1]+'</SimpleData>')
                    f.write('\n   <SimpleData name="UTC_Date">'+str(now.day)+'/'+str(now.month)+'/'+str(now.year)+'</SimpleData>')
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
            print "Error - createkml"
   
class generate :
    def routedown(self,routeid):
        '''
        Creates an object for each direction
        and calls download() in class Google

        '''
        #print routeid
        Route=['Arrayname','Route_ID','Direction','View','Resolution','environment'] # Defined the list

        Route[0]=routeid[0]
        Route[1]=routeid[1]
        Route[2]=routeid[2]
        Route[3]=routeid[3]
        Route[4]=routeid[4]
        Route[5]=routeid[5]
        
        
        if (routeid[2]=='both'):
            Route[2]='a'
            google = Google()
            google.download(Route)
            Route[2]='b'
            g1 = Google()
            g1.download(Route)
        else:
            google = Google()
            google.download(Route)
            
    

class index(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'base.html', context=None)
    def post(self, request):
        if request.body != '':
            
            ''' 
            Creates a thread on each request
            request.body : String which contains the Route_id , Direction and View  
            '''

            routes=list() # Created a list to store the route id direction and view 
            gen_flag = list()
            del routes[:] # Empty the contents of the list 
            
            routes=['Arrayname','Route_ID','Direction','View','Resolution','environment'] # Defined the list
            d1=request.body.replace('"',"").replace("[","").replace("]","").split(',') # Strips away all the unwanted characters from the above string 
            d2 = d1[1].split('-')
            ores = d1[4]
            env = d1[5]
            aws_key = getattr(settings, "AWS_"+env.upper()+"_KEY", None)
            aws_secret = getattr(settings, "AWS_"+env.upper()+"_KEY", None)

            resolutions=["High","Low"]
            if (d1[0]=="rid"):
                #d2[0] = "10 "
               
                '''Set the direction to a if string is West and b if string is East'''
                
                routes[0]="rid" #Changes the 1st element of the array to rid
                routes[1]=d2[0].replace(" ","") #Removes the white space in "10 " and stores it to the 2nd element of the array which is route_id
                routes[2]=d1[2] # Stores the direction
                routes[3]=d1[3] #Stores the View to 4th element of the array which is camangle
                routes[4]=ores
                routes[5]=env
                ''' calls routedown function in class generate as a thread '''
                if ores!='All':
                    thd = threading.Thread(target=generate().routedown,args=(routes,))
                    thd.setDaemon(True) # sets the thread as daemon thread
                    thd.start() # starts the thread
                
                if ores=='All':
                    routes[4]='High'
                    thd = threading.Thread(target=generate().routedown,args=(routes,))
                    thd.setDaemon(True) # sets the thread as daemon thread
                    thd.start() # starts the thread
                    time.sleep(5)
                    routes[4]='Low'
                    thd1 = threading.Thread(target=generate().routedown,args=(routes,))
                    thd1.setDaemon(True) # sets the thread as daemon thread
                    thd1.start() # starts the thread
                

                return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')
            elif (d1[0]=="dbinfo"):
                stats=list();
                cstats=list();
                del stats[:];
                del cstats[:];
                ptime=0
                stime=0
                
                mydb32 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                mycursor32 = mydb32.cursor()
                sql32 = 'SELECT * FROM routes_progress WHERE progress < 100'
                mycursor32.execute(sql32)
                stats = mycursor32.fetchall()
                mycursor32.close()
                mydb32.close()
                sqlstring="";
                for resl in resolutions:
                    
                    mydb33 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                    mycursor33 = mydb33.cursor()
                    sql33 = 'SELECT * FROM routes_progress WHERE route_id='+d2[0].replace(" ","")+' AND direction="'+d1[2]+'" AND view="'+d1[3]+'" AND resolution="'+resl+'" AND environment="'+env+'"'
                    mycursor33.execute(sql33)
                    cstats = mycursor33.fetchall()
                    mycursor33.close()
                    mydb33.close()
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    try:
                        ptime=(int(currentmin)-int(cstats[0][5]))
                        if(ptime<0):
                            ptime=ptime+60
                    
                        if (ptime>15):
                
                            mydb34 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                            mycursor34 = mydb34.cursor()
                            sql34 = 'UPDATE routes_progress SET gen_status=1 WHERE route_id='+str(cstats[0][1])+' AND direction="'+cstats[0][2]+'" AND view="'+cstats[0][3]+'" AND resolution="'+resl+'" AND environment="'+env+'"'
                            mycursor34.execute(sql34)
                            mydb34.commit()
                            mycursor34.close()
                            mydb34.close()
                            pass
                    
                
                        
                        if cstats[0][4]:
                            sqlstring+=str(cstats[0][1])+'/'+str(cstats[0][2])+'/'+str(cstats[0][3])+'/'+str(cstats[0][4])+'/'+str(cstats[0][6])+'/'+cstats[0][7]+'/'+cstats[0][8]+'|'
                        else:
                            sqlstring+=str(d2[0].replace(" ",""))+'/'+str(d1[2])+'/'+str(d1[3])+'/Please click on generate to start video generation./0/'+ores+'/'+env+'|'
                        
                    except:
                        sqlstring+=str(d2[0].replace(" ",""))+'/'+str(d1[2])+'/'+str(d1[3])+'/Please click on generate to start video generation./0/'+ores+'/'+env+'|'

                        pass

                for i in range(0,len(stats)):
                    if 1==1:
                        stime=(int(currentmin)-int(stats[i][5]))
                        if(stime<0):
                            stime=stime+60
                        if(stime>15):
                            mydb36 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                            mycursor36 = mydb36.cursor()
                            sql36 = 'UPDATE routes_progress SET gen_status=1 WHERE route_id='+str(stats[i][1])+' AND direction="'+stats[i][2]+'" AND view="'+stats[i][3]+'" AND resolution="'+stats[i][7]+'" AND environment="'+env+'"'
                            mycursor36.execute(sql36)
                            mydb36.commit()
                            mycursor36.close()
                            mydb36.close()
                        try:
                            if d1[3]=="All":
                                vw="Forward"
                            else:
                                vw=d1[3]
                            mydb38 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                            mycursor38 = mydb38.cursor()
                            sql38 = 'SELECT date_time FROM routes_log WHERE route_id='+str(stats[i][1])+' AND direction="'+str(stats[i][2])+'" AND type="VIDEO_'+str(vw)+'" AND resolution="'+stats[i][7]+'" AND environment="'+stats[i][8]+'" ORDER BY id DESC LIMIT 1'

                            mycursor38.execute(sql38)
                            dt = mycursor38.fetchall()
                            mycursor38.close()
                            mydb38.close()
                        except:
                            pass
                        try:
                            sqlstring+=str(stats[i][1])+'/'+str(stats[i][2])+'/'+str(stats[i][3])+'/'+str(stats[i][4])+'/'+str(stats[i][6])+'/'+stats[i][7]+'/'+stats[i][8]+'/'+str(dt[0][0])
                        except:
                            sqlstring+=str(stats[i][1])+'/'+str(stats[i][2])+'/'+str(stats[i][3])+'/'+str(stats[i][4])+'/'+str(stats[i][6])+'/'+stats[i][7]+'/'+stats[i][8]+'/'+str(str(os.popen('date').read()).replace("\n","").replace(" ","_"))

                        if i<len(stats):
                            sqlstring+="|"

                return HttpResponse(sqlstring)
            elif (d1[0]=='awslinks'):
                timee=""
                for resl in resolutions:
                    try:
                        if d1[3]=="All":
                            vw="Forward"
                        else:
                            vw=d1[3]
                        mydb38 = mysql.connector.connect(host=my_host,user=my_user,passwd=my_password,database=my_db,buffered=True)
                        mycursor38 = mydb38.cursor()
                        sql38 = 'SELECT date_time FROM routes_log WHERE route_id='+d2[0].replace(" ","")+' AND direction="'+d1[2]+'" AND type="VIDEO_'+vw+'" AND resolution="'+resl+'" AND environment="'+env+'" ORDER BY id DESC LIMIT 1'

                        mycursor38.execute(sql38)
                        dt = mycursor38.fetchall()
                        mycursor38.close()
                        mydb38.close()
                    except:
                        pass
                    try:
                        timee+=str(dt[0][0])+"/"
                    except:
                        pass
                    
                return HttpResponse(timee)
