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
    start_time1=time.time()+500

    # global flag 
    flag=1

    #espically for red_stop
    red_flag=0

    '''
    labeldict for each flag
    special condition:
    flag=1:  red_stop  green_go   flag=2: red_stop green_go   flag=4: red_stop green_go  flag=5: red_stop  green_go
    flag=1 and flag=4 also need to check green_go and pedestrian_crossing
    '''
    labeldict={0:'green_go',1:'pedestrian_crossing',2:'speed_limited',3:'speed_unlimited',4:'pedestrian_crossing',5:'yellow_back',6:'yellow_back',7:'yellow_back'}
    
    # initial queue for each condition
    green_go_num=deque([0,0,0,0,0,0,0],maxlen=7)
    pedestrian_crossing_num1=deque([0,0,0,0,0,0,0],maxlen=7)
    green_go_nosee_num1=deque([0,0,0,0,0,0,0],maxlen=7)
    speed_limited_num=deque([0,0,0,0,0,0,0],maxlen=7)
    speed_unlimited_num=deque([0,0,0,0,0,0,0],maxlen=7)
    pedestrian_crossing_num2=deque([0,0,0,0,0,0,0],maxlen=7)
    green_go_nosee_num2=deque([0,0,0,0,0,0,0],maxlen=7)
    yellow_back_num=deque([0,0,0,0,0,0,0],maxlen=7)
    yellow_back_nosee_num=deque([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],maxlen=20)

    red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
    green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)

    tmparea=0


    while not rospy.is_shutdown():
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
        s.connect((host,port))      
        data=s.recv(1024)

        if red_stop_num.count(1)>50000:
            red_flag=1
            msg_hilens =9
            for i in range(10):
                print('has detect the red_stop')
                pub1.publish(msg_hilens)                
                rate.sleep()
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)

        if green_go_num2.count(1)>5:
            msg_hilens=10
            for i in range(10):
                print('has detect the green_go')
                red_flag=2
                pub1.publish(msg_hilens)                
                rate.sleep()
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)



        # the situation that don't see anything
        if len(data)==0:
            print('null')
            if flag==0:
                green_go_num.append(0)
            if flag==1:
                green_go_nosee_num1.append(1)
                pedestrian_crossing_num1.append(0)
            if flag==2:
                speed_limited_num.append(0)
            if flag==3:
                speed_unlimited_num.append(0)
            if flag==4:
                green_go_nosee_num2.append(1)
                pedestrian_crossing_num1.append(0)
            if flag==5:
                yellow_back_num.append(0)
            if flag==6:
                yellow_back_nosee_num.append(1)
                time.sleep(0.08)

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
                if key=='red_stop' and (flag==1 or flag==2 or flag==4 or flag==5) and red_flag==0:
                    red_stop_num.append(1)
                    labelname='red_stop'
                    break
                if key=='green_go' and red_flag==1 and (flag==1 or flag==2 or flag==4 or flag==5):
                    labelname='green_go'
                    green_go_num2.append(1)
                    break
                if (key == labeldict[flag] and data[key][0]>0.6) or (key=='yellow_back' and (flag==6  or  flag==7)) or (key== 'green_go' and flag==0) or (key== 'pedestrian_crossing' and (flag==1 or flag==4)):
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
            if labelname=='red_stop':
                print('red_stop')
                s.close()
                continue 
                 
            if labelname=='green_go'and red_flag==1:
                print('green_go')
                s.close()
                continue 

                                                                
            if satisfied==1:

                if flag==0 :
                    green_go_num.append(1)
                if flag==1 :
                    if tmparea<1.2*area and  (xmax-xmin)>500:
                        pedestrian_crossing_num1.append(1)
                    tmparea=area
                    time.sleep(0.05)
                    
                num=0
                if flag==1:
                    for key in data:
                        if key=='green_go':
                            num+=1
                        if num==0:
                            green_go_nosee_num1.append(1)

                if flag==2  and area>20000 and ymin<300:
                    speed_limited_num.append(1)
                if flag==3  and area>20000 and ymin<150:
                    speed_unlimited_num.append(1)
                if flag==4  and (xmax-xmin)>450 and area>40000 :
                    pedestrian_crossing_num2.append(1)
                num1=0
                if flag==4:
                    for key in data:
                        if key=='green_go':
                            num1+=1
                        if num1==0:
                            green_go_nosee_num2.append(1)
                if flag==5:
                    yellow_back_num.append(1)
            else:
                print('no staisfied label')
                # the situation that don't see the corresponding thing
                if flag==0:
                    green_go_num.append(0)
                if flag==1:
                    pedestrian_crossing_num1.append(0)
                if flag==2:
                    speed_limited_num.append(0)
                if flag==3:
                    speed_unlimited_num.append(0)
                if flag==4:
                    pedestrian_crossing_num2.append(0)
                if flag==5:
                    yellow_back_num.append(0)
                if flag==6:
                    yellow_back_nosee_num.append(1)
                    time.sleep(0.03)


        #change flag and send message to hilens
        if flag==0 and green_go_num.count(1)>3:
            flag+=1
            msg_hilens =0
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
 
        if flag==1 and pedestrian_crossing_num1.count(1)>0:
            flag+=1
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)

            msg_hilens =1
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
       
      
        
        if flag==2 and speed_limited_num.count(1)>4:
            flag+=1
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)
            msg_hilens =2
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()

        if flag==3 and speed_unlimited_num.count(1)>4:
            flag+=1
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)
            msg_hilens =3
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
            time.sleep(15)

        if flag==4 and pedestrian_crossing_num2.count(1)>0:
            flag+=1
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)
            msg_hilens =4
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()

    

        if flag==5 and yellow_back_num.count(1)>4:
            flag+=1
            red_stop_num=deque([0,0,0,0,0,0,0],maxlen=7)
            green_go_num2=deque([0,0,0,0,0,0,0],maxlen=7)
            msg_hilens =5
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()
            time.sleep(4)

        if flag==6 and  yellow_back_nosee_num.count(1)>17:
            flag+=1
            msg_hilens =6
            for i in range(10):
                pub1.publish(msg_hilens)                
                rate.sleep()

        s.close()
        print('flag={}'.format(flag))

           

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
