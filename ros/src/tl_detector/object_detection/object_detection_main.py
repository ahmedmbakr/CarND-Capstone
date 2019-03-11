import numpy as np
import os
import inspect
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from distutils.version import StrictVersion
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)
########################## TO BE REMOVED ##############################################################
# For the sake of simplicity we will use only 2 images:
# image1.jpg
# image2.jpg
# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.

PATH_TO_TEST_IMAGES_DIR = 'test_images'
TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 3) ]
print(TEST_IMAGE_PATHS)
######################################################################################################

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")
from object_detection.utils import ops as utils_ops

if StrictVersion(tf.__version__) < StrictVersion('1.12.0'):
  raise ImportError('Please upgrade your TensorFlow installation to v1.12.*.')

from utils import label_map_util
from utils import visualization_utils as vis_util

import scipy.misc

class Object_detector(object):
	
	def __init__(self):
		# What model to download.
		MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
		MODEL_FILE = MODEL_NAME + '.tar.gz'
		DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
		CURRENT_FOLDER_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
		# Path to frozen detection graph. This is the actual model that is used for the object detection.
		PATH_TO_FROZEN_GRAPH = CURRENT_FOLDER_PATH + '/' + MODEL_NAME + '/frozen_inference_graph.pb'
		print("PATH_TO_FROZEN_GRAPH: " + PATH_TO_FROZEN_GRAPH)
		# List of the strings that is used to add correct label for each box.
		PATH_TO_LABELS = os.path.join(CURRENT_FOLDER_PATH, 'data', 'mscoco_label_map.pbtxt')
		# Load a (frozen) Tensorflow model into memory.
		self.detection_graph = tf.Graph()
		with self.detection_graph.as_default():
		  od_graph_def = tf.GraphDef()
		  with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
		    serialized_graph = fid.read()
		    od_graph_def.ParseFromString(serialized_graph)
		    tf.import_graph_def(od_graph_def, name='')

		#loading label map
		self.category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

	#Helper function
	def load_image_into_numpy_array(self, image):
	  (im_width, im_height) = image.size
	  return np.array(image.getdata()).reshape(
	      (im_height, im_width, 3)).astype(np.uint8)


	def run_inference_for_single_image(self, image, graph):
	  with graph.as_default():
	    with tf.Session() as sess:
	      # Get handles to input and output tensors
	      ops = tf.get_default_graph().get_operations()
	      all_tensor_names = {output.name for op in ops for output in op.outputs}
	      tensor_dict = {}
	      for key in [
		  'num_detections', 'detection_boxes', 'detection_scores',
		  'detection_classes', 'detection_masks'
	      ]:
		tensor_name = key + ':0'
		if tensor_name in all_tensor_names:
		  tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
		      tensor_name)
	      if 'detection_masks' in tensor_dict:
		# The following processing is only for single image
		detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
		detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
		# Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
		real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
		detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
		detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
		detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
		    detection_masks, detection_boxes, image.shape[0], image.shape[1])
		detection_masks_reframed = tf.cast(
		    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
		# Follow the convention by adding back the batch dimension
		tensor_dict['detection_masks'] = tf.expand_dims(
		    detection_masks_reframed, 0)
	      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

	      # Run inference
	      output_dict = sess.run(tensor_dict,
		                     feed_dict={image_tensor: np.expand_dims(image, 0)})

	      # all outputs are float32 numpy arrays, so convert types as appropriate
	      output_dict['num_detections'] = int(output_dict['num_detections'][0])
	      output_dict['detection_classes'] = output_dict[
		  'detection_classes'][0].astype(np.uint8)
	      output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
	      output_dict['detection_scores'] = output_dict['detection_scores'][0]
	      if 'detection_masks' in output_dict:
		output_dict['detection_masks'] = output_dict['detection_masks'][0]
	  return output_dict

	def test_function(self):
		image_counter = 0
		for image_path in TEST_IMAGE_PATHS:
		  print(image_path)
		  detection_counter = 0
		  image = Image.open(image_path)
		  # the array based representation of the image will be used later in order to prepare the
		  # result image with boxes and labels on it.
		  image_np = self.load_image_into_numpy_array(image)
		  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
		  image_np_expanded = np.expand_dims(image_np, axis=0)
		  # Actual detection.
		  output_dict = self.run_inference_for_single_image(image_np, self.detection_graph)
		  # Visualization of the results of a detection.
		  im, boxes = vis_util.get_boxes_and_classes_on_image_array(
		      image_np,
		      output_dict['detection_boxes'],
		      output_dict['detection_classes'],
		      output_dict['detection_scores'],
		      self.category_index,
		      instance_masks=output_dict.get('detection_masks'))
		  print(image_np.shape)
		  
		  for box, class_idx in boxes:
		    if not class_idx == 10: #The class for the traffic signs
			continue
		    im_width, im_height = image.size
		    ymin, xmin, ymax, xmax = box
		    ymin *= im_height
		    ymax *= im_height
		    xmin *= im_width
		    xmax *= im_width
		    #print("new shape: ", image_np.shape)
		    print("This is a box: ", ymin, ymax, xmin, xmax)
		    image_np2 = self.load_image_into_numpy_array(image)
		    image_np2 = image_np[int(ymin):int(ymax), int(xmin):int(xmax),:]
		    new_image_name = 'image-' + str(image_counter) + '-' + str(detection_counter) + '.png'
		    print new_image_name
		    scipy.misc.imsave(new_image_name, image_np2)
		    detection_counter += 1
		  image_counter += 1
		  #plt.figure(figsize=IMAGE_SIZE)
		  #plt.imshow(image_np)
	def detect_objects_in_img(self, image):
	  # image is an image created with Image.open(image_path)
	  image_counter = 0
	  detection_counter = 0
	  # the array based representation of the image will be used later in order to prepare the
	  # result image with boxes and labels on it.
	  image_np = self.load_image_into_numpy_array(image)
	  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
	  image_np_expanded = np.expand_dims(image_np, axis=0)
	  # Actual detection.
	  output_dict = self.run_inference_for_single_image(image_np, self.detection_graph)
	  # Visualization of the results of a detection.
	  im, boxes = vis_util.get_boxes_and_classes_on_image_array(
	      image_np,
	      output_dict['detection_boxes'],
	      output_dict['detection_classes'],
	      output_dict['detection_scores'],
	      self.category_index,
	      instance_masks=output_dict.get('detection_masks'))
	  print(image_np.shape)
	  
	  detected_imgs_np_list = []
	  for box, class_idx in boxes:
	    if not class_idx == 10: #The class for the traffic signs
		continue
	    im_width, im_height = image.size
	    ymin, xmin, ymax, xmax = box
	    ymin *= im_height
	    ymax *= im_height
	    xmin *= im_width
	    xmax *= im_width
	    #print("new shape: ", image_np.shape)
	    #print("This is a box: ", ymin, ymax, xmin, xmax)
	    image_np2 = self.load_image_into_numpy_array(image)
	    image_np2 = image_np[int(ymin):int(ymax), int(xmin):int(xmax),:]
	    detected_imgs_np_list.append(image_np2)	  
	  #plt.figure(figsize=IMAGE_SIZE)
	  #plt.imshow(image_np)
          return detected_imgs_np_list
 
# for test purposes only 
if __name__ == '__main__':
	test_ob = Object_detector()
	image_counter = 0
	for image_path in TEST_IMAGE_PATHS:
	  print(image_path)
	  detection_counter = 0
	  image = Image.open(image_path)
	  detected_imgs_np_list = test_ob.detect_objects_in_img(image)
	  for image_np2 in detected_imgs_np_list:
		new_image_name = 'image-' + str(image_counter) + '-' + str(detection_counter) + '.png'
		print new_image_name
		scipy.misc.imsave(new_image_name, image_np2)
		detection_counter += 1
	  image_counter += 1

