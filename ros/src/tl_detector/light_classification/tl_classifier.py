from styx_msgs.msg import TrafficLight
import numpy as np

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        pass

    def get_classification(self, image_np):
        """Determines the color of the traffic light in the image

        Args:
            image (numpy image): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
	#These acceptance rates are configured for the input image of size 200,150
	MIN_NUM_ACCEPTED_PIXElS = 2 
	MAX_NUM_REJECTED_PIXELS = 1

	"""#These acceptance rates are configured for the input image of size 800,600
	MIN_NUM_ACCEPTED_PIXElS = 100 
	MAX_NUM_REJECTED_PIXELS = 10"""
	
	image_np_red = image_np[:, :,0]
	image_np_red = image_np_red > 240
	
    	image_np_green = image_np[:,:,1]
	image_np_green = image_np_green > 240

    	num_green = self.count_np(image_np_green)
	num_red = self.count_np(image_np_red)
	print("num_green_pixels:", num_green)
	print("num_red_pixels:", num_red)
	if num_green <= MAX_NUM_REJECTED_PIXELS and num_red >= MIN_NUM_ACCEPTED_PIXElS:
		return TrafficLight.RED
	
	if num_green >= MIN_NUM_ACCEPTED_PIXElS and num_red <= MAX_NUM_REJECTED_PIXELS:
		return TrafficLight.GREEN
        #TODO implement light color prediction
        return TrafficLight.UNKNOWN
   
    def count_np(self, image_np):
	c = 0
	size = image_np.size
	print size
	for x in np.nditer(image_np):
		if x == True:
			c += 1
	#print("final c:", c)
	return c
	
