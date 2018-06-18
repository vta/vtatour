import os
import sys
import math
import json
import hmac
import base64
import urllib2
import hashlib
import commands
import urlparse
import datetime
import threading
import subprocess
import numpy as np
import google_streetview.api
from firebase import firebase
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from math import cos, sin, atan2, sqrt, radians, degrees, asin, modf

class Google(object):
    
    global fps
    fps='2.01' # Set video frame rate (frames per second)
    
    global firebase
    firebase = firebase.FirebaseApplication('https://vtavirtualtransit-7c904.firebaseio.com', None) # Configure firebase

    def download(self,data):
        if len(data)==4 : # checks if data has 4 elements
            if data[0]=='rid': #checks if the first element is 'rid'
                m=0 #Sets file number to 0
                routename = data[1] # Stores route id into routename
                dirid = data[2] # Stores direction into dirid
                camangle = data[3] # Stores view into camangle
                dirname = routename +'/'+ dirid #Stores base path of video directories
                video = routename+"_"+dirid #Base name of the video
                
                #Prints route id and direction in terminal
                print "Route_ID : ",routename  
                print "Direction : ",dirid

                base_dir = '/home/crowdplat/vta' #Base directory
                pdir='/' # Project directory
                
                sdata=list();
                kmlcords=list();
                fkml=list();
                del fkml[:]
                del kmlcords[:]
                del sdata[:]
                
                '''Creates the progress file and writes 201(if UI reads 201 it will display fetching coordinates)'''
                
                with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                    fh.write('201')
                    fh.close()
                    os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", 0o777)
                
                '''
                Status is set to zero if coordinates are fetched from firebase
                Status is set to one if coordinates are fetched from kml
                '''
                if (camangle=='All'):
                    sdata = self.firedata(routename,dirid,base_dir,pdir) # Gets coordinates from firebase
                    status=0 
                elif (camangle=='Forward'):
                    sdata = self.firedata(routename,dirid,base_dir,pdir) # Gets coordinates from firebase
                    status=0
                else:
                    status=1
                    sdata = self.kmldata(routename,dirid,base_dir,pdir) # Gets coordinates from kml
                    try:
                        if sdata==404:# If kml is not available coordinates will be fetched from firebase and new kml will be generated 
                            if camangle=='Forward':
                                sdata = self.firedata(routename,dirid,base_dir,pdir) # Gets coordinates from firebase
                            else:
                                try:
                                    #If View is Left, Right or Backward Overwrites 405 to progress file (UI will display create forward first)
                                    with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                                        fh.write('405')
                                        fh.close()
                                        os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", 0o777)
                                        return 0
                                except:
                                    pass
                    except:
                        pass

                # If no coordinates are present in firebase ,execution will stop here                
                if sdata==0: 
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
                except:
                    print "Directory exists!"
                    pass
                
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

                    # Compares adjacent coordinates to avoid downloading duplicate images only if status is 0 (Coordinates are fetched from firebase)
                    if status==0: 
                        try:
                        	   # Stores the metadata response(JSON) of rcord into htmltext
                            result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+rcord+'&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
                            htmletxt = result.read()
                            
                            # Converts it into JSON format and stores it into snap
                            snap = json.loads(htmletxt)
                            
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
                            pass
                    else:
                        rm=1 # If status is 1 rm is set to 1                      

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

                            except:
                                pass 
                            ang=int(self.calculate_initial_compass_bearing((a1,a2),(b1,b2))) # Calculate the Heading angle (Bearing angle)
                            
                            prog=(float(i)/(len(sdata)))*100 # Calculate the progress
                            
                            '''
                            Creates threads to download each Street view image
                            All threads are set to daemon (daemon thread closes automatically)
                            
                            Images are downloaded using grabimage() 

                            grabimage(coordinates,angle,resolution,basedirectory,projectdirectory,videodirectory,view,filenumber)
                                   
                            '''

                            if (camangle=='Forward') or (camangle=='All'):
                            	fwd=threading.Thread(target=self.grabimage,args=(ocord,ang+0,'1280x1000',base_dir,pdir,dirname,'forward',m,))
                                fwd.setDaemon(True)
                                fwd.start()
                            if (camangle=='Backward') or (camangle=='All'):
                                bck=threading.Thread(target=self.grabimage,args=(ocord,ang+180,'1280x1000',base_dir,pdir,dirname,'backward',m,))
                                bck.setDaemon(True)
                                bck.start()
                                
                            if (camangle=='Left') or (camangle=='All'):
                                lft=threading.Thread(target=self.grabimage,args=(ocord,ang+270,'1280x1000',base_dir,pdir,dirname,'left',m,))
                                lft.setDaemon(True)
                                lft.start()
                               
                            if (camangle=='Right') or (camangle=='All'):
                                rgt=threading.Thread(target=self.grabimage,args=(ocord,ang+90,'1280x1000',base_dir,pdir,dirname,'right',m,))
                                rgt.setDaemon(True)
                                rgt.start()
                               
                            try:
                            	   # Writes percentage of progress to the progress file
                                with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                                    fh.write(str(int(prog)))
                                    fh.close()
                                    os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", 0o777)
                            except:
                                pass

                            if (camangle=='Forward'):
                                try:
                                    fwd.join() # Waits till forward thread exits

                                    #Checks if forward image is downloaded by checking if its size is greater than 10kb 
                                    if ((float(os.stat(base_dir+pdir+dirname+"/original/forward/"+str(m)+".jpg").st_size)/1000)>10):
                                        kmlcords.append(ocord) # If image is downloaded ocord gets added to kml array
                                        m=m+1 # Increment file number
                                        ocord = rcord # To download next image
                                except:
                                    ocord = rcord 
                                    pass
                            if (camangle=='Backward'):
                                try:
                                    bwk.join() # Waits till backward thread exits
                                    
                                    #Checks if backward image is downloaded by checking if its size is greater than 10kb 
                                    if ((float(os.stat(base_dir+pdir+dirname+"/original/backward/"+str(m)+".jpg").st_size)/1000)>10):
                                        m=m+1 # Increment file number
                                        ocord = rcord # To download next image
                                except:
                                	   
                                	   # Will increment the coordinates in the heading direction until the missing image is downloaded
                                    self.missingimage(ocord,ang+180,'1280x1000',base_dir,pdir,dirname,camangle,m,0)
                                    m=m+1 # Increment file number
                                    ocord=rcord # To download next image
                                    pass
                            if (camangle=='Left'):
                                try:
                                    lft.join() # Waits till left thread exits
                                    
                                    #Checks if left image is downloaded by checking if its size is greater than 10kb 
                                    if ((float(os.stat(base_dir+pdir+dirname+"/original/left/"+str(m)+".jpg").st_size)/1000)>10):
                                        m=m+1 # Increment file number
                                        ocord = rcord # To download next image
                                except:
                                    
                                    # Will increment the coordinates in the heading direction until the missing image is downloaded
                                    self.missingimage(ocord,ang+270,'1280x1000',base_dir,pdir,dirname,camangle,m,0)
                                    m=m+1 # Increment file number
                                    ocord=rcord # To download next image
                                    pass
                            if (camangle=='Right'):
                                try:
                                    rgt.join() # Waits till right thread exits
                                    
                                    #Checks if right image is downloaded by checking if its size is greater than 10kb 
                                    if ((float(os.stat(base_dir+pdir+dirname+"/original/right/"+str(m)+".jpg").st_size)/1000)>10):
                                        m=m+1 # Increment file number
                                        ocord = rcord # To download next image
                                except:
                                    
                                    # Will increment the coordinates in the heading direction until the missing image is downloaded
                                    self.missingimage(ocord,ang+90,'1280x1000',base_dir,pdir,dirname,camangle,m,0)
                                    m=m+1 # Increment file number
                                    ocord=rcord # To download next image
                                    pass
                            
                            if (camangle=='All'):
                                try:

                                    # Checks if all images are downloaded
                                    if ((float(os.stat(base_dir+pdir+dirname+"/original/forward/"+str(m)+".jpg").st_size)/1000)>10):
                                        if ((float(os.stat(base_dir+pdir+dirname+"/original/right/"+str(m)+".jpg").st_size)/1000)>10):
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/backward/"+str(m)+".jpg").st_size)/1000)>10):
                                                if ((float(os.stat(base_dir+pdir+dirname+"/original/left/"+str(m)+".jpg").st_size)/1000)>10):
                                                    kmlcords.append(ocord) #ocord is added to kml array for kml creation
                                                    m=m+1 # Increment file number
                                                    ocord = rcord # To download next image
                                                  
                                except:
                                    ocord = rcord # To download next image
                                    pass
                            #Print the progress        
                            print "Route/dir: "+str(dirname)+" Progress : "+str(int(prog))+"% Downloading Image "+str(m)+" Status : OK"
                            
                        except:
                        	   #Calculate the progress
                            prog=(float(i)/(len(sdata)))*100

                            #Print the progress
                            print "Route_ID : "+str(dirname)+" Progress : "+str(int(prog))+"% Downloading Image "+str(m)+" Status : ERR"
                            try:
                                #Write the progress percentage to progress file
                                with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                                    fh.write(str(int(prog)))
                                    fh.close()
                                    os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", 0o777)
                            except:
                                pass
                            pass
                
                # Writes 100 to the progress file when downloads are done (UI will display Creating videos)
                try: 
                    with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                        fh.write("100")
                        fh.close()
                        os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+".txt", 0o777)
                except:
                    pass
                

                if(camangle=='All') or (camangle=='Forward'):
                    # Removes unwanted frames and crop the original images
                    fkml = self.rmspams(base_dir,pdir,dirname,kmlcords)
                else:
                    # Crops the original images
                    self.cropfunc(base_dir,pdir,dirname,camangle)

                # Prints Creating and uploading videos to s3 in terminal     
                print "Creating and uploading videos to s3"
                if (camangle=='Forward') or (camangle=='All'):
                    #Creates forward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_forward.mp4')
                    #Uploads forward video to s3
                    os.system('AWS_ACCESS_KEY_ID=AKIAIM2H3SCFWUPW4DZQ AWS_SECRET_ACCESS_KEY=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 aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_forward.mp4 s3://vta-tour-rtmp/'+routename+'/ --acl public-read-write')
                    #stores the duration of forward video to dutn 
                    dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+video+'_'+'forward'+'.mp4').read()
                    try:
                        #Creates KML file
                        if self.createkml(dutn,fkml,base_dir,pdir,dirname,video)==1 :
                            print "Uploading Kml"
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID=AKIAIM2H3SCFWUPW4DZQ AWS_SECRET_ACCESS_KEY=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 aws s3 cp '+base_dir+pdir+dirname+'/'+video+'.kml s3://vta-tour-rtmp/'+routename+'/ --acl public-read-write')
                            print "Done uploading Kml!"
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                                    
                if (camangle=='Backward') or (camangle=='All'):
                    #Creates backward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_backward.mp4')
                    #Upload backward video to s3
                    os.system('AWS_ACCESS_KEY_ID=AKIAIM2H3SCFWUPW4DZQ AWS_SECRET_ACCESS_KEY=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 aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_backward.mp4 s3://vta-tour-rtmp/'+routename+'/ --acl public-read-write')
                
                if (camangle=='Left') or (camangle=='All'):
                    #Create Left video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_left.mp4')
                    #Upload left video to s3
                    os.system('AWS_ACCESS_KEY_ID=AKIAIM2H3SCFWUPW4DZQ AWS_SECRET_ACCESS_KEY=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 aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_left.mp4 s3://vta-tour-rtmp/'+routename+'/ --acl public-read-write')
                
                if (camangle=='Right') or (camangle=='All'):
                    #Create right video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+video+'_right.mp4')
                    #Upload right video to s3
                    os.system('AWS_ACCESS_KEY_ID=AKIAIM2H3SCFWUPW4DZQ AWS_SECRET_ACCESS_KEY=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 aws s3 cp '+base_dir+pdir+dirname+'/'+video+'_right.mp4 s3://vta-tour-rtmp/'+routename+'/ --acl public-read-write')
                
                #Prints Done uploading videos in terminal
                print "Done uploading videos!"
                
                # Remove current video directory and files from server
                os.system('rm -r '+base_dir+pdir+routename+'/')
                print "Removed directory :",base_dir+pdir+routename,"/ !"
                
                #Writes 101 to progress file (UI will display the links to the videos and kml)
                try:
                    with open(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", "w+") as fh:
                        fh.write('101')
                        fh.close()
                        os.chmod(base_dir+pdir+"static/"+routename+"_"+dirid+"_"+camangle+".txt", 0o777)
                except:
                    pass

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
    def missingimage(self,data,angle,resln,br,pr,dr,path,fno,rc):
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

        # If no image is downloaded a plain black image of size less than 10kb is created
        os.system('convert -size 1280x1000 xc:black '+base_dir+pdir+dirname+'/original/'+path1+'/'+str(m)+'.jpg')
       
        while((float(os.stat(br+pr+dr+"/original/"+path1+"/"+str(fno)+".jpg").st_size)/1000)<10):

            if (rc==0):
                rc=data
            
            k=int(angle)
            #To keep angle under 360
            if k>360: 
                k=k-360
            
            wsc=rc # Assign rc to a temp varriable wsc
            kc=wsc.split(',') # Split wsc to lat and lng
            
            # Lat is assigned to k1 & lng is assigned to k2
            k1,k2=float(kc[0]),float(kc[1])  
            
            # Round off the coordinates to improve the chances to getting the missing image
            if len(str(k1))>8:
                r1=round(k1,5)
            else:
                r1=k1
            if len(str(k2))>8:
                r2=round(k2,5)
            else:
                r2=k2
            
            # Increments the coordinate in the heading direction
            if ((k>=338) and (k<=360)) or ((k>=0) and (k<=23)): #Heading N
                rc=str(k1+0.000005)+','+str(k2)
            if (angle>=24) and (angle<=68): #Heading NE
                rc=str(k1+0.000005)+','+str(k2+0.000005)
            if (angle>=69) and (angle<=113): #Heading E
                rc=str(k1)+','+str(k2+0.000005)
            if (angle>=114) and (angle<=158): #Heading SE
                rc=str(k1-0.000005)+','+str(k2+0.000005)
            if (k>=159) and (k<=203): #Heading S 
                rc=str(k1-0.000005)+','+str(k2)
            if (angle>=204) and (angle<=248): #Heading SW
                rc=str(k1-0.000005)+','+str(k2-0.000005)
            if (angle>=249) and (angle<=293): #Heading W
                rc=str(k1)+','+str(k2-0.000005)
            if (angle>=294) and (angle<=337): #Heading NW
                rc=str(k1+0.000005)+','+str(k2-0.000005)

            rcord1=str(r1)+','+str(r2) #creates the incremented coordinate pair

            #Downloads the image with the incremented coordinate pair
            params = [{
              'size': resln, # max 2048x2048 pixels
              'location': rcord1,
              'heading': k,
              'pitch': '0.0',
              'key': 'AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0'
            }]
            results = google_streetview.api.results(params)
            results.download_links(br+pr+dr+"/original/"+path1+"/",str(fno))

            #If an image is downloaded, the loop will exit else it will repeat until an image is obtained
            
            
    def cropfunc(self,b1,p1,d1,c1):
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
            while i!=(file_count):
                try:
                    print i
                    # Crops the images and stores it in cropped folder using ffmpeg
                    os.system('/usr/bin/ffmpeg -y -i '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+b1+p1+d1+'/cropped/'+cam+'/'+str(i)+'_cropped.jpg')
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

            kmlarr=list(); # Kml coordinates are stored into this array and is returned when cropping is finished
            del kmlarr[:] # Empties the kml array

            while i<(file_count-2):
                # Compares adjacent images to check their similarity  
                a = commands.getstatusoutput('compare -metric RMSE '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg '+bd+pd+dnme+'/original/forward/'+str(i+b)+'.jpg NULL:')
                val = a[1].split(" ")
                try:
                    if flag==1 or float(val[0])<14000: # If compare value is less than 14000 then the images are similar
                        '''Crops and removes the original image'''
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/forward/'+str(w)+'_cropped.jpg')
                            w=w+1
                            os.system('rm '+bd+pd+dnme+'/original/forward/'+str(i)+'.jpg')
                        except:
                            pass                        
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/backward/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/backward/'+str(x)+'_cropped.jpg')
                            x=x+1
                            os.system('rm '+bd+pd+dnme+'/original/backward/'+str(i)+'.jpg')
                        except:
                            pass
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/left/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/left/'+str(y)+'_cropped.jpg')
                            y=y+1
                            os.system('rm '+bd+pd+dnme+'/original/left/'+str(i)+'.jpg')
                        except:
                            pass
                        try:
                            os.system('/usr/bin/ffmpeg -y -i '+bd+pd+dnme+'/original/right/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-280" -loglevel quiet '+bd+pd+dnme+'/cropped/right/'+str(z)+'_cropped.jpg')
                            z=z+1
                            os.system('rm '+bd+pd+dnme+'/original/right/'+str(i)+'.jpg')
                        except:
                            pass
                        kmlarr.append(ckml[i]) # Appends the coordinates of the cropped images into the array discards the coordinates of spam images
                        flag=0
                        tmp=val[0]
                        i=i+b
                        b=1 
                    else:
                    #Scans for the next similar image
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
        return kmlarr

    def kmldata(self,routeid,dirid,base,pd):
        '''
        Read coordinates from kml file
        
        routeid : Route ID
        dirid : Direction
        base :  Base directory
        pd : Project directory
    
        returns kml coordinates if kml is available 
        else function returns 404 is kml is not available 
    
        '''
        chdkml=list(); # list to store the coordinates
        del chdkml[:]
        
        filename=base+pd+"static/"+routeid+"_"+dirid+".kml"
        
        #Remove the kml file if its already present in the server
        try:
            os.system("rm "+filename)
        except:
            pass
        
        #Downloads the kml file
        try:
            os.system("wget -P "+base+pd+"static/ https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/"+routeid+"/"+routeid+"_"+dirid+".kml") 
            os.chmod(filename, 0o777)
            try:
                with open(filename, "a+") as fh:
                    fh.write('</kml>')
                    fh.close()
                    os.chmod(filename, 0o777)
            except:
                pass
            
            # Read and store the coordinates into chdkml
            tree = ET.parse(filename)
            root = tree.getroot()
            for i in range(0,len(root[0])):
                chdkml.append(str(round(float(root[0][i][0].text),5))+','+str(round(float(root[0][i][1].text),5)))
        
        except:
            pass
        try:

            if chdkml==None:
                return 404
        except:
            pass
        
        if len(chdkml)<10:
            return 404
        else:
            return chdkml
    
    def firedata(self,rId,dId,br,pr):
        '''
        Gets coordinates from firebase,interpolates them 
        using geocords() and will then be passed through Snap To Roads

        rId : Route id
        dId : Direction
        br : Base directory
        pr : Project directory
         
        returns a list of snapped coordinates
        '''
        import json
        geopts=0
        
        data=list(); 
        fdata=list();
        del data[:]
        del fdata[:]

        #Sotres coordinates from firebase into geopts
        geopts = firebase.get('/route-details/'+rId+'/'+dId+'/originalVideoGeoPoints', None)
        
        if(geopts==None):
            print "No coordinates for : "+str(rId)+" Direction : "+str(dId)
            print threading.current_thread()
            return 0
        if(len(geopts)>0):
            print "Successfully received coordinates of route : "+str(rId)+" Direction : "+str(dId)
        

        # Interpolate geopts using geocords()
        for k in range(0,len(geopts)):
            try:
                angll=self.calculate_initial_compass_bearing((geopts[k]['lat'],geopts[k]['lng']),(geopts[k+1]['lat'],geopts[k+1]['lng']))
                fdata.append(self.geocords(1,angll,geopts[k]['lat'],geopts[k]['lng'],geopts[k+1]['lat'],geopts[k+1]['lng']))
            except:
                print "Error Null value"
        
        for x in fdata:
            for y in x:
                data.append(str(y[0])+','+str(y[1]))
        

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
            print "Snapping Progress : "+str(i)+"/"+str(len(data))
            
            #Requests for snapped coordinates and will store the result into sndata
            result = urllib2.urlopen('https://roads.googleapis.com/v1/snapToRoads?path='+string+'&interpolate=true&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
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

        print "Snapping Progress : "+str(a)+"/"+str(len(data))
        result = urllib2.urlopen('https://roads.googleapis.com/v1/snapToRoads?path='+string+'&interpolate=true&key=AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0')
        htmletxt = result.read()
        snap = json.loads(htmletxt)
        for j in range(0,len(snap['snappedPoints'])):
            try:
                sndata.append(str(snap['snappedPoints'][j]['location']['latitude'])+','+str(snap['snappedPoints'][j]['location']['longitude']))
            except:
                print "Out of range"
      
        
        return sndata
            
    def grabimage(self,data,angle,resln,br,pr,dr,path,fno):
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
            
            params = [{
              'size': resln, # max 2048x2048 pixels
              'location': data,
              'heading': angle,
              'pitch': '0.0',
              'key': 'AIzaSyC2zG8n0SSvjlED4driQO4cSToszU0WIc0'
            }]
            results = google_streetview.api.results(params)
            results.download_links(br+pr+dr+"/original/"+path+"/",str(fno))
                
        except:
            print "Error - grabimage"
        
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

    def createkml(self,timeinmsec,data,base,pi,di,video):
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
            print "Creating KML"
            time=0;
            tme=0;

            #Gets current date and time
            now = datetime.datetime.now()
            
            #time= (video duration in seconds) / (number of coordinates)
            time=(float(timeinmsec)/1000)/(len(data))
            
            f = open(base+pi+di+"/"+video+".kml", "w+")
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
        print routeid
        Route=['Arrayname','Route_ID','Direction','View'] # Defined the list

        Route[0]=routeid[0]
        Route[1]=routeid[1]
        Route[2]=routeid[2]
        Route[3]=routeid[3]
        
        if (routeid[2]=='a') or (routeid[2]=='both'):
            Route[2]='a'
            google = Google()
            google.download(Route)
        if (routeid[2]=='b') or (routeid[2]=='both'):
            Route[2]='b'
            g1 = Google()
            g1.download(Route)

    

class index(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)
    def post(self, request):
        if request.body != '':
            
            ''' 
            Creates a thread on each request
            request.body : String which contains the Route_id , Direction and View  
            '''
            
            routes=list() # Created a list to store the route id direction and view 
            del routes[:] # Empty the contents of the list 
            
            routes=['Arrayname','Route_ID','Direction','View'] # Defined the list
            
            #request.body : ["rid","10 - Santa Clara Transit to Metro Airport","West","All"]
            d1=request.body.replace('"',"").replace("[","").replace("]","").split(',') # Strips away all the unwanted characters from the above string 
            #d1 : [rid,10 - Santa Clara Transit to Metro Airport,West,All] 
            
            d2 = d1[1].split('-')#Splits "10 - Santa Clara Transit to Metro Airport" to two elements "10 " and " Santa Clara Transit to Metro Airport"
            #d2[0] = "10 "
            
            '''Set the direction to a if string is West and b if string is East'''
            if (d1[2]=='West'):
                dirr = 'a'
            if (d1[2]=='East'):
                dirr = 'b'
            if (d1[2]=='Both'):
                dirr = 'both'
            
            
            routes[0]="rid" #Changes the 1st element of the array to rid
            routes[1]=d2[0].replace(" ","") #Removes the white space in "10 " and stores it to the 2nd element of the array
            routes[2]=dirr # Stores the direction to 3rd element of the array
            routes[3]=d1[3] #Stores the View to 4th element of the array
            
            ''' calls routedown function in class generate as a thread '''
            thd = threading.Thread(target=generate().routedown,args=(routes,))
            thd.setDaemon(True) # sets the thread as daemon thread
            thd.start() # starts the thread
                     
            return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')



