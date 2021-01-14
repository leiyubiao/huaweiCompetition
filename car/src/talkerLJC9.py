#!/usr/bin/env python
# license removed for brevity
import rospy
import socket
import time
from std_msgs.msg import Int32
from collections import deque



       
def talker():
    host='192.168.2.111'
    port=7777
      
    pub1 = rospy.Publisher('/hilens', Int32 , queue_size=10)
    rospy.init_node('talker', anonymous=True)
    rate = rospy.Rate(10) # 10hz

    start_time=time.time()+500
  

    # global flag 
    flag=0


    '''
    labeldict for each flag
    '''
    labeldict={0:'green_go',1:'pedestrian_crossing',2:'speed_limited',3:'speed_unlimited',4:'pedestrian_crossing',5:'anything',6:'anything'}
    
    # initial queue for each condition(for situation in labeldict)
    green_go_num=deque([0,0,0,0,0,0,0],maxlen=7)
    pedestrian_crossing_num1=deque([0,0,0,0,0,0,0],maxlen=7)
    speed_limited_num=deque([0,0,0,0,0,0,0],maxlen=7)
    speed_unlimited_num=deque([0,0,0,0,0,0,0],maxlen=7)
    pedestrian_crossing_num2=deque([0,0,0,0,0,0,0],maxlen=7)

    pedestrian_crossing_no_see1=deque([0,0,0,0,0,0,0,0,0,0],maxlen=10)
    pedestrian_crossing_no_see2=deque([0,0,0,0,0,0,0,0,0,0],maxlen=10)
  

    yellow_back_num=deque([0,0,0,0,0,0,0,0,0,0],maxlen=10)


    tmparea=0

    havesepds1=0
    havesepds2=0
    yellowflag=0


    while not rospy.is_shutdown():
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
        s.connect((host,port))      
        data=s.recv(1024)


        # the situation that don't see anything
        if len(data)==0:
            print('null')
            if flag==0:
                green_go_num.append(0)
            if flag==1:
                pedestrian_crossing_num1.append(0)
            if flag==2:
                speed_limited_num.append(0)
            if flag==3:
                speed_unlimited_num.append(0)
            if flag==4:
                pedestrian_crossing_num1.append(0)

            if havesepds1==1 and flag==1:
                pedestrian_crossing_no_see1.append(1)
            if havesepds2==1 and flag==4:
                pedestrian_crossing_no_see2.append(1)

            #yellow_back_num is for special situation
            yellow_back_num.append(0)


        # the situation that see something
        if len(data)>0:
            data=eval(data)
            labelname=" "
            conf=0
            xmin=0
            xmax=0
            ymin=0
            ymax=0
            area=0
            satisfied=0

            for key in data:
                if key == labeldict[flag] or key =='yellow_back':
                    print('{}--{}--{}--{}--{}--{}'.format(key,data[key][0],data[key][1],data[key][2],data[key][3],data[key][4]))
                    labelname=key
                    conf=data[key][0]
                    xmin=data[key][1]
                    xmax=data[key][2]
                    ymin=data[key][3]
                    ymax=data[key][4]
                    area=abs(xmax-xmin)*abs(ymax-ymin)
                    satisfied=1
                    break
                                                               
            if satisfied==1:

                if labelname=='yellow_back'  and yellowflag==0:
  
                    yellow_back_num.append(1)
                    if  yellow_back_num.count(1)>3:
                        flag=6
                        msg_hilens =5
                        yellowflag=1
                        for i in range(10):
                            pub1.publish(msg_hilens)                
                            rate.sleep()

                    s.close()
                    continue

                if flag==0 :
                    green_go_num.append(1)
                if flag==1 :
                    if  (xmax-xmin)>700:
                        pedestrian_crossing_num1.append(1)  
                if flag==1 :
                    if (xmax-xmin)>500:
                        havesepds1=1
                        pedestrian_crossing_no_see1.append(0)

                if flag==2  and area>20000 and ymin<300:
                    speed_limited_num.append(1)
                if flag==3  and area>20000 and ymin<150:
                    speed_unlimited_num.append(1)
                if flag==4 :
                    if (xmax-xmin)>700:
                        pedestrian_crossing_num2.append(1)
                if flag==4:
                    if (xmax-xmin)>500:
                        havesepds1=1
                        pedestrian_crossing_no_see2.append(0)

            else:
                print('no staisfied label')
                # the situation that don't see the corresponding thing
                if flag==0:
                    green_go_num.append(0)
                if flag==1:
                    pedestrian_crossing_num1.append(0)
                if flag==1 and havesepds1==1:
                    pedestrian_crossing_no_see1.append(1)
                if flag==2:
                    speed_limited_num.append(0)
                if flag==3:
                    speed_unlimited_num.append(0)
                if flag==4:
                    pedestrian_crossing_num2.append(0)
                if flag==4 and havesepds2==1:
                    pedestrian_crossing_no_see2.append(1)


        #change flag and send message to hilens

        if flag==0 and green_go_num.count(1)>3:
            flag+=1
            msg_hilens =0
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
            start_time=time.time()

        if time.time()-start_time>25 and flag==1:
            flag+=1
            for i in range(10):
                print('change flag because surpass time')
 
        if flag==1 and pedestrian_crossing_num1.count(1)>1:
            flag+=1
            tmparea=0
            
            msg_hilens =1
            for i in range(5):
                pub1.publish(msg_hilens)                
                rate.sleep()
            for x in range(30):
                print('send by common  situation')
    

        if flag==1 and pedestrian_crossing_no_see1.count(1)>4:
            flag+=1
            msg_hilens =1
            for i in range(5):
                pub1.publish(msg_hilens)                
                rate.sleep()
            for x in range(30):
                print('send by obstacle  situation')

       
        
        if flag==2 and speed_limited_num.count(1)>4:
            flag+=1
            
            msg_hilens =2
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()

        if flag==3 and speed_unlimited_num.count(1)>4:
            flag+=1
            msg_hilens =3
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
            time.sleep(10)

        if flag==4 and pedestrian_crossing_num2.count(1)>1:
            flag+=1
            msg_hilens =4
            for i in range(5):
                pub1.publish(msg_hilens)                
                rate.sleep()
            for x in range(30):
                print('send by common  situation')

        if flag==4 and pedestrian_crossing_no_see2.count(1)>4:
            flag+=1
            msg_hilens =4
            for i in range(5):
                pub1.publish(msg_hilens)                
                rate.sleep()
            for x in range(30):
                print('send by obstacle  situation')
    
        s.close()
        print('flag={}'.format(flag))

           

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
