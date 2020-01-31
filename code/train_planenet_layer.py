import tensorflow as tf
import numpy as np
np.set_printoptions(precision=2, linewidth=200)
import cv2
import os
import time
import sys
import tf_nndistance
import argparse
import glob
import PIL
import scipy.ndimage as ndimage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import *
from plane_utils import *
from modules import *


from planenet_layer import PlaneNet
from RecordReader import *
from RecordReaderRGBD import *
from RecordReader3D import *
from RecordReaderAll import *
from SegmentationRefinement import *

#training_flag: toggle dropout and batch normalization mode
#it's true for training and false for validation, testing, prediction
#it also controls which data batch to use (*_train or *_val)


def build_graph(img_inp_train, img_inp_val, training_flag, options):
    with tf.device('/gpu:%d'%options.gpu_id):
        img_inp = tf.cond(training_flag, lambda: img_inp_train, lambda: img_inp_val)

        if options.suffix == 'sample':
            training_flag = tf.constant(True)
            pass
        
        net = PlaneNet({'img_inp': img_inp}, is_training=training_flag, options=options)

        #global predictions
        plane_pred = net.layers['plane_pred']
        
        segmentation_pred = net.layers['segmentation_pred']
        non_plane_mask_pred = net.layers['non_plane_mask_pred']
        non_plane_depth_pred = net.layers['non_plane_depth_pred']
        non_plane_normal_pred = net.layers['non_plane_normal_pred']
        
        empty_mask_pred = net.layers['empty_mask_pred']
        

        if False:
            mask_5_np = (cv2.imread(options.test_dir + '/mask_5.png', 0) > 128).astype(np.float32)
            mask_5 = tf.constant(mask_5_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])
            mask_14_np = (cv2.imread(options.test_dir + '/mask_14.png', 0) > 128).astype(np.float32)
            mask_14 = tf.constant(mask_14_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])        
            mask_empty_np = (cv2.imread(options.test_dir + '/mask_empty.png', 0) > 128).astype(np.float32)
            #mask_empty_np = np.logical_or(cv2.imread(options.test_dir + '/mask_gt_0.png', 0) > 128, cv2.imread(options.test_dir + '/mask_gt_1.png', 0) > 128).astype(np.float32)
            mask_empty = tf.constant(mask_empty_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])

            segmentation_pred = tf.concat([mask_5 * 100, mask_14 * 100, tf.zeros([options.batchSize, HEIGHT, WIDTH, 3]), tf.ones([options.batchSize, HEIGHT, WIDTH, 1]) * -100, segmentation_pred[:, :, :, 6:14], tf.ones([options.batchSize, HEIGHT, WIDTH, 1]) * -100, segmentation_pred[:, :, :, 15:]], axis=3)
            plane_pred = tf.concat([plane_pred[:, 5:6, :], plane_pred[:, 14:15, :], plane_pred[:, 2:, :]], axis=1)
            empty_mask_pred = mask_empty * 100
            pass

        
        if False:
            planeAreas = tf.reduce_sum(global_gt_dict['segmentation'], axis=[1, 2])
            _, sortInds = tf.nn.top_k(planeAreas, k = options.numOutputPlanes - options.numOutputPlanes_0)
            sortMap = tf.one_hot(sortInds, depth=options.numOutputPlanes, axis=1)
            gt_s = tf.reshape(tf.matmul(tf.reshape(global_gt_dict['segmentation'], [-1, HEIGHT * WIDTH, options.numOutputPlanes]), sortMap), [-1, HEIGHT, WIDTH, options.numOutputPlanes - options.numOutputPlanes_0])
            gt_p = tf.transpose(tf.matmul(tf.transpose(global_gt_dict['plane'], [0, 2, 1]), sortMap), [0, 2, 1])
            
            segmentation_pred = tf.concat([tf.zeros([options.batchSize, HEIGHT, WIDTH, 5]), gt_s * 100], axis=3)
            plane_pred = tf.concat([tf.zeros([options.batchSize, 5, 3]), gt_p], axis=1)

            
            mask_5_np = (cv2.imread(options.test_dir + '/mask_5.png', 0) > 128).astype(np.float32)
            mask_5 = tf.constant(mask_5_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])
            mask_14_np = (cv2.imread(options.test_dir + '/mask_14.png', 0) > 128).astype(np.float32)
            mask_14 = tf.constant(mask_14_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])        
            mask_empty_np = (cv2.imread(options.test_dir + '/mask_empty.png', 0) > 128).astype(np.float32)
            mask_empty = tf.constant(mask_empty_np.reshape(-1), shape=[options.batchSize, HEIGHT, WIDTH, 1])  
            empty_mask_pred = mask_empty * 100

            
            segmentation_pred = tf.concat([mask_5 * 100, mask_14 * 100, segmentation_pred[:, :, :, :6], segmentation_pred[:, :, :, 8:]], axis=3)
            plane_pred = tf.concat([plane_pred[:, 6:8, :], plane_pred[:, :6, :], plane_pred[:, 8:, :]], axis=1)

            #empty_mask_pred = tf.ones((options.batchSize, HEIGHT, WIDTH, 1)) * (-100)
            non_plane_mask_pred = global_gt_dict['non_plane_mask'] * 100
            non_plane_depth_pred = global_gt_dict['depth']
            pass

        if False:
            positive = tf.ones((options.batchSize, HEIGHT, WIDTH, 1)) * 100
            negative = tf.ones((options.batchSize, HEIGHT, WIDTH, 1)) * -100
            layer_segmentations_softmax_0 = tf.nn.softmax(segmentation_pred[:, :, :, :5])
            mask_7 = layer_segmentations_softmax_0[:, :, :, 0:1] * empty_mask_pred
            empty_mask_pred = segmentation_pred[:, :, :, 7:8]
            segmentation_pred = tf.concat([positive, tf.tile(negative, [1, 1, 1, 4]), segmentation_pred[:, :, :, 5:7], mask_7, segmentation_pred[:, :, :, 8:]], axis=3)
            plane_pred = tf.concat([plane_pred[:, 7:8, :], plane_pred[:, 1:7, :], plane_pred[:, 0:1, :], plane_pred[:, 8:, :]], axis=1)
            pass

        if False:
            segmentation_pred = tf.concat([segmentation_pred[:, :, :, 0:1], tf.minimum(segmentation_pred[:, :, :, 1:2], segmentation_pred[:, :, :, 3:4]), segmentation_pred[:, :, :, 2:3], tf.maximum(segmentation_pred[:, :, :, 1:2], segmentation_pred[:, :, :, 3:4]), segmentation_pred[:, :, :, 4:]], axis=3)
            pass
        
        #segmentation_pred = tf.concat([np.ones((options.batchSize, HEIGHT, WIDTH, 1)) * 100, np.zeros((options.batchSize, HEIGHT, WIDTH, 4)), segmentation_pred[:, :, :, 5:]], axis=3)

        
        global_pred_dict = {'plane': plane_pred, 'segmentation': segmentation_pred, 'non_plane_mask': non_plane_mask_pred, 'non_plane_depth': non_plane_depth_pred, 'non_plane_normal': non_plane_normal_pred, 'empty_mask': empty_mask_pred}

        if options.predictBoundary:
            global_pred_dict['boundary'] = net.layers['boundary_pred']
            pass
        if options.predictConfidence:
            global_pred_dict['confidence'] = net.layers['plane_confidence_pred']
            pass
        
        #local predictions
        if options.predictLocal:
            local_pred_dict = {'score': net.layers['local_score_pred'], 'plane': net.layers['local_plane_pred'], 'mask': net.layers['local_mask_pred']}
        else:
            local_pred_dict = {}
            pass

        
        #deep supervision
        deep_pred_dicts = []
        for layer in options.deepSupervisionLayers:
            pred_dict = {'plane': net.layers[layer+'_plane_pred'], 'segmentation': net.layers[layer+'_segmentation_pred'], 'non_plane_mask': net.layers[layer+'_non_plane_mask_pred']}
            #if options.predictConfidence:
            #pred_dict['confidence'] = net.layers[layer+'_plane_confidence_pred']
            #pass
            deep_pred_dicts.append(pred_dict)
            continue

        
        if options.anchorPlanes:
            anchors_np = np.load('dump/anchors_' + options.hybrid + '.npy')
            anchors = tf.reshape(tf.constant(anchors_np.reshape(-1)), anchors_np.shape)
            anchors = tf.tile(tf.expand_dims(anchors, 0), [options.batchSize, 1, 1])
            all_pred_dicts = deep_pred_dicts + [global_pred_dict]            
            for pred_index, pred_dict in enumerate(all_pred_dicts):
                all_pred_dicts[pred_index]['plane'] += anchors
                continue
            pass

        pass
    
    return global_pred_dict, local_pred_dict, deep_pred_dicts


def build_loss(global_pred_dict, deep_pred_dicts, global_gt_dict_train, global_gt_dict_val, training_flag, options):
    with tf.device('/gpu:%d'%options.gpu_id):
        debug_dict = {}
        
        global_gt_dict = {}
        for name in list(global_gt_dict_train.keys()):
            global_gt_dict[name] = tf.cond(training_flag, lambda: global_gt_dict_train[name], lambda: global_gt_dict_val[name])
            continue
        # local_gt_dict = {}
        # for name in local_gt_dict_train.keys():
        #     local_gt_dict[name] = tf.cond(tf.equal(training_flag % 2, 0), lambda: local_gt_dict_train[name], lambda: local_gt_dict_val[name])
        #     continue
        
        layerSupervision = False
        if layerSupervision:
            segmentations, planes = divideLayers(global_gt_dict['segmentation'], global_gt_dict['plane'], global_gt_dict['non_plane_mask'], global_gt_dict['info'][0], global_gt_dict['num_planes'])        
            global_gt_dict['segmentation'] = segmentations
            global_gt_dict['plane'] = planes
            pass
        
        plane_parameters = tf.reshape(global_pred_dict['plane'], (-1, 3))
        info = global_gt_dict['info'][0]
        plane_depths = planeDepthsModule(plane_parameters, WIDTH, HEIGHT, info)
        plane_depths = tf.transpose(tf.reshape(plane_depths, [HEIGHT, WIDTH, -1, options.numOutputPlanes]), [2, 0, 1, 3])

        non_plane_depth = global_pred_dict['non_plane_depth']
        all_depths = tf.concat([plane_depths, non_plane_depth], axis=3)

        layer_segmentations_0 = global_pred_dict['segmentation'][:, :, :, :options.numOutputPlanes_0]
        layer_segmentations_1 = global_pred_dict['segmentation'][:, :, :, options.numOutputPlanes_0:options.numOutputPlanes]
        layer_segmentations_softmax_0 = tf.nn.softmax(layer_segmentations_0)
        layer_segmentations_softmax_1 = tf.nn.softmax(layer_segmentations_1)
        empty_mask = tf.sigmoid(global_pred_dict['empty_mask'])
        non_plane_mask = tf.sigmoid(global_pred_dict['non_plane_mask'])
        all_segmentations_softmax = tf.concat([tf.concat([layer_segmentations_softmax_0 * empty_mask, layer_segmentations_softmax_1 * (1 - empty_mask)], axis=3) * (1 - non_plane_mask), non_plane_mask], axis=3)
        
        
        validPlaneMask = tf.cast(tf.less(tf.tile(tf.expand_dims(tf.range(options.numOutputPlanes), 0), [options.batchSize, 1]), tf.expand_dims(global_gt_dict['num_planes'], -1)), tf.float32)        
        backwardLossWeight = options.backwardLossWeight
        
        #plane loss and segmentation loss (summation over deep supervisions and final supervision)
        all_pred_dicts = deep_pred_dicts + [global_pred_dict]
        plane_loss = tf.constant(0.0)
        segmentation_loss = tf.constant(0.0)
        plane_confidence_loss = tf.constant(0.0)
        diverse_loss = tf.constant(0.0)
        
        #keep forward map (segmentation gt) from previous supervision so that we can have same matching for all supervisions (options.sameMatching = 1)
        previous_plane_gt = None
        previous_plane_confidence_gt = None        
        previous_segmentation_gt = None
        if options.anchorPlanes:
            anchors_np = np.load('dump/anchors_' + options.hybrid + '.npy')
            anchors = tf.reshape(tf.constant(anchors_np.reshape(-1)), anchors_np.shape)
            anchors = tf.tile(tf.expand_dims(anchors, 0), [options.batchSize, 1, 1])
            dists_forward, map_forward, dists_backward, _ = tf_nndistance.nn_distance(global_gt_dict['plane'], anchors)
                            
            forward_map = tf.one_hot(map_forward, depth=options.numOutputPlanes, axis=-1)
            forward_map *= tf.expand_dims(validPlaneMask, -1)
                
            #number of ground truth mapped for each prediction
            num_matches = tf.transpose(tf.reduce_sum(forward_map, axis=1, keep_dims=True), [0, 2, 1])
            previous_plane_gt = tf.transpose(tf.matmul(global_gt_dict['plane'], forward_map, transpose_a=True), [0, 2, 1]) / tf.maximum(num_matches, 1e-4)
            previous_plane_confidence_gt = tf.cast(num_matches > 0.5, tf.float32)

            segmentation_gt_shuffled = tf.reshape(tf.matmul(tf.reshape(global_gt_dict['segmentation'], [-1, HEIGHT * WIDTH, options.numOutputPlanes]), forward_map), [-1, HEIGHT, WIDTH, options.numOutputPlanes])
            segmentation_gt_shuffled = tf.concat([segmentation_gt_shuffled, global_gt_dict['non_plane_mask']], axis=3)
            previous_segmentation_gt = segmentation_gt_shuffled
            pass

        
        assert(len(all_pred_dicts) == 1)
        for pred_index, pred_dict in enumerate(all_pred_dicts):
            if (options.sameMatching and pred_index > 0) or options.anchorPlanes:
                assert(False)
                #use matching from previous supervision and map ground truth planes based on the mapping

                plane_loss += tf.reduce_mean(tf.squared_difference(pred_dict['plane'], previous_plane_gt) * previous_plane_confidence_gt) * 10000
                
                #all segmentations is the concatenation of plane segmentations and non plane mask
                #all_segmentations = tf.concat([pred_dict['segmentation'], pred_dict['non_plane_mask']], axis=3)

                if options.crf > 0:
                    all_segmentations_softmax = tf.nn.softmax(all_segmentations_softmax)          
                    with tf.variable_scope('crf'):
                        all_segmentations_softmax = segmentationRefinementModule(all_segmentations_softmax, all_depths, numIterations=options.crf, numOutputPlanes=21)
                        segmentation_loss += tf.reduce_mean(-tf.reduce_sum(previous_segmentation_gt, tf.log(all_segmentations), axis=-1))
                        pass
                    pass
                else:
                    segmentation_loss += tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=all_segmentations, labels=previous_segmentation_gt)) * 1000
                    pass
            else:
                #calculate new matching by finding nearest neighbors again
                if not layerSupervision:
                    dists_forward, map_forward, dists_backward, _ = tf_nndistance.nn_distance(global_gt_dict['plane'], pred_dict['plane'])
                    dists_forward *= validPlaneMask

                    dists = tf.concat([global_gt_dict['plane'], pred_dict['plane'], tf.stack([dists_forward, tf.cast(map_forward, tf.float32), dists_backward, tf.cast(_, tf.float32)], axis=2)], axis=2)
                    dists_forward = tf.reduce_mean(dists_forward)
                    dists_backward = tf.reduce_mean(dists_backward)
                    plane_loss += (dists_forward + dists_backward * backwardLossWeight) * 10000

                    forward_map = tf.one_hot(map_forward, depth=options.numOutputPlanes, axis=-1)
                    forward_map *= tf.expand_dims(validPlaneMask, -1)
                else:
                    dists_forward, map_forward, dists_backward, _ = tf_nndistance.nn_distance(global_gt_dict['plane'][:, :options.numOutputPlanes_0, :], pred_dict['plane'][:, :options.numOutputPlanes_0, :])
                    #dists_forward *= validPlaneMask
                
                    dists_forward = tf.reduce_mean(dists_forward)
                    dists_backward = tf.reduce_mean(dists_backward)
                    plane_loss += (dists_forward + dists_backward * backwardLossWeight) * 10000
                    
                    forward_map = tf.one_hot(map_forward, depth=options.numOutputPlanes, axis=-1)
                    
                    dists_forward, map_forward, dists_backward, _ = tf_nndistance.nn_distance(global_gt_dict['plane'][:, options.numOutputPlanes_0:, :], pred_dict['plane'][:, options.numOutputPlanes_0:, :])
                    #dists_forward *= validPlaneMask
                
                    dists_forward = tf.reduce_mean(dists_forward)
                    dists_backward = tf.reduce_mean(dists_backward)
                    plane_loss += (dists_forward + dists_backward * backwardLossWeight) * 10000
                    
                    forward_map = tf.concat([forward_map, tf.one_hot(map_forward + options.numOutputPlanes_0, depth=options.numOutputPlanes, axis=-1)], axis=1)
                    #forward_map *= tf.expand_dims(validPlaneMask, -1)
                    
    
                #number of ground truth mapped for each prediction
                num_matches = tf.transpose(tf.reduce_sum(forward_map, axis=1, keep_dims=True), [0, 2, 1])
                previous_plane_gt = tf.transpose(tf.matmul(global_gt_dict['plane'], forward_map, transpose_a=True), [0, 2, 1]) / tf.maximum(num_matches, 1e-4)
                previous_plane_confidence_gt = tf.cast(num_matches > 0.5, tf.float32)
                
                                              
                segmentation_gt_shuffled = tf.reshape(tf.matmul(tf.reshape(global_gt_dict['segmentation'], [-1, HEIGHT * WIDTH, options.numOutputPlanes]), forward_map), [-1, HEIGHT, WIDTH, options.numOutputPlanes])
                segmentation_gt_shuffled = tf.concat([segmentation_gt_shuffled, global_gt_dict['non_plane_mask']], axis=3)
                previous_segmentation_gt = segmentation_gt_shuffled
                
                #all_segmentations = tf.concat([pred_dict['segmentation'], pred_dict['non_plane_mask']], axis=3)
                
                #segmentation_loss += tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=all_segmentations, labels=segmentation_gt_shuffled)) * 1000
                segmentation_loss += tf.reduce_mean(-segmentation_gt_shuffled * tf.log(tf.maximum(all_segmentations_softmax, 1e-15))) * 1000 * 20
                pass

            if options.diverseLoss and False:
                plane_diff = tf.reduce_sum(tf.pow(tf.expand_dims(pred_dict['plane'], 1) - tf.expand_dims(pred_dict['plane'], 2), 2), axis=3)
                plane_diff = tf.matrix_set_diag(plane_diff, tf.ones((options.batchSize, options.numOutputPlanes)))
                minPlaneDiff = 0.1
                diverse_loss += tf.reduce_mean(tf.clip_by_value(1 - plane_diff / minPlaneDiff, 0, 1)) * 10000
                pass
              
            continue


        #if options.crf == 0:
        #all_segmentations_softmax = tf.nn.softmax(all_segmentations)
        #pass
        
        #depth loss
        validDepthMask = tf.cast(tf.greater(global_gt_dict['depth'], 1e-4), tf.float32)
        depth_loss = tf.reduce_mean(tf.reduce_sum(tf.squared_difference(all_depths, global_gt_dict['depth']) * all_segmentations_softmax, axis=3, keep_dims=True) * validDepthMask) * 10000

        debug_dict['depth'] = tf.squared_difference(all_depths, global_gt_dict['depth']) * all_segmentations_softmax

        
        #if options.predictPixelwise == 1:
        depth_loss += tf.reduce_mean(tf.squared_difference(global_pred_dict['non_plane_depth'], global_gt_dict['depth']) * validDepthMask) * 1000

        valid_normal_mask = tf.cast(tf.less(global_gt_dict['info'][0, 19], 2), tf.float32)
        normal_loss = tf.reduce_mean(tf.reduce_mean(tf.squared_difference(global_pred_dict['non_plane_normal'], global_gt_dict['normal']) * validDepthMask, axis=[1, 2, 3]) * valid_normal_mask) * 1000        
        #normal_loss = tf.constant(0.0)
        

        local_score_loss = tf.constant(0.0)
        local_plane_loss = tf.constant(0.0)
        local_mask_loss = tf.constant(0.0)
                
        #boundary loss
        boundary_loss = tf.constant(0.0)
        
        if False:
            kernel_size = 3
            padding = (kernel_size - 1) / 2
            neighbor_kernel_array = gaussian(kernel_size, kernel_size)
            neighbor_kernel_array[(kernel_size - 1) / 2][(kernel_size - 1) / 2] = 0
            neighbor_kernel_array /= neighbor_kernel_array.sum()
            neighbor_kernel_array *= -1
            neighbor_kernel_array[(kernel_size - 1) / 2][(kernel_size - 1) / 2] = 1
            neighbor_kernel = tf.constant(neighbor_kernel_array.reshape(-1), shape=neighbor_kernel_array.shape, dtype=tf.float32)
            neighbor_kernel = tf.reshape(neighbor_kernel, [kernel_size, kernel_size, 1, 1])
            
            #calculate boundary ground truth on-the-fly as the calculation is subject to change
        
            depth_diff = tf.abs(tf.nn.depthwise_conv2d(global_gt_dict['depth'], neighbor_kernel, strides=[1, 1, 1, 1], padding='VALID'))
            depth_diff = tf.pad(depth_diff, paddings = [[0, 0], [padding, padding], [padding, padding], [0, 0]])
            max_depth_diff = 0.1
            depth_boundary = tf.greater(depth_diff, max_depth_diff)

            plane_region = tf.nn.max_pool(1 - global_gt_dict['non_plane_mask'], ksize=[1, kernel_size, kernel_size, 1], strides=[1, 1, 1, 1], padding='SAME', name='max_pool')
            segmentation_eroded = 1 - tf.nn.max_pool(1 - global_gt_dict['segmentation'], ksize=[1, 3, 3, 1], strides=[1, 1, 1, 1], padding='SAME', name='max_pool')
            plane_region -= tf.reduce_max(segmentation_eroded, axis=3, keep_dims=True)
            boundary = tf.cast(depth_boundary, tf.float32) * plane_region
            smooth_boundary = global_gt_dict['smooth_boundary']
            boundary_gt = tf.concat([smooth_boundary, tf.maximum(boundary - smooth_boundary, 0)], axis=3)
            pass


        if True:
            kernel_size = 9
            # neighbor_kernel_array = gaussian(kernel_size)
            # neighbor_kernel_array[(kernel_size - 1) / 2][(kernel_size - 1) / 2] = 0
            # neighbor_kernel_array /= neighbor_kernel_array.sum()
            # neighbor_kernel = tf.constant(neighbor_kernel_array.reshape(-1), shape=neighbor_kernel_array.shape, dtype=tf.float32)
            # neighbor_kernel = tf.reshape(neighbor_kernel, [kernel_size, kernel_size, 1, 1])
            neighbor_kernel = tf.ones([kernel_size, kernel_size, 1, 1])

            #sigmaDepthDiff = 0.5
            #maxDepthDiff = 0.1
            labelWeight = 0.05
            emptyDepthDiff = pow(0.03, 2)
            nonPlaneDepthDiff = pow(1, 2)
            depthDiffVar = pow(0.2, 2)
            
            planesY = global_pred_dict['plane'][:, :, 1]
            planesD = tf.maximum(tf.norm(global_pred_dict['plane'], axis=-1), 1e-4)
            planesY /= planesD
            planesY = tf.concat([planesY, tf.ones((options.batchSize, 1)) * 100], axis=1)
            
            all_segmentations_onehot = tf.one_hot(tf.argmax(all_segmentations_softmax, 3), depth=options.numOutputPlanes + 1)
            normalY = tf.reduce_sum(all_segmentations_onehot * tf.reshape(planesY, [options.batchSize, 1, 1, -1]), axis=3, keep_dims=True)            
            depth_onehot = tf.reduce_sum(all_depths * all_segmentations_onehot, 3, keep_dims=True)

            
            layer_depths_0 = all_depths[:, :, :, :options.numOutputPlanes_0]
            layer_segmentations_onehot_0 = tf.one_hot(tf.argmax(layer_segmentations_0, 3), depth=options.numOutputPlanes_0)
            depth_diff_0 = layer_depths_0 - tf.reduce_sum(layer_depths_0 * layer_segmentations_onehot_0, 3, keep_dims=True)
            depth_diff_0 = tf.pow(depth_diff_0 * normalY, 2)
            DS_diff_0 = (1 + labelWeight) - tf.exp(-depth_diff_0 / depthDiffVar) - layer_segmentations_onehot_0 * labelWeight
            DS_0 = tf.nn.depthwise_conv2d(DS_diff_0, tf.tile(neighbor_kernel, [1, 1, options.numOutputPlanes_0, 1]), strides=[1, 1, 1, 1], padding='SAME')
            
            
            depth_diff_1 = plane_depths[:, :, :, options.numOutputPlanes_0:options.numOutputPlanes] - depth_onehot
            depth_diff_1 = tf.pow(depth_diff_1 * normalY, 2)
            #empty_mask_onehot = tf.reduce_sum(all_segmentations_onehot[:, :, :, :options.numOutputPlanes_0], axis=3, keep_dims=True)

            #depth_diff_1 = depth_diff_1 * (1 - empty_mask_onehot) + empty_mask_onehot * emptyDepthDiff
            #depth_diff_1 = tf.concat([(1 - empty_mask_onehot) * emptyDepthDiff, depth_diff_1, 1 - all_segmentations_onehot[:, :, :, options.numOutputPlanes:options.numOutputPlanes+1]], axis=3)
            depth_diff_1 = tf.concat([depth_diff_1, (1 - all_segmentations_onehot[:, :, :, options.numOutputPlanes:options.numOutputPlanes + 1]) * nonPlaneDepthDiff], axis=3)
            
            layer_segmentations_onehot_1 = all_segmentations_onehot[:, :, :, options.numOutputPlanes_0:options.numOutputPlanes + 1]
            DS_diff_1 = (1 + labelWeight) - tf.exp(-depth_diff_1 / depthDiffVar) - layer_segmentations_onehot_1 * labelWeight

            
            DS_1 = tf.nn.depthwise_conv2d(DS_diff_1, tf.tile(neighbor_kernel, [1, 1, options.numOutputPlanes + 1 - options.numOutputPlanes_0, 1]), strides=[1, 1, 1, 1], padding='SAME')

            #empty_mask_softmax = tf.reduce_sum(all_segmentations_softmax[:, :, :, :options.numOutputPlanes_0], axis=-1, keep_dims=True)            
            #layer_segmentations_softmax_1 = tf.concat([empty_mask_softmax, all_segmentations_softmax[:, :, :, options.numOutputPlanes_0:]], axis=3)
            layer_segmentations_softmax_1 = all_segmentations_softmax[:, :, :, options.numOutputPlanes_0:]
            
            boundary_loss += tf.reduce_mean(tf.concat([DS_0 * layer_segmentations_softmax_0 * 10, DS_1 * layer_segmentations_softmax_1], axis=3)) * 5000

            
            debug_dict['cost_mask'] = tf.concat([DS_0 * layer_segmentations_softmax_0, DS_1 * layer_segmentations_softmax_1], axis=3)
            #debug_dict['cost_mask'] = tf.reduce_sum(DS_0 * layer_segmentations_softmax_0, axis=3)
            #debug_dict['cost_mask'] = DS_1 * layer_segmentations_softmax_1
            #debug_dict['cost_mask'] = DS_1 * layer_segmentations_softmax_1
            #debug_dict['cost_mask'] = layer_segmentations_softmax_0
            pass
          
        if options.predictBoundary and False:
            #we predict boundaries directly for post-processing purpose
            boundary_loss += tf.reduce_mean(tf.losses.sigmoid_cross_entropy(logits=global_pred_dict['boundary'], multi_class_labels=global_gt_dict['boundary'], weights=tf.maximum(global_gt_dict['boundary'] * 3, 1))) * 1000
            pass


        label_loss = tf.constant(0.0)
        if options.labelLoss == 1:
            #label_loss = tf.reduce_mean(tf.reduce_max(all_segmentations_softmax[:, :, :, 5:], axis=[1, 2])) * 1000
            
            #label_loss += tf.reduce_mean(tf.maximum(1 - tf.reduce_sum(tf.reduce_max(all_segmentations_softmax[:, :, :, :5], axis=[1, 2]), axis=1), 0)) * 100000
            #label_loss += tf.reduce_mean(tf.maximum(layer_depths_0 - 10, 0) * layer_segmentations_softmax_0) * 1000
            #label_loss += tf.reduce_mean(tf.maximum(depth_onehot - layer_depths_0, 0) * layer_segmentations_softmax_0 * (1 - global_gt_dict['non_plane_mask'])) * 1000
            #label_loss = tf.reduce_mean(tf.reduce_max(all_segmentations_softmax, axis=[1, 2])) * 1000
            pass
        
        #regularization
        l2_losses = tf.add_n([options.l2Weight * tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'weights' in v.name])


        loss = plane_loss + segmentation_loss + depth_loss + normal_loss + plane_confidence_loss + diverse_loss + boundary_loss + local_score_loss + local_plane_loss + local_mask_loss + label_loss + l2_losses * 0

        #if options.pixelwiseLoss:
        #normal_loss = tf.reduce_mean(tf.squared_difference(global_pred_dict['non_plane_normal'], global_gt_dict['normal'])) * 1000
        #depth_loss = tf.reduce_mean(tf.squared_difference(global_pred_dict['non_plane_depth'], global_gt_dict['depth']) * validDepthMask) * 1000
        #pass

        loss_dict = {'plane': plane_loss, 'segmentation': segmentation_loss, 'depth': depth_loss, 'normal': normal_loss, 'boundary': boundary_loss, 'diverse': diverse_loss, 'confidence': plane_confidence_loss, 'local_score': local_score_loss, 'local_plane': local_plane_loss, 'local_mask': local_mask_loss, 'label': label_loss}

        
        debug_dict['segmentation_pred'] = all_segmentations_softmax
        debug_dict['segmentation'] = segmentation_gt_shuffled
        debug_dict['dists'] = dists
        #debug_dict['background'] = background_planes
        pass
    return loss, loss_dict, debug_dict


def main(options):
    if not os.path.exists(options.checkpoint_dir):
        os.system("mkdir -p %s"%options.checkpoint_dir)
        pass
    if not os.path.exists(options.test_dir):
        os.system("mkdir -p %s"%options.test_dir)
        pass
    
    min_after_dequeue = 1000


    train_inputs = []
    val_inputs = []
    if '0' in options.hybrid:
        train_inputs.append(options.rootFolder + '/planes_SUNCG_train.tfrecords')
        val_inputs.append(options.rootFolder + '/planes_SUNCG_val.tfrecords')        
        pass
    if '1' in options.hybrid:
        for _ in range(10):
            train_inputs.append(options.rootFolder + '/planes_nyu_rgbd_train.tfrecords')
            val_inputs.append(options.rootFolder + '/planes_nyu_rgbd_val.tfrecords')
            continue
        pass
    if '2' in options.hybrid:
        train_inputs.append(options.rootFolder + '/planes_matterport_train.tfrecords')
        val_inputs.append(options.rootFolder + '/planes_matterport_val.tfrecords')
        pass
    if '3' in options.hybrid:
        if options.suffix == 'sample':
            train_inputs.append('../planes_scannet_train_sample.tfrecords')        
            val_inputs.append('../planes_scannet_train_sample.tfrecords')
        else:
            train_inputs.append(options.rootFolder + '/planes_scannet_train.tfrecords')
            val_inputs.append(options.rootFolder + '/planes_scannet_val.tfrecords')
            pass
        pass
    
    reader_train = RecordReaderAll()
    filename_queue_train = tf.train.string_input_producer(train_inputs, num_epochs=1000000)    
    img_inp_train, global_gt_dict_train, local_gt_dict_train = reader_train.getBatch(filename_queue_train, numOutputPlanes=options.numOutputPlanes, batchSize=options.batchSize, min_after_dequeue=min_after_dequeue, getLocal=True)

    reader_val = RecordReaderAll()
    filename_queue_val = tf.train.string_input_producer(val_inputs, num_epochs=1000000)
    img_inp_val, global_gt_dict_val, local_gt_dict_val = reader_val.getBatch(filename_queue_val, numOutputPlanes=options.numOutputPlanes, batchSize=options.batchSize, min_after_dequeue=min_after_dequeue, getLocal=True)
    
    training_flag = tf.placeholder(tf.bool, shape=[], name='training_flag')
    
    #global_pred_dict, local_pred_dict, deep_pred_dicts = build_graph(img_inp_train, img_inp_val, img_inp_rgbd_train, img_inp_rgbd_val, img_inp_3d_train, img_inp_3d_val, training_flag, options)
    global_pred_dict, local_pred_dict, deep_pred_dicts = build_graph(img_inp_train, img_inp_val, training_flag, options)
    
    var_to_restore = [v for v in tf.global_variables()]
    
    #loss, loss_dict, _ = build_loss(global_pred_dict, local_pred_dict, deep_pred_dicts, global_gt_dict_train, local_gt_dict_train, global_gt_dict_val, local_gt_dict_val, training_flag, options)
    #loss_rgbd, loss_dict_rgbd, _ = build_loss_rgbd(global_pred_dict, deep_pred_dicts, global_gt_dict_rgbd_train, global_gt_dict_rgbd_val, training_flag, options)
    loss, loss_dict, _ = build_loss(global_pred_dict, deep_pred_dicts, global_gt_dict_train, global_gt_dict_val, training_flag, options)    
        
    #loss = tf.cond(tf.less(training_flag, 2), lambda: loss, lambda: tf.cond(tf.less(training_flag, 4), lambda: loss_rgbd, lambda: loss_3d))

    
    #train_writer = tf.summary.FileWriter(options.log_dir + '/train')
    #val_writer = tf.summary.FileWriter(options.log_dir + '/val')
    #train_writer_rgbd = tf.summary.FileWriter(options.log_dir + '/train_rgbd')
    #val_writer_rgbd = tf.summary.FileWriter(options.log_dir + '/val_rgbd')
    #writers = [train_writer, val_writer, train_writer_rgbd, val_writer_rgbd]
    
    tf.summary.scalar('loss', loss)
    summary_op = tf.summary.merge_all()

    with tf.variable_scope('statistics'):
        batchno = tf.Variable(0, dtype=tf.int32, trainable=False, name='batchno')
        batchnoinc=batchno.assign(batchno+1)
        pass


    optimizer = tf.train.AdamOptimizer(options.LR)
    train_op = optimizer.minimize(loss, global_step=batchno)

    
    config=tf.ConfigProto()
    config.allow_soft_placement=True    
    #config.gpu_options.allow_growth=True
    config.gpu_options.per_process_gpu_memory_fraction=0.9
    saver=tf.train.Saver()

    init_op = tf.group(tf.global_variables_initializer(),
                       tf.local_variables_initializer())
    
    with tf.Session(config=config) as sess:
        sess.run(init_op)
        if options.restore == 0:
            #fine-tune from DeepLab model
            var_to_restore = [v for v in var_to_restore if 'res5d' not in v.name and 'segmentation' not in v.name and 'plane' not in v.name and 'deep_supervision' not in v.name and 'local' not in v.name and 'boundary' not in v.name and 'degridding' not in v.name and 'res2a_branch2a' not in v.name and 'res2a_branch1' not in v.name and 'empty' not in v.name]
            pretrained_model_loader = tf.train.Saver(var_to_restore)
            pretrained_model_loader.restore(sess,"../pretrained_models/deeplab_resnet.ckpt")
        elif options.restore == 1:
            #restore the same model from checkpoint
            loader = tf.train.Saver(var_to_restore)
            loader.restore(sess,"%s/checkpoint.ckpt"%(options.checkpoint_dir))
            bno=sess.run(batchno)
            print(bno)
        elif options.restore == 2:            
            #restore the same model from checkpoint but reset batchno to 1
            loader = tf.train.Saver(var_to_restore)
            loader.restore(sess,"%s/checkpoint.ckpt"%(options.checkpoint_dir))
            sess.run(batchno.assign(1))
        elif options.restore == 3:            
            #restore the same model from standard training
            # if options.predictBoundary == 1:
            #     var_to_restore = [v for v in var_to_restore if 'boundary' not in v.name]
            #     pass            
            # if options.predictConfidence == 1:
            #     var_to_restore = [v for v in var_to_restore if 'confidence' not in v.name]
            #     pass
            var_to_restore = [v for v in var_to_restore if 'empty' not in v.name]
            loader = tf.train.Saver(var_to_restore)
            loader.restore(sess, options.rootFolder + '/checkpoint/planenet_hybrid' + options.hybrid + '_ll1_bw0.5_pb_pp_sm0/checkpoint.ckpt')
            #loader.restore(sess,"checkpoint/planenet/checkpoint.ckpt")
            sess.run(batchno.assign(1))
        elif options.restore == 4:
            #fine-tune another model
            #var_to_restore = [v for v in var_to_restore if 'res4b22_relu_non_plane' not in v.name]
            loader = tf.train.Saver(var_to_restore)
            loader.restore(sess, options.fineTuningCheckpoint)
            sess.run(batchno.assign(1))
            pass
        # Start input enqueue threads.
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)

        MOVING_AVERAGE_DECAY = 0.99
        ema = [0., 0., 0., 0.]
        ema_acc = [1e-10, 1e-10, 1e-10, 1e-10]
        last_snapshot_time = time.time()
        bno=sess.run(batchno)

        try:
            while bno<300000:
                t0 = time.time()

                batchIndexPeriod = bno % 100
                if batchIndexPeriod < len(options.hybrid):
                    #batchType = int(options.hybrid[batchIndexPeriod]) * 2 + 1
                    batchType = 1
                else:
                    batchType = 0
                    pass

                _, total_loss, losses, summary_str, global_gt = sess.run([train_op, loss, loss_dict, summary_op, global_gt_dict_train], feed_dict = {training_flag: batchType == 0})
                for batchIndex in range(options.batchSize):
                    if np.isnan(global_gt['plane'][batchIndex]).any():
                        #print(losses)
                        #print(global_gt['plane'][batchIndex])
                        print((global_gt['num_planes'][batchIndex]))
                        for planeIndex in range(global_gt['num_planes'][batchIndex]):
                            cv2.imwrite('test/mask_' + str(planeIndex) + '.png', drawMaskImage(global_gt['segmentation'][batchIndex, :, :, planeIndex]))
                            continue
                        np.save('temp/plane.npy', global_gt['plane'][batchIndex])                        
                        np.save('temp/depth.npy', global_gt['depth'][batchIndex])
                        np.save('temp/segmentation.npy', global_gt['segmentation'][batchIndex])
                        np.save('temp/info.npy', global_gt['info'][batchIndex])
                        np.save('temp/num_planes.npy', global_gt['num_planes'][batchIndex])
                        planes, segmentation, numPlanes = removeSmallSegments(global_gt['plane'][batchIndex], np.zeros((HEIGHT, WIDTH, 3)), global_gt['depth'][batchIndex].squeeze(), np.zeros((HEIGHT, WIDTH, 3)), np.argmax(global_gt['segmentation'][batchIndex], axis=-1), global_gt['semantics'][batchIndex], global_gt['info'][batchIndex], global_gt['num_planes'][batchIndex])
                        print(planes)
                        exit(1)
                        pass
                    continue
                #writers[batchType].add_summary(summary_str, bno)
                ema[batchType] = ema[batchType] * MOVING_AVERAGE_DECAY + total_loss
                ema_acc[batchType] = ema_acc[batchType] * MOVING_AVERAGE_DECAY + 1

                bno = sess.run(batchno)
                if time.time()-last_snapshot_time > 900:
                    print('save snapshot')
                    saver.save(sess,'%s/checkpoint.ckpt'%options.checkpoint_dir)
                    last_snapshot_time = time.time()
                    pass
        
                print((bno,'train', ema[0] / ema_acc[0], 'val', ema[1] / ema_acc[1], 'train rgbd', ema[2] / ema_acc[2], 'val rgbd', ema[3] / ema_acc[3], 'loss', total_loss, 'time', time.time()-t0))

                if np.random.random() < 0.01 or True:
                    print(losses)
                    pass                
                continue

        except tf.errors.OutOfRangeError:
            print('Done training -- epoch limit reached')
        finally:
            # When done, ask the threads to stop.
            coord.request_stop()
            pass
        
        # Wait for threads to finish.
        coord.join(threads)
        sess.close()
        pass
    return


def test(options):
    if not os.path.exists(options.test_dir):
        os.system("mkdir -p %s"%options.test_dir)
        pass

    if options.dataset == '':
        assert(len(options.hybrid) == 1)
        if options.hybrid == '0':
            options.dataset = 'SUNCG'
        elif options.hybrid == '1':
            options.dataset = 'NYU_RGBD'
        elif options.hybrid == '2':
            options.dataset = 'matterport'
        elif options.hybrid == '3':
            options.dataset = 'ScanNet'
            
        options.dataset
    options.batchSize = 1
    min_after_dequeue = 1000

    reader = RecordReaderAll()
    if options.dataset == 'SUNCG':
        filename_queue = tf.train.string_input_producer([options.rootFolder + '/planes_SUNCG_val.tfrecords'], num_epochs=10000)
    elif options.dataset == 'NYU_RGBD':
        filename_queue = tf.train.string_input_producer([options.rootFolder + '/planes_nyu_rgbd_train.tfrecords'], num_epochs=1)
        options.deepSupervision = 0
        options.predictLocal = 0
    elif options.dataset == 'matterport':
        filename_queue = tf.train.string_input_producer([options.rootFolder + '/planes_matterport_val.tfrecords'], num_epochs=1)
    else:
        if options.suffix == 'sample':
            filename_queue = tf.train.string_input_producer(['../planes_scannet_train_sample.tfrecords'], num_epochs=1)
        else:
            filename_queue = tf.train.string_input_producer([options.rootFolder + '/planes_scannet_val.tfrecords'], num_epochs=1)
            pass
        pass
    img_inp, global_gt_dict, local_gt_dict = reader.getBatch(filename_queue, numOutputPlanes=options.numOutputPlanes, batchSize=options.batchSize, min_after_dequeue=min_after_dequeue, getLocal=True, random=False)

    if options.suffix == 'sample':
        training_flag = tf.constant(True, tf.bool)
    else:
        training_flag = tf.constant(False, tf.bool)
        pass
    
    global_pred_dict, local_pred_dict, deep_pred_dicts = build_graph(img_inp, img_inp, training_flag, options)
    var_to_restore = tf.global_variables()

    loss, loss_dict, debug_dict = build_loss(global_pred_dict, deep_pred_dicts, global_gt_dict, global_gt_dict, training_flag, options)
    

    config=tf.ConfigProto()
    config.gpu_options.allow_growth=True
    config.allow_soft_placement=True

    init_op = tf.group(tf.global_variables_initializer(),
                       tf.local_variables_initializer())
    
    with tf.Session(config=config) as sess:
        sess.run(init_op)
        #var_to_restore = [v for v in var_to_restore if 'res4b22_relu_non_plane' not in v.name]
        loader = tf.train.Saver(var_to_restore)
        loader.restore(sess, "%s/checkpoint.ckpt"%(options.checkpoint_dir))
        #loader.restore(sess, "%s/checkpoint.ckpt"%('checkpoint/planenet_pb_pp_hybrid1'))
        #loader.restore(sess, options.fineTuningCheckpoint)
        
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)
        
        
        try:
            gtDepths = []
            predDepths = []
            planeMasks = []
            #predMasks = []
            gtPlanes = []
            predPlanes = []
            gtSegmentations = []
            predSegmentations = []
            gtNumPlanes = []
            
            imageWidth = WIDTH
            imageHeight = HEIGHT
            focalLength = 517.97
            urange = np.arange(imageWidth).reshape(1, -1).repeat(imageHeight, 0) - imageWidth * 0.5
            vrange = np.arange(imageHeight).reshape(-1, 1).repeat(imageWidth, 1) - imageHeight * 0.5
            ranges = np.array([urange / imageWidth * 640 / focalLength, np.ones(urange.shape), -vrange / imageHeight * 480 / focalLength]).transpose([1, 2, 0])


            for index in range(10):
                print(('image', index))
                t0=time.time()

                img, global_gt, local_gt, global_pred, local_pred, deep_preds, total_loss, losses, debug = sess.run([img_inp, global_gt_dict, local_gt_dict, global_pred_dict, local_pred_dict, deep_pred_dicts, loss, loss_dict, debug_dict])

                # print(options.test_dir)
                # cv2.imwrite(options.test_dir + '/depth.png', drawDepthImage(debug['depth'][0]))
                # cv2.imwrite(options.test_dir + '/normal.png', drawNormalImage(debug['normal'][0]))
                # boundary = debug['boundary'][0]
                # boundary = np.concatenate([boundary, np.zeros((HEIGHT, WIDTH, 1))], axis=2)
                # cv2.imwrite(options.test_dir + '/boundary.png', drawMaskImage(boundary))
                # cv2.imwrite(options.test_dir + '/depth_gt.png', drawDepthImage(debug['depth_gt'][0].squeeze()))
                # exit(1)

                if 'pixelwise' in options.suffix:
                    image = ((img[0] + 0.5) * 255).astype(np.uint8)
                    gt_d = global_gt['depth'].squeeze()
                    pred_d = global_pred['non_plane_depth'].squeeze()
                    #depth = global_gt['depth'].squeeze()
                    if '_2' in options.suffix:
                        pred_p, pred_s, pred_d = fitPlanes(pred_d, numPlanes=20, planeAreaThreshold=3*4, numIterations=100, distanceThreshold=0.05, local=0.2)
                    elif '_3' in options.suffix:
                        pred_p, pred_s, pred_d = fitPlanes(gt_d, numPlanes=20, planeAreaThreshold=3*4, numIterations=100, distanceThreshold=0.05, local=0.2)
                        pass

                    # gt_p = global_gt['plane'][0]
                    # pred_p = planes
                    # valid_mask = (np.linalg.norm(gt_p, axis=1) > 0).astype(np.float32)
                    # diff = np.min(np.linalg.norm(np.expand_dims(gt_p, 1) - np.expand_dims(pred_p, 0), axis=2), 1)
                    # num += valid_mask.sum()
                    # lossSum += (diff * valid_mask).sum()
                    if options.dataset == 'SUNCG':
                        planeMask = np.squeeze(debug['segmentation']).sum(axis=2)
                    else:
                        planeMask = np.ones((HEIGHT, WIDTH))
                        if '_2' in options.suffix or '_3' in options.suffix:
                            planeMask *= (pred_s < 20).astype(np.float32)
                        pass
                    
                    if index < 10:
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_image.png', image)
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_depth.png', drawDepthImage(gt_d))
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', drawDepthImage(pred_d))
                        if '_2' in options.suffix or '_3' in options.suffix:
                            cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred.png', drawSegmentationImage(pred_s))
                            pass
                        #cv2.imwrite(options.test_dir + '/' + str(index) + '_plane_mask.png', drawMaskImage(planeMask))                
                        pass

                        
                    gtDepths.append(gt_d)
                    predDepths.append(pred_d)
                    planeMasks.append(planeMask)


                    if options.dataset != 'NYU_RGBD' and ('_2' in options.suffix or '_3' in options.suffix):
                        gt_p = global_gt['plane'][0]
                        gt_s = global_gt['segmentation'][0]
                        gt_num_p = global_gt['num_planes'][0]

                        pred_s = (np.expand_dims(pred_s, -1) == np.reshape(np.arange(options.numOutputPlanes), [1, 1, -1])).astype(np.float32)
                        gtPlanes.append(gt_p)
                        predPlanes.append(pred_p)
                        gtSegmentations.append(gt_s)
                        gtNumPlanes.append(gt_num_p)
                        predSegmentations.append(pred_s)
                        pass
                    
                    #planeMasks.append((planeSegmentation < 20).astype(np.float32))
                    continue
                
                print(losses)
                print(total_loss)
                #print(losses)
                #exit(1)
                im = img[0]
                image = ((im + 0.5) * 255).astype(np.uint8)                

                gt_d = global_gt['depth'].squeeze()
                                

                if options.predictLocal:
                    pred_local_s = 1 / (1 + np.exp(-local_pred['score'][0]))
                    pred_local_p = local_pred['plane'][0]
                    pred_local_m = local_pred['mask'][0]
                  
                    gt_local_s = local_gt['score'][0]
                    gt_local_m = local_gt['mask'][0]

                    #visualize local plane prediction
                    stride = 8
                    boxSize = 64
                    xs = np.arange(WIDTH / stride) * stride + stride / 2
                    ys = np.arange(HEIGHT / stride) * stride + stride / 2
                    padding = boxSize / 2 + 1
                    maskImage = np.zeros((HEIGHT + padding * 2, WIDTH + padding * 2, 3), dtype=np.uint8)
                    maskImage[padding:padding + HEIGHT, padding:padding + WIDTH, :] = image / 2
                    for gridY, y in enumerate(ys):
                        for gridX, x in enumerate(xs):
                            score = pred_local_s[gridY][gridX]
                            if score < 0.5:
                                continue                              
                            mask = pred_local_m[gridY][gridX].reshape([16, 16])        
                            mask = cv2.resize(mask, (boxSize, boxSize))
                            maskImage[y - boxSize / 2 + padding:y + boxSize / 2 + padding, x - boxSize / 2 + padding:x + boxSize / 2 + padding, 0][mask > 0.5] = 255
                            continue
                        continue
                    for gridY, y in enumerate(ys):
                        for gridX, x in enumerate(xs):
                            score = gt_local_s[gridY][gridX]
                            if score < 0.5:
                                continue                              
                            mask = gt_local_m[gridY][gridX].reshape([16, 16])        
                            mask = cv2.resize(mask, (boxSize, boxSize))
                            maskImage[y - boxSize / 2 + padding:y + boxSize / 2 + padding, x - boxSize / 2 + padding:x + boxSize / 2 + padding, 2][mask > 0.5] = 255
                            continue
                        continue
                    pass

                pred_p = global_pred['plane'][0]
                pred_s = global_pred['segmentation'][0]

                pred_np_m = global_pred['non_plane_mask'][0]
                pred_np_d = global_pred['non_plane_depth'][0]
                pred_np_n = global_pred['non_plane_normal'][0]
                
                planeMask = 1 - global_gt['non_plane_mask'][0]
                info = global_gt['info'][0]


                layer_segmentations_0 = pred_s[:, :, :options.numOutputPlanes_0]
                layer_segmentations_softmax_0 = softmax(layer_segmentations_0)
                layer_segmentations_1 = pred_s[:, :, options.numOutputPlanes_0:options.numOutputPlanes]
                layer_segmentations_softmax_1 = softmax(layer_segmentations_1)
                #all_segmentations = np.concatenate([layer_segmentations_softmax_0 * global_pred['empty_mask'][0], layer_segmentations_1, pred_np_m], axis=2)
                #all_segmentations_softmax = softmax(all_segmentations)
                empty_mask = sigmoid(global_pred['empty_mask'][0])
                non_plane_mask = sigmoid(pred_np_m)
                all_segmentations_softmax = np.concatenate([layer_segmentations_softmax_0 * empty_mask * (1 - non_plane_mask), layer_segmentations_softmax_1 * (1 - empty_mask) * (1 - non_plane_mask), non_plane_mask], axis=2)
                
                plane_depths = calcPlaneDepths(pred_p, WIDTH, HEIGHT, info)
                all_depths = np.concatenate([plane_depths, pred_np_d], axis=2)

                segmentation = np.argmax(all_segmentations_softmax, 2)
                pred_d = all_depths.reshape(-1, options.numOutputPlanes + 1)[np.arange(WIDTH * HEIGHT), segmentation.reshape(-1)].reshape(HEIGHT, WIDTH)


                if False:
                    gt_s = global_gt['segmentation'][0]
                    all_segmentations = np.concatenate([gt_s, 1 - planeMask], axis=2)
                    gt_p = global_gt['plane'][0]

                    # valid_mask = (np.linalg.norm(gt_p, axis=1) > 0).astype(np.float32)
                    # diff = np.min(np.linalg.norm(np.expand_dims(gt_p, 1) - np.expand_dims(pred_p, 0), axis=2), 1)
                    # num += valid_mask.sum()
                    # lossSum += (diff * valid_mask).sum()
                    #gt_p = np.stack([-gt_p[:, 0], -gt_p[:, 2], -gt_p[:, 1]], axis=1)
                    
                    plane_depths = calcPlaneDepths(gt_p, WIDTH, HEIGHT, info)
                    all_depths = np.concatenate([plane_depths, pred_np_d], axis=2)

                    segmentation = np.argmax(all_segmentations, 2)
                    pred_d = all_depths.reshape(-1, options.numOutputPlanes + 1)[np.arange(WIDTH * HEIGHT), segmentation.reshape(-1)].reshape(HEIGHT, WIDTH)
                    # print(gt_p)
                    # for segmentIndex in xrange(options.numOutputPlanes):
                    #     cv2.imwrite(options.test_dir + '/' + str(index) + '_mask_' + str(segmentIndex) + '.png', drawMaskImage(segmentation == segmentIndex))
                    #     continue
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', drawDepthImage(pred_d))
                    #exit(1)
                    pass

                

                if options.dataset != 'NYU_RGBD':
                    gt_p = global_gt['plane'][0]
                    gt_s = global_gt['segmentation'][0]
                    gt_num_p = global_gt['num_planes'][0]
                    gtPlanes.append(gt_p)
                    predPlanes.append(pred_p)
                    gtSegmentations.append(gt_s)
                    gtNumPlanes.append(gt_num_p)
                    predSegmentations.append(pred_s)
                    pass
            
                gtDepths.append(gt_d)
                planeMasks.append(planeMask.squeeze())
                predDepths.append(pred_d)
                evaluateDepths(predDepths[-1], gtDepths[-1], gtDepths[-1] > 0, planeMasks[-1])
                
                
                if index >= 10:
                    continue


                if 'normal' in global_gt and global_gt['info'][0][19] < 2:
                    gt_n = global_gt['normal'][0]
                    #gt_n = np.stack([-gt_n[:, :, 0], -gt_n[:, :, 2], -gt_n[:, :, 1]], axis=2)
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_normal_gt.png', drawNormalImage(gt_n))
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_normal_pred.png', drawNormalImage(pred_np_n))
                    pass
                
                if 'segmentation' in global_gt:
                    gt_s_ori = global_gt['segmentation'][0]
                    gt_s, gt_p = sortSegmentations(gt_s_ori, gt_p, pred_p)
                    #print(np.concatenate([pred_p, gt_p], axis=1))
                    #print(pow(np.linalg.norm(pred_p - gt_p, axis=1), 2).mean() * 10000)
                    #print(debug['dists'])
                    #exit(1)
                    #cv2.imwrite(options.test_dir + '/' + str(index) + '_plane_mask_gt.png', drawMaskImage(planeMask))  
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_gt.png', drawSegmentationImage(np.concatenate([gt_s, 1 - planeMask], axis=2), blackIndex=options.numOutputPlanes)
)
                    #cv2.imwrite(options.test_dir + '/' + str(index) + '_test.png', drawMaskImage(np.sum(np.concatenate([gt_s, 1 - planeMask], axis=2), axis=2)))
                    #exit(1)
                    #exit(1)
                    pass


                if options.predictConfidence == 1 and options.dataset == 'SUNCG':
                    pred_p_c = global_pred['confidence'][0]
                    pred_p_c = 1 / (1 + np.exp(-pred_p_c))
                    #print(pred_p_c)
                    # print(losses)
                    # print(debug['plane'][0])
                    # print(pred_p)
                    # exit(1)
                    numPlanes = global_gt['num_planes'][0]
                    print((numPlanes, (pred_p_c > 0.5).sum()))
                    
                    pred_p_c = (pred_p_c > 0.5).astype(np.float32)
                    pred_p *= pred_p_c
                    pred_s -= (1 - pred_p_c.reshape([1, 1, options.numOutputPlanes])) * 10
                    pass
                  
                if False:
                    #dump results for post processing
                    if index >= 10:
                        break
                    np.save(options.dump_dir + '/planes_' + str(index) + '.npy', pred_p)
                    np.save(options.dump_dir + '/segmentations_' + str(index) + '.npy', pred_s)
                    np.save(options.dump_dir + '/segmentations_gt_' + str(index) + '.npy', gt_s)
                    np.save(options.dump_dir + '/non_plane_depth_' + str(index) + '.npy', pred_np_d)
                    np.save(options.dump_dir + '/non_plane_segmentation_' + str(index) + '.npy', pred_np_m)
                    boundary = pred_boundary[0]
                    boundary = 1 / (1 + np.exp(-boundary))
                    boundary = np.concatenate([boundary, np.zeros((HEIGHT, WIDTH, 1))], axis=2)                    
                    cv2.imwrite(options.dump_dir + '/boundary_' + str(index) + '.png', drawMaskImage(boundary))
                    cv2.imwrite(options.dump_dir + '/image_' + str(index) + '.png', cv2.resize(image, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR))
                    np.save(options.dump_dir + '/depth_' + str(index) + '.npy', gt_d)
                    continue                

                cv2.imwrite(options.test_dir + '/' + str(index) + '_image.png', image)
                cv2.imwrite(options.test_dir + '/' + str(index) + '_depth.png', drawDepthImage(gt_d))
                #cv2.imwrite(options.test_dir + '/' + str(index) + '_overlay.png', drawDepthImageOverlay(image, gt_d))
                
                if options.predictBoundary:
                    pred_boundary = global_pred['boundary'][0]
                    pred_boundary = 1 / (1 + np.exp(-pred_boundary))
                    boundary = np.concatenate([pred_boundary, np.zeros((HEIGHT, WIDTH, 1))], axis=2)
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_boundary_pred.png', drawMaskImage(boundary))
                    pass

                if 'boundary' in global_gt:
                    gt_boundary = global_gt['boundary'][0]
                    boundary = np.concatenate([gt_boundary, np.zeros((HEIGHT, WIDTH, 1))], axis=2)                
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_boundary_gt.png', drawMaskImage(boundary))
                    pass


                if options.deepSupervision >= 1 and False:
                    segmentation_deep = np.argmax(deep_preds[0]['segmentation'][0], 2)
                    segmentation_deep[segmentation_deep == options.numOutputPlanes] = -1
                    segmentation_deep += 1
                
                    plane_depths_deep = calcPlaneDepths(deep_preds[0]['plane'][0], WIDTH, HEIGHT, info)
                    all_depths_deep = np.concatenate([pred_np_d, plane_depths_deep], axis=2)
                    pred_d_deep = all_depths_deep.reshape(-1, options.numOutputPlanes + 1)[np.arange(WIDTH * HEIGHT), segmentation_deep.reshape(-1)].reshape(HEIGHT, WIDTH)
                
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred_0.png', drawSegmentationImage(deep_preds[0]['segmentation'][0]))
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred_0.png', drawDepthImage(pred_d_deep))
                    pass


                #print(pred_np_m)
                #print(pred_s)
                #print(global_gt['plane'][0])
                #print(pred_p)
                #exit(1)

                segmentation = np.argmax(layer_segmentations_0, axis=-1)
                layer_depth_0 = all_depths.reshape(-1, options.numOutputPlanes + 1)[np.arange(WIDTH * HEIGHT), segmentation.reshape(-1)].reshape(HEIGHT, WIDTH) 
                cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred_0.png', drawDepthImage(layer_depth_0))
                cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred_0.png', drawSegmentationImage(segmentation))
                cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred.png', drawSegmentationImage(all_segmentations_softmax, blackIndex=options.numOutputPlanes))
                #exit(1)
                cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', drawDepthImage(pred_d))


                if 'cost_mask' in debug:
                    #cv2.imwrite(options.test_dir + '/' + str(index) + '_cost_mask.png', drawMaskImage(debug['cost_mask'][0]))
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_cost_mask.png', drawMaskImage(debug['cost_mask'][0].sum(2)))


                    for planeIndex in range(debug['depth'].shape[-1]):
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_cost_depth_' + str(planeIndex) + '.png', drawMaskImage(debug['depth'][0, :, :, planeIndex]))
                        print((planeIndex, debug['depth'][0, :, :, planeIndex].mean()))
                        continue
                        
                    total_loss = 0
                    for planeIndex in range(debug['cost_mask'].shape[-1]):
                        print((planeIndex, debug['cost_mask'][0, :, :, planeIndex].max(), debug['cost_mask'][0, :, :, planeIndex].min(), debug['cost_mask'][0, :, :, planeIndex].mean() * 200000. / 22))
                        total_loss += debug['cost_mask'][0, :, :, planeIndex].mean() * 200000. / 22
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_cost_mask_' + str(planeIndex) + '.png', drawMaskImage(debug['cost_mask'][0, :, :, planeIndex]))
                        continue
                    print(total_loss)
                    
                    for planeIndex in range(options.numOutputPlanes + 1):
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_mask_' + str(planeIndex) + '.png', drawMaskImage(all_segmentations_softmax[:, :, planeIndex]))
                        continue

                    for planeIndex in range(options.numOutputPlanes_0):
                        cv2.imwrite(options.test_dir + '/' + str(index) + '_layer_mask_' + str(planeIndex) + '.png', drawMaskImage(layer_segmentations_softmax_0[:, :, planeIndex]))
                        continue

                    cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_gt.png', drawSegmentationImage(np.concatenate([gt_s_ori, 1 - planeMask], axis=2), blackIndex=options.numOutputPlanes))
                    gt_s_ori = debug['segmentation'][0]
                    for planeIndex in range(options.numOutputPlanes):
                        cv2.imwrite(options.test_dir + '/mask_gt_' + str(planeIndex) + '.png', drawMaskImage(gt_s[:, :, planeIndex]))
                        #cv2.imwrite(options.test_dir + '/mask_background_' + str(planeIndex) + '.png', drawMaskImage(debug['background'][0, :, :, planeIndex]))
                        continue
                    #print(debug['background'][0])
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_empty_mask_pred.png', drawMaskImage(all_segmentations_softmax[:, :, :options.numOutputPlanes_0].sum(2)))                    
                    #exit(1)
                    


                    print(pred_p)
                    
                    # print(pred_s.max(0).max(0))
                    # print(pred_s.min(0).min(0))
                    # print(all_segmentations_softmax.max(0).max(0))
                    # print(all_segmentations_softmax.min(0).min(0))

                    print((pred_s[150][150]))
                    print((all_segmentations_softmax[150][150]))
                    print((layer_segmentations_softmax_0[150][150]))
                    print((global_pred['empty_mask'][0][150][150]))
                    #cv2.imwrite(options.test_dir + '/mask_empty.png', drawMaskImage(gt_s[:, :, 5] + gt_s[:, :, 14]))
                    # plane_depths = calcPlaneDepths(gt_p, WIDTH, HEIGHT, global_gt['info'][0])
                    # mask_5 = plane_depths[:, :, 5] < plane_depths[:, :, 14]
                    # mask_14 = plane_depths[:, :, 5] > plane_depths[:, :, 14]
                    # mask_5[gt_s[:, :, 5].astype(np.bool)] = True
                    # mask_14[gt_s[:, :, 5].astype(np.bool)] = False
                    # mask_5[gt_s[:, :, 14].astype(np.bool)] = False
                    # mask_14[gt_s[:, :, 14].astype(np.bool)] = True
                    # cv2.imwrite(options.test_dir + '/mask_5.png', drawMaskImage(mask_5))
                    # cv2.imwrite(options.test_dir + '/mask_14.png', drawMaskImage(plane_depths[:, :, 5] > plane_depths[:, :, 14]))
                    # print(debug['segmentation_loss'].shape)

                    pred_s = debug['segmentation_pred'][0]
                    gt_s = debug['segmentation'][0]
                    #all_segmentations_softmax = softmax(pred_s)
                    all_segmentations_softmax = pred_s
                    print((gt_s.sum(2).max(), gt_s.sum(2).min(), all_segmentations_softmax.sum(2).max(), all_segmentations_softmax.sum(2).min(), all_segmentations_softmax.max(), all_segmentations_softmax.min()))
                    #print(gt_s[:, :, 7].max())
                    total_loss = 0
                    for planeIndex in range(options.numOutputPlanes + 1):                    
                        #print(debug['segmentation_loss'][0, planeIndex].mean())
                        if planeIndex < options.numOutputPlanes:
                            loss = -(gt_s[:, :, planeIndex] * np.log(np.maximum(all_segmentations_softmax[:, :, planeIndex], 1e-31))).mean() * 1000
                        else:
                            loss = -(global_gt['non_plane_mask'][0, :, :, 0] * np.log(np.maximum(all_segmentations_softmax[:, :, planeIndex], 1e-10))).mean() * 1000
                            pass
                        print(loss)
                        total_loss += loss
                        continue
                    print(total_loss)
                    exit(1)
                    pass
                    
                continue

            # if options.dataset == 'SUNCG':
            #     if 'pixelwise' not in options.suffix:
            #         evaluatePlaneSegmentation(np.array(predPlanes), np.array(predSegmentations), np.array(gtPlanes), np.array(gtSegmentations), np.array(gtNumPlanes), planeDistanceThreshold = 0.3, IOUThreshold = 0.5, prefix='test/planenet_')
            #     elif '_2' in options.suffix:
            #         evaluatePlaneSegmentation(np.array(predPlanes), np.array(predSegmentations), np.array(gtPlanes), np.array(gtSegmentations), np.array(gtNumPlanes), planeDistanceThreshold = 0.3, IOUThreshold = 0.5, prefix='test/pixelwise_pred_')
            #     elif '_3' in options.suffix:
            #         evaluatePlaneSegmentation(np.array(predPlanes), np.array(predSegmentations), np.array(gtPlanes), np.array(gtSegmentations), np.array(gtNumPlanes), planeDistanceThreshold = 0.3, IOUThreshold = 0.5, prefix='test/pixelwise_gt_')
            #         pass
            #     pass
            
            predDepths = np.array(predDepths)
            gtDepths = np.array(gtDepths)
            planeMasks = np.array(planeMasks)
            #predMasks = np.array(predMasks)
            evaluateDepths(predDepths, gtDepths, gtDepths > 0, planeMasks)
            exit(1)

        except tf.errors.OutOfRangeError:
            print('Done training -- epoch limit reached')
        finally:
            # When done, ask the threads to stop.
            coord.request_stop()
            pass
        
        # Wait for threads to finish.
        coord.join(threads)
        sess.close()
        pass
    return


def predict(options):
    options.test_dir += '_predict'
    if not os.path.exists(options.test_dir):
        os.system("mkdir -p %s"%options.test_dir)
        pass

    batchSize = 1
    img_inp = tf.placeholder(tf.float32,shape=(batchSize,HEIGHT,WIDTH,3),name='img_inp')
    plane_gt=tf.placeholder(tf.float32,shape=(batchSize,options.numOutputPlanes, 3),name='plane_inp')
    validating_inp = tf.constant(0, tf.int32)

    global_pred_dict, local_pred_dict, deep_pred_dicts = build_graph(img_inp_train, img_inp_val, img_inp_rgbd_train, img_inp_rgbd_val, training_flag, options)

    var_to_restore = tf.global_variables()
    
 
    config=tf.ConfigProto()
    config.gpu_options.allow_growth=True
    config.allow_soft_placement=True


    if dataset == 'SUNCG':
        image_list_file = os.path.join('../PythonScripts/SUNCG/image_list_100_tail_500000.txt')
        with open(image_list_file) as f:
            im_names = [{'image': im_name.strip().replace('plane_global.npy', 'mlt.png'), 'depth': im_name.strip().replace('plane_global.npy', 'depth.png'), 'normal': im_name.strip().replace('plane_global.npy', 'norm_camera.png'), 'valid': im_name.strip().replace('plane_global.npy', 'valid.png'), 'plane': im_name.strip()} for im_name in f.readlines()]
            pass
    else:
        im_names = glob.glob('../../Data/NYU_RGBD/*_color.png')
        im_names = [{'image': im_name, 'depth': im_name.replace('color.png', 'depth.png'), 'normal': im_name.replace('color.png', 'norm_camera.png'), 'invalid_mask': im_name.replace('color.png', 'valid.png')} for im_name in im_names]
        pass
      
    if numImages > 0:
        im_names = im_names[:numImages]
        pass

    #if args.imageIndex > 0:
    #im_names = im_names[args.imageIndex:args.imageIndex + 1]
    #pass    

    init_op = tf.group(tf.global_variables_initializer(),
                       tf.local_variables_initializer())


    with tf.Session(config=config) as sess:
        saver = tf.train.Saver()
        #sess.run(tf.global_variables_initializer())
        saver.restore(sess,"%s/%s.ckpt"%(options.checkpoint_dir,keyname))

        gtDepths = []
        predDepths = []
        segmentationDepths = []
        predDepthsOneHot = []
        planeMasks = []
        predMasks = []

        imageWidth = WIDTH
        imageHeight = HEIGHT
        focalLength = 517.97
        urange = np.arange(imageWidth).reshape(1, -1).repeat(imageHeight, 0) - imageWidth * 0.5
        vrange = np.arange(imageHeight).reshape(-1, 1).repeat(imageWidth, 1) - imageHeight * 0.5
        ranges = np.array([urange / focalLength, np.ones(urange.shape), -vrange / focalLength]).transpose([1, 2, 0])
        
        cv2.imwrite(options.test_dir + '/one.png', np.ones((HEIGHT, WIDTH), dtype=np.uint8) * 255)
        cv2.imwrite(options.test_dir + '/zero.png', np.zeros((HEIGHT, WIDTH), dtype=np.uint8) * 255)
        for index, im_name in enumerate(im_names):
            if index <= -1:
                continue
            print((im_name['image']))
            im = cv2.imread(im_name['image'])
            image = im.astype(np.float32, copy=False)
            image = image / 255 - 0.5
            image = cv2.resize(image, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)

            #planes = np.load(im_name['plane'])
            # numPlanes = planes.shape[0]
            # if numPlanes > options.numOutputPlanes:
            #     planeAreas = planes[:, 3:].sum(1)
            #     sortInds = np.argsort(planeAreas)[::-1]
            #     planes = planes[sortInds[:options.numOutputPlanes]]
            #     pass
            # gt_p = np.zeros((1, options.numOutputPlanes, 3))
            # gt_p[0, :numPlanes] = planes[:numPlanes, :3]

            normal = np.array(PIL.Image.open(im_name['normal'])).astype(np.float) / 255 * 2 - 1
            norm = np.linalg.norm(normal, 2, 2)
            for c in range(3):
                normal[:, :, c] /= norm
                continue
            normal = cv2.resize(normal, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)
            
            depth = np.array(PIL.Image.open(im_name['depth'])).astype(np.float) / 1000
            depth = cv2.resize(depth, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)

            invalid_mask = cv2.resize(cv2.imread(im_name['invalid_mask'], 0), (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR) > 128

            gtDepths.append(depth)

            
            pred_p, pred_d, pred_n, pred_s, pred_np_m, pred_np_d, pred_np_n, pred_boundary, pred_local_score, pred_local_p, pred_local_mask = sess.run([plane_pred, depth_pred, normal_pred, segmentation_pred, non_plane_mask_pred, non_plane_depth_pred, non_plane_normal_pred, boundary_pred, local_score_pred, local_p_pred, local_mask_pred], feed_dict = {img_inp:np.expand_dims(image, 0), plane_gt: np.zeros((batchSize, options.numOutputPlanes, 3))})


            pred_s = pred_s[0] 
            pred_p = pred_p[0]
            pred_np_m = pred_np_m[0]
            pred_np_d = pred_np_d[0]
            pred_np_n = pred_np_n[0]
            #pred_s = 1 / (1 + np.exp(-pred_s))

            plane_depths = calcPlaneDepths(pred_p, WIDTH, HEIGHT)
            all_depths = np.concatenate([pred_np_d, plane_depths], axis=2)

            all_segmentations = np.concatenate([pred_np_m, pred_s], axis=2)
            segmentation = np.argmax(all_segmentations, 2)
            if suffix != 'pixelwise':
                pred_d = all_depths.reshape(-1, options.numOutputPlanes + 1)[np.arange(WIDTH * HEIGHT), segmentation.reshape(-1)].reshape(HEIGHT, WIDTH)
            else:
                pred_d = np.squeeze(pred_np_d)
                pass
            predDepths.append(pred_d)
            predMasks.append(segmentation != 0)
            planeMasks.append(invalid_mask)

            #depthError, normalError, occupancy, segmentationTest, reconstructedDepth, occupancyMask = evaluatePlanes(pred_p, im_name['image'])
            #reconstructedDepth = cv2.resize(reconstructedDepth, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)
            
            #evaluatePlanes(pred_p[0], im_name, options.test_dir, index)
            #print(pred_p)
            #print(gt_p)
            #print((pow(pred_d[0, :, :, 0] - depth, 2) * (gt_s.max(2) > 0.5)).mean())
            #print((depthError, normalError, occupancy))
            
            evaluateDepths(predDepths[index], gtDepths[index], np.ones(planeMasks[index].shape), planeMasks[index])

            if index >= 10:
                continue
            cv2.imwrite(options.test_dir + '/' + str(index) + '_image.png', cv2.resize(im, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR))
            #cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_gt.png', (minDepth / np.clip(depth, minDepth, 20) * 255).astype(np.uint8))
            #cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', (minDepth / np.clip(pred_d[0, :, :, 0], minDepth, 20) * 255).astype(np.uint8))
            #cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_plane.png', (minDepth / np.clip(reconstructedDepth, minDepth, 20) * 255).astype(np.uint8))

            pred_boundary = pred_boundary[0]
            boundary = (1 / (1 + np.exp(-pred_boundary)) * 255).astype(np.uint8)
            boundary = np.concatenate([boundary, np.zeros((HEIGHT, WIDTH, 1))], axis=2)
            cv2.imwrite(options.test_dir + '/' + str(index) + '_boundary_pred.png', boundary)
            
            cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_inp.png', drawDepthImage(depth))
            cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', drawDepthImage(pred_d))
            #cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_plane.png', drawDepthImage(reconstructedDepth))
            cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred_diff.png', drawDiffImage(pred_d, depth, 0.5))
            #cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_plane_diff.png', np.minimum(np.abs(reconstructedDepth - depth) / 0.5 * 255, 255).astype(np.uint8))
            cv2.imwrite(options.test_dir + '/' + str(index) + '_normal_inp.png', drawNormalImage(normal))
            cv2.imwrite(options.test_dir + '/' + str(index) + '_normal_pred.png', drawNormalImage(pred_np_n))
            cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred.png', drawSegmentationImage(all_segmentations, black=True))

            segmentation = np.argmax(pred_s, 2)
            #writePLYFile(options.test_dir, index, image, pred_p, segmentation)

            if index < 0:
                for planeIndex in range(options.numOutputPlanes):
                    cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_' + str(planeIndex) + '.png', drawMaskImage(pred_s[:, :, planeIndex]))
                    #cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_' + str(planeIndex) + '_gt.png', drawMaskImage(gt_s[:, :, planeIndex]))
                    continue
                pass
            continue
        predDepths = np.array(predDepths)
        gtDepths = np.array(gtDepths)
        planeMasks = np.array(planeMasks)
        predMasks = np.array(predMasks)
        #evaluateDepths(predDepths, gtDepths, planeMasks, predMasks)
        evaluateDepths(predDepths, gtDepths, planeMasks, planeMasks)
        #exit(1)
        pass
    return


def fitPlanesRGBD(options):
    writeHTMLRGBD('../results/RANSAC_RGBD/index.html', 10)
    exit(1)
    if not os.path.exists(options.checkpoint_dir):
        os.system("mkdir -p %s"%options.checkpoint_dir)
        pass
    if not os.path.exists(options.test_dir):
        os.system("mkdir -p %s"%options.test_dir)
        pass
    
    min_after_dequeue = 1000

    reader_rgbd = RecordReaderRGBD()
    filename_queue_rgbd = tf.train.string_input_producer(['../planes_nyu_rgbd_train.tfrecords'], num_epochs=1)
    img_inp_rgbd, global_gt_dict_rgbd, local_gt_dict_rgbd = reader_rgbd.getBatch(filename_queue_rgbd, numOutputPlanes=options.numOutputPlanes, batchSize=1, min_after_dequeue=min_after_dequeue, getLocal=True)

    config=tf.ConfigProto()
    config.gpu_options.allow_growth=True
    config.allow_soft_placement=True

    init_op = tf.group(tf.global_variables_initializer(),
                       tf.local_variables_initializer())

    with tf.Session(config=config) as sess:
        sess.run(init_op)

        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)

        try:
            gtDepths = []
            predDepths = []
            planeMasks = []
            for index in range(10):
                image, depth, path = sess.run([img_inp_rgbd, global_gt_dict_rgbd['depth'], global_gt_dict_rgbd['path']])
                image = ((image[0] + 0.5) * 255).astype(np.uint8)
                depth = depth.squeeze()
                
                cv2.imwrite(options.test_dir + '/' + str(index) + '_image.png', image)
                cv2.imwrite(options.test_dir + '/' + str(index) + '_depth.png', drawDepthImage(depth))
                #cv2.imwrite(options.test_dir + '/' + str(index) + '_mask.png', drawMaskImage(depth == 0))
                planes, planeSegmentation, depthPred = fitPlanes(depth, numPlanes=20)                
                cv2.imwrite(options.test_dir + '/' + str(index) + '_segmentation_pred.png', drawSegmentationImage(planeSegmentation))
                cv2.imwrite(options.test_dir + '/' + str(index) + '_depth_pred.png', drawDepthImage(depthPred))

                gtDepths.append(depth)
                predDepths.append(depthPred)
                planeMasks.append((planeSegmentation < 20).astype(np.float32))
                continue
            predDepths = np.array(predDepths)
            gtDepths = np.array(gtDepths)
            planeMasks = np.array(planeMasks)
            evaluateDepths(predDepths, gtDepths, np.ones(planeMasks.shape, dtype=np.bool), planeMasks)            
        except tf.errors.OutOfRangeError:
            print('done fitting')
        finally:
            # When done, ask the threads to stop.
            coord.request_stop()
            pass
    return

def writeInfo(options):
    x = (np.arange(11) * 0.1).tolist()
    ys = []
    ys.append(np.load('test/planenet_pixel_IOU.npy').tolist())
    ys.append(np.load('test/pixelwise_pred_pixel_IOU.npy').tolist())
    ys.append(np.load('test/pixelwise_gt_pixel_IOU.npy').tolist())
    plotCurves(x, ys, filename = 'test/plane_comparison.png', xlabel='IOU', ylabel='pixel coverage', labels=['planenet', 'pixelwise+RANSAC', 'GT+RANSAC'])

    x = (0.5 - np.arange(11) * 0.05).tolist()
    ys = []
    ys.append(np.load('test/planenet_pixel_diff.npy').tolist())
    ys.append(np.load('test/pixelwise_pred_pixel_diff.npy').tolist())
    ys.append(np.load('test/pixelwise_gt_pixel_diff.npy').tolist())
    plotCurves(x, ys, filename = 'test/plane_comparison_diff.png', xlabel='diff', ylabel='pixel coverage', labels=['planenet', 'pixelwise+RANSAC', 'GT+RANSAC'])
    
    return

def parse_args():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(description='Planenet')
    parser.add_argument('--gpu', dest='gpu_id',
                        help='GPU device id to use [0]',
                        default=0, type=int)
    #task: [train, test, predict]
    parser.add_argument('--task', dest='task',
                        help='task type: [train, test, predict]',
                        default='train', type=str)
    parser.add_argument('--restore', dest='restore',
                        help='how to restore the model',
                        default=0, type=int)
    parser.add_argument('--numOutputPlanes', dest='numOutputPlanes',
                        help='the number of output planes',
                        default=20, type=int)
    parser.add_argument('--numOutputPlanes_0', dest='numOutputPlanes_0',
                        help='the number of output planes',
                        default=5, type=int)    
    parser.add_argument('--batchSize', dest='batchSize',
                        help='batch size',
                        default=16, type=int)
    parser.add_argument('--dataset', dest='dataset',
                        help='dataset name for test/predict',
                        default='', type=str)
    parser.add_argument('--numImages', dest='numImages',
                        help='the number of images to test/predict',
                        default=100, type=int)
    parser.add_argument('--boundaryLoss', dest='boundaryLoss',
                        help='use boundary loss: [0, 1]',
                        default=1, type=int)
    parser.add_argument('--diverseLoss', dest='diverseLoss',
                        help='use diverse loss: [0, 1]',
                        default=1, type=int)
    parser.add_argument('--labelLoss', dest='labelLoss',
                        help='use label loss: [0, 1]',
                        default=0, type=int)    
    parser.add_argument('--deepSupervision', dest='deepSupervision',
                        help='deep supervision level: [0, 1, 2]',
                        default=1, type=int)
    parser.add_argument('--sameMatching', dest='sameMatching',
                        help='use the same matching for all deep supervision layers and the final prediction: [0, 1]',
                        default=1, type=int)    
    parser.add_argument('--anchorPlanes', dest='anchorPlanes',
                        help='use anchor planes for all deep supervision layers and the final prediction: [0, 1]',
                        default=0, type=int) 
    parser.add_argument('--crf', dest='crf',
                        help='the number of CRF iterations',
                        default=0, type=int)
    parser.add_argument('--backwardLossWeight', dest='backwardLossWeight',
                        help='backward matching loss',
                        default=0, type=float)
    parser.add_argument('--predictBoundary', dest='predictBoundary',
                        help='whether predict boundary or not: [0, 1]',
                        default=0, type=int)
    parser.add_argument('--predictLocal', dest='predictLocal',
                        help='whether predict local planes or not: [0, 1]',
                        default=0, type=int)
    parser.add_argument('--predictConfidence', dest='predictConfidence',
                        help='whether predict plane confidence or not: [0, 1]',
                        default=0, type=int)
    parser.add_argument('--predictPixelwise', dest='predictPixelwise',
                        help='whether predict pixelwise depth or not: [0, 1]',
                        default=0, type=int)    
    parser.add_argument('--fineTuningCheckpoint', dest='fineTuningCheckpoint',
                        help='specify the model for fine-tuning',
                        default='../PlaneSetGeneration/dump_planenet_diverse/train_planenet_diverse.ckpt', type=str)
    parser.add_argument('--suffix', dest='suffix',
                        help='add a suffix to keyname to distinguish experiments',
                        default='', type=str)
    parser.add_argument('--l2Weight', dest='l2Weight',
                        help='L2 regulation weight',
                        default=5e-4, type=float)
    parser.add_argument('--LR', dest='LR',
                        help='learning rate',
                        default=3e-5, type=float)
    parser.add_argument('--hybrid', dest='hybrid',
                        help='hybrid training',
                        default='0', type=str)
    parser.add_argument('--rootFolder', dest='rootFolder',
                        help='root folder',
                        default='/mnt/vision/PlaneNet/', type=str)
    

    args = parser.parse_args()
    args.keyname = os.path.basename(__file__).rstrip('.py')
    args.keyname = args.keyname.replace('train_', '')

    if args.numOutputPlanes != 20:
        args.keyname += '_np' + str(args.numOutputPlanes)
        pass
    args.keyname += '_hybrid' + args.hybrid
    
    if args.boundaryLoss != 1:
        args.keyname += '_bl' + str(args.boundaryLoss)
        pass
    if args.diverseLoss == 0:
        args.keyname += '_dl0'
        pass
    if args.labelLoss == 1:
        args.keyname += '_ll1'
        pass    
    if args.deepSupervision != 1:
        args.keyname += '_ds' + str(args.deepSupervision)
        pass
    if args.crf > 0:
        args.keyname += '_crf' + str(args.crf)
        pass
    if args.backwardLossWeight > 0:
        args.keyname += '_bw' + str(args.backwardLossWeight)
        pass
    if args.predictBoundary == 1:
        args.keyname += '_pb'
        pass
    if args.predictConfidence == 1:
        args.keyname += '_pc'
        pass        
    if args.predictLocal == 1:
        args.keyname += '_pl'
        pass
    if args.predictPixelwise == 1:
        args.keyname += '_pp'
        pass    
    if args.sameMatching == 0:
        args.keyname += '_sm0'
        pass
    if args.anchorPlanes == 1:
        args.keyname += '_ap1'
        pass

    
    args.checkpoint_dir = args.rootFolder + '/checkpoint/' + args.keyname
    args.log_dir = 'log/' + args.keyname
    args.test_dir = 'test/' + args.keyname + '_' + args.dataset
    args.predict_dir = 'predict/' + args.keyname + '_' + args.dataset
    args.dump_dir = 'dump/' + args.keyname
    
    #layers where deep supervision happens
    args.deepSupervisionLayers = []
    # if args.deepSupervision >= 1:
    #     args.deepSupervisionLayers.append('res4b22_relu')
    #     pass
    # if args.deepSupervision >= 2:
    #     args.deepSupervisionLayers.append('res4b12_relu')
    #     pass
    return args


if __name__=='__main__':

    # plane = np.load('temp/plane.npy')
    # depth = np.load('temp/depth.npy')    
    # segmentation = np.load('temp/segmentation.npy')
    # info = np.load('temp/info.npy')
    # num_planes = np.load('temp/num_planes.npy')
    # segmentation = np.argmax(segmentation, axis=-1)
    # print(segmentation.shape)
    # planes, segmentation, numPlanes = removeSmallSegments(plane, np.zeros((HEIGHT, WIDTH, 3)), depth.squeeze(), np.zeros((HEIGHT, WIDTH, 3)), segmentation, np.zeros((HEIGHT, WIDTH)), info, num_planes)
    # print(planes)
    # exit(1)
    
    args = parse_args()

    print(("keyname=%s task=%s started"%(args.keyname, args.task)))
    try:
        if args.task == "train":
            main(args)
        elif args.task == "test":
            test(args)
        elif args.task == "predict":
            predict(args)
        elif args.task == "fit":
            fitPlanesRGBD(args)
        elif args.task == "write":
            writeInfo(args)
        else:
            assert False,"format wrong"
            pass
    finally:
        pass

