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
	image_np_red = image_np[:, :,0]
	image_np_red = image_np_red > 240

    	image_np_green = image_np[:,:,1]
	image_np_green = image_np_green > 240

    	num_green_pixels = np.sum(image_np_green == 1)
	num_red_pixels = np.sum(image_np_red == 1)
	
	if num_green_pixels == 0 and num_red_pixels > 100:
		return TrafficLight.RED
	
	if num_green_pixels > 100 and num_red_pixels == 0:
		return TrafficLight.GREEN
        #TODO implement light color prediction
        return TrafficLight.UNKNOWN
