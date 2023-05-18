#!/usr/bin/env python

import rospy
import message_filters
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
from MapUtil import *

HasAnInputMap = False
ReadFile = "/home/user/catkin_ws/src/mapping0/record/MapEditedDemo.json" #Input map
MapLogFile = "/home/user/catkin_ws/src/mapping0/record/MapMeasDemo2.json" #Output map

if(HasAnInputMap):
    Edited_Map = get_data_from_json(ReadFile)
    DimX = np.array([Edited_Map.xmin,Edited_Map.xmax])
    DimY = np.array([Edited_Map.ymin,Edited_Map.ymax])
    EpsilonX = Edited_Map.stepx
    EpsilonY = Edited_Map.stepy
    Threshold = Edited_Map.level
else:
    DimX = np.array([-3,3])
    DimY = np.array([-3,3])
    EpsilonX = 0.015 #meters
    EpsilonY = 0.015 #meters
    Threshold = 10

CoordX = np.linspace(DimX[0]-EpsilonX/2,DimX[1]+EpsilonX/2,((DimX[1]-DimX[0])/EpsilonX)+1)
CoordY = np.linspace(DimY[0]-EpsilonY/2,DimY[1]+EpsilonY/2,((DimY[1]-DimY[0])/EpsilonY)+1)
CoordMapX,CoordMapY = np.meshgrid(CoordX,CoordY)

Map = None
if(HasAnInputMap):
    Map = np.reshape(Edited_Map.map,(CoordX.size,CoordY.size))
    Map = Map*Threshold
else:
    Map = np.zeros((CoordX.size,CoordY.size))

Angles = np.radians(np.arange(360))

global ScanRanges
global Pos_X, Pos_Y, Pos_Theta
Pos_X = 0
Pos_Y = 0
Pos_Theta = 0

def SyncCallback_Map(in_Scan,in_Odom):
    global CoordX, CoordY, Pos_Theta
    global Angles
    global ScanRanges
    global Pos_X, Pos_Y, Pos_Theta

    ScanRanges = np.array(in_Scan.ranges) #Get the scan measurements
    RangeMin = in_Scan.range_min #Get the limits of the measurements
    RangeMax = in_Scan.range_max

    #Get the pos measurements
    Pos_X = in_Odom.pose.pose.position.x
    Pos_Y = in_Odom.pose.pose.position.y
    Quad = in_Odom.pose.pose.orientation
    #Finf the euleur angle from the quaternion
    QuadList = [Quad.x, Quad.y, Quad.z, Quad.w]
    Pos_Theta=euler_from_quaternion(QuadList,)[2] #0:Roll, 1:Pitch, 2:Yaw

    #Keep only the valid measurements i.e those that are in the confidence range according to the manufacturer
    ValidScansId = np.asarray(np.where((ScanRanges>RangeMin)&(ScanRanges<RangeMax)))[0]

    #Compute the real position of the measured points
    Phi = Pos_Theta + Angles[ValidScansId]
    Point_X = Pos_X + ScanRanges[ValidScansId] * np.cos(Phi)
    Point_Y = Pos_Y + ScanRanges[ValidScansId] * np.sin(Phi)

    #Find in which cell of the map do they fall without duplicates
    cell_id_x = np.argmin(np.abs(CoordX - Point_X.reshape(-1, 1)), axis=1)
    cell_id_y = np.argmin(np.abs(CoordY - Point_Y.reshape(-1, 1)), axis=1)
    #Increment the cells'value
    Map[cell_id_y,cell_id_x] += 1


def mapping():
    NodeFreq = 10 #/scan=5Hz, /odom=30Hz
    TimeSyncWindow = 0.25*1/NodeFreq

    Scan_sub = message_filters.Subscriber("scan",data_class=LaserScan)
    Odom_sub = message_filters.Subscriber("odom",data_class=Odometry)
    Synchronizer = message_filters.ApproximateTimeSynchronizer([Scan_sub,Odom_sub],1,TimeSyncWindow)
    Synchronizer.registerCallback(SyncCallback_Map)
    
    rospy.init_node("Mapper",anonymous=False)
    rate = rospy.Rate(NodeFreq)

    global Map
    global Threshold
    global CoordMapX,CoordMapY
    global ScanRanges
    global Angles
    global Pos_X, Pos_Y, Pos_Theta

    plt.ion() #figure can be updated
    fig = plt.figure()
    axcart = fig.add_subplot(1,1,1)

    while not rospy.is_shutdown():
        #Normalising for the display
        MapShown = Map/Threshold
        MapShown[MapShown>1] = 1

        axcart.cla() #Clearing the plot
        axcart.contourf(CoordMapX,CoordMapY,MapShown) #Plot the map
        mkr_angle = Pos_Theta*360/np.pi #Turning the marker to reflect the robot pos
        axcart.scatter(Pos_X,Pos_Y,marker=(3,1,mkr_angle),color='red') #Plot the robot pos
        axcart.axis('equal') #Make a square zoom
        plt.pause(0.01) #display the figure
        rate.sleep()


if __name__ =='__main__':
    try: #Main
        mapping()
    except rospy.ROSInterruptException: #Shutdown
        LogMap = map_data_class()
        LogMap.xmin = -3
        LogMap.xmax = 3
        LogMap.ymin = -3
        LogMap.ymax = 3
        LogMap.stepx = EpsilonX
        LogMap.stepy = EpsilonY
        LogMap.level = Threshold
        LogMap.map = Map/Threshold
        array_to_json(LogMap, LogMap, MapLogFile)
    pass