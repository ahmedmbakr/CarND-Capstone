from styx_msgs.msg import TrafficLight
import numpy as np
import cv2
import os

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        self.img_counter = 0
	"""self.recorded_imgs_directory = '../../../recorded_imgs_classifier/'
	if not os.path.exists(self.recorded_imgs_directory):
		os.makedirs(self.recorded_imgs_directory)"""

    def get_classification(self, cv_image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv2 image): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
	cv_image = cv2.resize(cv_image, (200, 180), interpolation = cv2.INTER_AREA)
	YELLOW_MIN_ACCEPTANCE_NUM_PIXELS = 70	
	RED_MIN_ACCEPTANCE_NUM_PIXELS = 50	
	GREEN_MIN_ACCEPTANCE_NUM_PIXELS = 1	

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

	num_yellow_pixels = np.sum(output_yellow == 1)
	num_red_pixels = np.sum(output_red == 1)
	num_green_pixels = np.sum(output_green == 1)

  	print("num_yellow_pixels:", num_yellow_pixels)
	print("num_red_pixels:", num_red_pixels)
	print("num_green_pixels:", num_green_pixels)

	traffic_state = TrafficLight.UNKNOWN
	if(num_red_pixels > RED_MIN_ACCEPTANCE_NUM_PIXELS and num_red_pixels > num_yellow_pixels and num_red_pixels > num_green_pixels):
	    print(" is red")
	    traffic_state = TrafficLight.RED	    
        elif(num_yellow_pixels > YELLOW_MIN_ACCEPTANCE_NUM_PIXELS and num_yellow_pixels > num_red_pixels and num_yellow_pixels > num_green_pixels):
	    print(" is yellow")
	    traffic_state = TrafficLight.YELLOW
        elif num_green_pixels > GREEN_MIN_ACCEPTANCE_NUM_PIXELS:
	    print(" is green")
            traffic_state = TrafficLight.GREEN
	elif traffic_state == TrafficLight.UNKNOWN:#recovery mechanism. consider the unkown as the red traffic
	    print(" UNKOWN, recover to RED")
	    self.img_counter += 1
	    #new_image_path = self.recorded_imgs_directory + 'UNKOWN_' +str(self.img_counter) + '_' + str(num_red_pixels) + '_' + str(num_yellow_pixels) + '_' + str(num_green_pixels) + '.jpg'
	    #cv2.imwrite(new_image_path, cv_image)
	    traffic_state = TrafficLight.RED
        return traffic_state
	
