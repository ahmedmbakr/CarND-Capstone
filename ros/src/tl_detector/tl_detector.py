#!/usr/bin/env python
import rospy
from std_msgs.msg import Int32
from geometry_msgs.msg import PoseStamped, Pose
from styx_msgs.msg import TrafficLightArray, TrafficLight
from styx_msgs.msg import Lane
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from light_classification.tl_classifier import TLClassifier
import tf
import cv2
import yaml
from scipy.spatial import KDTree
import os
from object_detection.object_detection_main import Object_detector
import PIL
import scipy.misc
import numpy as np

STATE_COUNT_THRESHOLD = 3

class TLDetector(object):
    def __init__(self):
        rospy.init_node('tl_detector')

        self.pose = None
        self.waypoints = None
        self.camera_image = None
	
	self.waypoints_2d = None
	self.waypoint_tree = None
	self.img_counter = 0

        self.lights = []

        self.object_detector = Object_detector()

        sub1 = rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        sub2 = rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        '''
        /vehicle/traffic_lights provides you with the location of the traffic light in 3D map space and
        helps you acquire an accurate ground truth data source for the traffic light
        classifier by sending the current color state of all traffic lights in the
        simulator. When testing on the vehicle, the color state will not be available. You'll need to
        rely on the position of the light and the camera image to predict it.
        '''
        sub3 = rospy.Subscriber('/vehicle/traffic_lights', TrafficLightArray, self.traffic_cb)
        sub6 = rospy.Subscriber('/image_color', Image, self.image_cb, queue_size=1, buff_size = 2*52428800)

        config_string = rospy.get_param("/traffic_light_config")
        self.config = yaml.load(config_string)

        self.upcoming_red_light_pub = rospy.Publisher('/traffic_waypoint', Int32, queue_size=1)

        self.bridge = CvBridge()
        self.light_classifier = TLClassifier()
        self.listener = tf.TransformListener()

        self.state = TrafficLight.UNKNOWN
        self.last_state = TrafficLight.UNKNOWN
        self.last_wp = -1
        self.state_count = 0

        self.loop()

    def loop(self):
	rate = rospy.Rate(10)
	while not rospy.is_shutdown():
		rate.sleep()

    def pose_cb(self, msg):
        self.pose = msg

    def waypoints_cb(self, waypoints):
        self.waypoints = waypoints
	if not self.waypoints_2d:
		self.waypoints_2d = [[waypoint.pose.pose.position.x, waypoint.pose.pose.position.y] for waypoint in waypoints.waypoints]
		self.waypoint_tree = KDTree(self.waypoints_2d) #searches for the nearest way point to the car point in log(n)

    def traffic_cb(self, msg):
        self.lights = msg.lights

    def image_cb(self, msg):
        """Identifies red lights in the incoming camera image and publishes the index
            of the waypoint closest to the red light's stop line to /traffic_waypoint

        Args:
            msg (Image): image from car-mounted camera

        """
        self.has_image = True
        self.camera_image = msg
        light_wp, state = self.process_traffic_lights()

        '''
        Publish upcoming red lights at camera frequency.
        Each predicted state has to occur `STATE_COUNT_THRESHOLD` number
        of times till we start using it. Otherwise the previous stable state is
        used.
        '''
        if self.state != state:
            self.state_count = 0
            self.state = state
        elif self.state_count >= STATE_COUNT_THRESHOLD:
            self.last_state = self.state
            light_wp = light_wp if (state == TrafficLight.RED or state == TrafficLight.YELLOW) else -1
            self.last_wp = light_wp
	    print("red-light location published by detector:", light_wp)
            self.upcoming_red_light_pub.publish(Int32(light_wp))
        else:
            self.upcoming_red_light_pub.publish(Int32(self.last_wp))
        self.state_count += 1

    def get_closest_waypoint(self, x, y):
        """Identifies the closest path waypoint to the given position
            https://en.wikipedia.org/wiki/Closest_pair_of_points_problem
        Args:
            pose (Pose): position to match a waypoint to

        Returns:
            int: index of the closest waypoint in self.waypoints

        """
        #TODO implement
	closest_idx = self.waypoint_tree.query([x,y], 1)[1]
	return closest_idx


    def get_light_state(self, light):
        """Determines the current color of the traffic light

        Args:
            light (TrafficLight): light to classify

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """	
	# For testing just return the light state
	recorded_imgs_directory = "../../../recorded_imgs/"
	if not os.path.exists(recorded_imgs_directory):
		os.makedirs(recorded_imgs_directory)
	self.img_counter += 1 
	num_imgs_to_drop = 10
	"""if ((self.img_counter % num_imgs_to_drop) == 0):	
		cv_image = self.bridge.imgmsg_to_cv2(self.camera_image, "bgr8")
		new_image_path = recorded_imgs_directory + 'img_' + str(light.state) + '_' + str(self.img_counter / num_imgs_to_drop) + '.png'
		cv2.imwrite(new_image_path ,cv_image)
		rospy.logerr("light.state:{0}".format(light.state))"""
	
	print("new image recieved by get_light_state")
	########################return light.state#####################################################
        if(not self.has_image):
            self.prev_light_loc = None
            return False

        cv_image = self.bridge.imgmsg_to_cv2(self.camera_image, "bgr8")
	#new_image_path = 'curr_img.jpg'
	#cv2.imwrite(new_image_path ,cv_image)
	#image_path = new_image_path
	#image = PIL.Image.open(image_path)
	#resize = 200, 160
  	#image.thumbnail(resize, PIL.Image.ANTIALIAS)
	
	#lower_yellow = np.array([25,146,190], dtype = "uint8")
	#upper_yellow = np.array([62,174,255], dtype = "uint8")
	lower_yellow = np.array([0,150,150], dtype = "uint8")
	upper_yellow = np.array([62,255,255], dtype = "uint8")

	lower_red = np.array([17,15,100], dtype = "uint8")
	upper_red = np.array([50,56,255], dtype = "uint8")
	
	lower_green = np.array([0,100,0], dtype = "uint8")
	upper_green = np.array([50,255,56], dtype = "uint8")
	

	yellow_mask = cv2.inRange(cv_image, lower_yellow, upper_yellow)
	red_mask = cv2.inRange(cv_image, lower_red, upper_red)
	green_mask = cv2.inRange(cv_image, lower_green, upper_green)

	output_yellow = cv2.bitwise_and(cv_image, cv_image, mask = yellow_mask)
	output_red = cv2.bitwise_and(cv_image, cv_image, mask = red_mask)
	output_green = cv2.bitwise_and(cv_image, cv_image, mask = green_mask)

	output_yellow = output_yellow > 150
	output_red = output_red > 100
	output_green = output_green > 100

	#output_yellow = output_yellow > 150
	#cv_image = np.hstack([cv_image, output_green])

	num_yellow_pixels = np.sum(output_yellow == 1)
	num_red_pixels = np.sum(output_red == 1)
	num_green_pixels = np.sum(output_green == 1)

  	print("num_yellow_pixels:", num_yellow_pixels)

	traffic_state = TrafficLight.UNKNOWN
	if(num_red_pixels > 70 and num_red_pixels > num_yellow_pixels and num_red_pixels > num_green_pixels):
	    print(" is red")
	    traffic_state = TrafficLight.RED	    
        elif(num_yellow_pixels > 100 and num_yellow_pixels > num_red_pixels and num_yellow_pixels > num_green_pixels):
	    print(" is yellow")
	    traffic_state = TrafficLight.YELLOW
        elif num_green_pixels > 20:
	    print(" is green")
            traffic_state = TrafficLight.GREEN
	#return light.state#####################################################
        #Get classification
	new_image_path = recorded_imgs_directory + 'img_' + str(self.img_counter) + '_' + str(light.state) + '_' + str(traffic_state) + '.png'
	cv2.imwrite(new_image_path ,cv_image)
        return traffic_state

    def process_traffic_lights(self):
        """Finds closest visible traffic light, if one exists, and determines its
            location and color

        Returns:
            int: index of waypoint closes to the upcoming stop line for a traffic light (-1 if none exists)
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        closest_light = None
	line_wp_idx = None

        # List of positions that correspond to the line to stop in front of for a given intersection
        stop_line_positions = self.config['stop_line_positions']
        if(self.pose):
            car_wp_idx = self.get_closest_waypoint(self.pose.pose.position.x, self.pose.pose.position.y)
	    
	    diff = len(self.waypoints.waypoints)
	    for i, light in enumerate(self.lights):
		#Get stop line waypoint index
		line = stop_line_positions[i]
		temp_wp_idx = self.get_closest_waypoint(line[0], line[1])
		#Find closest stop line waypoint index
		d = temp_wp_idx - car_wp_idx
		if d>=0 and d < diff:
			diff = d
			closest_light = light
			line_wp_idx = temp_wp_idx
	if diff > 70:
		return -1, TrafficLight.UNKNOWN
        #TODO find the closest visible traffic light (if one exists)

        if closest_light:
            state = self.get_light_state(closest_light)
	    print("red light detected:", line_wp_idx, " state is :", state)
            return line_wp_idx, state
        ######self.waypoints = None
        return -1, TrafficLight.UNKNOWN

if __name__ == '__main__':
    try:
        TLDetector()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start traffic node.')
