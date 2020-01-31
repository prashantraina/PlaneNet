from layers import PlaneDepthLayer
import numpy as np
import PIL.Image
import copy
import sys
import os
import cv2
import scipy.ndimage as ndimage
#import pydensecrf.densecrf as dcrf
# from pydensecrf.utils import compute_unary, create_pairwise_bilateral, \
#create_pairwise_gaussian, unary_from_softmax
from skimage import segmentation
#from skimage.future import graph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#from layers import PlaneNormalLayer
#from SegmentationRefinement import *


class ColorPalette:
    def __init__(self, numColors):
        # np.random.seed(2)
        #self.colorMap = np.random.randint(255, size = (numColors, 3))
        #self.colorMap[0] = 0

        self.colorMap = np.array([[255, 0, 0],
                                  [0, 255, 0],
                                  [0, 0, 255],
                                  [80, 128, 255],
                                  [255, 230, 180],
                                  [255, 0, 255],
                                  [0, 255, 255],
                                  [100, 0, 0],
                                  [0, 100, 0],
                                  [255, 255, 0],
                                  [50, 150, 0],
                                  [200, 255, 255],
                                  [255, 200, 255],
                                  [128, 128, 80],
                                  [0, 50, 128],
                                  [0, 100, 100],
                                  [0, 255, 128],
                                  [0, 128, 255],
                                  [255, 0, 128],
                                  [128, 0, 255],
                                  [255, 128, 0],
                                  [128, 255, 0],
                                  ])

        if numColors > self.colorMap.shape[0]:
            self.colorMap = np.random.randint(255, size=(numColors, 3))
            pass

        return

    def getColorMap(self):
        return self.colorMap

    def getColor(self, index):
        if index >= colorMap.shape[0]:
            return np.random.randint(255, size=(3))
        else:
            return self.colorMap[index]
            pass


def writePointCloud(filename, pointCloud, color=[255, 255, 255]):
    with open(filename, 'w') as f:
        header = """ply
format ascii 1.0
element vertex """
        header += str(pointCloud.shape[0])
        header += """
property float x
property float y
property float z
property uchar red                                     { start of vertex color }
property uchar green
property uchar blue
end_header
"""
        f.write(header)
        for point in pointCloud:
            for value in point:
                f.write(str(value) + ' ')
                continue
            for value in color:
                f.write(str(value) + ' ')
                continue
            f.write('\n')
            continue
        f.close()
        pass
    return


def writeClusteringPointCloud(filename, pointCloud, clusters):
    with open(filename, 'w') as f:
        header = """ply
format ascii 1.0
element vertex """
        header += str(pointCloud.shape[0])
        header += """
property float x
property float y
property float z
property uchar red                                     { start of vertex color }
property uchar green
property uchar blue
end_header
"""
        colorMap = np.random.randint(255, size=clusters.shape)
        assignment = np.argmin(np.linalg.norm(
            pointCloud.reshape(-1, 1, 3).repeat(clusters.shape[0], 1)[:] - clusters, 2, 2), 1)
        f.write(header)
        for pointIndex, point in enumerate(pointCloud):
            for value in point:
                f.write(str(value) + ' ')
                continue
            color = colorMap[assignment[pointIndex]]
            for value in color:
                f.write(str(value) + ' ')
                continue
            f.write('\n')
            continue
        f.close()
        pass
    return


def writeNearestNeighbors(filename, pointCloudSource, pointCloudTarget):
    with open(filename, 'w') as f:
        header = """ply
format ascii 1.0
element vertex """
        header += str((pointCloudSource.shape[0] +
                       pointCloudTarget.shape[0] + pointCloudSource.shape[0]) * 4)
        header += """
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element face """
        header += str(pointCloudSource.shape[0] +
                      pointCloudTarget.shape[0] + pointCloudSource.shape[0])
        header += """
property list uchar int vertex_index
end_header
"""
        f.write(header)

        sourceColor = [0, 255, 0]
        targetColor = [0, 0, 255]
        colorMap = np.random.randint(255, size=pointCloudSource.shape)

        # for pointIndex, point in enumerate(pointCloudSource):
        #     for value in point:
        #         f.write(str(value) + ' ')
        #         continue
        #     color = sourceColor
        #     for value in color:
        #         f.write(str(value) + ' ')
        #         continue
        #     f.write('\n')
        #     continue

        # for pointIndex, point in enumerate(pointCloudTarget):
        #     for value in point:
        #         f.write(str(value) + ' ')
        #         continue
        #     color = targetColor
        #     for value in color:
        #         f.write(str(value) + ' ')
        #         continue
        #     f.write('\n')
        #     continue

        planeSize = 0.1
        for planeType, planes in enumerate([pointCloudSource, pointCloudTarget]):
            for planeIndex, plane in enumerate(planes):
                planeD = np.linalg.norm(plane)
                planeNormal = -plane / planeD

                maxNormalDim = np.argmax(np.abs(plane))
                allDims = [0, 1, 2]
                allDims.remove(maxNormalDim)
                dim_1, dim_2 = allDims
                for delta_1, delta_2 in [(-planeSize, -planeSize), (planeSize, -planeSize), (planeSize, planeSize), (-planeSize, planeSize)]:
                    point = copy.deepcopy(plane)
                    point[dim_1] += delta_1
                    point[dim_2] += delta_2
                    point[maxNormalDim] = (-planeD - planeNormal[dim_1] * point[dim_1] -
                                           planeNormal[dim_2] * point[dim_2]) / planeNormal[maxNormalDim]

                    for value in point:
                        f.write(str(value) + ' ')
                        continue
                    if planeType == 0:
                        color = sourceColor
                    else:
                        color = targetColor
                        pass

                    for value in color:
                        f.write(str(value) + ' ')
                        continue
                    f.write('\n')
                    continue
                continue
            continue

        assignment = np.argmin(np.linalg.norm(pointCloudSource.reshape(-1, 1, 3).repeat(
            pointCloudTarget.shape[0], 1)[:] - pointCloudTarget, 2, 2), 1)

        planeSize = 0.01
        lineColor = [255, 0, 0]
        for planeIndex, planeSource in enumerate(pointCloudSource):
            planeD = np.linalg.norm(planeSource)
            planeNormal = -planeSource / planeD

            maxNormalDim = np.argmax(np.abs(planeSource))
            allDims = [0, 1, 2]
            allDims.remove(maxNormalDim)
            dim_1, dim_2 = allDims
            minNormalDim = np.argmin(np.abs(planeSource))

            for delta in [-planeSize, planeSize]:
                point = copy.deepcopy(planeSource)
                point[minNormalDim] += delta
                point[maxNormalDim] = (-planeD - planeNormal[dim_1] * point[dim_1] -
                                       planeNormal[dim_2] * point[dim_2]) / planeNormal[maxNormalDim]
                for value in point:
                    f.write(str(value) + ' ')
                    continue
                color = lineColor
                for value in color:
                    f.write(str(value) + ' ')
                    continue
                f.write('\n')
                continue

            planeTarget = pointCloudTarget[assignment[planeIndex]]
            planeDTarget = np.linalg.norm(plane)
            planeNormalTarget = -plane / planeD
            planeD = np.linalg.norm(planeTarget)
            planeNormal = -planeTarget / planeD

            for delta in [planeSize, -planeSize]:
                point = copy.deepcopy(planeTarget)
                point[minNormalDim] += delta
                point[maxNormalDim] = (-planeD - planeNormal[dim_1] * point[dim_1] -
                                       planeNormal[dim_2] * point[dim_2]) / planeNormal[maxNormalDim]
                for value in point:
                    f.write(str(value) + ' ')
                    continue
                color = lineColor
                for value in color:
                    f.write(str(value) + ' ')
                    continue
                f.write('\n')
                continue
            continue

        for index in range(pointCloudSource.shape[0] + pointCloudTarget.shape[0] + pointCloudSource.shape[0]):
            planeIndex = index * 4
            f.write('4 ' + str(planeIndex + 0) + ' ' + str(planeIndex + 1) +
                    ' ' + str(planeIndex + 2) + ' ' + str(planeIndex + 3) + '\n')
            continue

        # for pointIndexSource, point in enumerate(pointCloudSource):
    #     pointIndexTarget = assignment[pointIndexSource]
#     f.write(str(pointIndexSource) + ' ' + str(pointIndexTarget + pointCloudSource.shape[0]) + ' ')
        #     color = colorMap[pointIndexSource]
    #     for value in color:
#         f.write(str(value) + ' ')
        #         continue
    #     f.write('\n')
#     continue

        f.close()
        pass
    return


# def evaluatePlanes(planes, filename = None, depths = None, normals = None, invalidMask = None, outputFolder = None, outputIndex = 0, colorMap = None):
#     if filename != None:
#         if 'mlt' not in filename:
#             filename = filename.replace('color', 'mlt')
#             pass
#         normalFilename = filename.replace('mlt', 'norm_camera')
#         normals = np.array(PIL.Image.open(normalFilename)).astype(np.float) / 255 * 2 - 1
#         norm = np.linalg.norm(normals, 2, 2)
#         for c in xrange(3):
#             normals[:, :, c] /= norm
#             continue

#         depthFilename = filename.replace('mlt', 'depth')
#         depths = np.array(PIL.Image.open(depthFilename)).astype(np.float) / 1000
#         # if len(depths.shape) == 3:
#         #     depths = depths.mean(2)
#         #     pass
#         maskFilename = filename.replace('mlt', 'valid')
#         invalidMask = np.array(PIL.Image.open(maskFilename))
#         invalidMask = invalidMask < 128
#         invalidMask += depths > 10
#         pass

#     height = normals.shape[0]
#     width = normals.shape[1]
#     focalLength = 517.97
#     urange = np.arange(width).reshape(1, -1).repeat(height, 0) - width * 0.5
#     vrange = np.arange(height).reshape(-1, 1).repeat(width, 1) - height * 0.5
#     ranges = np.array([urange / focalLength, np.ones(urange.shape), -vrange / focalLength]).transpose([1, 2, 0])

#     X = depths / focalLength * urange
#     Y = depths
#     Z = -depths / focalLength * vrange
#     d = -(normals[:, :, 0] * X + normals[:, :, 1] * Y + normals[:, :, 2] * Z)


#     normalDotThreshold = np.cos(np.deg2rad(30))
#     distanceThreshold = 50000

#     reconstructedNormals = np.zeros(normals.shape)
#     reconstructedDepths = np.zeros(depths.shape)
#     segmentationImage = np.zeros((height, width, 3))
#     distanceMap = np.ones((height, width)) * distanceThreshold
#     occupancyMask = np.zeros((height, width)).astype(np.bool)
#     segmentationTest = np.zeros((height, width))
#     y = 297
#     x = 540
#     for planeIndex, plane in enumerate(planes):
#         planeD = np.linalg.norm(plane)
#         planeNormal = -plane / planeD

#         normalXYZ = np.dot(ranges, planeNormal)
#         normalXYZ = np.reciprocal(normalXYZ)
#         planeY = -normalXYZ * planeD

#         distance = np.abs(planeNormal[0] * X + planeNormal[1] * Y + planeNormal[2] * Z + planeD) / np.abs(np.dot(normals, planeNormal))
#         #distance = np.abs(planeY - depths)

#         mask = (distance < distanceMap) * (planeY > 0) * (np.abs(np.dot(normals, planeNormal)) > normalDotThreshold) * (np.abs(planeY - depths) < 0.5)
#         occupancyMask += mask

#         reconstructedNormals[mask] = planeNormal


#         #if planeNormal[2] > 0.9:
#         #print(planeD)
#         #print(planeNormal)
#         # minDepth = depths.min()
#         # maxDepth = depths.max()
#         # print(depths[300][300])
#         # print(planeY[300][300])
#         # print(depths[350][350])
#         # print(planeY[350][350])
#         # PIL.Image.fromarray((np.maximum(np.minimum((planeY - minDepth) / (maxDepth - minDepth), 1), 0) * 255).astype(np.uint8)).save(outputFolder + '/plane.png')
#         # exit(1)
#         #pass
#         reconstructedDepths[mask] = planeY[mask]
#         if colorMap != None and planeIndex in colorMap:
#             segmentationImage[mask] = colorMap[planeIndex]
#         else:
#             segmentationImage[mask] = np.random.randint(255, size=(3,))
#             pass
#         distanceMap[mask] = distance[mask]
#         segmentationTest[mask] = planeIndex + 1
#         #print((planeIndex, planeY[y][x], distance[y][x], np.abs(np.dot(normals, planeNormal))[y][x]))
#         continue

#     # print(distanceMap.mean())
# # print(distanceMap.max())
#     # print(np.abs(reconstructedDepths - depths)[occupancyMask].max())
# # print(pow(reconstructedDepths - depths, 2)[True - invalidMask].mean())
#     # exit(1)

#     # planeIndex = segmentationTest[y][x]
# # print(normals[y][x])
#     # plane = planes[int(planeIndex)]
# # planeD = np.linalg.norm(plane)
#     # planeNormal = -plane / planeD
# # print((planeNormal, planeD))
#     # print(depths[y][x])
# # print(reconstructedDepths[y][x])
#     # print(segmentationTest[y][x])

#     if outputFolder != None:
#         depths[invalidMask] = 0
#         normals[invalidMask] = 0
#         reconstructedDepths[invalidMask] = 0
#         reconstructedNormals[invalidMask] = 0
#         minDepth = depths.min()
#         maxDepth = depths.max()
#         #print(minDepth)
#         #print(maxDepth)
#         PIL.Image.fromarray(((depths - minDepth) / (maxDepth - minDepth) * 255).astype(np.uint8)).save(outputFolder + '/' + str(outputIndex) + '_depth.png')
#         PIL.Image.fromarray((np.maximum(np.minimum((reconstructedDepths - minDepth) / (maxDepth - minDepth), 1), 0) * 255).astype(np.uint8)).save(outputFolder + '/' + str(outputIndex) + '_depth_reconstructed.png')
#         #PIL.Image.fromarray((np.maximum(np.minimum((reconstructedDepths - depths) / (distanceThreshold), 1), 0) * 255).astype(np.uint8)).save(outputFolder + '/depth_' + str(outputIndex) + '_diff.png')
#         PIL.Image.fromarray(((normals + 1) / 2 * 255).astype(np.uint8)).save(outputFolder + '/' + str(outputIndex) + '_normal_.png')
#         PIL.Image.fromarray(((reconstructedNormals + 1) / 2 * 255).astype(np.uint8)).save(outputFolder + '/' + str(outputIndex) + '_normal_reconstructed.png')
#         PIL.Image.fromarray(segmentationImage.astype(np.uint8)).save(outputFolder + '/' + str(outputIndex) + '_plane_segmentation.png')
#         #depthImage = ((depths - minDepth) / (maxDepth - minDepth) * 255).astype(np.uint8)
#         #PIL.Image.fromarray((invalidMask * 255).astype(np.uint8)).save(outputFolder + '/mask.png')
#         #exit(1)
#     else:
#         occupancy = (occupancyMask > 0.5).astype(np.float32).sum() / (1 - invalidMask).sum()
#         invalidMask += np.invert(occupancyMask)
#         #PIL.Image.fromarray(invalidMask.astype(np.uint8) * 255).save(outputFolder + '/mask.png')
#         reconstructedDepths = np.maximum(np.minimum(reconstructedDepths, 10), 0)
#         depthError = pow(reconstructedDepths - depths, 2)[np.invert(invalidMask)].mean()
#         #depthError = distanceMap.mean()
#         normalError = np.arccos(np.maximum(np.minimum(np.sum(reconstructedNormals * normals, 2), 1), -1))[np.invert(invalidMask)].mean()
#         #normalError = pow(np.linalg.norm(reconstructedNormals - normals, 2, 2), 2)[True - invalidMask].mean()
#         #print((depthError, normalError, occupancy))
#         # print(depths.max())
#         # print(depths.min())
#         # print(reconstructedDepths.max())
#         # print(reconstructedDepths.min())
#         # print(occupancy)
#         # exit(1)

#         #reconstructedDepths[np.invert(occupancyMask)] = depths[np.invert(occupancyMask)]
#         return depthError, normalError, occupancy, segmentationTest, reconstructedDepths, occupancyMask
#     return


# def evaluatePlanesSeparately(planes, filename, outputFolder = None, outputIndex = 0):
#     if 'mlt' not in filename:
#         filename = filename.replace('color', 'mlt')
#         pass
#     colorImage = np.array(PIL.Image.open(filename))
#     normalFilename = filename.replace('mlt', 'norm_camera')
#     normals = np.array(PIL.Image.open(normalFilename)).astype(np.float) / 255 * 2 - 1
#     height = normals.shape[0]
#     width = normals.shape[1]
#     norm = np.linalg.norm(normals, 2, 2)
#     for c in xrange(3):
#         normals[:, :, c] /= norm
#         continue


#     depthFilename = filename.replace('mlt', 'depth')
#     depths = np.array(PIL.Image.open(depthFilename)).astype(np.float) / 1000
#     # if len(depths.shape) == 3:
#     #     depths = depths.mean(2)
#     #     pass

#     focalLength = 517.97
#     urange = np.arange(width).reshape(1, -1).repeat(height, 0) - width * 0.5
#     vrange = np.arange(height).reshape(-1, 1).repeat(width, 1) - height * 0.5
#     ranges = np.array([urange / focalLength, np.ones(urange.shape), -vrange / focalLength]).transpose([1, 2, 0])
#     X = depths / focalLength * urange
#     Y = depths
#     Z = -depths / focalLength * vrange
#     d = -(normals[:, :, 0] * X + normals[:, :, 1] * Y + normals[:, :, 2] * Z)


#     maskFilename = filename.replace('mlt', 'valid')
#     invalidMask = np.array(PIL.Image.open(maskFilename))
#     # if len(invalidMask.shape) == 3:
#     #     invalidMask = invalidMask.mean(2)
#     #     pass
#     invalidMask = invalidMask < 128
#     invalidMask += depths > 10


#     normalDotThreshold = np.cos(np.deg2rad(15))
#     distanceThreshold = 0.15
#     colorPalette = ColorPalette(len(planes))
#     for planeIndex, plane in enumerate(planes):
#         planeD = np.linalg.norm(plane)
#         planeNormal = -plane / planeD

#         distance = np.abs(planeNormal[0] * X + planeNormal[1] * Y + planeNormal[2] * Z + planeD)

#         normalXYZ = np.dot(ranges, planeNormal)
#         normalXYZ = np.reciprocal(normalXYZ)
#         planeY = -normalXYZ * planeD

#         mask = (planeY > 0) * (np.abs(np.dot(normals, planeNormal)) > normalDotThreshold) * (distance < distanceThreshold)

#         maxDepth = 10
#         minDepth = 0
#         #PIL.Image.fromarray((np.minimum(np.maximum((planeY - minDepth) / (maxDepth - minDepth), 0), 1) * 255).astype(np.uint8)).save(outputFolder + '/plane_depth_' + str(planeIndex) + '.png')
#         #PIL.Image.fromarray(((planeNormal.reshape(1, 1, 3).repeat(height, 0).repeat(width, 1) + 1) / 2 * 255).astype(np.uint8)).save(outputFolder + '/plane_normal_' + str(planeIndex) + '.png')
#         planeImage = colorImage * 0.3
#         planeImage[mask] += colorPalette.getColor(planeIndex) * 0.7
#         PIL.Image.fromarray(planeImage.astype(np.uint8)).save(outputFolder + '/plane_mask_' + str(planeIndex) + '_' + str(outputIndex) + '.png')
#         #PIL.Image.fromarray(mask.astype(np.uint8) * 255).save(outputFolder + '/mask_' + str(planeIndex) + '.png')
#         continue
#     return

def residual2Planes(residualPlanes, predefinedPlanes):
    numClusters = predefinedPlanes.shape[0]
    planes = []
    for residualPlane in residualPlanes:
        gridIndex = int(residualPlane[0]) / numClusters
        planeIndex = int(residualPlane[0]) % numClusters
        planes.append(predefinedPlanes[planeIndex] + residualPlane[1:])
        continue
    return planes


def residual2PlanesGlobal(residualPlanes, predefinedPlanes):
    numClusters = predefinedPlanes.shape[0]
    planes = []
    for residualPlane in residualPlanes:
        planeIndex = int(residualPlane[0])
        planes.append(predefinedPlanes[planeIndex] + residualPlane[1:])
        continue
    return planes


def getPlaneInfo(planes):
    imageWidth = 640
    imageHeight = 480
    focalLength = 517.97
    urange = np.arange(imageWidth).reshape(
        1, -1).repeat(imageHeight, 0) - imageWidth * 0.5
    vrange = np.arange(imageHeight).reshape(-1,
                                            1).repeat(imageWidth, 1) - imageHeight * 0.5
    ranges = np.array([urange / focalLength, np.ones(urange.shape), -
                       vrange / focalLength]).transpose([1, 2, 0])

    planeDepths = PlaneDepthLayer(planes, ranges)
    planeNormals = PlaneNormalLayer(planes, ranges)
    return planeDepths, planeNormals


def getProbability(image, segmentation):
    width = image.shape[1]
    height = image.shape[0]
    numPlanes = segmentation.shape[0]
    probabilities = np.exp(segmentation)
    probabilities = probabilities / probabilities.sum(0)
    # The input should be the negative of the logarithm of probability values
    # Look up the definition of the softmax_to_unary for more information
    unary = unary_from_softmax(probabilities)

    # The inputs should be C-continious -- we are using Cython wrapper
    unary = np.ascontiguousarray(unary)

    d = dcrf.DenseCRF(height * width, numPlanes)

    d.setUnaryEnergy(unary)

    # This potential penalizes small pieces of segmentation that are
    # spatially isolated -- enforces more spatially consistent segmentations
    # feats = create_pairwise_gaussian(sdims=(10, 10), shape=(height, width))
    # d.addPairwiseEnergy(feats, compat=300,
    #                                         kernel=dcrf.DIAG_KERNEL,
    #                                         normalization=dcrf.NORMALIZE_SYMMETRIC)

    # This creates the color-dependent features --
    # because the segmentation that we get from CNN are too coarse
    # and we can use local color features to refine them

    feats = create_pairwise_bilateral(sdims=(50, 50), schan=(20, 20, 20),
                                      img=image, chdim=2)
    d.addPairwiseEnergy(feats, compat=10,
                        kernel=dcrf.DIAG_KERNEL,
                        normalization=dcrf.NORMALIZE_SYMMETRIC)

    Q = d.inference(50)

    inds = np.argmax(Q, axis=0).reshape((height, width))
    probabilities = np.zeros((height * width, numPlanes))
    probabilities[np.arange(height * width), inds.reshape(-1)] = 1
    probabilities = probabilities.reshape([height, width, -1])
    # print(res.shape)
    return probabilities


def getProbabilityMax(segmentation):
    width = segmentation.shape[2]
    height = segmentation.shape[1]
    numPlanes = segmentation.shape[0]
    inds = np.argmax(segmentation.reshape([-1, height * width]), axis=0)
    probabilities = np.zeros((height * width, numPlanes))
    probabilities[np.arange(height * width), inds] = 1
    probabilities = probabilities.reshape([height, width, -1])
    return probabilities


def evaluateNormal(predNormal, gtSegmentations, numPlanes):
    numImages = predNormal.shape[0]
    normal = np.linalg.norm(predNormal, axis=-1)
    errors = []
    for imageIndex in range(numImages):
        var = 0
        count = 0

        invalidNormalMask = np.linalg.norm(
            predNormal[imageIndex], axis=-1) > 1 - 1e-4
        for planeIndex in range(numPlanes[imageIndex]):
            #mask = gtSegmentations[imageIndex, :, :, planeIndex].astype(np.bool)
            mask = gtSegmentations[imageIndex] == planeIndex
            mask = cv2.erode(mask.astype(np.float32), np.ones((5, 5))) > 0.5
            mask = np.logical_and(mask, invalidNormalMask)
            if mask.sum() == 0:
                continue
            normals = predNormal[imageIndex][mask]
            averageNormal = np.mean(normals, axis=0, keepdims=True)
            averageNormal /= np.linalg.norm(averageNormal)
            degrees = np.rad2deg(np.arccos(np.minimum(
                np.sum(normals * averageNormal, axis=-1), 1)))
            #degrees = np.rad2deg(np.arccos(np.sum(normals * averageNormal, axis=-1)))
            degrees = np.minimum(degrees, 180 - degrees)
            var += degrees.sum()
            count += degrees.shape[0]
            #var += degrees.mean()
            #totalNumPlanes += 1
            #print(np.sum(normals * averageNormal, axis=-1))
            print((planeIndex, degrees.sum() / degrees.shape[0]))
            cv2.imwrite('test/mask_' + str(planeIndex) +
                        '.png', drawMaskImage(mask))
            # print(normals)
            # if planeIndex == 4:
            #     for normal in normals:
            #         print(normal)
            #         continue
            #     print(normals.mean(0))
            #     exit(1)
            # print(degrees)
            # print(planeIndex, averageNormal, degrees.mean())
            # print(normals[degrees > 90])

            continue
        var /= count
        errors.append(var)
        #print(var / totalNumPlanes)
        # exit(1)
        continue
    var = np.array(errors).mean()
    print(var)
    return var


def evaluateDepths(predDepths, gtDepths, validMasks, planeMasks=True, printInfo=True):
    masks = np.logical_and(np.logical_and(
        validMasks, planeMasks), gtDepths > 1e-4)

    numPixels = float(masks.sum())

    rmse = np.sqrt((pow(predDepths - gtDepths, 2) * masks).sum() / numPixels)
    rmse_log = np.sqrt(
        (pow(np.log(predDepths) - np.log(gtDepths), 2) * masks).sum() / numPixels)
    log10 = (np.abs(np.log10(np.maximum(predDepths, 1e-4)) -
                    np.log10(np.maximum(gtDepths, 1e-4))) * masks).sum() / numPixels
    rel = (np.abs(predDepths - gtDepths) /
           np.maximum(gtDepths, 1e-4) * masks).sum() / numPixels
    rel_sqr = (pow(predDepths - gtDepths, 2) /
               np.maximum(gtDepths, 1e-4) * masks).sum() / numPixels
    deltas = np.maximum(predDepths / np.maximum(gtDepths, 1e-4), gtDepths /
                        np.maximum(predDepths, 1e-4)) + (1 - masks.astype(np.float32)) * 10000
    accuracy_1 = (deltas < 1.25).sum() / numPixels
    accuracy_2 = (deltas < pow(1.25, 2)).sum() / numPixels
    accuracy_3 = (deltas < pow(1.25, 3)).sum() / numPixels
    recall = float(masks.sum()) / validMasks.sum()
    #print((rms, recall))
    if printInfo:
        print(('evaluate', rel, rel_sqr, log10, rmse, rmse_log,
               accuracy_1, accuracy_2, accuracy_3, recall))
        pass
    return rel, rel_sqr, log10, rmse, rmse_log, accuracy_1, accuracy_2, accuracy_3, recall
    # return rel, log10, rms, accuracy_1, accuracy_2, accuracy_3, recall


def drawDepthImage(depth):
    # return cv2.applyColorMap(np.clip(depth / 10 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_JET)
    return 255 - np.clip(depth / 5 * 255, 0, 255).astype(np.uint8)


def drawDepthImageOverlay(image, depth):
    # return cv2.applyColorMap(np.clip(depth / 10 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_JET)
    depth = np.clip(depth / min(np.max(depth), 10)
                    * 255, 0, 255).astype(np.uint8)
    imageOverlay = np.stack([image[:, :, 1], depth, image[:, :, 2]], axis=2)
    return imageOverlay


def drawNormalImage(normal):
    return ((normal + 1) / 2 * 255).astype(np.uint8)


def drawSegmentationImage(segmentations, randomColor=None, numColors=22, blackIndex=-1):
    if segmentations.ndim == 2:
        numColors = max(numColors, segmentations.max() + 2, blackIndex + 1)
    else:
        numColors = max(numColors, segmentations.shape[2] + 2, blackIndex + 1)
        pass
    randomColor = ColorPalette(numColors).getColorMap()
    if blackIndex >= 0:
        randomColor[blackIndex] = 0
        pass
    width = segmentations.shape[1]
    height = segmentations.shape[0]
    if segmentations.ndim == 3:
        #segmentation = (np.argmax(segmentations, 2) + 1) * (np.max(segmentations, 2) > 0.5)
        segmentation = np.argmax(segmentations, 2)
    else:
        segmentation = segmentations
        pass
    segmentation = segmentation.astype(np.int)
    return randomColor[segmentation.reshape(-1)].reshape((height, width, 3))


def drawMaskImage(mask):
    return (np.clip(mask * 255, 0, 255)).astype(np.uint8)


def drawDiffImage(values_1, values_2, threshold):
    # return cv2.applyColorMap(np.clip(np.abs(values_1 - values_2) / threshold * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_JET)
    return np.clip(np.abs(values_1 - values_2) / threshold * 255, 0, 255).astype(np.uint8)


def getSuperpixels(depth, normal, width, height, numPlanes=50, numGlobalPlanes=10):
    depth = np.expand_dims(depth, -1)

    urange = (np.arange(width, dtype=np.float32) /
              (width + 1) - 0.5) / focalLength * 641
    urange = np.tile(np.reshape(urange, [1, -1]), [height, 1])
    vrange = (np.arange(height, dtype=np.float32) /
              (height + 1) - 0.5) / focalLength * 481
    vrange = np.tile(np.reshape(vrange, [-1, 1]), [1, width])

    ranges = np.stack([urange, np.ones([height, width]), -vrange], axis=2)
    #ranges = np.expand_dims(ranges, 0)

    planeImage = np.sum(normal * ranges, axis=2,
                        keepdims=True) * depth * normal
    planeImage = planeImage / 10 * 1000

    superpixels = segmentation.slic(planeImage, compactness=30, n_segments=400)
    g = graph.rag_mean_color(planeImage, superpixels, mode='similarity')
    planeSegmentation = graph.cut_normalized(superpixels, g)
    return planeSegmentation, superpixels


def calcPlaneDepths(planes, width, height, info):
    urange = np.arange(width, dtype=np.float32).reshape(
        1, -1).repeat(height, 0) / (width + 1) * (info[16] + 1) - info[2]
    vrange = np.arange(height, dtype=np.float32).reshape(-1,
                                                         1).repeat(width, 1) / (height + 1) * (info[17] + 1) - info[6]
    ranges = np.array([urange / info[0], np.ones(urange.shape), -
                       vrange / info[5]]).transpose([1, 2, 0])
    planeDepths = PlaneDepthLayer(planes, ranges)
    return planeDepths


def calcPlaneNormals(planes, width, height):
    planeNormals = -planes / \
        np.maximum(np.linalg.norm(planes, axis=-1, keepdims=True), 1e-4)
    return np.tile(planeNormals.reshape([1, 1, -1, 3]), [height, width, 1, 1])


def writePLYFile(folder, index, image, depth, segmentation, planes, info):
    imageFilename = str(index) + '_model_texture.png'
    cv2.imwrite(folder + '/' + imageFilename, image)

    width = image.shape[1]
    height = image.shape[0]

    numPlanes = planes.shape[0]

    camera = getCameraFromInfo(info)

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    XYZ = np.stack([X, Y, Z], axis=2)

    #focalLength = 517.97

    faces = []
    #minDepthDiff = 0.15
    #maxDepthDiff = 0.3
    #occlusionBoundary = boundaries[:, :, 1]
    betweenRegionThreshold = 0.1
    nonPlanarRegionThreshold = 0.02

    planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    planeNormals = -planes / np.maximum(planesD, 1e-4)

    croppingRatio = -0.05
    dotThreshold = np.cos(np.deg2rad(30))

    for y in range(height - 1):
        for x in range(width - 1):
            if y < height * croppingRatio or y > height * (1 - croppingRatio) or x < width * croppingRatio or x > width * (1 - croppingRatio):
                continue

            segmentIndex = segmentation[y][x]
            if segmentIndex == -1:
                continue

            point = XYZ[y][x]
            #neighborPixels = []
            validNeighborPixels = []
            for neighborPixel in [(x, y + 1), (x + 1, y), (x + 1, y + 1)]:
                neighborSegmentIndex = segmentation[neighborPixel[1]
                                                    ][neighborPixel[0]]
                if neighborSegmentIndex == segmentIndex:
                    if segmentIndex < numPlanes:
                        validNeighborPixels.append(neighborPixel)
                    else:
                        neighborPoint = XYZ[neighborPixel[1]][neighborPixel[0]]
                        if np.linalg.norm(neighborPoint - point) < nonPlanarRegionThreshold:
                            validNeighborPixels.append(neighborPixel)
                            pass
                        pass
                else:
                    neighborPoint = XYZ[neighborPixel[1]][neighborPixel[0]]
                    if segmentIndex < numPlanes and neighborSegmentIndex < numPlanes:
                        if (abs(np.dot(planeNormals[segmentIndex], neighborPoint) + planesD[segmentIndex]) < betweenRegionThreshold or abs(np.dot(planeNormals[neighborSegmentIndex], point) + planesD[neighborSegmentIndex]) < betweenRegionThreshold) and np.abs(np.dot(planeNormals[segmentIndex], planeNormals[neighborSegmentIndex])) < dotThreshold:
                            validNeighborPixels.append(neighborPixel)
                            pass
                    else:
                        if np.linalg.norm(neighborPoint - point) < betweenRegionThreshold:
                            validNeighborPixels.append(neighborPixel)
                            pass
                        pass
                    pass
                continue
            if len(validNeighborPixels) == 3:
                faces.append((x, y, x + 1, y + 1, x + 1, y))
                faces.append((x, y, x, y + 1, x + 1, y + 1))
            elif len(validNeighborPixels) == 2 and segmentIndex < numPlanes:
                faces.append((x, y, validNeighborPixels[0][0], validNeighborPixels[0]
                              [1], validNeighborPixels[1][0], validNeighborPixels[1][1]))
                pass
            continue
        continue

    with open(folder + '/' + str(index) + '_model.ply', 'w') as f:
        header = """ply
format ascii 1.0
comment VCGLIB generated
comment TextureFile """
        header += imageFilename
        header += """
element vertex """
        header += str(width * height)
        header += """
property float x
property float y
property float z
element face """
        header += str(len(faces))
        header += """
property list uchar int vertex_indices
property list uchar float texcoord
end_header
"""
        f.write(header)
        for y in range(height):
            for x in range(width):
                segmentIndex = segmentation[y][x]
                if segmentIndex == -1:
                    f.write("0.0 0.0 0.0\n")
                    continue
                point = XYZ[y][x]
                X = point[0]
                Y = point[1]
                Z = point[2]
                #Y = depth[y][x]
                #X = Y / focalLength * (x - width / 2) / width * 640
                #Z = -Y / focalLength * (y - height / 2) / height * 480
                f.write(str(X) + ' ' + str(Z) + ' ' + str(-Y) + '\n')
                continue
            continue

        for face in faces:
            f.write('3 ')
            for c in range(3):
                f.write(str(face[c * 2 + 1] * width + face[c * 2]) + ' ')
                continue
            f.write('6 ')
            for c in range(3):
                f.write(str(float(face[c * 2]) / width) + ' ' +
                        str(1 - float(face[c * 2 + 1]) / height) + ' ')
                continue
            f.write('\n')
            continue
        f.close()
        pass
    return


def writePLYFileDepth(folder, index, image, depth, segmentation, planes, info):
    imageFilename = str(index) + '_segmentation_pred_blended_0.png'
    #cv2.imwrite(folder + '/' + imageFilename, image)

    numPlanes = planes.shape[0]

    camera = getCameraFromInfo(info)

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    XYZ = np.stack([X, Y, Z], axis=2).reshape(-1, 3)

    #focalLength = 517.97
    width = image.shape[1]
    height = image.shape[0]

    faces = []
    minDepthDiff = 0.15
    maxDepthDiff = 0.3
    #occlusionBoundary = boundaries[:, :, 1]

    for y in range(height - 1):
        for x in range(width - 1):
            segmentIndex = segmentation[y][x]
            if segmentIndex == -1:
                continue
            # if segmentIndex == 0:
            # continue
            #depths = [depth[y][x], depth[y + 1][x], depth[y + 1][x + 1]]
            # if segmentIndex >= 0 or (max([occlusionBoundary[y][x], occlusionBoundary[y + 1][x], occlusionBoundary[y + 1][x + 1]]) < 0.5 and (max(depths) - min(depths)) < maxDepthDiff):
            #     if segmentation[y + 1][x] == segmentIndex and segmentation[y + 1][x + 1] == segmentIndex:
            #         if min(depths) > 0 and max(depths) < 10:
            #             faces.append((x, y, x, y + 1, x + 1, y + 1))
            #             pass
            #         pass
            #     elif max(depths) - min(depths) < minDepthDiff:
            #         faces.append((x, y, x, y + 1, x + 1, y + 1))
            #         pass
            #     pass

            if segmentation[y + 1][x] == segmentIndex and segmentation[y + 1][x + 1] == segmentIndex and min(depths) > 0 and max(depths) < 10:
                faces.append((x, y, x, y + 1, x + 1, y + 1))
                pass

            depths = [depth[y][x], depth[y][x + 1], depth[y + 1][x + 1]]
            # if segmentIndex > 0 or (max([occlusionBoundary[y][x], occlusionBoundary[y][x + 1], occlusionBoundary[y + 1][x + 1]]) < 0.5 and (max(depths) - min(depths)) < maxDepthDiff):
            #     if segmentation[y][x + 1] == segmentIndex and segmentation[y + 1][x + 1] == segmentIndex:
            #         if min(depths) > 0 and max(depths) < 10:
            #             faces.append((x, y, x + 1, y + 1, x + 1, y))
            #             pass
            #         pass
            #     elif max(depths) - min(depths) < minDepthDiff:
            #         faces.append((x, y, x + 1, y + 1, x + 1, y))
            #         pass
            #     pass
            if segmentation[y][x + 1] == segmentIndex and segmentation[y + 1][x + 1] == segmentIndex and min(depths) > 0 and max(depths) < 10:
                faces.append((x, y, x + 1, y + 1, x + 1, y))
                pass
            continue
        continue

    # print(len(faces))
    print(folder)
    with open(folder + '/' + str(index) + '_model.ply', 'w') as f:
        header = """ply
format ascii 1.0
comment VCGLIB generated
comment TextureFile """
        header += imageFilename
        header += """
element vertex """
        header += str(width * height)
        header += """
property float x
property float y
property float z
element face """
        header += str(len(faces))
        header += """
property list uchar int vertex_indices
property list uchar float texcoord
end_header
"""
        f.write(header)
        for y in range(height):
            for x in range(width):
                segmentIndex = segmentation[y][x]
                if segmentIndex == -1:
                    f.write("0.0 0.0 0.0\n")
                    continue
                Y = depth[y][x]
                X = Y / focalLength * (x - width / 2) / width * 640
                Z = -Y / focalLength * (y - height / 2) / height * 480
                f.write(str(X) + ' ' + str(Z) + ' ' + str(-Y) + '\n')
                continue
            continue

        for face in faces:
            f.write('3 ')
            for c in range(3):
                f.write(str(face[c * 2 + 1] * width + face[c * 2]) + ' ')
                continue
            f.write('6 ')
            for c in range(3):
                f.write(str(float(face[c * 2]) / width) + ' ' +
                        str(1 - float(face[c * 2 + 1]) / height) + ' ')
                continue
            f.write('\n')
            continue
        f.close()
        pass
        return


def writeHTML(folder, numImages):
    from html import HTML

    h = HTML('html')
    h.p('Results')
    h.br()
    #suffixes = ['', '_crf_1']
    #folders = ['test_all_resnet_v2' + suffix + '/' for suffix in suffixes]
    for index in range(numImages):
        t = h.table(border='1')
        r_inp = t.tr()
        r_inp.td('input')
        r_inp.td().img(src=str(index) + '_image.png')
        r_inp.td().img(src='one.png')
        r_inp.td().img(src='one.png')
        # r_inp.td().img(src='one.png')
        r_inp.td().img(src=str(index) + '_model.png')

        r_gt = t.tr()
        r_gt.td('gt')
        r_gt.td().img(src=str(index) + '_segmentation_gt.png')
        r_gt.td().img(src=str(index) + '_depth.png')
        r_gt.td().img(src='one.png')
        r_gt.td().img(src=str(index) + '_normal.png')

        #r_gt.td().img(src=folders[0] + str(index) + '_depth_gt.png')
        #r_gt.td().img(src=folders[0] + '_depth_gt_diff.png')
        #r_gt.td().img(src=folders[0] + str(index) + '_normal_gt.png')

        r_pred = t.tr()
        r_pred.td('pred')
        r_pred.td().img(src=str(index) + '_segmentation_pred.png')
        r_pred.td().img(src=str(index) + '_depth_pred.png')
        r_pred.td().img(src=str(index) + '_depth_pred_diff.png')
        r_pred.td().img(src=str(index) + '_normal_pred.png')

        h.br()
        continue

    html_file = open(folder + '/index.html', 'w')
    html_file.write(str(h))
    html_file.close()
    return


def writeHTMLRGBD(filename, numImages=10):
    from html import HTML

    # 0.227 0.194 0.163 0.157 0.100
    # 0.196 0.150 0.143 0.488 0.082
    h = HTML('html')
    h.p('Results')
    h.br()
    path = ''
    folders = ['pred', 'local_02', 'local_05',
               'local_07', 'local_10', 'local_12']
    second_folders = ['pred_local_02', 'pred_local_05',
                      'pred_local_07', 'pred_local_10', 'pred_local_12']
    for index in range(numImages):
        firstFolder = path + folders[0]
        t = h.table(border='1')
        r_inp = t.tr()
        r_inp.td('input')
        r_inp.td().img(src=firstFolder + '/' + str(index) + '_image.png')
        r_inp.td().img(src=firstFolder + '/' + str(index) + '_depth.png')

        r = t.tr()
        r.td('PlaneNet prediction')
        r.td().img(src=firstFolder + '/' + str(index) + '_segmentation_pred.png')
        r.td().img(src=firstFolder + '/' + str(index) + '_depth_pred.png')

        r = t.tr()
        r.td('segmentation')
        for folder in folders[1:6]:
            r.td().img(src=folder + '/' + str(index) + '_segmentation_pred.png')
            continue

        r = t.tr()
        r.td('depth')
        for folder in folders[1:6]:
            folder = path + folder
            r.td().img(src=folder + '/' + str(index) + '_depth_pred.png')
            continue

        r = t.tr()
        r.td('pixelwise prediction')
        r.td().img(src=path +
                   second_folders[0] + '/' + str(index) + '_depth.png')

        r = t.tr()
        r.td('segmentation')
        for folder in second_folders[0:5]:
            r.td().img(src=folder + '/' + str(index) + '_segmentation_pred.png')
            continue

        r = t.tr()
        r.td('depth')
        for folder in second_folders[0:5]:
            folder = path + folder
            r.td().img(src=folder + '/' + str(index) + '_depth_pred.png')
            continue

        h.br()
        continue

    html_file = open(filename, 'w')
    html_file.write(str(h))
    html_file.close()
    return


def writeHTMLPlane(filename, numImages=10):
    from html import HTML

    # 0.227 0.194 0.163 0.157 0.100
    # 0.196 0.150 0.143 0.488 0.082
    h = HTML('html')
    h.p('Results')
    h.br()
    path = ''
    folders = ['PlaneNet_hybrid', 'PlaneNet', 'GT_RANSAC', 'pixelwise_RANSAC']
    for index in range(numImages):
        firstFolder = path + folders[0]
        t = h.table(border='1')
        r_inp = t.tr()
        r_inp.td('input')
        r_inp.td().img(src=firstFolder + '/' + str(index) + '_image.png')
        r_inp.td().img(src=firstFolder + '/' + str(index) + '_depth.png')

        # r = t.tr()
        # r.td('PlaneNet prediction')
        # r.td().img(src=firstFolder + '/' + str(index) + '_segmentation_pred.png')
        # r.td().img(src=firstFolder + '/' + str(index) + '_depth_pred.png')

        r = t.tr()
        r.td('segmentation')
        for folder in folders[0:6]:
            r.td().img(src=folder + '/' + str(index) + '_segmentation_pred.png')
            continue

        r = t.tr()
        r.td('depth')
        for folder in folders[0:6]:
            folder = path + folder
            r.td().img(src=folder + '/' + str(index) + '_depth_pred.png')
            continue

        h.br()
        continue

    html_file = open(filename, 'w')
    html_file.write(str(h))
    html_file.close()
    return


def getNYURGBDCamera():
    camera = {}
    camera['fx'] = 5.1885790117450188e+02
    camera['fy'] = 5.1946961112127485e+02
    camera['cx'] = 3.2558244941119034e+02 - 40
    camera['cy'] = 2.5373616633400465e+02 - 44
    camera['width'] = 561
    camera['height'] = 427
    camera['depth_shift'] = 1000
    return camera


def getSUNCGCamera():
    camera = {}
    camera['fx'] = 517.97
    camera['fy'] = 517.97
    camera['cx'] = 320
    camera['cy'] = 240
    camera['width'] = 640
    camera['height'] = 480
    camera['depth_shift'] = 1000
    return camera


def get3DCamera():
    camera = {}
    camera['fx'] = 1075
    camera['fy'] = 1075
    camera['cx'] = 637
    camera['cy'] = 508
    camera['width'] = 1280
    camera['height'] = 1024
    camera['depth_shift'] = 4000
    return camera


def getCameraFromInfo(info):
    camera = {}
    camera['fx'] = info[0]
    camera['fy'] = info[5]
    camera['cx'] = info[2]
    camera['cy'] = info[6]
    camera['width'] = info[16]
    camera['height'] = info[17]
    camera['depth_shift'] = info[18]
    return camera


def fitPlane(points):
    if points.shape[0] == points.shape[1]:
        return np.linalg.solve(points, np.ones(points.shape[0]))
    else:
        return np.linalg.lstsq(points, np.ones(points.shape[0]))[0]


def fitPlanes(depth, info, numPlanes=50, planeAreaThreshold=3*4, numIterations=100, distanceThreshold=0.05, local=-1):
    camera = getCameraFromInfo(info)
    width = depth.shape[1]
    height = depth.shape[0]

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    # print(depth[:10, :10])
    # print(X[:10, :10])
    # print(Z[:10, :10])
    # print(urange[:10, :10])
    # print(vrange[:10, :10])
    # exit(1)
    XYZ = np.stack([X, Y, Z], axis=2).reshape(-1, 3)
    XYZ = XYZ[depth.reshape(-1) != 0]
    planes = []
    planePointsArray = []
    for planeIndex in range(numPlanes):
        maxNumInliers = planeAreaThreshold
        for iteration in range(numIterations):
            if local > 0:
                sampledPoint = XYZ[np.random.randint(XYZ.shape[0], size=(1))]
                sampledPoints = XYZ[np.linalg.norm(
                    XYZ - sampledPoint, 2, 1) < local]
                if sampledPoints.shape[0] < 3:
                    continue
                elif sampledPoints.shape[0] > 3:
                    sampledPoints = sampledPoints[np.random.choice(
                        np.arange(sampledPoints.shape[0]), size=(3))]
                    pass
            else:
                sampledPoints = XYZ[np.random.choice(
                    np.arange(XYZ.shape[0]), size=(3))]
                pass

            try:
                plane = fitPlane(sampledPoints)
                pass
            except:
                continue
            diff = np.abs(np.matmul(XYZ, plane) -
                          np.ones(XYZ.shape[0])) / np.linalg.norm(plane)
            numInliers = np.sum(diff < distanceThreshold)
            if numInliers > maxNumInliers:
                maxNumInliers = numInliers
                bestPlane = plane
                pass
            continue
        if maxNumInliers == planeAreaThreshold:
            break
        planes.append(bestPlane)

        diff = np.abs(np.matmul(XYZ, bestPlane) -
                      np.ones(XYZ.shape[0])) / np.linalg.norm(bestPlane)
        inlierIndices = diff < distanceThreshold
        inliersPoints = XYZ[inlierIndices]
        planePointsArray.append(inliersPoints)
        XYZ = XYZ[np.logical_not(inlierIndices)]
        if XYZ.shape[0] < planeAreaThreshold:
            break
        continue

    planes = np.array(planes)
    if len(planes.shape) == 0:
        planes = np.zeros((numPlanes, 3))
        pass
    if len(planes.shape) == 1:
        if planes.shape[0] == 3:
            planes = np.expand_dims(planes, 0)
        else:
            planes = np.zeros((numPlanes, 3))
            pass
        pass

    planeSegmentation = np.ones(depth.shape) * numPlanes
    for planeIndex, planePoints in enumerate(planePointsArray):
        planeDepth = planePoints[:, 1]
        u = np.round((planePoints[:, 0] / planeDepth * camera['fx'] +
                      camera['cx']) / camera['width'] * width).astype(np.int32)
        v = np.round((-planePoints[:, 2] / planeDepth * camera['fy'] +
                      camera['cy']) / camera['height'] * height).astype(np.int32)
        planeSegmentation[v, u] = planeIndex
        continue

    planesD = 1 / np.linalg.norm(planes, 2, axis=1, keepdims=True)
    planes *= pow(planesD, 2)

    if planes.shape[0] < numPlanes:
        # print(planes.shape)
        planes = np.concatenate(
            [planes, np.zeros((numPlanes - planes.shape[0], 3))], axis=0)
        pass

    planeDepths = calcPlaneDepths(planes, width, height, info)

    allDepths = np.concatenate(
        [planeDepths, np.zeros((height, width, 1))], axis=2)
    depthPred = allDepths.reshape(-1, numPlanes + 1)[np.arange(
        width * height), planeSegmentation.astype(np.int32).reshape(-1)].reshape(height, width)

    return planes, planeSegmentation, depthPred


def fitPlanesSegmentation(depth, segmentation, info, numPlanes=50, numPlanesPerSegment=3, planeAreaThreshold=3*4, numIterations=100, distanceThreshold=0.05, local=-1):

    camera = getCameraFromInfo(info)
    width = depth.shape[1]
    height = depth.shape[0]

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    allXYZ = np.stack([X, Y, Z], axis=2).reshape(-1, 3)

    planes = []
    planePointIndices = []

    for segmentIndex in range(segmentation.max()):
        segmentMask = np.logical_and(segmentation == segmentIndex, depth != 0)
        XYZ = allXYZ[segmentMask.reshape(-1)]
        if XYZ.shape[0] < planeAreaThreshold:
            continue
        for planeIndex in range(numPlanesPerSegment):
            maxNumInliers = planeAreaThreshold
            for iteration in range(numIterations):
                if local > 0:
                    sampledPoint = XYZ[np.random.randint(
                        XYZ.shape[0], size=(1))]
                    sampledPoints = XYZ[np.linalg.norm(
                        XYZ - sampledPoint, 2, 1) < local]

                    if sampledPoints.shape[0] < 3:
                        continue
                    elif sampledPoints.shape[0] > 3:
                        sampledPoints = sampledPoints[np.random.choice(
                            np.arange(sampledPoints.shape[0]), size=(3))]
                        pass
                else:
                    sampledPoints = XYZ[np.random.choice(
                        np.arange(XYZ.shape[0]), size=(3))]
                    pass

                try:
                    plane = fitPlane(sampledPoints)
                    pass
                except:
                    continue
                diff = np.abs(np.matmul(XYZ, plane) -
                              np.ones(XYZ.shape[0])) / np.linalg.norm(plane)
                numInliers = np.sum(diff < distanceThreshold)
                if numInliers > maxNumInliers:
                    maxNumInliers = numInliers
                    bestPlane = plane
                    pass
                continue
            if maxNumInliers == planeAreaThreshold:
                break
            planes.append(bestPlane)

            diff = np.abs(np.matmul(XYZ, bestPlane) -
                          np.ones(XYZ.shape[0])) / np.linalg.norm(bestPlane)
            inlierIndices = diff < distanceThreshold
            inliersPoints = XYZ[inlierIndices]
            planePointIndices.append(inliersPoints)
            XYZ = XYZ[np.logical_not(inlierIndices)]
            if XYZ.shape[0] < planeAreaThreshold:
                break
            continue
        continue

    if len(planes) > numPlanes:
        planeList = list(zip(planes, planePointIndices))
        planeList = sorted(planeList, key=lambda x: -len(x[1]))
        planeList = planeList[:numPlanes]
        planes, planePointIndices = list(zip(*planeList))
        pass

    planeSegmentation = np.ones(depth.shape) * numPlanes
    for planeIndex, planePoints in enumerate(planePointIndices):
        planeDepth = planePoints[:, 1]
        u = np.round((planePoints[:, 0] / planeDepth * camera['fx'] +
                      camera['cx']) / camera['width'] * width).astype(np.int32)
        v = np.round((-planePoints[:, 2] / planeDepth * camera['fy'] +
                      camera['cy']) / camera['height'] * height).astype(np.int32)
        planeSegmentation[v, u] = planeIndex
        continue

    planes = np.array(planes)
    planesD = 1 / np.linalg.norm(planes, 2, 1, keepdims=True)
    planes *= pow(planesD, 2)
    if planes.shape[0] < numPlanes:
        planes = np.concatenate(
            [planes, np.zeros((numPlanes - planes.shape[0], 3))], axis=0)
        pass

    planeDepths = calcPlaneDepths(planes, width, height, info)

    allDepths = np.concatenate(
        [planeDepths, np.zeros((height, width, 1))], axis=2)
    depthPred = allDepths.reshape([height * width, numPlanes + 1])[np.arange(
        width * height), planeSegmentation.astype(np.int32).reshape(-1)].reshape(height, width)

    return planes, planeSegmentation, depthPred


def fitPlanesNYU(image, depth, normal, semantics, info, numOutputPlanes=20, local=-1, parameters={}):
    camera = getCameraFromInfo(info)
    width = depth.shape[1]
    height = depth.shape[0]

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    # print(depth[:10, :10])
    # print(X[:10, :10])
    # print(Z[:10, :10])
    # print(urange[:10, :10])
    # print(vrange[:10, :10])
    # exit(1)
    XYZ = np.stack([X, Y, Z], axis=2).reshape(-1, 3)
    #XYZ = XYZ[depth.reshape(-1) != 0]
    planes = []
    planeMasks = []
    invalidDepthMask = depth < 1e-4

    if 'planeAreaThreshold' in parameters:
        planeAreaThreshold = parameters['planeAreaThreshold']
    else:
        planeAreaThreshold = 500
        pass
    if 'distanceThreshold' in parameters:
        distanceThreshold = parameters['distanceThreshold']
    else:
        distanceThreshold = 0.05
        pass
    if 'local' in parameters:
        local = parameters['local']
    else:
        local = 0.2
        pass

    for y in range(5, height, 10):
        for x in range(5, width, 10):
            if invalidDepthMask[y][x]:
                continue
            sampledPoint = XYZ[y * width + x]
            sampledPoints = XYZ[np.linalg.norm(
                XYZ - sampledPoint, 2, 1) < local]
            if sampledPoints.shape[0] < 3:
                continue
            sampledPoints = sampledPoints[np.random.choice(
                np.arange(sampledPoints.shape[0]), size=(3))]
            try:
                plane = fitPlane(sampledPoints)
                pass
            except:
                continue

            diff = np.abs(np.matmul(XYZ, plane) -
                          np.ones(XYZ.shape[0])) / np.linalg.norm(plane)
            inlierIndices = diff < distanceThreshold
            #print(np.sum(inlierIndices), planeAreaThreshold)
            if np.sum(inlierIndices) < planeAreaThreshold:
                continue

            planes.append(plane)
            planeMasks.append(inlierIndices.reshape((height, width)))
            continue
        continue

    planes = np.array(planes)

    planeList = list(zip(planes, planeMasks))
    planeList = sorted(planeList, key=lambda x: -x[1].sum())
    planes, planeMasks = list(zip(*planeList))

    invalidMask = np.zeros((height, width), np.bool)
    validPlanes = []
    validPlaneMasks = []

    for planeIndex, plane in enumerate(planes):
        planeMask = planeMasks[planeIndex]
        if np.logical_and(planeMask, invalidMask).sum() > planeMask.sum() * 0.5:
            continue
        # if len(validPlanes) > 0:
        #     cv2.imwrite('test/mask_' + str(len(validPlanes) - 1) + '_available.png', drawMaskImage(1 - invalidMask))
        #     pass
        validPlanes.append(plane)
        validPlaneMasks.append(planeMask)
        invalidMask = np.logical_or(invalidMask, planeMask)
        continue
    planes = np.array(validPlanes)
    planesD = 1 / np.maximum(np.linalg.norm(planes, 2, 1, keepdims=True), 1e-4)
    planes *= pow(planesD, 2)

    planeMasks = np.stack(validPlaneMasks, axis=2)

    cv2.imwrite('test/depth.png', drawDepthImage(depth))
    for planeIndex in range(planes.shape[0]):
        cv2.imwrite('test/mask_' + str(planeIndex) + '.png',
                    drawMaskImage(planeMasks[:, :, planeIndex]))
        continue

    print(('number of planes: ' + str(planes.shape[0])))

    planeSegmentation = getSegmentationsGraphCut(
        planes, image, depth, normal, semantics, info, parameters=parameters)

    cv2.imwrite('test/segmentation_refined.png',
                drawSegmentationImage(planeSegmentation, blackIndex=planes.shape[0]))

    #planeSegmentation[planes.shape[0]] = numOutputPlanes

    return planes, planeSegmentation


def limitPlaneNumber(planes, planeSegmentation, numOutputPlanes):
    if planes.shape[0] > numOutputPlanes:
        planeInfo = []
        for planeIndex in range(planes.shape[0]):
            mask = planeSegmentation == planeIndex
            planeInfo.append((planes[planeIndex], mask))
            continue
        planeInfo = sorted(planeInfo, key=lambda x: -x[1].sum())
        newPlanes = []
        newPlaneSegmentation = np.full(
            planeSegmentation.shape, numOutputPlanes)
        for planeIndex in range(numOutputPlanes):
            newPlanes.append(planeInfo[planeIndex][0])
            newPlaneSegmentation[planeInfo[planeIndex][1]] = planeIndex
            continue
        newPlanes = np.array(newPlanes)
        return newPlanes, newPlaneSegmentation
    else:
        planeSegmentation[planeSegmentation ==
                          planes.shape[0]] = numOutputPlanes
        planes = np.concatenate(
            [planes, np.zeros((numOutputPlanes - planes.shape[0], 3))], axis=0)
        return planes, planeSegmentation
    return


def removeSmallPlanes(planes, planeSegmentation, planeAreaThreshold):
    planeInfo = []
    for planeIndex in range(planes.shape[0]):
        mask = planeSegmentation == planeIndex
        planeInfo.append((planes[planeIndex], mask, mask.sum()))
        continue
    planeInfo = sorted(planeInfo, key=lambda x: -x[2])
    newPlanes = []
    newPlaneSegmentation = np.full(planeSegmentation.shape, numOutputPlanes)
    for planeIndex, info in enumerate(planeInfo):
        if info[2] < planeAreaThreshold:
            break
        newPlanes.append(info[0])
        newPlaneSegmentation[info[1]] = planeIndex
        continue
    newPlanes = np.array(newPlanes)
    return newPlanes, newPlaneSegmentation


def calcDepthFromPlanes(planes, planeSegmentation, info, nonPlaneInfo={}):
    width = planeSegmentation.shape[1]
    height = planeSegmentation.shape[0]
    planeDepths = calcPlaneDepths(planes, width, height, info)

    if 'depth' in nonPlaneInfo:
        allDepths = np.concatenate(
            [planeDepths, np.expand_dims(nonPlaneInfo['depth'], -1)], axis=2)
    else:
        allDepths = planeDepths
        pass

    depthPred = allDepths.reshape([height * width, -1])[np.arange(width * height),
                                                        planeSegmentation.astype(np.int32).reshape(-1)].reshape(height, width)
    return depthPred


def calcNormalFromPlanes(planes, planeSegmentation, info, nonPlaneInfo={}):
    width = planeSegmentation.shape[1]
    height = planeSegmentation.shape[0]
    planeNormals = calcPlaneNormals(planes, width, height)

    if 'normal' in nonPlaneInfo:
        allNormals = np.concatenate(
            [planeNormals, np.expand_dims(nonPlaneInfo['normal'], 2), ], axis=2)
    else:
        allNormals = planeNormals
        pass
    normalPred = allNormals.reshape(width * height, -1, 3)[np.arange(
        width * height), planeSegmentation.reshape(-1)].reshape((height, width, 3))
    return normalPred


def fitPlanesPoints(points, segmentation, groupSegments, numPlanes=50, numPlanesPerSegment=3, numPlanesPerGroup=8, segmentRatio=0.1, planeAreaThreshold=100, numIterations=100, distanceThreshold=0.05, local=-1):
    allXYZ = points.reshape(-1, 3)

    # planeDiffThreshold = distanceThreshold
    # planes = np.load('test/planes.pny.npy')
    # planePointIndices = np.load('test/plane_indices.pny.npy')
    # planeIndex_1 = 1
    # planeIndex_2 = 2
    # for planeIndex_1 in [1, ]:
    #     for planeIndex_2 in [2, 5, 7, 10]:
    #         plane_1 = planes[planeIndex_1]
    #         plane_2 = planes[planeIndex_2]
    #         points_1 = allXYZ[planePointIndices[planeIndex_1]]
    #         points_2 = allXYZ[planePointIndices[planeIndex_2]]

    #         diff_1 = np.abs(np.matmul(points_2, plane_1) - np.ones(points_2.shape[0])) / np.linalg.norm(plane_1)
    #         diff_2 = np.abs(np.matmul(points_1, plane_2) - np.ones(points_1.shape[0])) / np.linalg.norm(plane_2)
    #         print(np.sum(diff_1 < planeDiffThreshold), diff_1.shape[0])
    #         print(np.sum(diff_2 < planeDiffThreshold), diff_2.shape[0])
    #         print((diff_1.mean(), diff_2.mean()))
    #         # if np.sum(diff_1 < planeDiffThreshold) > diff_1.shape[0] * inlierThreshold or np.sum(diff_2 < planeDiffThreshold) > diff_2.shape[0] * inlierThreshold:
    #         #     planesDiff[planeIndex][otherPlaneIndex] = 1
    #         #     planesDiff[otherPlaneIndex][planeIndex] = 1
    #         #     pass

    #         # if min(diff_1.mean(), diff_2.mean()) < planeDiffThreshold:
    #         #     planesDiff[planeIndex][otherPlaneIndex] = 1
    #         #     planesDiff[otherPlaneIndex][planeIndex] = 1
    #         #     pass

    #         continue
    #     continue

    # print(planes / np.linalg.norm(planes, axis=1, keepdims=True))
    # exit(1)

    planes = []
    planePointIndices = []
    groupNumPlanes = []
    for groupIndex, group in enumerate(groupSegments):
        groupPlanes = []
        groupPlanePointIndices = []
        for segmentIndex in group:
            segmentMask = segmentation == segmentIndex
            # planes.append(np.ones(3))
            # planePointIndices.append(segmentMask.nonzero()[0])
            # continue

            XYZ = allXYZ[segmentMask.reshape(-1)]
            numPoints = XYZ.shape[0]

            if numPoints <= planeAreaThreshold:
                if numPoints > 0:
                    groupPlanes.append(np.random.random(3))
                    groupPlanePointIndices.append(segmentMask.nonzero()[0])
                    pass
                continue

            for planeIndex in range(numPlanesPerSegment):
                maxNumInliers = 0
                for iteration in range(numIterations):
                    if local > 0:
                        sampledPoint = XYZ[np.random.randint(
                            XYZ.shape[0], size=(1))]
                        sampledPoints = XYZ[np.linalg.norm(
                            XYZ - sampledPoint, axis=1) < local]

                        if sampledPoints.shape[0] < 3:
                            continue
                        elif sampledPoints.shape[0] > 3:
                            sampledPoints = sampledPoints[np.random.choice(
                                np.arange(sampledPoints.shape[0]), size=(3))]
                            pass
                        pass
                    else:
                        sampledPoints = XYZ[np.random.choice(
                            np.arange(XYZ.shape[0]), size=(3))]
                        pass

                    try:
                        plane = fitPlane(sampledPoints)
                        pass
                    except:
                        continue
                    diff = np.abs(np.matmul(XYZ, plane) -
                                  np.ones(XYZ.shape[0])) / np.linalg.norm(plane)
                    numInliers = np.sum(diff < distanceThreshold)
                    if numInliers > maxNumInliers:
                        maxNumInliers = numInliers
                        bestPlane = plane
                        pass
                    continue

                groupPlanes.append(bestPlane)

                diff = np.abs(np.matmul(XYZ, bestPlane) -
                              np.ones(XYZ.shape[0])) / np.linalg.norm(bestPlane)
                inlierIndices = diff < distanceThreshold
                if inlierIndices.sum() > numPoints * (1 - segmentRatio):
                    inlierIndices = np.ones(diff.shape, dtype=np.bool)
                    pass
                pointIndices = segmentMask.nonzero()[0][inlierIndices]
                groupPlanePointIndices.append(pointIndices)
                segmentMask[pointIndices] = 0

                XYZ = XYZ[np.logical_not(inlierIndices)]
                if XYZ.shape[0] <= planeAreaThreshold:
                    if XYZ.shape[0] > 0:
                        groupPlanes.append(np.random.random(3))
                        groupPlanePointIndices.append(segmentMask.nonzero()[0])
                        pass
                    break
                continue
            continue
        if len(groupPlanes) == 0:
            continue

        # planeList = zip(groupPlanes, groupPlanePointIndices)
        # planeList = sorted(planeList, key=lambda x:-len(x[1]))
        # groupPlanes, groupPlanePointIndices = zip(*planeList)

        # groupMask = np.zeros(segmentation.shape, np.bool)
        # for segmentIndex in group:
        #     groupMask = np.logical_or(groupMask, segmentation == segmentIndex)
        #     continue

        # groupPlanePointIndices = []
        # for plane in groupPlanes:
        #     groupPoints = allXYZ[groupMask]
        #     diff = np.abs(np.matmul(groupPoints, plane) - np.ones(groupPoints.shape[0])) / np.linalg.norm(plane)
        #     inlierIndices = diff < distanceThreshold
        #     pointIndices = groupMask.nonzero()[0][inlierIndices]
        #     groupPlanePointIndices.append(pointIndices)
        #     groupMask[pointIndices] = 0
        #     continue

        # if len(groupPlanes) > numPlanesPerGroup:
        #     planeList = zip(groupPlanes, groupPlanePointIndices)
        #     planeList = sorted(planeList, key=lambda x:-len(x[1]))
        #     planeList = planeList[:numPlanesPerGroup]
        #     groupPlanes, groupPlanePointIndices = zip(*planeList)
        #     pass

        numPointsOri = 0
        for indices in groupPlanePointIndices:
            numPointsOri += len(indices)
            continue

        groupPlanes, groupPlanePointIndices = mergePlanes(
            points, groupPlanes, groupPlanePointIndices, planeDiffThreshold=distanceThreshold, planeAreaThreshold=planeAreaThreshold)
        if len(groupPlanes) > 1:
            groupPlanes, groupPlanePointIndices = mergePlanes(
                points, groupPlanes, groupPlanePointIndices, planeDiffThreshold=distanceThreshold, planeAreaThreshold=planeAreaThreshold)
            pass
        #groupPlanes, groupPlanePointIndices = mergePlanes(points, groupPlanes, groupPlanePointIndices, planeDiffThreshold=distanceThreshold)

        # if groupIndex == 14:
        #     groupPlanes, groupPlanePointIndices = mergePlanes(points, groupPlanes, groupPlanePointIndices, planeDiffThreshold=distanceThreshold)
        #     planesTest = np.array(groupPlanes)
        #     np.save('test/planes.npy', planesTest)
        #     np.save('test/plane_indices.npy', groupPlanePointIndices)
        #     print(planesTest / np.linalg.norm(planesTest, axis=1, keepdims=True))
        #     #exit(1)
        #     pass

        numPoints = 0
        for indices in groupPlanePointIndices:
            numPoints += len(indices)
            continue
        planes += groupPlanes
        planePointIndices += groupPlanePointIndices
        groupNumPlanes.append(len(groupPlanes))
        #planeSegmentation[groupPlaneSegmentation >= 0] = groupPlaneSegmentation[groupPlaneSegmentation >= 0] + numPlanes
        continue

    #planes = np.concatenate(planes, axis=0)

    # if len(planes) > numPlanes:
    #     planeList = zip(planes, planePointsArray)
    #     planeList = sorted(planeList, key=lambda x:-len(x[1]))
    #     planeList = planeList[:numPlanes]
    #     planes, planePointsArray = zip(*planeList)
    #     pass

    # if len(planes) > numPlanes:
    #     planeList = zip(planes, planePointIndices)
    #     planeList = sorted(planeList, key=lambda x:-len(x[1]))
    #     planeList = planeList[:numPlanes]
    #     planes, planePointIndices = zip(*planeList)
    #     pass

    if len(planes) == 0:
        return np.array([]), np.ones(segmentation.shape).astype(np.int32) * (-1), []

    planes = np.array(planes)
    print(('number of planes: ' + str(planes.shape[0])))

    # print(planes)
    # for v in planePointsArray:
    #     print(len(v))
    # if planes.shape[0] < numPlanes:
    #     planes = np.concatenate([planes, np.zeros((numPlanes - planes.shape[0], 3))], axis=0)
    #     pass

    planeSegmentation = np.ones(segmentation.shape) * (-1)
    for planeIndex, planePoints in enumerate(planePointIndices):
        planeSegmentation[planePoints] = planeIndex
        continue

    planesD = 1 / np.linalg.norm(planes, 2, 1, keepdims=True)
    planes *= pow(planesD, 2)

    return planes, planeSegmentation, groupNumPlanes


def mergePlanes3D(points, planes, planePointIndices, planeDiffThreshold=0.05, planeAngleThreshold=30, inlierThreshold=0.9, planeAreaThreshold=100):

    # planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    # planes = planes / pow(planesD, 2)
    # planesDiff = (np.linalg.norm(np.expand_dims(planes, 1) - np.expand_dims(planes, 0), axis=2) < planeDiffThreshold).astype(np.int32)

    planeList = list(zip(planes, planePointIndices))
    planeList = sorted(planeList, key=lambda x: -len(x[1]))
    planes, planePointIndices = list(zip(*planeList))

    groupedPlanes = []
    groupedPlanePointIndices = []

    numPlanes = len(planes)
    usedPlaneConfidence = np.ones(numPlanes, np.float32) * (-1)
    usedPlaneMap = np.ones(numPlanes, np.int32) * (-1)

    for planeIndex, plane in enumerate(planes):
        if usedPlaneConfidence[planeIndex] > 0:
            continue
        usedPlaneConfidence[planeIndex] = 1
        usedPlaneMap[planeIndex] = planeIndex
        XYZ = points[planePointIndices[planeIndex]]
        for otherPlaneIndex in range(planeIndex + 1, numPlanes):
            # if planeIndex not in [0, 1, 2, ]:
            # break
            # if usedPlanes[otherPlaneIndex]:
            # continue
            #otherPlane = planes[otherPlaneIndex]
            # if np.abs(np.dot(plane, otherPlane)) / (np.linalg.norm(plane) * np.linalg.norm(otherPlane)) < np.cos(np.deg2rad(planeAngleThreshold)):
            # continue

            otherXYZ = points[planePointIndices[otherPlaneIndex]]

            diff_1 = np.abs(np.matmul(otherXYZ, plane) -
                            np.ones(otherXYZ.shape[0])) / np.linalg.norm(plane)
            #diff_2 = np.abs(np.matmul(XYZ, otherPlane) - np.ones(XYZ.shape[0])) / np.linalg.norm(otherPlane)
            ratio = float(np.sum(diff_1 < planeDiffThreshold)) / \
                diff_1.shape[0]
            if ratio > max(inlierThreshold, usedPlaneConfidence[otherPlaneIndex]):
                usedPlaneConfidence[otherPlaneIndex] = ratio
                usedPlaneMap[otherPlaneIndex] = planeIndex
                pass
            continue
        continue

    for planeIndex in range(numPlanes):
        mergedPlanes = (usedPlaneMap == planeIndex).nonzero()[0].tolist()
        if len(mergedPlanes) == 0:
            continue
        pointIndices = []
        for mergedPlaneIndex in mergedPlanes:
            pointIndices += planePointIndices[mergedPlaneIndex].tolist()
            continue
        if len(pointIndices) <= planeAreaThreshold:
            continue
        XYZ = points[pointIndices]
        ranges = XYZ.max(0) - XYZ.min(0)
        ranges.sort()
        #print((planeIndex, ranges.tolist() + XYZ.mean(0).tolist()))
        if ranges[1] < 0.2:
            continue
        # continue
        # print(XYZ.shape[0])
        # print(ranges)
        # if ranges.max() * 5 >= XYZ.shape[0]:
        # continue
        plane = fitPlane(XYZ)
        groupedPlanes.append(plane)
        groupedPlanePointIndices.append(np.array(pointIndices))
        continue

    return groupedPlanes, groupedPlanePointIndices


def mergePlanesBackup(points, planes, planePointIndices, planeDiffThreshold=0.05, planeAngleThreshold=30, inlierThreshold=0.8):

    # planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    # planes = planes / pow(planesD, 2)
    # planesDiff = (np.linalg.norm(np.expand_dims(planes, 1) - np.expand_dims(planes, 0), axis=2) < planeDiffThreshold).astype(np.int32)
    numPlanes = len(planes)
    planesDiff = np.diag(np.ones(numPlanes))
    for planeIndex, plane in enumerate(planes):
        for otherPlaneIndex in range(planeIndex + 1, numPlanes):
            otherPlane = planes[otherPlaneIndex]
            if np.abs(np.dot(plane, otherPlane)) / (np.linalg.norm(plane) * np.linalg.norm(otherPlane)) < np.cos(np.deg2rad(planeAngleThreshold)):
                continue
            XYZ = points[planePointIndices[planeIndex]]
            otherXYZ = points[planePointIndices[otherPlaneIndex]]
            diff_1 = np.abs(np.matmul(otherXYZ, plane) -
                            np.ones(otherXYZ.shape[0])) / np.linalg.norm(plane)
            diff_2 = np.abs(np.matmul(XYZ, otherPlane) -
                            np.ones(XYZ.shape[0])) / np.linalg.norm(otherPlane)

            if np.sum(diff_1 < planeDiffThreshold) > diff_1.shape[0] * inlierThreshold or np.sum(diff_2 < planeDiffThreshold) > diff_2.shape[0] * inlierThreshold:
                planesDiff[planeIndex][otherPlaneIndex] = 1
                planesDiff[otherPlaneIndex][planeIndex] = 1
                pass

            # if min(diff_1.mean(), diff_2.mean()) < planeDiffThreshold:
            #     planesDiff[planeIndex][otherPlaneIndex] = 1
            #     planesDiff[otherPlaneIndex][planeIndex] = 1
            #     pass

            # if diff_1.mean() < planeDiffThreshold:
            #     planesDiff[planeIndex][otherPlaneIndex] = 1
            #     pass
            # if diff_2.mean() < planeDiffThreshold:
            #     planesDiff[otherPlaneIndex][planeIndex] = 1
            #     pass
            continue
        continue

    # while True:
    #     #nextPlanesDiff = (np.matmul(planesDiff, planesDiff) > 0.5).astype(np.int32)
    #     nextPlanesDiff = ((planesDiff + np.matmul(np.transpose(planesDiff), planesDiff)) > 0.5).astype(np.int32)
    #     if np.all(nextPlanesDiff == planesDiff):
    #         break
    #     planesDiff = nextPlanesDiff
    #     continue

    # print(planesDiff)
    usedPlanes = np.zeros(planesDiff.shape[0])
    uniquePlanesDiff = []
    for planeIndex in range(planesDiff.shape[0]):
        planesMask = np.maximum(planesDiff[planeIndex] - usedPlanes, 0)
        if planesMask[planeIndex] > 0:
            uniquePlanesDiff.append(planesMask)
            usedPlanes += planesMask
            pass
        continue
    planesDiff = np.array(uniquePlanesDiff)
    # print(planesDiff)

    # diffMatrix = np.diag(np.ones(planesDiff.shape[0])).astype(np.float64)
    # diffMatrix -= np.tril(np.ones(planesDiff.shape), -1)
    # planesDiff = np.maximum(np.matmul(diffMatrix, planesDiff), 0)
    # planesDiff *= np.expand_dims(np.diag(planesDiff), -1)
    # planesDiff = np.unique(planesDiff, axis=0)

    groupedPlanes = []
    groupedPlanePointIndices = []
    for groupIndex in range(planesDiff.shape[0]):
        if planesDiff[groupIndex].sum() == 0:
            continue
        segmentIndices = planesDiff[groupIndex].nonzero()[0]
        pointIndices = []
        for segmentIndex in segmentIndices.tolist():
            pointIndices += planePointIndices[segmentIndex].tolist()
            continue
        XYZ = points[pointIndices]
        plane = fitPlane(XYZ)
        groupedPlanes.append(plane)
        groupedPlanePointIndices.append(np.array(pointIndices))
        continue

    return groupedPlanes, groupedPlanePointIndices


# def evaluatePlaneSegmentation(predPlanes, predSegmentations, gtPlanes, gtSegmentations, gtNumPlanes, prefix = '', numOutputPlanes = 20):
#     if len(gtSegmentations.shape) == 3:
#         gtSegmentations = (np.expand_dims(gtSegmentations, -1) == np.arange(numOutputPlanes)).astype(np.float32)
#         pass
#     if len(predSegmentations.shape) == 3:
#         predSegmentations = (np.expand_dims(predSegmentations, -1) == np.arange(numOutputPlanes)).astype(np.float32)
#         pass

#     width = predSegmentations.shape[2]
#     height = predSegmentations.shape[1]

#     planeDiffs = np.linalg.norm(np.expand_dims(gtPlanes, 2) - np.expand_dims(predPlanes, 1), axis=3)
#     #print(gtPlanes[0])
#     #print(predPlanes[0])
#     #print(planeDiffs[0])

#     planeAreas = np.sum(np.sum(gtSegmentations, axis=1), axis=1)
#     intersection = np.sum((np.expand_dims(gtSegmentations, -1) * np.expand_dims(predSegmentations, 3) > 0.5).astype(np.float32), axis=(1, 2))
#     union = np.sum((np.expand_dims(gtSegmentations, -1) + np.expand_dims(predSegmentations, 3) > 0.5).astype(np.float32), axis=(1, 2))
#     planeIOUs = intersection / np.maximum(union, 1e-4)

#     planeMask = np.expand_dims(np.arange(predPlanes.shape[1]), 0) < np.expand_dims(gtNumPlanes, 1)
#     for index, numPlanes in enumerate(gtNumPlanes.tolist()):
#         planeDiffs[index, numPlanes:] = 1000000
#         planeIOUs[index, numPlanes:] = -1
#         pass

#     totalNumPlanes = gtNumPlanes.sum()

#     numPixels = planeAreas.sum(1)

#     # planeDistanceThreshold = 0.5
#     # diffMask = (planeDiffs < planeDistanceThreshold).astype(np.float32)
#     # maxIOU = np.max(planeIOUs * diffMask, axis=2)
#     # IOU = 0.5
#     # print(maxIOU[0])
#     # print(planeMask[0])
#     # print(((maxIOU >= IOU) * planeMask).sum(1).astype(np.float32))
#     # print(gtNumPlanes)
#     # print(float(((maxIOU >= IOU) * planeMask).sum()) / totalNumPlanes)

#     # exit(1)

#     pixel_curves = []
#     plane_curves = []
#     for planeDistanceThreshold in [0.1, 0.3, 0.5]:
#         diffMask = (planeDiffs < planeDistanceThreshold).astype(np.float32)
#         maxIOU = np.max(planeIOUs * diffMask, axis=2)
#         stride = 0.1
#         planeRecalls = []
#         pixelRecalls = []
#         for step in xrange(int(1 / stride + 1)):
#             IOU = step * stride
#             pixelRecalls.append((np.minimum((intersection * (planeIOUs >= IOU).astype(np.float32) * diffMask).sum(2), planeAreas).sum(1) / numPixels).mean())
#             planeRecalls.append(float(((maxIOU >= IOU) * planeMask).sum()) / totalNumPlanes)
#             continue

#         pixel_curves.append(pixelRecalls)
#         plane_curves.append(planeRecalls)
#         pass

#     for IOUThreshold in [0.3, 0.5, 0.7]:
#         IOUMask = (planeIOUs > IOUThreshold).astype(np.float32)
#         minDiff = np.min(planeDiffs * IOUMask + 1000000 * (1 - IOUMask), axis=2)
#         stride = 0.05
#         planeRecalls = []
#         pixelRecalls = []
#         for step in xrange(int(0.5 / stride + 1)):
#             diff = step * stride
#             pixelRecalls.append((np.minimum((intersection * (planeDiffs <= diff).astype(np.float32) * IOUMask).sum(2), planeAreas).sum(1) / numPixels).mean())
#             planeRecalls.append(float(((minDiff <= diff) * planeMask).sum()) / totalNumPlanes)
#             continue
#         pixel_curves.append(pixelRecalls)
#         plane_curves.append(planeRecalls)
#         pass


#     if prefix == '':
#         return pixel_curves, plane_curves
#     else:
#         np.save(prefix + 'curves.npy', pixel_curves + plane_curves)
#         return


# def evaluatePlanes(predDepths, predSegmentations, predNumPlanes, gtDepths, gtSegmentations, gtNumPlanes, prefix = ''):
#     if len(gtSegmentations.shape) == 3:
#         gtSegmentations = (np.expand_dims(gtSegmentations, -1) == np.arange(gtNumPlanes)).astype(np.float32)
#         pass
#     if len(predSegmentations.shape) == 3:
#         predSegmentations = (np.expand_dims(predSegmentations, -1) == np.arange(predNumPlanes)).astype(np.float32)
#         pass

#     width = predSegmentations.shape[2]
#     height = predSegmentations.shape[1]


#     #print(gtPlanes[0])
#     #print(predPlanes[0])
#     #print(planeDiffs[0])

#     planeAreas = np.sum(np.sum(gtSegmentations, axis=1), axis=1)
#     intersectionMask = np.expand_dims(gtSegmentations, -1) * np.expand_dims(predSegmentations, 3) > 0.5
#     depthDiffs = np.expand_dims(gtDepths, -1) - np.expand_dims(predDepths, 3)
#     intersection = np.sum((intersectionMask).astype(np.float32), axis=(1, 2))

#     planeDiffs = np.abs(depthDiffs * intersectionMask).sum(1).sum(1) / np.maximum(intersection, 1e-4)

#     union = np.sum((np.expand_dims(gtSegmentations, -1) + np.expand_dims(predSegmentations, 3) > 0.5).astype(np.float32), axis=(1, 2))
#     planeIOUs = intersection / np.maximum(union, 1e-4)


#     for index, numPlanes in enumerate(gtNumPlanes.tolist()):
#         planeDiffs[index, numPlanes:] = 1000000
#         planeIOUs[index, numPlanes:] = -1
#         pass

#     totalNumPlanes = gtNumPlanes.sum()
#     totalNumPredictions = predSegmentations.max(1).max(1).sum()

#     numPixels = planeAreas.sum(1)

#     # planeDistanceThreshold = 0.5
#     # diffMask = (planeDiffs < planeDistanceThreshold).astype(np.float32)
#     # maxIOU = np.max(planeIOUs * diffMask, axis=2)
#     # IOU = 0.5
#     # print(maxIOU[0])
#     # print(planeMask[0])
#     # print(((maxIOU >= IOU) * planeMask).sum(1).astype(np.float32))
#     # print(gtNumPlanes)
#     # print(float(((maxIOU >= IOU) * planeMask).sum()) / totalNumPlanes)

#     # exit(1)

#     pixel_curves = []
#     plane_curves = []

#     validPlaneMask = np.expand_dims(np.arange(gtNumPlanes), 0) < np.expand_dims(gtNumPlanes, 1)
#     for planeDistanceThreshold in [0.05, 0.10, 0.15]:
#         diffMask = (planeDiffs < planeDistanceThreshold).astype(np.float32)
#         maxIOU = np.max(planeIOUs * diffMask, axis=2)
#         stride = 0.1
#         planeStatistics = []
#         pixelRecalls = []
#         for step in xrange(int(1 / stride + 1)):
#             IOU = step * stride
#             pixelRecalls.append((np.minimum((intersection * (planeIOUs >= IOU).astype(np.float32) * diffMask).sum(2), planeAreas).sum(1) / numPixels).mean())
#             planeStatistics.append((float((((maxIOU >= IOU) * validPlaneMask)).sum()), totalNumPlanes, totalNumPredictions))
#             continue

#         pixel_curves.append(pixelRecalls)
#         plane_curves.append(planeStatistics)
#         pass


#     for IOUThreshold in [0.3, 0.5, 0.7]:
#         IOUMask = (planeIOUs > IOUThreshold).astype(np.float32)
#         minDiff = np.min(planeDiffs * IOUMask + 1000000 * (1 - IOUMask), axis=2)
#         stride = 0.02
#         planeStatistics = []
#         pixelRecalls = []
#         for step in xrange(int(0.2 / stride + 1)):
#             diff = step * stride
#             pixelRecalls.append((np.minimum((intersection * (planeDiffs <= diff).astype(np.float32) * IOUMask).sum(2), planeAreas).sum(1) / numPixels).mean())
#             planeStatistics.append(((((minDiff <= diff) * validPlaneMask).sum()), totalNumPlanes, totalNumPredictions))
#             continue
#         pixel_curves.append(pixelRecalls)
#         plane_curves.append(planeStatistics)
#         pass


#     if prefix == '':
#         return pixel_curves, plane_curves
#     else:
#         np.save(prefix + 'curves.npy', pixel_curves + plane_curves)
#         return

def evaluatePlanePrediction(predDepths, predSegmentations, predNumPlanes, gtDepths, gtSegmentations, gtNumPlanes, prefix=''):
    if len(gtSegmentations.shape) == 2:
        gtSegmentations = (np.expand_dims(gtSegmentations, -1)
                           == np.arange(gtNumPlanes)).astype(np.float32)
        pass
    if len(predSegmentations.shape) == 2:
        predSegmentations = (np.expand_dims(
            predSegmentations, -1) == np.arange(predNumPlanes)).astype(np.float32)
        pass

    width = predSegmentations.shape[1]
    height = predSegmentations.shape[0]

    # print(gtPlanes[0])
    # print(predPlanes[0])
    # print(planeDiffs[0])

    planeAreas = gtSegmentations.sum(axis=(0, 1))
    intersectionMask = np.expand_dims(
        gtSegmentations, -1) * np.expand_dims(predSegmentations, 2) > 0.5
    depthDiffs = np.expand_dims(gtDepths, -1) - np.expand_dims(predDepths, 2)
    intersection = np.sum((intersectionMask).astype(np.float32), axis=(0, 1))

    planeDiffs = np.abs(
        depthDiffs * intersectionMask).sum(axis=(0, 1)) / np.maximum(intersection, 1e-4)

    #planeDiffs = np.linalg.norm(np.expand_dims(gtPlanes, 1) - np.expand_dims(predPlanes, 0), axis=2)

    planeDiffs[intersection < 1e-4] = 1

    union = np.sum(((np.expand_dims(gtSegmentations, -1) + np.expand_dims(
        predSegmentations, 2)) > 0.5).astype(np.float32), axis=(0, 1))
    planeIOUs = intersection / np.maximum(union, 1e-4)

    planeDiffs[gtNumPlanes:] = 1000000
    planeIOUs[gtNumPlanes:] = -1

    numPredictions = int(predSegmentations.max(axis=(0, 1)).sum())

    numPixels = planeAreas.sum()

    # print(gtNumPlanes)
    # #print('IOU')
    # print(np.stack([planeIOUs.max(1), planeIOUs.argmax(1)], axis=1))
    # print('diff')
    # #print(np.abs(depthDiffs * intersectionMask).sum(axis=(0, 1)))
    # #print(np.maximum(intersection, 1e-4))
    # #print(np.stack([depthDiffs.min(1), depthDiffs.argmin(1)], axis=1))
    # print(np.stack([planeDiffs.min(1) * 10000, planeDiffs.argmin(1)], axis=1))
    # print(planeDiffs)
    # #exit(1)

    pixel_curves = []
    plane_curves = []

    for planeDistanceThreshold in [0.1, 0.2, 0.3]:
        diffMask = (planeDiffs < planeDistanceThreshold).astype(np.float32)
        maxIOU = np.max(planeIOUs * diffMask, axis=1)
        stride = 0.1
        planeStatistics = []
        pixelRecalls = []
        for step in range(int(1.21 / stride + 1)):
            IOU = step * stride
            pixelRecalls.append(np.minimum((intersection * (planeIOUs >= IOU).astype(
                np.float32) * diffMask).sum(1), planeAreas).sum(0) / numPixels)
            planeStatistics.append(
                (((maxIOU >= IOU)[:gtNumPlanes]).sum(), gtNumPlanes, numPredictions))
            continue

        pixel_curves.append(pixelRecalls)
        plane_curves.append(planeStatistics)
        pass

    for IOUThreshold in [0.3, 0.5, 0.7]:
        IOUMask = (planeIOUs > IOUThreshold).astype(np.float32)
        minDiff = np.min(planeDiffs * IOUMask +
                         1000000 * (1 - IOUMask), axis=1)
        stride = 0.05
        planeStatistics = []
        pixelRecalls = []
        for step in range(int(0.61 / stride + 1)):
            diff = step * stride
            pixelRecalls.append(np.minimum((intersection * (planeDiffs <= diff).astype(
                np.float32) * IOUMask).sum(1), planeAreas).sum() / numPixels)
            planeStatistics.append(
                (((minDiff <= diff)[:gtNumPlanes]).sum(), gtNumPlanes, numPredictions))
            continue
        pixel_curves.append(pixelRecalls)
        plane_curves.append(planeStatistics)
        pass

    if prefix == '':
        return pixel_curves, plane_curves
    else:
        np.save(prefix + 'curves.npy', pixel_curves + plane_curves)
        return


def plotCurves(x, ys, filename='test/test.png', xlabel='', ylabel='', title='', labels=[]):
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = plt.gca()
    colors = []
    markers = []
    sizes = []
    for label in labels:
        if 'PlaneNet' in label:
            colors.append('blue')
        elif 'NYU' in label:
            colors.append('red')
        elif 'Manhattan' in label:
            colors.append('orange')
        else:
            colors.append('brown')
            pass
        if 'Oracle' in label:
            markers.append('o')
        else:
            markers.append('')
            pass
        if 'PlaneNet' in label:
            sizes.append(2)
        else:
            sizes.append(1)
            pass
        continue

    ordering = [1, 2, 3, 4, 5, 6, 0]
    final_labels = ['PlaneNet', '[25]+depth', '[25]',
                    '[9]+depth', '[9]', '[26]+depth', '[26]']

    # for index, y in enumerate(ys):
    for order in ordering:
        plt.plot(x, ys[order], figure=fig, label=final_labels[order],
                 color=colors[order], marker=markers[order], linewidth=sizes[order])
        continue
    #plt.legend(loc='upper right')
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
               ncol=4, fancybox=True, shadow=True, handletextpad=0.1)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel + ' %')
    ax.set_yticklabels(np.arange(0, 101, 20))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    #ax.xaxis.set_label_coords(1.1, -0.025)
    # plt.title(title)
    plt.xlim((x[0], x[-1] + 0.01))
    plt.ylim((0, 1))
    plt.tight_layout(w_pad=0.3)
    plt.savefig(filename)
    return


def plotCurvesSplit(x, ys, filenames, xlabel='', ylabel='', title='', labels=[]):
    import matplotlib
    matplotlib.rcParams.update({'font.size': 16})
    matplotlib.rcParams.update({'font.family': 'Times New Roman'})
    #font = {'size'   : 22}
    #matplotlib.rc('font', **font)
    #matplotlib.rc('xtick', labelsize=22)
    #matplotlib.rc('ytick', labelsize=22)
    #matplotlib.rc('xticklabels', fontsize=22)
    #matplotlib.rc('yticklabels', fontsize=22)
    #matplotlib.rc('xlabel', size=22)
    #matplotlib.rc('xlabel', size=22)
    import matplotlib.pyplot as plt

    #plt.rcParams.update({'font.size': 16})

    drawLegend = True

    colors = []
    markers = []
    sizes = []
    for label in labels:
        if 'PlaneNet' in label:
            colors.append('blue')
        elif 'NYU' in label:
            colors.append('red')
        elif 'Manhattan' in label:
            colors.append('orange')
        else:
            colors.append('brown')
            pass
        if 'Oracle' in label:
            markers.append('o')
        else:
            markers.append('')
            pass
        if 'PlaneNet' in label:
            sizes.append(3)
        else:
            sizes.append(2)
            pass
        continue

    final_labels = ['PlaneNet', '[30] + GT depth', '[30] + Inferred depth',
                    '[12] + GT depth', '[12] + Inferred depth', '[31] + GT depth', '[31] + Inferred depth']

    if drawLegend:
        fig = plt.figure(figsize=(12, 6))
    else:
        fig = plt.figure()
        pass

    ax = plt.gca()

    ordering = [2, 4, 6, 0]

    # for index, y in enumerate(ys):
    for order in ordering:
        if drawLegend:
            plt.plot(x, np.zeros(ys[order].shape), figure=fig, label=final_labels[order],
                     color=colors[order], marker=markers[order], linewidth=sizes[order])
        else:
            plt.plot(x, ys[order], figure=fig, label=final_labels[order],
                     color=colors[order], marker=markers[order], linewidth=sizes[order])
            pass
        continue

    if drawLegend:
        plt.legend(loc='upper right')
        pass
    #plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fancybox=True, shadow=True, handletextpad=0.1)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel + ' %')

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(22)

    ax.set_yticklabels(np.arange(0, 101, 20))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.tick_params(width=2, length=8)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    #ax.xaxis.set_label_coords(1.1, -0.025)
    # plt.title(title)
    plt.xlim((x[0], x[-1] + 0.01))
    plt.ylim((0, 1))
    plt.tight_layout(w_pad=0.3)
    plt.savefig(filenames[0])

    if drawLegend:
        fig = plt.figure(figsize=(12, 6))
    else:
        fig = plt.figure()
        pass

    ax = plt.gca()

    ordering = [1, 3, 5, 0]

    # for index, y in enumerate(ys):
    for order in ordering:
        if drawLegend:
            plt.plot(x, np.zeros(ys[order].shape), figure=fig, label=final_labels[order],
                     color=colors[order], marker=markers[order], linewidth=sizes[order])
        else:
            plt.plot(x, ys[order], figure=fig, label=final_labels[order],
                     color=colors[order], marker=markers[order], linewidth=sizes[order])
            pass
        continue

    if drawLegend:
        plt.legend(loc='upper right')
        pass
    #plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fancybox=True, shadow=True, handletextpad=0.1)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel + ' %')

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(22)

    ax.set_yticklabels(np.arange(0, 101, 20))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.tick_params(width=2, length=8)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    #ax.xaxis.set_label_coords(1.1, -0.025)
    # plt.title(title)
    plt.xlim((x[0], x[-1] + 0.01))
    plt.ylim((0, 1))
    plt.tight_layout(w_pad=0.3)
    plt.savefig(filenames[1])
    return


def plotCurvesSubplot(x, ysArray, filenames, xlabel='', ylabels=[], labels=[]):
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.size': 14})

    colors = []
    markers = []
    sizes = []
    for label in labels:
        if 'PlaneNet' in label:
            colors.append('blue')
        elif 'NYU' in label:
            colors.append('red')
        elif 'Manhattan' in label:
            colors.append('orange')
        else:
            colors.append('brown')
            pass
        if 'Oracle' in label:
            markers.append('o')
        else:
            markers.append('')
            pass
        if 'PlaneNet' in label:
            sizes.append(2)
        else:
            sizes.append(1)
            pass
        continue
    final_labels = ['PlaneNet', '[25]+GT depth', '[25]',
                    '[9]+GT depth', '[9]', '[26]+GT depth', '[26]']

    orderingArray = [[2, 4, 6, 0], [1, 3, 5, 0]]

    for groupIndex in range(2):
        fig = plt.figure(groupIndex)
        ax = plt.gca()

        ordering = orderingArray[groupIndex]
        for metricIndex in range(2):
            plt.subplot(1, 2, metricIndex + 1)
            # for index, y in enumerate(ys):
            ys = ysArray[metricIndex]
            for order in ordering:
                plt.plot(x, ys[order], figure=fig, label=final_labels[order],
                         color=colors[order], marker=markers[order], linewidth=sizes[order])
                continue
            plt.xlabel(xlabel)
            plt.ylabel(ylabels[metricIndex] + ' %')

            ax.set_yticklabels(np.arange(0, 101, 20))
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.get_xaxis().tick_bottom()
            ax.get_yaxis().tick_left()
            #ax.xaxis.set_label_coords(1.1, -0.025)
            # plt.title(title)

            plt.xlim((x[0], x[-1] + 0.01))
            plt.ylim((0, 1))

            continue

        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                   ncol=4, fancybox=True, shadow=True, handletextpad=0.1)

        plt.tight_layout(w_pad=0.3)
        plt.savefig(filenames[groupIndex])

        continue
    #plt.legend(loc='upper right')
    return


def plotCurvesSimple(x, ys, filename='test/test.png', xlabel='', ylabel='', title='', labels=[]):
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = plt.gca()

    ordering = np.arange(len(labels)).tolist()
    final_labels = labels

    # for index, y in enumerate(ys):
    for order in ordering:
        plt.plot(x, ys[order], figure=fig, label=final_labels[order])
        continue
    plt.legend(loc='upper right', ncol=2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel + ' %')
    ax.set_yticklabels(np.arange(0, 101, 20))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    #ax.xaxis.set_label_coords(1.1, -0.025)
    # plt.title(title)
    plt.xlim((x[0], x[-1] + 0.01))
    plt.ylim((0, 1))
    plt.tight_layout(w_pad=0.3)
    plt.savefig(filename)
    return


def transformPlanes(planes, transformation):

    centers = planes
    planesD = np.maximum(np.linalg.norm(planes, axis=1, keepdims=True), 1e-4)
    refPoints = centers - planes / planesD

    centers = np.concatenate([centers, np.ones((planes.shape[0], 1))], axis=1)
    refPoints = np.concatenate(
        [refPoints, np.ones((planes.shape[0], 1))], axis=1)

    newCenters = np.transpose(np.matmul(transformation, np.transpose(centers)))
    newRefPoints = np.transpose(
        np.matmul(transformation, np.transpose(refPoints)))

    newCenters = newCenters[:, :3] / newCenters[:, 3:4]
    newRefPoints = newRefPoints[:, :3] / newRefPoints[:, 3:4]

    planeNormals = newRefPoints - newCenters
    planesD = -np.sum(newCenters * planeNormals, axis=1, keepdims=True)
    newPlanes = -planeNormals * planesD
    return newPlanes


def softmax(values):
    exp = np.exp(values - values.max())
    return exp / exp.sum(-1, keepdims=True)


def one_hot(values, depth):
    maxInds = values.reshape(-1)
    results = np.zeros([maxInds.shape[0], depth])
    results[np.arange(maxInds.shape[0]), maxInds] = 1
    results = results.reshape(list(values.shape) + [depth])
    return results


def sigmoid(values):
    return 1 / (1 + np.exp(-values))


def normalize(values):
    return values / np.maximum(np.linalg.norm(values, axis=-1, keepdims=True), 1e-4)


def sortSegmentations(segmentations, planes, planesTarget):
    diff = np.linalg.norm(np.expand_dims(planes, 1) -
                          np.expand_dims(planesTarget, 0), axis=2)
    planeMap = one_hot(np.argmin(diff, axis=-1), depth=diff.shape[-1])
    # print(planeMap)
    segmentationsTarget = np.matmul(segmentations, planeMap)
    return segmentationsTarget, np.matmul(planes.transpose(), planeMap).transpose()


def refitPlanes(planes, segmentation, depth, info, numOutputPlanes=20, planeAreaThreshold=6*8):
    camera = getCameraFromInfo(info)
    width = depth.shape[1]
    height = depth.shape[0]

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    XYZ = np.stack([X, Y, Z], axis=2)

    validDepthMask = depth > 1e-4

    newPlaneInfo = []
    for planeIndex in range(numOutputPlanes):
        mask = segmentation == planeIndex
        points = XYZ[np.logical_and(cv2.erode(mask.astype(
            np.float32), np.ones((3, 3))) > 0.5, validDepthMask)]
        if points.shape[0] >= 3:
            try:
                plane = fitPlane(points)
                plane /= pow(np.linalg.norm(plane), 2)
                newPlaneInfo.append((plane, mask, points.shape[0]))
                #newPlaneInfo.append((planes[planeIndex], mask, points.shape[0]))
            except:
                pass
            pass
        continue

    newPlaneInfo = sorted(newPlaneInfo, key=lambda x: -x[2])

    newPlanes = []
    newSegmentation = np.ones(
        segmentation.shape, dtype=np.uint8) * numOutputPlanes
    for planeIndex, planeInfo in enumerate(newPlaneInfo):
        newPlanes.append(planeInfo[0])
        newSegmentation[planeInfo[1]] = planeIndex
        continue

    numPlanes = len(newPlaneInfo)
    if numPlanes == 0:
        return np.zeros((numOutputPlanes, 3)), newSegmentation, numPlanes

    newPlanes = np.array(newPlanes)
    if numPlanes < numOutputPlanes:
        newPlanes = np.concatenate(
            [newPlanes, np.zeros((numOutputPlanes - numPlanes, 3))], axis=0)
        pass

    return newPlanes, newSegmentation, numPlanes

# def filterPlanesPred(planes, segmentations, depth, info, segmentationsTarget, numOutputPlanes=20, nonPlaneRatioThreshold=0.7, coveredPlaneRatioThreshold=0.5, planeDistanceThreshold=0.05, planeAngleThreshold=np.cos(np.deg2rad(20))):

#     camera = getCameraFromInfo(info)
#     width = depth.shape[1]
#     height = depth.shape[0]

#     #camera = getNYURGBDCamera()
#     #camera = getSUNCGCamera()

#     urange = (np.arange(width, dtype=np.float32) / width * camera['width'] - camera['cx']) / camera['fx']
#     urange = urange.reshape(1, -1).repeat(height, 0)
#     vrange = (np.arange(height, dtype=np.float32) / height * camera['height'] - camera['cy']) / camera['fy']
#     vrange = vrange.reshape(-1, 1).repeat(width, 1)
#     X = depth * urange
#     Y = depth
#     Z = -depth * vrange

#     XYZ = np.stack([X, Y, Z], axis=2)

#     validDepthMask = depth > 1e-4

#     #numPlanes = planes.shape[0]
#     validPlaneInfo = []
#     emptyMaskTarget = segmentationsTarget[:, :, numOutputPlanes]
#     emptyMask = segmentations[:, :, numOutputPlanes]
#     for planeIndex in xrange(numOutputPlanes):
#         mask = segmentations[:, :, planeIndex]
#         if (emptyMaskTarget * mask).sum() < mask.sum() * nonPlaneRatioThreshold:
#             points = XYZ[np.logical_and(cv2.erode(mask, np.ones((3, 3))) > 0.5, validDepthMask)]
#             if points.shape[0] >= 3:
#                 try:
#                     plane = fitPlane(points)
#                     plane /= pow(np.linalg.norm(plane), 2)
#                     validPlaneInfo.append((plane, mask, points))
#                 except:
#                     emptyMask += mask
#                 pass
#             else:
#                 emptyMask += mask
#         else:
#             emptyMask += mask
#             pass
#         continue

#     #validPlaneInfo = sorted(validPlaneInfo, key=lambda x:-x[2])

#     for planeIndex, planeInfo in enumerate(validPlaneInfo):
#         cv2.imwrite('test/mask_' + str(planeIndex) + '.png', drawMaskImage(planeInfo[1]))
#         print(planeIndex, planeInfo[0])
#         continue

#     emptyMask = (emptyMask > 0.5).astype(np.float32)
#     for planeIndexTarget in xrange(numOutputPlanes):
#         maskTarget = segmentationsTarget[:, :, planeIndexTarget]
#         excludedMask = ((maskTarget + emptyMask) > 0.5).astype(np.float32)
#         coveredPlanes = []
#         for planeIndex, planeInfo in enumerate(validPlaneInfo):
#             mask = planeInfo[1]
#             area = mask.sum()
#             if (maskTarget * mask).sum() / area > coveredPlaneRatioThreshold:
#                 coveredPlanes.append((planeIndex, planeInfo[0], planeInfo[2]))
#                 pass
#             continue
#         if len(coveredPlanes) <= 1:
#             continue

#         coveredPlanes = sorted(coveredPlanes, key=lambda x:-x[2].shape[0])


#         majorPlane = coveredPlanes[0][1]
#         majorPlaneD = np.linalg.norm(majorPlane)
#         majorPlaneNormal = majorPlane / majorPlaneD
#         mergedPlanes = [coveredPlanes[0][0], ]
#         for planeInfo in coveredPlanes[1:]:
#             #if np.linalg.norm(planeInfo[1] - majorPlane) < planeDistanceThreshold:
#             distance = np.abs(np.sum(planeInfo[2] * majorPlaneNormal, axis=-1) - majorPlaneD)
#             print(distance.mean())
#             print(distance.max())
#             planeNormal = planeInfo[1] / np.linalg.norm(planeInfo[1])
#             print(np.sum(planeNormal * majorPlaneNormal), planeAngleThreshold)
#             exit(1)
#             if distance.mean() < planeDistanceThreshold and np.sum(planeNormal * majorPlaneNormal) > planeAngleThreshold:
#                 mergedPlanes.append(planeInfo[0])
#                 pass
#             continue
#         if mergedPlanes <= 1:
#             continue
#         newValidPlaneInfo = []
#         mergedPlaneMask = np.zeros(emptyMask.shape)
#         for planeIndex, planeInfo in enumerate(validPlaneInfo):
#             if planeIndex not in mergedPlanes:
#                 if (excludedMask * planeInfo[1]).sum() < planeInfo[1].sum() * nonPlaneRatioThreshold:
#                     newValidPlaneInfo.append(planeInfo)
#                     pass
#             else:
#                 mergedPlaneMask += planeInfo[1]
#                 pass
#             continue
#         cv2.erode(mergedPlaneMask, np.ones((3, 3)))
#         mergedPlaneMask = mergedPlaneMask > 0.5
#         points = XYZ[np.logical_and(mergedPlaneMask, validDepthMask)]
#         if points.shape[0] >= 3:
#             try:
#                 mergedPlane = fitPlane(points)
#                 mergedPlane = mergedPlane / pow(np.linalg.norm(mergedPlane), 2)
#                 newValidPlaneInfo.append((mergedPlane, mergedPlaneMask.astype(np.float32), points))
#             except:
#                 pass
#             pass
#         validPlaneInfo = newValidPlaneInfo
#         continue

#     validPlaneInfo = sorted(validPlaneInfo, key=lambda x: -x[1].sum())

#     newPlanes = []
#     newSegmentation = np.ones(emptyMask.shape) * numOutputPlanes
#     for planeIndex, planeInfo in enumerate(validPlaneInfo):
#         newPlanes.append(planeInfo[0])
#         newSegmentation[planeInfo[1].astype(np.bool)] = planeIndex
#         continue
#     numPlanes = len(newPlanes)
#     if numPlanes == 0:
#         return np.zeros((numOutputPlanes, 3)), newSegmentation, numPlanes

#     newPlanes = np.array(newPlanes)
#     if numPlanes < numOutputPlanes:
#         newPlanes = np.concatenate([newPlanes, np.zeros((numOutputPlanes - numPlanes, 3))], axis=0)
#         pass

#     return newPlanes, newSegmentation.astype(np.uint8), numPlanes

def filterPlanes(planes, segmentations, depth, info, numOutputPlanes=20, coveredPlaneRatioThreshold=0.5, planeDistanceThreshold=0.05, normalDotThreshold=np.cos(np.deg2rad(20)), planeFittingThreshold=0.03):

    camera = getCameraFromInfo(info)
    width = depth.shape[1]
    height = depth.shape[0]

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    XYZ = np.stack([X, Y, Z], axis=2)

    validDepthMask = depth > 1e-4

    #numPlanes = planes.shape[0]
    validPlaneInfo = []
    for planeIndex in range(numOutputPlanes):
        mask = segmentations[:, :, planeIndex]
        points = XYZ[np.logical_and(
            cv2.erode(mask, np.ones((3, 3)), 2) > 0.5, validDepthMask)]
        if points.shape[0] >= 3:
            try:
                plane = fitPlane(points)
                plane /= pow(np.linalg.norm(plane), 2)
                #plane = planes[planeIndex]

                #planeD = np.linalg.norm(plane)
                #diff = np.abs(np.sum(points * (plane / planeD), axis=-1) - planeD).mean()
                #validMask = np.abs(np.sum(points * (plane / planeD), axis=-1) - planeD) < planeDistanceThreshold

                #diff = (np.abs((np.sum(points * plane, axis=-1) - 1) / np.linalg.norm(plane)) > 0.05).astype(np.float32).mean()

                #print(planeIndex, diff, mask.sum())
                #cv2.imwrite('test/mask_' + str(planeIndex) + '.png', drawMaskImage(mask))
                # if diff < planeFittingThreshold:
                validPlaneInfo.append((plane, mask, points))
                #    pass
            except:
                pass
            pass
        continue

    #validPlaneInfo = sorted(validPlaneInfo, key=lambda x:-x[2])

    validPlaneInfo = sorted(validPlaneInfo, key=lambda x: -x[2].shape[0])

    if False:
        for planeIndex, planeInfo in enumerate(validPlaneInfo):
            cv2.imwrite('test/mask_' + str(planeIndex) +
                        '.png', drawMaskImage(planeInfo[1]))
            print((planeIndex, planeInfo[0], planeInfo[3], planeInfo[1].sum()))
            continue
        pass

    newPlaneInfo = []
    usedPlaneMask = np.zeros(len(validPlaneInfo), dtype=np.bool)
    for majorPlaneIndex, majorPlaneInfo in enumerate(validPlaneInfo):
        if usedPlaneMask[majorPlaneIndex]:
            continue
        usedPlaneMask[majorPlaneIndex] = True

        majorPlane = majorPlaneInfo[0]
        majorPlaneD = np.linalg.norm(majorPlane)
        majorPlaneNormal = majorPlane / majorPlaneD

        mergedPlaneMask = majorPlaneInfo[1].copy()
        planeMerged = False
        for planeIndex, planeInfo in enumerate(validPlaneInfo):
            if planeIndex <= majorPlaneIndex or usedPlaneMask[planeIndex]:
                continue

            fittingDiff = np.abs(
                np.sum(planeInfo[2] * majorPlaneNormal, axis=-1) - majorPlaneD)
            planeNormal = planeInfo[0] / np.linalg.norm(planeInfo[0])
            normalDot = np.sum(planeNormal * majorPlaneNormal)

            #print(majorPlaneIndex, planeIndex)
            #print(majorPlane, planeInfo[0])
            #print(fittingDiff.mean(), (fittingDiff < 0.05).astype(np.float32).mean(), normalDot, normalDotThreshold)

            if fittingDiff.mean() < planeDistanceThreshold and normalDot > normalDotThreshold:
                #print('merge', majorPlaneIndex, planeIndex)
                mergedPlaneMask += planeInfo[1]
                usedPlaneMask[planeIndex] = True
                planeMerged = True
                pass
            continue

        if planeMerged:
            mergedPlaneMask = (mergedPlaneMask > 0.5).astype(np.float32)
            pass

        newPlaneInfo.append((majorPlaneInfo[0], mergedPlaneMask))
        continue

    newPlaneInfo = sorted(newPlaneInfo, key=lambda x: -x[1].sum())

    newPlanes = []
    newSegmentation = np.ones(
        (height, width), dtype=np.uint8) * numOutputPlanes
    for planeIndex, planeInfo in enumerate(newPlaneInfo):
        area = planeInfo[1].sum()
        xs = planeInfo[1].max(0).nonzero()[0]
        ys = planeInfo[1].max(1).nonzero()[0]
        length = np.sqrt(pow(xs.max() - xs.min() + 1, 2) +
                         pow(ys.max() - ys.min() + 1, 2))
        if area < (width * height / 100.) or area / length < 10:
            continue
        newSegmentation[planeInfo[1].astype(np.bool)] = len(newPlanes)
        newPlanes.append(planeInfo[0])
        continue
    numPlanes = len(newPlanes)
    if numPlanes == 0:
        return np.zeros((numOutputPlanes, 3)), newSegmentation, numPlanes

    newPlanes = np.array(newPlanes)
    if numPlanes < numOutputPlanes:
        newPlanes = np.concatenate(
            [newPlanes, np.zeros((numOutputPlanes - numPlanes, 3))], axis=0)
        pass

    return newPlanes, newSegmentation, numPlanes


def getSegmentationsTRWS(planes, image, depth, normal, semantics, info, useSemantics=False, numPlanes=20, numProposals=3):
    from pystruct.inference import get_installed, inference_ogm, inference_dispatch

    numOutputPlanes = planes.shape[0]
    height = depth.shape[0]
    width = depth.shape[1]

    camera = getCameraFromInfo(info)
    urange = (np.arange(width, dtype=np.float32) / (width) *
              (camera['width']) - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / (height) *
              (camera['height']) - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)

    X = depth * urange
    Y = depth
    Z = -depth * vrange
    points = np.stack([X, Y, Z], axis=2)

    planes = planes[:numPlanes]
    planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    planeNormals = planes / np.maximum(planesD, 1e-4)

    distanceCostThreshold = 0.05
    distanceCost = np.abs(np.tensordot(points, planeNormals, axes=(
        [2, 1])) - np.reshape(planesD, [1, 1, -1])) / distanceCostThreshold
    distanceCost = np.concatenate(
        [distanceCost, np.ones((height, width, 1))], axis=2)
    #cv2.imwrite('test/mask.png', drawMaskImage(np.minimum(distanceCost[:, :, 2] /  5, 1)))
    #distanceCost[:, :, numPlanes:numOutputPlanes] = 10000
    normalCostThreshold = 1 - np.cos(np.deg2rad(30))
    normalCost = (1 - np.tensordot(normal, planeNormals,
                                   axes=([2, 1]))) / normalCostThreshold
    #normalCost[:, :, numPlanes:] = 10000
    normalCost = np.concatenate(
        [normalCost, np.ones((height, width, 1))], axis=2)

    unaryCost = distanceCost

    if useSemantics:
        planeMasks = []
        for planeIndex in range(numPlanes):
            #print(np.bincount(semantics[segmentation == planeIndex]))
            planeMaskOri = segmentation == planeIndex
            semantic = np.bincount(semantics[planeMaskOri]).argmax()
            # print(semantic)
            planeMask = cv2.dilate((np.logical_and(np.logical_or(semantics == semantic, planeMaskOri), distanceCost[:, :, planeIndex])).astype(
                np.uint8), np.ones((3, 3), dtype=np.uint8)).astype(np.float32)
            planeMasks.append(planeMask)
            #cv2.imwrite('test/mask_' + str(planeIndex) + '.png', drawMaskImage(segmentation == planeIndex))
            #cv2.imwrite('test/mask_2.png', drawMaskImage(semantics == semantic))
            continue
        planeMasks = np.stack(planeMasks, 2)
        unaryCost += (1 - planeMasks) * 10000
        pass

    unaryCost = np.concatenate(
        [unaryCost, np.ones((height, width, 1))], axis=2)

    proposals = np.argpartition(unaryCost, numProposals)[:, :, :numProposals]
    unaries = -readProposalInfo(unaryCost,
                                proposals).reshape((-1, numProposals))

    # refined_segmentation = np.argmax(unaries, axis=1)
    # refined_segmentation = refined_segmentation.reshape([height, width, 1])
    # refined_segmentation = readProposalInfo(proposals, refined_segmentation)
    # refined_segmentation = refined_segmentation.reshape([height, width])
    # refined_segmentation[refined_segmentation == numPlanes] = numOutputPlanes

    proposals = proposals.reshape((-1, numProposals))
    #cv2.imwrite('test/segmentation.png', drawSegmentationImage(unaries.reshape((height, width, -1)), blackIndex=numOutputPlanes))

    nodes = np.arange(height * width).reshape((height, width))

    image = image.astype(np.float32)
    colors = image.reshape((-1, 3))
    deltas = [(0, 1), (1, 0), (-1, 1), (1, 1)]
    intensityDifferenceSum = 0.0
    intensityDifferenceCount = 0
    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        intensityDifferenceSum += np.sum(
            pow(colors[partial_nodes] - colors[partial_nodes + (deltaY * width + deltaX)], 2))
        intensityDifferenceCount += partial_nodes.shape[0]
        continue
    intensityDifference = intensityDifferenceSum / intensityDifferenceCount

    edges = []
    edges_features = []

    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        edges.append(
            np.stack([partial_nodes, partial_nodes + (deltaY * width + deltaX)], axis=1))

        labelDiff = (np.expand_dims(proposals[partial_nodes], -1) != np.expand_dims(
            proposals[partial_nodes + (deltaY * width + deltaX)], 1)).astype(np.float32)
        colorDiff = np.sum(pow(
            colors[partial_nodes] - colors[partial_nodes + (deltaY * width + deltaX)], 2), axis=1)
        pairwise_cost = labelDiff * \
            np.reshape(1 + 45 * np.exp(-colorDiff /
                                       intensityDifference), [-1, 1, 1])
        #pairwise_cost = np.expand_dims(pairwise_matrix, 0) * np.ones(np.reshape(1 + 45 * np.exp(-colorDiff / np.maximum(intensityDifference[partial_nodes], 1e-4)), [-1, 1, 1]).shape)
        edges_features.append(-pairwise_cost)
        continue

    edges = np.concatenate(edges, axis=0)
    edges_features = np.concatenate(edges_features, axis=0)

    refined_segmentation = inference_ogm(
        unaries * 10, edges_features, edges, return_energy=False, alg='trw')
    # print(pairwise_matrix)
    #refined_segmentation = inference_ogm(unaries * 5, -pairwise_matrix, edges, return_energy=False, alg='alphaexp')
    refined_segmentation = refined_segmentation.reshape([height, width, 1])
    refined_segmentation = readProposalInfo(proposals, refined_segmentation)
    refined_segmentation = refined_segmentation.reshape([height, width])
    refined_segmentation[refined_segmentation == numPlanes] = numOutputPlanes
    return refined_segmentation


def getSegmentationsGraphCut(planes, image, depth, normal, semantics, info, parameters={}):

    height = depth.shape[0]
    width = depth.shape[1]

    # planeMap = []
    # planeMasks = []
    # for planeIndex in xrange(numPlanes):
    #     planeMask = segmentation == planeIndex
    #     if planeMask.sum() < 6 * 8:
    #         continue
    #     planeMap.append(planeIndex)
    #     semantic = np.bincount(semantics[planeMask]).argmax()
    #     for _ in xrange(2):
    #         planeMask = cv2.dilate(planeMask.astype(np.float32), np.ones((3, 3), dtype=np.float32))
    #         continue
    #     planeMask = np.logical_and(np.logical_or(semantics == semantic, semantics == 0), planeMask).astype(np.float32)
    #     for _ in xrange(1):
    #         planeMask = cv2.dilate(planeMask, np.ones((3, 3), dtype=np.float32))
    #         continue
    #     planeMasks.append(planeMask)
    #     continue
    # planeMap = one_hot(np.array(planeMap), depth=planes.shape[0])
    #planes = np.matmul(planeMap, planes)
    #planeMasks = np.stack(planeMasks, 2).reshape((-1, numPlanes))

    numPlanes = planes.shape[0]

    # if numPlanes < numOutputPlanes:
    #planeMasks = np.concatenate([planeMasks, np.zeros((height, width, numOutputPlanes - numPlanes))], axis=2)
    # pass

    # print(info)
    camera = getCameraFromInfo(info)
    urange = (np.arange(width, dtype=np.float32) / (width) *
              (camera['width']) - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / (height) *
              (camera['height']) - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)

    X = depth * urange
    Y = depth
    Z = -depth * vrange

    points = np.stack([X, Y, Z], axis=2)
    planes = planes[:numPlanes]
    planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    planeNormals = planes / np.maximum(planesD, 1e-4)

    if 'distanceCostThreshold' in parameters:
        distanceCostThreshold = parameters['distanceCostThreshold']
    else:
        distanceCostThreshold = 0.05
        pass

    #distanceCost = 1 - np.exp(-np.abs(np.tensordot(points, planeNormals, axes=([2, 1])) - np.reshape(planesD, [1, 1, -1])) / distanceCostThreshold)
    #distanceCost = np.concatenate([distanceCost, np.ones((height, width, 1)) * (1 - np.exp(-1))], axis=2)
    distanceCost = np.abs(np.tensordot(points, planeNormals, axes=(
        [2, 1])) - np.reshape(planesD, [1, 1, -1])) / distanceCostThreshold
    distanceCost = np.concatenate(
        [distanceCost, np.ones((height, width, 1))], axis=2)
    #cv2.imwrite('test/mask.png', drawMaskImage(np.minimum(distanceCost[:, :, 2] /  5, 1)))
    #distanceCost[:, :, numPlanes:numOutputPlanes] = 10000

    normalCostThreshold = 1 - np.cos(np.deg2rad(30))
    normalCost = (1 - np.abs(np.tensordot(normal, planeNormals,
                                          axes=([2, 1])))) / normalCostThreshold
    #normalCost[:, :, numPlanes:] = 10000
    normalCost = np.concatenate(
        [normalCost, np.ones((height, width, 1))], axis=2)

    unaryCost = distanceCost + normalCost
    unaryCost *= np.expand_dims((depth > 1e-4).astype(np.float32), -1)
    unaries = -unaryCost.reshape((-1, numPlanes + 1))

    cv2.imwrite('test/distance_cost.png', drawSegmentationImage(-distanceCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))
    cv2.imwrite('test/normal_cost.png', drawSegmentationImage(-normalCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))
    cv2.imwrite('test/unary_cost.png', drawSegmentationImage(-unaryCost.reshape(
        (height, width, -1)), blackIndex=unaryCost.shape[-1] - 1))

    #unaries[:, :numPlanes] -= (1 - planeMasks) * 10000

    # print(planes)
    # print(distanceCost[150][200])
    # print(unaryCost[150][200])
    # print(np.argmax(-unaryCost[60][150]))

    #cv2.imwrite('test/depth.png', drawDepthImage(depth))
    cv2.imwrite('test/segmentation.png', drawSegmentationImage(
        unaries.reshape((height, width, -1)), blackIndex=numPlanes))
    #cv2.imwrite('test/mask.png', drawSegmentationImage(planeMasks.reshape((height, width, -1))))
    # exit(1)

    nodes = np.arange(height * width).reshape((height, width))

    image = image.astype(np.float32)
    colors = image.reshape((-1, 3))

    deltas = [(0, 1), (1, 0), (-1, 1), (1, 1)]

    intensityDifferenceSum = 0.0
    intensityDifferenceCount = 0
    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        intensityDifferenceSum += np.sum(
            pow(colors[partial_nodes] - colors[partial_nodes + (deltaY * width + deltaX)], 2))
        intensityDifferenceCount += partial_nodes.shape[0]
        continue
    intensityDifference = intensityDifferenceSum / intensityDifferenceCount

    edges = []
    edges_features = []
    pairwise_matrix = 1 - np.diag(np.ones(numPlanes + 1))

    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        edges.append(
            np.stack([partial_nodes, partial_nodes + (deltaY * width + deltaX)], axis=1))

        colorDiff = np.sum(pow(
            colors[partial_nodes] - colors[partial_nodes + (deltaY * width + deltaX)], 2), axis=1)

        pairwise_cost = np.expand_dims(pairwise_matrix, 0) * np.reshape(
            1 + 45 * np.exp(-colorDiff / intensityDifference), [-1, 1, 1])
        #pairwise_cost = np.expand_dims(pairwise_matrix, 0) * np.ones(np.reshape(1 + 45 * np.exp(-colorDiff / np.maximum(intensityDifference[partial_nodes], 1e-4)), [-1, 1, 1]).shape)
        edges_features.append(pairwise_cost)
        continue

    edges = np.concatenate(edges, axis=0)
    edges_features = np.concatenate(edges_features, axis=0)

    if 'smoothnessWeight' in parameters:
        smoothnessWeight = parameters['smoothnessWeight']
    else:
        smoothnessWeight = 0.02
        pass

    refined_segmentation = inference_ogm(
        unaries, -edges_features * smoothnessWeight, edges, return_energy=False, alg='alphaexp')
    # print(pairwise_matrix)
    #refined_segmentation = inference_ogm(unaries * 5, -pairwise_matrix, edges, return_energy=False, alg='alphaexp')
    refined_segmentation = refined_segmentation.reshape([height, width])

    if 'semantics' in parameters and parameters['semantics']:
        for semanticIndex in range(semantics.max() + 1):
            mask = semantics == semanticIndex
            segmentInds = refined_segmentation[mask]
            uniqueSegments, counts = np.unique(segmentInds, return_counts=True)
            for index, count in enumerate(counts):
                if count > segmentInds.shape[0] * 0.9:
                    refined_segmentation[mask] = uniqueSegments[index]
                    pass
                continue
            continue
        pass

    return refined_segmentation


def calcNormal(depth, info):

    height = depth.shape[0]
    width = depth.shape[1]

    camera = getCameraFromInfo(info)
    urange = (np.arange(width, dtype=np.float32) / (width) *
              (camera['width']) - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / (height) *
              (camera['height']) - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)

    X = depth * urange
    Y = depth
    Z = -depth * vrange

    points = np.stack([X, Y, Z], axis=2).reshape(-1, 3)

    if width > 300:
        grids = np.array([-9, -6, -3, -1, 0, 1, 3, 6, 9])
    else:
        grids = np.array([-5, -3, -1, 0, 1, 3, 5])

    normals = []
    for index in range(width * height):
        us = index % width + grids
        us = us[np.logical_and(us >= 0, us < width)]
        vs = index / width + grids
        vs = vs[np.logical_and(vs >= 0, vs < height)]
        indices = (np.expand_dims(vs, -1) * width +
                   np.expand_dims(us, 0)).reshape(-1)
        planePoints = points[indices]
        planePoints = planePoints[np.linalg.norm(planePoints, axis=-1) > 1e-4]

        planePoints = planePoints[np.abs(
            planePoints[:, 1] - points[index][1]) < 0.05]
        # if index == 53 * width + 183 or index == 58 * width + 183:
        #     print(np.stack([indices % width, indices / width], axis=-1))
        #     print(index)
        #     print(planePoints)
        #     print(planePoints.shape)
        #     plane = fitPlane(planePoints)
        #     print(plane)
        #     print(plane / np.maximum(np.linalg.norm(plane), 1e-4))
        #     pass

        try:
            plane = fitPlane(planePoints)
            normals.append(-plane / np.maximum(np.linalg.norm(plane), 1e-4))
        except:
            if len(normals) > 0:
                normals.append(normals[-1])
            else:
                normals.append([0, -1, 0])
                pass
            pass
        continue
    normal = np.array(normals).reshape((height, width, 3))
    return normal


def readProposalInfo(info, proposals):
    numProposals = proposals.shape[-1]
    outputShape = list(info.shape)
    outputShape[-1] = numProposals
    info = info.reshape([-1, info.shape[-1]])
    proposals = proposals.reshape([-1, proposals.shape[-1]])
    proposalInfo = []

    for proposal in range(numProposals):
        proposalInfo.append(
            info[np.arange(info.shape[0]), proposals[:, proposal]])
        continue
    proposalInfo = np.stack(proposalInfo, axis=1).reshape(outputShape)
    return proposalInfo


def fitPlanesManhattan(image, depth, normal, info, numOutputPlanes=20, imageIndex=1, parameters={}):
    if 'meanshift' in parameters and parameters['meanshift'] > 0:
        import sklearn.cluster
        meanshift = sklearn.cluster.MeanShift(parameters['meanshift'])
        pass

    height = depth.shape[0]
    width = depth.shape[1]

    camera = getCameraFromInfo(info)
    urange = (np.arange(width, dtype=np.float32) / (width) *
              (camera['width']) - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / (height) *
              (camera['height']) - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)

    X = depth * urange
    Y = depth
    Z = -depth * vrange

    normals = normal.reshape((-1, 3))
    normals = normals / \
        np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-4)

    validMask = np.logical_and(np.linalg.norm(
        normals, axis=-1) > 1e-4, depth.reshape(-1) > 1e-4)

    valid_normals = normals[validMask]

    points = np.stack([X, Y, Z], axis=2).reshape(-1, 3)
    valid_points = points[validMask]

    polarAngles = np.arange(16) * np.pi / 2 / 16
    azimuthalAngles = np.arange(64) * np.pi * 2 / 64
    polarAngles = np.expand_dims(polarAngles, -1)
    azimuthalAngles = np.expand_dims(azimuthalAngles, 0)

    normalBins = np.stack([np.sin(polarAngles) * np.cos(azimuthalAngles), np.tile(np.cos(polarAngles), [
                          1, azimuthalAngles.shape[1]]), -np.sin(polarAngles) * np.sin(azimuthalAngles)], axis=2)
    normalBins = np.reshape(normalBins, [-1, 3])
    numBins = normalBins.shape[0]

    normalDiff = np.tensordot(valid_normals, normalBins, axes=([1], [1]))
    normalDiffSign = np.sign(normalDiff)
    normalDiff = np.maximum(normalDiff, -normalDiff)
    normalMask = one_hot(np.argmax(normalDiff, axis=-1), numBins)
    bins = normalMask.sum(0)
    np.expand_dims(valid_normals, 1) * np.expand_dims(normalMask, -1)

    maxNormals = np.expand_dims(valid_normals, 1) * \
        np.expand_dims(normalMask, -1)
    maxNormals *= np.expand_dims(normalDiffSign, -1)
    averageNormals = maxNormals.sum(
        0) / np.maximum(np.expand_dims(bins, -1), 1e-4)
    averageNormals /= np.maximum(np.linalg.norm(averageNormals,
                                                axis=-1, keepdims=True), 1e-4)
    # print(bins.nonzero())
    dominantNormal_1 = averageNormals[np.argmax(bins)]

    dotThreshold_1 = np.cos(np.deg2rad(100))
    dotThreshold_2 = np.cos(np.deg2rad(80))

    dot_1 = np.tensordot(normalBins, dominantNormal_1, axes=([1], [0]))
    bins[np.logical_or(dot_1 < dotThreshold_1, dot_1 > dotThreshold_2)] = 0
    dominantNormal_2 = averageNormals[np.argmax(bins)]
    # print(normalBins[np.argmax(bins)])
    # print(dominantNormal_2)
    # exit(1)
    dot_2 = np.tensordot(normalBins, dominantNormal_2, axes=([1], [0]))
    bins[np.logical_or(dot_2 < dotThreshold_1, dot_2 > dotThreshold_2)] = 0

    dominantNormal_3 = averageNormals[np.argmax(bins)]

    dominantNormals = np.stack(
        [dominantNormal_1, dominantNormal_2, dominantNormal_3], axis=0)

    dominantNormalImage = np.abs(
        np.matmul(normal, dominantNormals.transpose()))
    cv2.imwrite('test/dominant_normal.png', drawMaskImage(dominantNormalImage))

    planeHypothesisAreaThreshold = width * height * 0.01

    planes = []

    if 'offsetGap' in parameters:
        offsetGap = parameters['offsetGap']
    else:
        offsetGap = 0.1
        pass
    for dominantNormal in dominantNormals:
        offsets = np.tensordot(valid_points, dominantNormal, axes=([1], [0]))
        #offsets = np.sort(offsets)

        if 'meanshift' in parameters and parameters['meanshift'] > 0:
            sampleInds = np.arange(offsets.shape[0])
            np.random.shuffle(sampleInds)
            meanshift.fit(np.expand_dims(
                offsets[sampleInds[:int(offsets.shape[0] * 0.02)]], -1))
            for offset in meanshift.cluster_centers_:
                planes.append(dominantNormal * offset)
                continue

        #clusters = meanshift.fit_predict(offsets)
        # print(clusters.score_samples(offsets))
        # print(offsets)
        # print(np.argmax(offsets))
        # print(clusters.score_samples(np.array([[offsets.max()]])))
        # print(clusters.sample(10))
        # exit(1)
        # for clusterIndex in xrange(clusters.max()):
        #     clusterMask = clusters == clusterIndex
        #     print(clusterMask.sum())
        #     if clusterMask.sum() < planeHypothesisAreaThreshold:
        #         continue
        #     planeD = offsets[clusterMask].mean()
        #     planes.append(dominantNormal * planeD)
        #     continue

        offset = offsets.min()
        maxOffset = offsets.max()
        while offset < maxOffset:
            planeMask = np.logical_and(
                offsets >= offset, offsets < offset + offsetGap)
            segmentOffsets = offsets[np.logical_and(
                offsets >= offset, offsets < offset + offsetGap)]
            if segmentOffsets.shape[0] < planeHypothesisAreaThreshold:
                offset += offsetGap
                continue
            planeD = segmentOffsets.mean()
            planes.append(dominantNormal * planeD)
            offset = planeD + offsetGap
            #print(planeD, segmentOffsets.shape[0])
            #cv2.imwrite('test/mask_' + str(len(planes) - 1) + '.png', drawMaskImage(planeMask.reshape((height, width))))
            continue
        continue

    if len(planes) == 0:
        return np.array([]), np.zeros(segmentation.shape).astype(np.int32)

    planes = np.array(planes)
    print(('number of planes ', planes.shape[0]))

    # transformedDominantNormals = np.matmul(info[:16].reshape(4, 4), np.transpose([np.concatenate(dominantNormals, np.ones((3, 1))], axis=1)))
    vanishingPoints = np.stack([dominantNormals[:, 0] / np.maximum(dominantNormals[:, 1], 1e-4) * info[0] +
                                info[2], -dominantNormals[:, 2] / np.maximum(dominantNormals[:, 1], 1e-4) * info[5] + info[6]], axis=1)
    vanishingPoints[:, 0] *= width / info[16]
    vanishingPoints[:, 1] *= height / info[17]

    # print(dominantNormals)
    # print(vanishingPoints)
    #us = np.tile(np.expand_dims(np.arange(width), 0), [height, 1])
    #vs = np.tile(np.expand_dims(np.arange(height), -1), [1, width])
    indices = np.arange(width * height, dtype=np.int32)
    uv = np.stack([indices % width, indices / width], axis=1)
    colors = image.reshape((-1, 3))
    windowW = 9
    windowH = 3
    dominantLineMaps = []
    for vanishingPointIndex, vanishingPoint in enumerate(vanishingPoints):
        horizontalDirection = uv - np.expand_dims(vanishingPoint, 0)
        horizontalDirection = horizontalDirection / \
            np.maximum(np.linalg.norm(horizontalDirection,
                                      axis=1, keepdims=True), 1e-4)
        verticalDirection = np.stack(
            [horizontalDirection[:, 1], -horizontalDirection[:, 0]], axis=1)

        colorDiffs = []
        for directionIndex, direction in enumerate([horizontalDirection, verticalDirection]):
            neighbors = uv + direction
            neighborsX = neighbors[:, 0]
            neighborsY = neighbors[:, 1]
            neighborsMinX = np.maximum(np.minimum(
                np.floor(neighborsX).astype(np.int32), width - 1), 0)
            neighborsMaxX = np.maximum(np.minimum(
                np.ceil(neighborsX).astype(np.int32), width - 1), 0)
            neighborsMinY = np.maximum(np.minimum(
                np.floor(neighborsY).astype(np.int32), height - 1), 0)
            neighborsMaxY = np.maximum(np.minimum(
                np.ceil(neighborsY).astype(np.int32), height - 1), 0)
            indices_1 = neighborsMinY * width + neighborsMinX
            indices_2 = neighborsMaxY * width + neighborsMinX
            indices_3 = neighborsMinY * width + neighborsMaxX
            indices_4 = neighborsMaxY * width + neighborsMaxX
            areas_1 = (neighborsMaxX - neighborsX) * \
                (neighborsMaxY - neighborsY)
            areas_2 = (neighborsMaxX - neighborsX) * \
                (neighborsY - neighborsMinY)
            areas_3 = (neighborsX - neighborsMinX) * \
                (neighborsMaxY - neighborsY)
            areas_4 = (neighborsX - neighborsMinX) * \
                (neighborsY - neighborsMinY)

            neighborsColor = colors[indices_1] * np.expand_dims(areas_1, -1) + colors[indices_2] * np.expand_dims(
                areas_2, -1) + colors[indices_3] * np.expand_dims(areas_3, -1) + colors[indices_4] * np.expand_dims(areas_4, -1)
            colorDiff = np.linalg.norm(neighborsColor - colors, axis=-1)

            #cv2.imwrite('test/color_diff_' + str(vanishingPointIndex) + '_' + str(directionIndex) + '.png', drawMaskImage(colorDiff.reshape((height, width)) / 100))
            colorDiffs.append(colorDiff)
            continue
        colorDiffs = np.stack(colorDiffs, 1)

        deltaUs, deltaVs = np.meshgrid(
            np.arange(windowW) - (windowW - 1) / 2, np.arange(windowH) - (windowH - 1) / 2)
        deltas = deltaUs.reshape((1, -1, 1)) * np.expand_dims(horizontalDirection, axis=1) + \
            deltaVs.reshape((1, -1, 1)) * \
            np.expand_dims(verticalDirection, axis=1)

        windowIndices = np.expand_dims(uv, 1) - deltas
        windowIndices = (np.minimum(np.maximum(np.round(windowIndices[:, :, 1]), 0), height - 1) * width + np.minimum(
            np.maximum(np.round(windowIndices[:, :, 0]), 0), width - 1)).astype(np.int32)

        dominantLineMap = []

        # index = 361 * width + 146
        # mask = np.zeros((height * width))
        # mask[windowIndices[index]] = 1
        # cv2.imwrite('test/mask.png', drawMaskImage(mask.reshape((height, width))))
        # exit(1)
        for pixels in windowIndices:
            gradientSums = colorDiffs[pixels].sum(0)
            dominantLineMap.append(
                gradientSums[1] / max(gradientSums[0], 1e-4))
            continue
        dominantLineMaps.append(
            np.array(dominantLineMap).reshape((height, width)))
        # dominantLines = []
        # for pixel in uv:
        #     sums = colorDiffs[:, max(pixel[1] - windowSize, 0):min(pixel[1] + windowSize + 1, height - 1), max(pixel[0] - windowSize, 0):min(pixel[0] + windowSize + 1, width - 1)].sum(1).sum(1)
        #     dominantLines.append(sums[1] / np.maximum(sums[0], 1e-4))
        #     continue
        # dominantLines = np.array(dominantLines).reshape((height, width))
        # smoothnessWeightMask = np.logical_or(smoothnessWeightMask, dominantLines > 5)

        #cv2.imwrite('test/dominant_lines_' + str(vanishingPointIndex) + '.png', drawMaskImage(dominantLines / 5))
        continue
    dominantLineMaps = np.stack(dominantLineMaps, axis=2)
    #cv2.imwrite('test/dominant_lines.png', drawMaskImage(dominantLineMaps / 5))
    if 'dominantLineThreshold' in parameters:
        dominantLineThreshold = parameters['dominantLineThreshold']
    else:
        dominantLineThreshold = 3
        pass

    if imageIndex >= 0:
        cv2.imwrite('test/' + str(imageIndex) + '_dominant_lines.png',
                    drawMaskImage(dominantLineMaps / dominantLineThreshold))
    else:
        cv2.imwrite('test/dominant_lines.png',
                    drawMaskImage(dominantLineMaps / dominantLineThreshold))
        pass

    smoothnessWeightMask = dominantLineMaps.max(2) > dominantLineThreshold
    cv2.imwrite('test/dominant_lines_mask.png',
                drawMaskImage(smoothnessWeightMask))

    planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    planeNormals = planes / np.maximum(planesD, 1e-4)

    if 'distanceCostThreshold' in parameters:
        distanceCostThreshold = parameters['distanceCostThreshold']
    else:
        distanceCostThreshold = 0.05
        pass

    distanceCost = np.abs(np.tensordot(points, planeNormals, axes=(
        [1, 1])) - np.reshape(planesD, [1, -1])) / distanceCostThreshold
    #distanceCost = np.concatenate([distanceCost, np.ones((height * width, 1))], axis=1)

    normalCost = 0
    normalCostThreshold = 1 - np.cos(np.deg2rad(30))
    normalCost = (1 - np.abs(np.tensordot(normals, planeNormals,
                                          axes=([1, 1])))) / normalCostThreshold

    unaryCost = distanceCost + normalCost
    unaryCost *= np.expand_dims(validMask.astype(np.float32), -1)
    unaries = unaryCost.reshape((width * height, -1))

    cv2.imwrite('test/distance_cost.png', drawSegmentationImage(-distanceCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))
    cv2.imwrite('test/normal_cost.png', drawSegmentationImage(-normalCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))
    cv2.imwrite('test/unary_cost.png', drawSegmentationImage(-unaryCost.reshape(
        (height, width, -1)), blackIndex=unaryCost.shape[-1] - 1))

    cv2.imwrite('test/segmentation.png', drawSegmentationImage(-unaries.reshape(
        (height, width, -1)), blackIndex=unaries.shape[-1]))

    #cv2.imwrite('test/mask.png', drawSegmentationImage(planeMasks.reshape((height, width, -1))))
    # exit(1)

    if 'numProposals' in parameters:
        numProposals = parameters['numProposals']
    else:
        numProposals = 3
        pass
    numProposals = min(numProposals, unaries.shape[-1] - 1)
    proposals = np.argpartition(unaries, numProposals)[:, :numProposals]
    proposals[np.logical_not(validMask)] = 0

    unaries = -readProposalInfo(unaries, proposals).reshape((-1, numProposals))

    nodes = np.arange(height * width).reshape((height, width))

    #deltas = [(0, 1), (1, 0), (-1, 1), (1, 1)]
    deltas = [(0, 1), (1, 0)]

    edges = []
    edges_features = []
    smoothnessWeights = 1 - 0.99 * smoothnessWeightMask.astype(np.float32)

    #edges_features = np.concatenate(edges_features, axis=0)
    # print(proposals.shape)
    # print(unaries.shape)
    #print(width * height)
    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        edges.append(
            np.stack([partial_nodes, partial_nodes + (deltaY * width + deltaX)], axis=1))

        labelDiff = (np.expand_dims(proposals[partial_nodes], -1) != np.expand_dims(
            proposals[partial_nodes + (deltaY * width + deltaX)], 1)).astype(np.float32)
        #labelDiff = labelDiff.transpose([0, 2, 1])
        # print(labelDiff.shape)
        edges_features.append(labelDiff * smoothnessWeights.reshape(
            (width * height, -1))[partial_nodes].reshape(-1, 1, 1))
        continue

    # exit(1)

    edges = np.concatenate(edges, axis=0)
    edges_features = np.concatenate(edges_features, axis=0)

    # y = 71
    # x = 145
    # print(proposals[y * width + x])
    # print(unaries[y * width + x] * 10000)
    # print(proposals[(y + 1) * width + x])
    # print(unaries[(y + 1) * width + x] * 10000)
    # print(edges_features[y * width + x])

    if 'smoothnessWeight' in parameters:
        smoothnessWeight = parameters['smoothnessWeight']
    else:
        smoothnessWeight = 40
        pass

    refined_segmentation = inference_ogm(
        unaries, -edges_features * smoothnessWeight, edges, return_energy=False, alg='trw')

    refined_segmentation = refined_segmentation.reshape([height, width, 1])
    refined_segmentation = readProposalInfo(proposals, refined_segmentation)
    # print(pairwise_matrix)
    #refined_segmentation = inference_ogm(unaries * 5, -pairwise_matrix, edges, return_energy=False, alg='alphaexp')
    planeSegmentation = refined_segmentation.reshape([height, width])

    planeSegmentation[np.logical_not(
        validMask.reshape((height, width)))] = planes.shape[0]

    cv2.imwrite('test/segmentation_refined.png',
                drawSegmentationImage(planeSegmentation))
    # exit(1)

    # if planes.shape[0] > numOutputPlanes:
    #     planeInfo = []
    #     for planeIndex in xrange(planes.shape[0]):
    #         mask = planeSegmentation == planeIndex
    #         planeInfo.append((planes[planeIndex], mask))
    #         continue
    #     planeInfo = sorted(planeInfo, key=lambda x: -x[1].sum())
    #     newPlanes = []
    #     newPlaneSegmentation = np.full(planeSegmentation.shape, numOutputPlanes)
    #     for planeIndex in xrange(numOutputPlanes):
    #         newPlanes.append(planeInfo[planeIndex][0])
    #         newPlaneSegmentation[planeInfo[planeIndex][1]] = planeIndex
    #         continue
    #     planeSegmentation = newPlaneSegmentation
    #     planes = np.array(newPlanes)
    # else:
    #     planeSegmentation[planeSegmentation == planes.shape[0]] = numOutputPlanes
    #     pass

    # if planes.shape[0] < numOutputPlanes:
    #     planes = np.concatenate([planes, np.zeros((numOutputPlanes - planes.shape[0], 3))], axis=0)
    #     pass

    # planeDepths = calcPlaneDepths(planes, width, height, info)

    # allDepths = np.concatenate([planeDepths, np.expand_dims(depth, -1)], axis=2)
    # depthPred = allDepths.reshape([height * width, planes.shape[0] + 1])[np.arange(width * height), planeSegmentation.astype(np.int32).reshape(-1)].reshape(height, width)

    # planeNormals = calcPlaneNormals(planes, width, height)
    # allNormals = np.concatenate([planeNormals, np.expand_dims(normal, 2)], axis=2)
    # normalPred = allNormals.reshape(-1, planes.shape[0] + 1, 3)[np.arange(width * height), planeSegmentation.reshape(-1)].reshape((height, width, 3))

    return planes, planeSegmentation


def calcVanishingPoint(lines):
    points = lines[:, :2]
    normals = lines[:, 2:4] - lines[:, :2]
    normals /= np.maximum(np.linalg.norm(normals,
                                         axis=-1, keepdims=True), 1e-4)
    normals = np.stack([normals[:, 1], -normals[:, 0]], axis=1)
    normalPointDot = (normals * points).sum(1)

    if lines.shape[0] == 2:
        VP = np.linalg.solve(normals, normalPointDot)
    else:
        VP = np.linalg.lstsq(normals, normalPointDot)[0]
        pass

    # print(lines)
    # print(points)
    # print(normals)
    # print(VP)
    # exit(1)
    return VP


def calcVanishingPoints(allLines, numVPs):
    distanceThreshold = np.sin(np.deg2rad(5))
    lines = allLines.copy()
    VPs = []
    VPLines = []
    for VPIndex in range(numVPs):
        points = lines[:, :2]
        lengths = np.linalg.norm(lines[:, 2:4] - lines[:, :2], axis=-1)
        normals = lines[:, 2:4] - lines[:, :2]
        normals /= np.maximum(np.linalg.norm(normals,
                                             axis=-1, keepdims=True), 1e-4)
        normals = np.stack([normals[:, 1], -normals[:, 0]], axis=1)
        maxNumInliers = 0
        bestVP = np.zeros(2)
        # for _ in xrange(int(np.sqrt(lines.shape[0]))):
        for _ in range(min(pow(lines.shape[0], 2), 100)):
            sampledInds = np.random.choice(lines.shape[0], 2)
            if sampledInds[0] == sampledInds[1]:
                continue
            sampledLines = lines[sampledInds]
            try:
                VP = calcVanishingPoint(sampledLines)
            except:
                continue

            inliers = np.abs(((np.expand_dims(VP, 0) - points) * normals).sum(-1)) / \
                np.linalg.norm(np.expand_dims(VP, 0) - points,
                               axis=-1) < distanceThreshold
            # print(sampledLines)
            # print(VP)
            # print(normals[inliers])
            # exit(1)

            #numInliers = inliers.sum()
            numInliers = lengths[inliers].sum()
            if numInliers > maxNumInliers:
                maxNumInliers = numInliers
                bestVP = VP
                bestVPInliers = inliers
                pass
            continue
        if maxNumInliers > 0:
            inlierLines = lines[bestVPInliers]
            VP = calcVanishingPoint(inlierLines)
            VPs.append(VP)
            # print(bestVP)
            # print(inlierLines)
            # print(VP)
            # exit(1)
            VPLines.append(inlierLines)
            lines = lines[np.logical_not(bestVPInliers)]
            pass
        continue
    VPs = np.stack(VPs, axis=0)
    return VPs, VPLines, lines


def fitPlanesPiecewise(image, depth, normal, info, numOutputPlanes=20, imageIndex=1, parameters={}):
    if 'meanshift' in parameters and parameters['meanshift'] > 0:
        import sklearn.cluster
        meanshift = sklearn.cluster.MeanShift(parameters['meanshift'])
        pass

    #import sklearn.neighbors
    #meanshift = sklearn.neighbors.KernelDensity(0.05)
    from pylsd.lsd import lsd

    height = depth.shape[0]
    width = depth.shape[1]

    camera = getCameraFromInfo(info)
    urange = (np.arange(width, dtype=np.float32) / (width) *
              (camera['width']) - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / (height) *
              (camera['height']) - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)

    X = depth * urange
    Y = depth
    Z = -depth * vrange

    normals = normal.reshape((-1, 3))
    normals = normals / \
        np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-4)
    validMask = np.logical_and(np.linalg.norm(
        normals, axis=-1) > 1e-4, depth.reshape(-1) > 1e-4)

    points = np.stack([X, Y, Z], axis=2).reshape(-1, 3)
    valid_points = points[validMask]

    lines = lsd(image.mean(2))

    lineImage = image.copy()
    for line in lines:
        cv2.line(lineImage, (int(line[0]), int(line[1])), (int(
            line[2]), int(line[3])), (0, 0, 255), int(np.ceil(line[4] / 2)))
        continue
    cv2.imwrite('test/lines.png', lineImage)

    numVPs = 3
    VPs, VPLines, remainingLines = calcVanishingPoints(lines, numVPs=numVPs)

    lineImage = image.copy()
    for VPIndex, lines in enumerate(VPLines):
        for line in lines:
            cv2.line(lineImage, (int(line[0]), int(line[1])), (int(line[2]), int(line[3])), ((
                VPIndex == 0) * 255, (VPIndex == 1) * 255, (VPIndex == 2) * 255), int(np.ceil(line[4] / 2)))
            continue
        continue
    cv2.imwrite('test/lines_vp.png', lineImage)
    # exit(1)

    dominantNormals = np.stack([(VPs[:, 0] * info[16] / width - info[2]) / info[0], np.ones(
        numVPs), -(VPs[:, 1] * info[17] / height - info[6]) / info[5]], axis=1)
    dominantNormals /= np.maximum(np.linalg.norm(dominantNormals,
                                                 axis=1, keepdims=True), 1e-4)

    dotThreshold = np.cos(np.deg2rad(20))
    for normalIndex, crossNormals in enumerate([[1, 2], [2, 0], [0, 1]]):
        normal = np.cross(
            dominantNormals[crossNormals[0]], dominantNormals[crossNormals[1]])
        normal = normalize(normal)
        if np.dot(normal, dominantNormals[normalIndex]) < dotThreshold:
            dominantNormals = np.concatenate(
                [dominantNormals, np.expand_dims(normal, 0)], axis=0)
            pass
        continue

    print(VPs)
    print(dominantNormals)

    dominantNormalImage = np.abs(
        np.matmul(normal, dominantNormals.transpose()))
    cv2.imwrite('test/dominant_normal.png', drawMaskImage(dominantNormalImage))
    # exit(1)

    planeHypothesisAreaThreshold = width * height * 0.01

    planes = []
    vpPlaneIndices = []
    if 'offsetGap' in parameters:
        offsetGap = parameters['offsetGap']
    else:
        offsetGap = 0.1
        pass
    planeIndexOffset = 0

    for dominantNormal in dominantNormals:
        if np.linalg.norm(dominantNormal) < 1e-4:
            continue
        offsets = np.tensordot(valid_points, dominantNormal, axes=([1], [0]))

        if 'meanshift' in parameters and parameters['meanshift'] > 0:
            sampleInds = np.arange(offsets.shape[0])
            np.random.shuffle(sampleInds)
            meanshift.fit(np.expand_dims(
                offsets[sampleInds[:int(offsets.shape[0] * 0.02)]], -1))
            for offset in meanshift.cluster_centers_:
                planes.append(dominantNormal * offset)
                continue
        else:
            offset = offsets.min()
            maxOffset = offsets.max()
            while offset < maxOffset:
                planeMask = np.logical_and(
                    offsets >= offset, offsets < offset + offsetGap)
                segmentOffsets = offsets[np.logical_and(
                    offsets >= offset, offsets < offset + offsetGap)]
                if segmentOffsets.shape[0] < planeHypothesisAreaThreshold:
                    offset += offsetGap
                    continue
                planeD = segmentOffsets.mean()
                planes.append(dominantNormal * planeD)
                offset = planeD + offsetGap

                #print(planeD, segmentOffsets.shape[0])
                #cv2.imwrite('test/mask_' + str(len(planes) - 1) + '.png', drawMaskImage(planeMask.reshape((height, width))))
                continue
            pass

        vpPlaneIndices.append(np.arange(planeIndexOffset, len(planes)))
        planeIndexOffset = len(planes)
        continue

    if len(planes) == 0:
        return np.array([]), np.zeros(segmentation.shape).astype(np.int32)
    planes = np.array(planes)

    planesD = np.linalg.norm(planes, axis=1, keepdims=True)
    planeNormals = planes / np.maximum(planesD, 1e-4)

    if 'distanceCostThreshold' in parameters:
        distanceCostThreshold = parameters['distanceCostThreshold']
    else:
        distanceCostThreshold = 0.05
        pass

    # print(planes)
    # print(np.abs(np.tensordot(points, planeNormals, axes=([1, 1])) - np.reshape(planesD, [1, -1])).max())
    # print(np.abs(np.tensordot(points, planeNormals, axes=([1, 1])) - np.reshape(planesD, [1, -1])).min())
    # print(distanceCostThreshold)

    distanceCost = np.abs(np.tensordot(points, planeNormals, axes=(
        [1, 1])) - np.reshape(planesD, [1, -1])) / distanceCostThreshold
    #distanceCost = np.concatenate([distanceCost, np.ones((height * width, 1))], axis=1)

    #valid_normals = normals[validMask]
    normalCostThreshold = 1 - np.cos(np.deg2rad(30))
    normalCost = (1 - np.abs(np.tensordot(normals, planeNormals,
                                          axes=([1, 1])))) / normalCostThreshold

    if 'normalWeight' in parameters:
        normalWeight = parameters['normalWeight']
    else:
        normalWeight = 1
        pass

    unaryCost = distanceCost + normalCost * normalWeight
    unaryCost *= np.expand_dims(validMask.astype(np.float32), -1)
    unaries = unaryCost.reshape((width * height, -1))

    print(('number of planes ', planes.shape[0]))
    cv2.imwrite('test/distance_cost.png', drawSegmentationImage(-distanceCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))

    cv2.imwrite('test/normal_cost.png', drawSegmentationImage(-normalCost.reshape(
        (height, width, -1)), unaryCost.shape[-1] - 1))

    cv2.imwrite('test/unary_cost.png', drawSegmentationImage(-unaryCost.reshape(
        (height, width, -1)), blackIndex=unaryCost.shape[-1] - 1))

    cv2.imwrite('test/segmentation.png', drawSegmentationImage(-unaries.reshape(
        (height, width, -1)), blackIndex=unaries.shape[-1]))

    #cv2.imwrite('test/mask.png', drawSegmentationImage(planeMasks.reshape((height, width, -1))))
    # exit(1)

    if 'numProposals' in parameters:
        numProposals = parameters['numProposals']
    else:
        numProposals = 3
        pass

    numProposals = min(numProposals, unaries.shape[-1] - 1)

    proposals = np.argpartition(unaries, numProposals)[:, :numProposals]
    unaries = -readProposalInfo(unaries, proposals).reshape((-1, numProposals))

    nodes = np.arange(height * width).reshape((height, width))

    #deltas = [(0, 1), (1, 0), (-1, 1), (1, 1)]
    deltas = [(0, 1), (1, 0)]

    edges = []
    edges_features = []

    #edges_features = np.concatenate(edges_features, axis=0)
    for delta in deltas:
        deltaX = delta[0]
        deltaY = delta[1]
        partial_nodes = nodes[max(-deltaY, 0):min(height - deltaY, height),
                              max(-deltaX, 0):min(width - deltaX, width)].reshape(-1)
        edges.append(
            np.stack([partial_nodes, partial_nodes + (deltaY * width + deltaX)], axis=1))

        labelDiff = (np.expand_dims(proposals[partial_nodes], -1) != np.expand_dims(
            proposals[partial_nodes + (deltaY * width + deltaX)], 1)).astype(np.float32)

        edges_features.append(labelDiff)
        continue

    edges = np.concatenate(edges, axis=0)
    edges_features = np.concatenate(edges_features, axis=0)

    if 'edgeWeights' in parameters:
        edgeWeights = parameters['edgeWeights']
    else:
        edgeWeights = [0.5, 0.6, 0.6]
        pass

    lineSets = np.zeros((height * width, 3))
    creaseLines = np.expand_dims(np.stack(
        [planeNormals[:, 0] / info[0], planeNormals[:, 1], -planeNormals[:, 2] / info[5]], axis=1), 1) * planesD.reshape((1, -1, 1))
    creaseLines = creaseLines - np.transpose(creaseLines, [1, 0, 2])
    for planeIndex_1 in range(planes.shape[0]):
        for planeIndex_2 in range(planeIndex_1 + 1, planes.shape[0]):
            creaseLine = creaseLines[planeIndex_1, planeIndex_2]
            if abs(creaseLine[0]) > abs(creaseLine[2]):
                vs = np.arange(height)
                us = -(creaseLine[1] + (vs - info[6]) *
                       creaseLine[2]) / creaseLine[0] + info[2]
                minUs = np.floor(us).astype(np.int32)
                maxUs = minUs + 1
                validIndicesMask = np.logical_and(minUs >= 0, maxUs < width)
                if validIndicesMask.sum() == 0:
                    continue
                vs = vs[validIndicesMask]
                minUs = minUs[validIndicesMask]
                maxUs = maxUs[validIndicesMask]
                edgeIndices = (height - 1) * width + (vs * (width - 1) + minUs)
                for index, edgeIndex in enumerate(edgeIndices):
                    pixel_1 = vs[index] * width + minUs[index]
                    pixel_2 = vs[index] * width + maxUs[index]
                    proposals_1 = proposals[pixel_1]
                    proposals_2 = proposals[pixel_2]
                    if planeIndex_1 in proposals_1 and planeIndex_2 in proposals_2:
                        proposalIndex_1 = np.where(
                            proposals_1 == planeIndex_1)[0][0]
                        proposalIndex_2 = np.where(
                            proposals_2 == planeIndex_2)[0][0]
                        edges_features[edgeIndex, proposalIndex_1,
                                       proposalIndex_2] *= edgeWeights[0]
                        pass
                    if planeIndex_2 in proposals_1 and planeIndex_1 in proposals_2:
                        proposalIndex_1 = np.where(
                            proposals_1 == planeIndex_2)[0][0]
                        proposalIndex_2 = np.where(
                            proposals_2 == planeIndex_1)[0][0]
                        edges_features[edgeIndex, proposalIndex_1,
                                       proposalIndex_2] *= edgeWeights[0]
                        pass
                    continue

                lineSets[vs * width + minUs, 0] = 1
                lineSets[vs * width + maxUs, 0] = 1
            else:
                us = np.arange(width)
                vs = -(creaseLine[1] + (us - info[2]) *
                       creaseLine[0]) / creaseLine[2] + info[6]
                minVs = np.floor(vs).astype(np.int32)
                maxVs = minVs + 1
                validIndicesMask = np.logical_and(minVs >= 0, maxVs < height)
                if validIndicesMask.sum() == 0:
                    continue
                us = us[validIndicesMask]
                minVs = minVs[validIndicesMask]
                maxVs = maxVs[validIndicesMask]
                edgeIndices = (minVs * width + us)
                for index, edgeIndex in enumerate(edgeIndices):
                    pixel_1 = minVs[index] * width + us[index]
                    pixel_2 = maxVs[index] * width + us[index]
                    proposals_1 = proposals[pixel_1]
                    proposals_2 = proposals[pixel_2]
                    if planeIndex_1 in proposals_1 and planeIndex_2 in proposals_2:
                        proposalIndex_1 = np.where(
                            proposals_1 == planeIndex_1)[0][0]
                        proposalIndex_2 = np.where(
                            proposals_2 == planeIndex_2)[0][0]
                        edges_features[edgeIndex, proposalIndex_1,
                                       proposalIndex_2] *= edgeWeights[0]
                        pass
                    if planeIndex_2 in proposals_1 and planeIndex_1 in proposals_2:
                        proposalIndex_1 = np.where(
                            proposals_1 == planeIndex_2)[0][0]
                        proposalIndex_2 = np.where(
                            proposals_2 == planeIndex_1)[0][0]
                        edges_features[edgeIndex, proposalIndex_1,
                                       proposalIndex_2] *= edgeWeights[0]
                        pass
                    continue
                lineSets[minVs * width + us, 0] = 1
                lineSets[maxVs * width + us, 0] = 1
                pass
            continue
        continue

    planeDepths = calcPlaneDepths(
        planes, width, height, info).reshape((height * width, -1))
    planeDepths = readProposalInfo(
        planeDepths, proposals).reshape((-1, numProposals))

    planeHorizontalVPMask = np.ones((planes.shape[0], 3), dtype=np.bool)
    for VPIndex, planeIndices in enumerate(vpPlaneIndices):
        planeHorizontalVPMask[planeIndices] = False
        continue

    for VPIndex, lines in enumerate(VPLines):
        lp = lines[:, :2]
        ln = lines[:, 2:4] - lines[:, :2]
        ln /= np.maximum(np.linalg.norm(ln, axis=-1, keepdims=True), 1e-4)
        ln = np.stack([ln[:, 1], -ln[:, 0]], axis=1)
        lnp = (ln * lp).sum(1, keepdims=True)
        occlusionLines = np.concatenate([ln, lnp], axis=1)
        for occlusionLine in occlusionLines:
            if abs(occlusionLine[0]) > abs(occlusionLine[1]):
                vs = np.arange(height)
                us = (occlusionLine[2] - vs *
                      occlusionLine[1]) / occlusionLine[0]
                minUs = np.floor(us).astype(np.int32)
                maxUs = minUs + 1
                validIndicesMask = np.logical_and(minUs >= 0, maxUs < width)
                vs = vs[validIndicesMask]
                minUs = minUs[validIndicesMask]
                maxUs = maxUs[validIndicesMask]
                edgeIndices = (height - 1) * width + (vs * (width - 1) + minUs)
                for index, edgeIndex in enumerate(edgeIndices):
                    pixel_1 = vs[index] * width + minUs[index]
                    pixel_2 = vs[index] * width + maxUs[index]
                    proposals_1 = proposals[pixel_1]
                    proposals_2 = proposals[pixel_2]
                    for proposalIndex_1, planeIndex_1 in enumerate(proposals_1):
                        if not planeHorizontalVPMask[planeIndex_1][VPIndex]:
                            continue
                        planeDepth_1 = planeDepths[pixel_1][proposalIndex_1]
                        for proposalIndex_2, planeIndex_2 in enumerate(proposals_2):
                            if planeDepths[pixel_2][proposalIndex_2] > planeDepth_1:
                                edges_features[edgeIndex, proposalIndex_1,
                                               proposalIndex_2] *= edgeWeights[1]
                                pass
                            continue
                        continue
                    continue
                lineSets[vs * width + minUs, 1] = 1
                lineSets[vs * width + maxUs, 1] = 1
            else:
                us = np.arange(width)
                vs = (occlusionLine[2] - us *
                      occlusionLine[0]) / occlusionLine[1]

                minVs = np.floor(vs).astype(np.int32)
                maxVs = minVs + 1
                validIndicesMask = np.logical_and(minVs >= 0, maxVs < height)
                us = us[validIndicesMask]
                minVs = minVs[validIndicesMask]
                maxVs = maxVs[validIndicesMask]
                edgeIndices = (minVs * width + us)
                for index, edgeIndex in enumerate(edgeIndices):
                    pixel_1 = minVs[index] * width + us[index]
                    pixel_2 = maxVs[index] * width + us[index]
                    proposals_1 = proposals[pixel_1]
                    proposals_2 = proposals[pixel_2]
                    for proposalIndex_1, planeIndex_1 in enumerate(proposals_1):
                        if not planeHorizontalVPMask[planeIndex_1][VPIndex]:
                            continue
                        planeDepth_1 = planeDepths[pixel_1][proposalIndex_1]
                        for proposalIndex_2, planeIndex_2 in enumerate(proposals_2):
                            if planeDepths[pixel_2][proposalIndex_2] > planeDepth_1:
                                edges_features[edgeIndex, proposalIndex_1,
                                               proposalIndex_2] *= edgeWeights[1]
                                pass
                            continue
                        continue
                    continue
                lineSets[minVs * width + us, 1] = 1
                lineSets[maxVs * width + us, 1] = 1
                pass
            continue
        continue

    # lp = remainingLines[:, :2]
    # ln = remainingLines[:, 2:4] - remainingLines[:, :2]
    # ln /= np.maximum(np.linalg.norm(ln, axis=-1, keepdims=True), 1e-4)
    # ln = np.stack([ln[:, 1], -ln[:, 0]], axis=1)
    # lnp = (ln * lp).sum(1, keepdims=True)
    # occusionLines = np.concatenate([ln, lnp], axis=1)

    for line in remainingLines:
        if abs(line[3] - line[1]) > abs(line[2] - line[0]):
            if line[3] < line[1]:
                line = np.array([line[2], line[3], line[0], line[1]])
                pass
            vs = np.arange(line[1], line[3] + 1, dtype=np.int32)
            us = line[0] + (vs - line[1]) / (line[3] -
                                             line[1]) * (line[2] - line[0])
            minUs = np.floor(us).astype(np.int32)
            maxUs = minUs + 1
            validIndicesMask = np.logical_and(minUs >= 0, maxUs < width)
            vs = vs[validIndicesMask]
            minUs = minUs[validIndicesMask]
            maxUs = maxUs[validIndicesMask]
            edgeIndices = (height - 1) * width + (vs * (width - 1) + minUs)
            for edgeIndex in edgeIndices:
                edges_features[edgeIndex] *= edgeWeights[2]
                continue
            lineSets[(vs * width + minUs), 2] = 1
            lineSets[(vs * width + maxUs), 2] = 1
        else:
            if line[2] < line[0]:
                line = np.array([line[2], line[3], line[0], line[1]])
                pass
            us = np.arange(line[0], line[2] + 1, dtype=np.int32)
            vs = line[1] + (us - line[0]) / (line[2] -
                                             line[0]) * (line[3] - line[1])

            minVs = np.floor(vs).astype(np.int32)
            maxVs = minVs + 1
            validIndicesMask = np.logical_and(minVs >= 0, maxVs < height)
            us = us[validIndicesMask]
            minVs = minVs[validIndicesMask]
            maxVs = maxVs[validIndicesMask]
            edgeIndices = (minVs * width + us)
            for edgeIndex in edgeIndices:
                edges_features[edgeIndex] *= edgeWeights[2]
                continue
            lineSets[minVs * width + us, 2] = 1
            lineSets[maxVs * width + us, 2] = 1
            continue
        continue
    cv2.imwrite('test/line_sets.png',
                drawMaskImage(lineSets.reshape((height, width, 3))))

    if 'smoothnessWeight' in parameters:
        smoothnessWeight = parameters['smoothnessWeight']
    else:
        smoothnessWeight = 4
        pass

    refined_segmentation = inference_ogm(
        unaries, -edges_features * smoothnessWeight, edges, return_energy=False, alg='trw')
    refined_segmentation = refined_segmentation.reshape([height, width, 1])
    refined_segmentation = readProposalInfo(proposals, refined_segmentation)
    # print(pairwise_matrix)
    #refined_segmentation = inference_ogm(unaries * 5, -pairwise_matrix, edges, return_energy=False, alg='alphaexp')
    planeSegmentation = refined_segmentation.reshape([height, width])

    planeSegmentation[np.logical_not(
        validMask.reshape((height, width)))] = planes.shape[0]
    cv2.imwrite('test/segmentation_refined.png',
                drawSegmentationImage(planeSegmentation))
    # exit(1)

    # if planes.shape[0] > numOutputPlanes:
    #     planeInfo = []
    #     for planeIndex in xrange(planes.shape[0]):
    #         mask = planeSegmentation == planeIndex
    #         planeInfo.append((planes[planeIndex], mask))
    #         continue
    #     planeInfo = sorted(planeInfo, key=lambda x: -x[1].sum())
    #     newPlanes = []
    #     newPlaneSegmentation = np.full(planeSegmentation.shape, numOutputPlanes)
    #     for planeIndex in xrange(numOutputPlanes):
    #         newPlanes.append(planeInfo[planeIndex][0])
    #         newPlaneSegmentation[planeInfo[planeIndex][1]] = planeIndex
    #         continue
    #     planeSegmentation = newPlaneSegmentation
    #     planes = np.array(newPlanes)
    # else:
    #     planeSegmentation[planeSegmentation == planes.shape[0]] = numOutputPlanes
    #     pass

    # if planes.shape[0] < numOutputPlanes:
    #     planes = np.concatenate([planes, np.zeros((numOutputPlanes - planes.shape[0], 3))], axis=0)
    #     pass

    # planeDepths = calcPlaneDepths(planes, width, height, info)

    # allDepths = np.concatenate([planeDepths, np.expand_dims(depth, -1)], axis=2)
    # depthPred = allDepths.reshape([height * width, numOutputPlanes + 1])[np.arange(width * height), planeSegmentation.astype(np.int32).reshape(-1)].reshape(height, width)

    # planeNormals = calcPlaneNormals(planes, width, height)
    # allNormals = np.concatenate([np.expand_dims(normal, 2), planeNormals], axis=2)
    # normalPred = allNormals.reshape(-1, numOutputPlanes + 1, 3)[np.arange(width * height), planeSegmentation.reshape(-1)].reshape((height, width, 3))

    return planes, planeSegmentation


def testPlaneExtraction():
    depth = cv2.imread(
        '../../Data/SUNCG/0004d52d1aeeb8ae6de39d6bd993e992/000000_depth.png', -1).astype(np.float32) / 1000
    normal = (cv2.imread(
        '../../Data/SUNCG/0004d52d1aeeb8ae6de39d6bd993e992/000000_norm_camera.png').astype(np.float32) / 255) * 2 - 1
    normal = np.stack(
        [normal[:, :, 2], normal[:, :, 1], normal[:, :, 0]], axis=2)
    image = cv2.imread(
        '../../Data/SUNCG/0004d52d1aeeb8ae6de39d6bd993e992/000000_mlt.png')

    cv2.imwrite('test/depth.png', drawDepthImage(depth))
    cv2.imwrite('test/normal.png', drawNormalImage(normal))
    cv2.imwrite('test/image.png', image)

    info = np.zeros(20)
    info[0] = 517.97
    info[2] = 320
    info[5] = 517.97
    info[6] = 240
    info[10] = 1
    info[15] = 1
    info[16] = 640
    info[17] = 480
    info[18] = 1000
    info[19] = 0

    parameters = {'distanceCostThreshold': 0.05, 'numProposals': 3,
                  'smoothnessWeight': 30, 'offsetGap': 0.05},
    #pred_p, pred_s, pred_d, pred_n = fitPlanesManhattan(image, depth, normal, info, numOutputPlanes=20, imageIndex=-1, parameters=parameters)
    pred_p, pred_s, pred_d, pred_n = fitPlanesPiecewise(
        image, depth, normal, info, numOutputPlanes=20, imageIndex=-1, parameters=parameters)
    exit(1)
    return


def estimateFocalLength(image):
    from pylsd.lsd import lsd

    height = image.shape[0]
    width = image.shape[1]

    lines = lsd(image.mean(2))

    lineImage = image.copy()
    for line in lines:
        cv2.line(lineImage, (int(line[0]), int(line[1])), (int(
            line[2]), int(line[3])), (0, 0, 255), int(np.ceil(line[4] / 2)))
        continue
    cv2.imwrite('test/lines.png', lineImage)

    numVPs = 3
    VPs, VPLines, remainingLines = calcVanishingPoints(lines, numVPs=numVPs)
    #focalLength = (np.sqrt(np.linalg.norm(np.cross(VPs[0], VPs[1]))) + np.sqrt(np.linalg.norm(np.cross(VPs[0], VPs[2]))) + np.sqrt(np.linalg.norm(np.cross(VPs[1], VPs[2])))) / 3
    focalLength = (np.sqrt(np.abs(np.dot(VPs[0], VPs[1]))) + np.sqrt(
        np.abs(np.dot(VPs[0], VPs[2]))) + np.sqrt(np.abs(np.dot(VPs[1], VPs[2])))) / 3
    return focalLength


def calcEdgeMap(segmentation, edgeWidth=3):
    edges = np.zeros(segmentation.shape, np.bool)
    for shift in [-1, 1]:
        for c in [0, 1]:
            edges = np.logical_or(edges, segmentation !=
                                  np.roll(segmentation, shift, axis=c))
            continue
        continue
    edges = edges.astype(np.float32)
    edges[0] = 0
    edges[-1] = 0
    edges[:, 0] = 0
    edges[:, -1] = 0
    edges = cv2.dilate(edges, np.ones((3, 3)), iterations=edgeWidth)
    return edges > 0.5

# testPlaneExtraction()


def findFloorPlane(planes, segmentation):
    minZ = 0
    minZPlaneIndex = -1
    minFloorArea = 32 * 24
    for planeIndex, plane in enumerate(planes):
        if plane[2] < 0 and abs(plane[2]) > max(abs(plane[0]), abs(plane[1])) and plane[2] < minZ and (segmentation == planeIndex).sum() > minFloorArea:
            minZPlaneIndex = planeIndex
            minZ = plane[2]
            pass
        continue
    return minZPlaneIndex


def findCornerPoints(plane, depth, mask, info, axis=2, rectangle=True):
    width = depth.shape[1]
    height = depth.shape[0]

    camera = getCameraFromInfo(info)

    #camera = getNYURGBDCamera()
    #camera = getSUNCGCamera()

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange

    XYZ = np.stack([X, Y, Z], axis=2)
    XYZ = XYZ.reshape((-1, 3))

    maxs = XYZ.max(0)
    mins = XYZ.min(0)

    planeD = np.linalg.norm(plane)
    planeNormal = plane / np.maximum(planeD, 1e-4)

    if axis == 2:
        points = np.array([[mins[0], mins[1]], [mins[0], maxs[1]], [
                          maxs[0], mins[1]], [maxs[0], maxs[1]]])
        pointsZ = (planeD - planeNormal[0] * points[:, 0] -
                   planeNormal[1] * points[:, 1]) / planeNormal[2]
        points = np.concatenate([points, np.expand_dims(pointsZ, -1)], axis=1)
        pass

    u = (points[:, 0] / points[:, 1] * camera['fx'] +
         camera['cx']) / camera['width'] * width
    v = (-points[:, 2] / points[:, 1] * camera['fy'] +
         camera['cy']) / camera['height'] * height

    if rectangle:
        minU = u.min()
        maxU = u.max()
        minV = v.min()
        maxV = v.max()
        uv = np.array([[minU, minV], [minU, maxV], [maxU, minV], [maxU, maxV]])
    else:
        uv = np.stack([u, v], axis=1)
        pass
    return uv


def findCornerPoints2D(mask):
    from pylsd.lsd import lsd
    lines = lsd(mask)

    #lineImage = mask.copy()
    lineImage = np.zeros(mask.shape + (3, ))
    print((lines.shape))
    print(lines)
    for line in lines:
        cv2.line(lineImage, (int(line[0]), int(line[1])), (int(
            line[2]), int(line[3])), (0, 0, 255), int(np.ceil(line[4] / 2)))
        continue
    cv2.imwrite('test/lines.png', lineImage)
    exit(1)


# def copyTexture(image, planes, segmentation, info, denotedPlaneIndex=-1, textureIndex=-1):
#     import glob

#     width = segmentation.shape[1]
#     height = segmentation.shape[0]

#     plane_depths = calcPlaneDepths(planes, width, height, info)

#     texture_image_names = glob.glob('../texture_images/*.png') + glob.glob('../texture_images/*.jpg')
#     if textureIndex >= 0:
#         texture_image_names = [texture_image_names[textureIndex]]
#         pass

#     resultImages = []
#     for texture_index, texture_image_name in enumerate(texture_image_names):
#         textureImage = cv2.imread(texture_image_name)
#         #textureImage = cv2.imread('../textures/texture_2.jpg')
#         textureImage = cv2.resize(textureImage, (width, height), interpolation=cv2.INTER_LINEAR)

#         if denotedPlaneIndex < 0:
#             denotedPlaneIndex = findFloorPlane(planes, segmentation)
#             pass

#         mask = segmentation == denotedPlaneIndex
#         #mask = cv2.resize(mask.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR) > 0.5
#         #plane_depths = calcPlaneDepths(pred_p, width, height)
#         depth = plane_depths[:, :, denotedPlaneIndex]
#         #depth = cv2.resize(depth, (width, height), interpolation=cv2.INTER_LINEAR) > 0.5
#         #uv = findCornerPoints(planes[denotedPlaneIndex], depth, mask, info)
#         uv = findCornerPoints2D(mask.astype(np.uint8) * 255)
#         #print(uv)
#         source_uv = np.array([[0, 0], [0, height], [width, 0], [width, height]])

#         h, status = cv2.findHomography(source_uv, uv)
#         #textureImageWarped = cv2.warpPerspective(textureImage, h, (WIDTH, HEIGHT))
#         textureImageWarped = cv2.warpPerspective(textureImage, h, (width, height))
#         resultImage = image.copy()

#         resultImage[mask] = textureImageWarped[mask]
#         resultImages.append(resultImage)
#         #cv2.imwrite(options.test_dir + '/' + str(index) + '_texture.png', textureImageWarped)
#         #cv2.imwrite(options.test_dir + '/' + str(index) + '_result_' + str(texture_index) + '.png', resultImage)
#         continue
#     return resultImages


# the logo copying application
def copyLogo(textureImageFilename, folder, index, image, depth, planes, segmentation, info):
    from sklearn.cluster import KMeans
    from skimage import measure
    #from sklearn.decomposition import PCA

    width = segmentation.shape[1]
    height = segmentation.shape[0]

    camera = getCameraFromInfo(info)

    # calculate corresponding 3D position for each pixel
    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange
    XYZ = np.stack([X, Y, Z], axis=2)
    #plane_depths = calcPlaneDepths(planes, width, height, info)

    # calculate plane offsets and normals
    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    planeAreaThreshold = width * height / 100

    normals = []
    for planeIndex in range(planes.shape[0]):
        mask = segmentation == planeIndex
        if mask.sum() < planeAreaThreshold:
            continue
        normals.append(planesNormal[planeIndex])
        continue
    normals = np.stack(normals, axis=0)
    normals[normals[:, 1] < 0] *= -1

    # find dominant directions
    kmeans = KMeans(n_clusters=3).fit(normals)
    dominantNormals = kmeans.cluster_centers_
    dominantNormals = dominantNormals / \
        np.maximum(np.linalg.norm(dominantNormals,
                                  axis=-1, keepdims=True), 1e-4)

    normals = planesNormal.copy()
    normals[normals[:, 1] < 0] *= -1
    planeClusters = kmeans.predict(normals)

    #texture_image_names = glob.glob('../texture_images/*.png') + glob.glob('../texture_images/*.jpg')

    #imageFilename = '/home/chenliu/Projects/PlaneNet/texture_images/CVPR.jpg'
    #textureImage = cv2.imread(imageFilename)

    #textureImage = cv2.imread('../texture_images/CVPR_transparent.png')
    textureImage = cv2.imread(textureImageFilename)
    imageFilename = 'CVPR.png'
    cv2.imwrite(folder + '/' + imageFilename, textureImage)

    backgroundMask = textureImage.mean(2) > 224
    #backgroundMask = cv2.erode(backgroundMask.astype(np.uint8), np.ones((3, 3)))
    #cv2.imwrite('test/mask.png', drawMaskImage(background))
    # exit(1)

    textureHeight = textureImage.shape[0]
    textureWidth = textureImage.shape[1]
    textureRatio = float(textureHeight) / textureWidth
    #textureImage = cv2.imread('../textures/texture_2.jpg')
    #textureImage = cv2.resize(textureImage, (width, height), interpolation=cv2.INTER_LINEAR)

    # copy the texture image in 3D
    faces = []
    texcoords = []
    #maskImage = np.full(segmentation.shape, planes.shape[0])
    maskImage = image.copy()
    for planeIndex in range(planes.shape[0]):
        globalMask = segmentation == planeIndex
        if globalMask.sum() < planeAreaThreshold:
            continue

        masks = measure.label(globalMask.astype(np.int32), background=0)
        # print(masks.max())
        # print(masks.min())
        #cv2.imwrite('test/mask.png', drawSegmentationImage(masks, blackIndex=planes.shape[0]))
        # exit(1)
        for maskIndex in range(masks.min() + 1, masks.max() + 1):
            mask = masks == maskIndex
            if mask.sum() < planeAreaThreshold:
                continue

            planeNormal = planesNormal[planeIndex]

            # maxs = points.max(0)
            # mins = points.min(0)

            # planeNormal = planesNormal[planeIndex]
            # maxAxis = np.argmax(np.abs(planeNormal))
            # center = points.mean(0)
            # if maxAxis != 2:
            #     direction_u = np.cross(planeNormal, np.array([0, 0, 1]))
            #     direction_u = direction_u / np.maximum(np.linalg.norm(direction_u), 1e-4)
            #     direction_v = np.cross(planeNormal, direction_u)
            #     direction_v = direction_v / np.maximum(np.linalg.norm(direction_v), 1e-4)
            # else:
            #     pca = PCA(n_components=1)
            #     pca.fit(points[:, :2])
            #     direction = np.concatenate([pca.components_[0], np.zeros(1)], axis=0)

            #     direction_u = np.cross(planeNormal, direction)
            #     direction_u = direction_u / np.maximum(np.linalg.norm(direction_u), 1e-4)
            #     direction_v = np.cross(planeNormal, direction_u)
            #     direction_v = direction_v / np.maximum(np.linalg.norm(direction_v), 1e-4)
            #     pass

            cluster = planeClusters[planeIndex]
            dominantNormal = dominantNormals[(cluster + 1) % 3]
            direction_u = np.cross(planeNormal, dominantNormal)
            direction_u = direction_u / \
                np.maximum(np.linalg.norm(direction_u), 1e-4)
            direction_v = np.cross(planeNormal, direction_u)
            direction_v = direction_v / \
                np.maximum(np.linalg.norm(direction_v), 1e-4)

            points = XYZ[mask]
            projection_u = np.tensordot(points, direction_u, axes=([1], [0]))
            range_u = [projection_u.min(), projection_u.max()]
            projection_v = np.tensordot(points, direction_v, axes=([1], [0]))
            range_v = [projection_v.min(), projection_v.max()]
            if range_v[1] - range_v[0] > range_u[1] - range_u[0]:
                range_u, range_v = range_v, range_u
                direction_u, direction_v = direction_v, direction_u
                pass

            if (np.argmax(np.abs(direction_v)) == 2 and direction_v[2] < 0) or (np.argmax(np.abs(direction_v)) != 2 and np.dot(np.array([0, 1, 0]), direction_v) < 0):
                direction_v *= -1
                projection_v *= -1
                range_v = [-range_v[1], -range_v[0]]
                pass
            if np.dot(np.cross(planeNormal, direction_v), direction_u) < 0:
                direction_u *= -1
                projection_u *= -1
                range_u = [-range_u[1], -range_u[0]]
                pass

            print((planeIndex, dominantNormal, direction_u, direction_v))

            length_u = range_u[1] - range_u[0]
            length_v = range_v[1] - range_v[0]
            if length_u * textureRatio > length_v:
                length_u = length_v / textureRatio
            else:
                length_v = length_u * textureRatio
                pass

            logoSize = 0.35

            center_u = (range_u[0] + range_u[1]) / 2
            range_u = [center_u - length_u * logoSize,
                       center_u + length_u * logoSize]

            center_v = (range_v[0] + range_v[1]) / 2
            range_v = [center_v - length_v * logoSize,
                       center_v + length_v * logoSize]

            projection_u = np.tensordot(XYZ, direction_u, axes=([2], [0]))
            projection_v = np.tensordot(XYZ, direction_v, axes=([2], [0]))
            projection_u = (
                projection_u - range_u[0]) / (range_u[1] - range_u[0])
            projection_v = (
                projection_v - range_v[0]) / (range_v[1] - range_v[0])
            rectangleMask = np.logical_and(np.logical_and(
                projection_u >= 0, projection_u <= 1), np.logical_and(projection_v >= 0, projection_v <= 1))

            rectangleMask = np.logical_and(rectangleMask, mask)
            #maskImage[rectangleMask] = planeIndex

            for y in range(height - 1):
                for x in range(width - 1):
                    facePixels = []
                    for pixel in [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]:
                        if rectangleMask[pixel[1]][pixel[0]]:
                            u = projection_u[pixel[1]][pixel[0]]
                            v = projection_v[pixel[1]][pixel[0]]
                            u = min(max(int(round(u * textureWidth)), 0),
                                    textureWidth - 1)
                            v = min(
                                max(textureHeight - 1 - int(round(v * textureHeight)), 0), textureHeight - 1)
                            if backgroundMask[v][u] == False:
                                facePixels.append(pixel)

                                if pixel == (x, y):
                                    maskImage[y][x] = textureImage[v][u]
                                    pass
                                pass
                            pass
                        continue

                    if len(facePixels) == 3:
                        faces.append(facePixels[0] +
                                     facePixels[1] + facePixels[2])
                        vt = []
                        for c in [0, 1, 2]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                    elif len(facePixels) == 4:
                        faces.append(facePixels[0] +
                                     facePixels[1] + facePixels[2])
                        vt = []
                        for c in [0, 1, 2]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                        faces.append(facePixels[0] +
                                     facePixels[2] + facePixels[3])
                        vt = []
                        for c in [0, 2, 3]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                        pass
                    continue
                continue
            continue
        continue

    #cv2.imwrite('test/mask.png', drawSegmentationImage(maskImage, blackIndex=planes.shape[0]))
    #cv2.imwrite('test/mask.png', drawSegmentationImage(maskImage, blackIndex=planes.shape[0]))

    # write a .ply file
    with open(folder + '/' + str(index) + '_logo.ply', 'w') as f:
        header = """ply
format ascii 1.0
comment VCGLIB generated
comment TextureFile """
        header += imageFilename
        header += """
element vertex """
        header += str(width * height)
        header += """
property float x
property float y
property float z
element face """
        header += str(len(faces))
        header += """
property list uchar int vertex_indices
property list uchar float texcoord
end_header
"""
        f.write(header)
        for y in range(height):
            for x in range(width):
                segmentIndex = segmentation[y][x]
                if segmentIndex == -1:
                    f.write("0.0 0.0 0.0\n")
                    continue
                point = XYZ[y][x]
                X = point[0] * 0.9999
                Y = point[1] * 0.9999
                Z = point[2] * 0.9999
                #Y = depth[y][x]
                #X = Y / focalLength * (x - width / 2) / width * 640
                #Z = -Y / focalLength * (y - height / 2) / height * 480
                f.write(str(X) + ' ' + str(Z) + ' ' + str(-Y) + '\n')
                continue
            continue

        for faceIndex, face in enumerate(faces):
            f.write('3 ')
            for c in range(3):
                f.write(str(face[c * 2 + 1] * width + face[c * 2]) + ' ')
                continue
            f.write('6 ')
            vt = texcoords[faceIndex]
            for value in vt:
                f.write(str(value) + ' ')
                continue
            # for c in xrange(3):
            #     f.write(str(float(face[c * 2]) / width) + ' ' + str(1 - float(face[c * 2 + 1]) / height) + ' ')
            #     continue
            f.write('\n')
            continue
        f.close()
        pass
    return maskImage


# the wall texture copying application, similar with the logo copying application
def copyWallTexture(textureImageFilename, folder, index, image, depth, planes, segmentation, info, wallPlanes=[]):
    from sklearn.cluster import KMeans
    from skimage import measure
    #from sklearn.decomposition import PCA

    width = segmentation.shape[1]
    height = segmentation.shape[0]

    camera = getCameraFromInfo(info)

    # calculate corresponding 3D position for each pixel
    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange
    XYZ = np.stack([X, Y, Z], axis=2)
    #plane_depths = calcPlaneDepths(planes, width, height, info)

    # calculate plane offsets and normals
    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    planeAreaThreshold = width * height / 100

    normals = []
    for planeIndex in range(planes.shape[0]):
        mask = segmentation == planeIndex
        if mask.sum() < planeAreaThreshold:
            continue
        normals.append(planesNormal[planeIndex])
        continue
    normals = np.stack(normals, axis=0)
    normals[normals[:, 1] < 0] *= -1

    # find dominant directions
    kmeans = KMeans(n_clusters=3).fit(normals)
    dominantNormals = kmeans.cluster_centers_
    dominantNormals = dominantNormals / \
        np.maximum(np.linalg.norm(dominantNormals,
                                  axis=-1, keepdims=True), 1e-4)

    normals = planesNormal.copy()
    normals[normals[:, 1] < 0] *= -1
    planeClusters = kmeans.predict(normals)

    #texture_image_names = glob.glob('../texture_images/*.png') + glob.glob('../texture_images/*.jpg')

    #imageFilename = '/home/chenliu/Projects/PlaneNet/texture_images/CVPR.jpg'
    #textureImage = cv2.imread(imageFilename)

    #textureImage = cv2.imread('../texture_images/CVPR_transparent.png')
    #textureImage = cv2.imread('../texture_images/checkerboard.jpg')
    textureImage = cv2.imread(textureImageFilename)
    imageFilename = 'texture.png'
    cv2.imwrite(folder + '/' + imageFilename, textureImage)

    #background = textureImage.mean(2) > 224
    #background = cv2.erode(background.astype(np.uint8), np.ones((3, 3)))
    #cv2.imwrite('test/mask.png', drawMaskImage(background))
    # exit(1)

    textureHeight = textureImage.shape[0]
    textureWidth = textureImage.shape[1]
    textureRatio = float(textureHeight) / textureWidth
    #textureImage = cv2.imread('../textures/texture_2.jpg')
    #textureImage = cv2.resize(textureImage, (width, height), interpolation=cv2.INTER_LINEAR)

    # copy wall texture in 3D
    faces = []
    texcoords = []
    #maskImage = np.full(segmentation.shape, planes.shape[0])
    maskImage = image.copy()
    for planeIndex in range(planes.shape[0]):
        if planeIndex not in wallPlanes:
            continue
        globalMask = segmentation == planeIndex
        if globalMask.sum() < planeAreaThreshold:
            continue

        masks = measure.label(globalMask.astype(np.int32), background=0)
        # print(masks.max())
        # print(masks.min())
        cv2.imwrite('test/mask.png', drawSegmentationImage(masks,
                                                           blackIndex=planes.shape[0]))
        #print((masks == 1).sum(), planeAreaThreshold)
        # print(planeAreaThreshold)
        # exit(1)
        for maskIndex in range(masks.min() + 1, masks.max() + 1):
            mask = masks == maskIndex
            if mask.sum() < planeAreaThreshold:
                continue

            planeNormal = planesNormal[planeIndex]

            # maxs = points.max(0)
            # mins = points.min(0)

            # planeNormal = planesNormal[planeIndex]
            # maxAxis = np.argmax(np.abs(planeNormal))
            # center = points.mean(0)
            # if maxAxis != 2:
            #     direction_u = np.cross(planeNormal, np.array([0, 0, 1]))
            #     direction_u = direction_u / np.maximum(np.linalg.norm(direction_u), 1e-4)
            #     direction_v = np.cross(planeNormal, direction_u)
            #     direction_v = direction_v / np.maximum(np.linalg.norm(direction_v), 1e-4)
            # else:
            #     pca = PCA(n_components=1)
            #     pca.fit(points[:, :2])
            #     direction = np.concatenate([pca.components_[0], np.zeros(1)], axis=0)

            #     direction_u = np.cross(planeNormal, direction)
            #     direction_u = direction_u / np.maximum(np.linalg.norm(direction_u), 1e-4)
            #     direction_v = np.cross(planeNormal, direction_u)
            #     direction_v = direction_v / np.maximum(np.linalg.norm(direction_v), 1e-4)
            #     pass

            cluster = planeClusters[planeIndex]
            dominantNormal = dominantNormals[(cluster + 1) % 3]
            direction_u = np.cross(planeNormal, dominantNormal)
            direction_u = direction_u / \
                np.maximum(np.linalg.norm(direction_u), 1e-4)
            direction_v = np.cross(planeNormal, direction_u)
            direction_v = direction_v / \
                np.maximum(np.linalg.norm(direction_v), 1e-4)

            points = XYZ[mask]
            projection_u = np.tensordot(points, direction_u, axes=([1], [0]))
            range_u = [projection_u.min(), projection_u.max()]
            projection_v = np.tensordot(points, direction_v, axes=([1], [0]))
            range_v = [projection_v.min(), projection_v.max()]
            if range_v[1] - range_v[0] > range_u[1] - range_u[0]:
                range_u, range_v = range_v, range_u
                direction_u, direction_v = direction_v, direction_u
                pass

            if (np.argmax(np.abs(direction_v)) == 2 and direction_v[2] < 0) or (np.argmax(np.abs(direction_v)) != 2 and np.dot(np.array([0, 1, 0]), direction_v) < 0):
                direction_v *= -1
                projection_v *= -1
                range_v = [-range_v[1], -range_v[0]]
                pass
            if np.dot(np.cross(planeNormal, direction_v), direction_u) < 0:
                direction_u *= -1
                projection_u *= -1
                range_u = [-range_u[1], -range_u[0]]
                pass

            print((planeIndex, dominantNormal, direction_u, direction_v))

            length_u = range_u[1] - range_u[0]
            length_v = range_v[1] - range_v[0]
            if length_u * textureRatio > length_v:
                length_u = length_v / textureRatio
            else:
                length_v = length_u * textureRatio
                pass

            #logoSize = 0.35

            # center_u = (range_u[0] + range_u[1]) / 2
            # range_u = [center_u - length_u * logoSize, center_u + length_u * logoSize]

            # center_v = (range_v[0] + range_v[1]) / 2
            # range_v = [center_v - length_v * logoSize, center_v + length_v * logoSize]

            projection_u = np.tensordot(XYZ, direction_u, axes=([2], [0]))
            projection_v = np.tensordot(XYZ, direction_v, axes=([2], [0]))
            #projection_u = (projection_u - range_u[0]) / (range_u[1] - range_u[0])
            #projection_v = (projection_v - range_v[0]) / (range_v[1] - range_v[0])

            #rectangleMask = np.logical_and(np.logical_and(projection_u >= 0, projection_u <= 1), np.logical_and(projection_v >= 0, projection_v <= 1))
            #rectangleMask = np.logical_and(rectangleMask, mask)

            textureSize = 1
            projection_u = (projection_u / textureSize) % 1
            projection_v = (projection_v / textureSize) % 1
            rectangleMask = mask

            #maskImage[rectangleMask] = planeIndex

            for y in range(height - 1):
                for x in range(width - 1):
                    facePixels = []
                    for pixel in [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]:
                        if rectangleMask[pixel[1]][pixel[0]]:
                            # u = projection_u[pixel[1]][pixel[0]]
                            # v = projection_v[pixel[1]][pixel[0]]
                            # u = min(max(int(round(u * textureWidth)), 0), textureWidth - 1)
                            # v = min(max(textureHeight - 1 - int(round(v * textureHeight)), 0), textureHeight - 1)
                            # if background[v][u] == False:
                            facePixels.append(pixel)

                            #print(pixel, (x, y))
                            if pixel == (x, y):
                                u = projection_u[pixel[1]][pixel[0]]
                                v = projection_v[pixel[1]][pixel[0]]
                                u = min(
                                    max(int(round(u * textureWidth)), 0), textureWidth - 1)
                                v = min(
                                    max(textureHeight - 1 - int(round(v * textureHeight)), 0), textureHeight - 1)

                                #print(x, y)
                                #print(u, v)

                                maskImage[y][x] = textureImage[v][u]
                                pass
                            pass
                        continue

                    if len(facePixels) == 3:
                        faces.append(facePixels[0] +
                                     facePixels[1] + facePixels[2])
                        vt = []
                        for c in [0, 1, 2]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                    elif len(facePixels) == 4:
                        faces.append(facePixels[0] +
                                     facePixels[1] + facePixels[2])
                        vt = []
                        for c in [0, 1, 2]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                        faces.append(facePixels[0] +
                                     facePixels[2] + facePixels[3])
                        vt = []
                        for c in [0, 2, 3]:
                            vt.append(
                                projection_u[facePixels[c][1]][facePixels[c][0]])
                            vt.append(
                                projection_v[facePixels[c][1]][facePixels[c][0]])
                            continue
                        texcoords.append(vt)
                        pass
                    continue
                continue
            continue
        continue

    #cv2.imwrite('test/mask.png', drawSegmentationImage(maskImage, blackIndex=planes.shape[0]))

    # write a .ply file
    with open(folder + '/' + str(index) + '_logo.ply', 'w') as f:
        header = """ply
format ascii 1.0
comment VCGLIB generated
comment TextureFile """
        header += imageFilename
        header += """
element vertex """
        header += str(width * height)
        header += """
property float x
property float y
property float z
element face """
        header += str(len(faces))
        header += """
property list uchar int vertex_indices
property list uchar float texcoord
end_header
"""
        f.write(header)
        for y in range(height):
            for x in range(width):
                segmentIndex = segmentation[y][x]
                if segmentIndex == -1:
                    f.write("0.0 0.0 0.0\n")
                    continue
                point = XYZ[y][x]
                X = point[0] * 0.9999
                Y = point[1] * 0.9999
                Z = point[2] * 0.9999
                #Y = depth[y][x]
                #X = Y / focalLength * (x - width / 2) / width * 640
                #Z = -Y / focalLength * (y - height / 2) / height * 480
                f.write(str(X) + ' ' + str(Z) + ' ' + str(-Y) + '\n')
                continue
            continue

        for faceIndex, face in enumerate(faces):
            f.write('3 ')
            for c in range(3):
                f.write(str(face[c * 2 + 1] * width + face[c * 2]) + ' ')
                continue
            f.write('6 ')
            vt = texcoords[faceIndex]
            for value in vt:
                f.write(str(value) + ' ')
                continue
            # for c in xrange(3):
            #     f.write(str(float(face[c * 2]) / width) + ' ' + str(1 - float(face[c * 2 + 1]) / height) + ' ')
            #     continue
            f.write('\n')
            continue
        f.close()
        pass
    return maskImage


# video applications (extension the logo/texture copying application)
def copyLogoVideo(textureImageFilename, folder, index, image, depth, planes, segmentation, info, textureType='logo', wallInds=[]):
    from sklearn.cluster import KMeans
    from skimage import measure
    #from sklearn.decomposition import PCA

    width = segmentation.shape[1]
    height = segmentation.shape[0]

    camera = getCameraFromInfo(info)

    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange
    XYZ = np.stack([X, Y, Z], axis=2)
    #plane_depths = calcPlaneDepths(planes, width, height, info)

    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    planeAreaThreshold = width * height / 100
    normals = []
    for planeIndex in range(planes.shape[0]):
        mask = segmentation == planeIndex
        if mask.sum() < planeAreaThreshold:
            continue
        normals.append(planesNormal[planeIndex])
        continue

    normals = np.stack(normals, axis=0)
    normals[normals[:, 1] < 0] *= -1

    kmeans = KMeans(n_clusters=3).fit(normals)
    dominantNormals = kmeans.cluster_centers_
    dominantNormals = dominantNormals / \
        np.maximum(np.linalg.norm(dominantNormals,
                                  axis=-1, keepdims=True), 1e-4)

    normals = planesNormal.copy()
    normals[normals[:, 1] < 0] *= -1
    planeClusters = kmeans.predict(normals)

    #texture_image_names = glob.glob('../texture_images/*.png') + glob.glob('../texture_images/*.jpg')

    #imageFilename = '/home/chenliu/Projects/PlaneNet/texture_images/CVPR.jpg'
    #textureImage = cv2.imread(imageFilename)

    #textureImage = cv2.imread('../texture_images/CVPR_transparent.png')

    # either copy a logo or a wall texture or a TV screen
    if textureType == 'wall':
        textureImage = cv2.imread(textureImageFilename)
        alphaMask = np.ones((textureImage.shape[0], textureImage.shape[1], 1))
    elif textureType == 'logo':
        textureImage = cv2.imread(textureImageFilename)
        alphaMask = (textureImage.mean(2) < 224).astype(np.float32)
        alphaMask = np.expand_dims(alphaMask, -1)
    else:
        textureVideo = cv2.VideoCapture(textureImageFilename)
        ret, textureImage = textureVideo.read()
        # numFrames = 0
        # for i in xrange(500):
        #     ret, textureImage = textureVideo.read()
        #     if not ret:
        #         break
        #     numFrames += 1
        #     print(i, textureImage.shape)
        #     continue
        # print(numFrames)
        # print(textureImage.shape)
        # exit(1)
        alphaMask = np.ones((textureImage.shape[0], textureImage.shape[1], 1))
        pass

    #backgroundMask = cv2.erode(backgroundMask.astype(np.uint8), np.ones((3, 3)))
    #cv2.imwrite('test/mask.png', drawMaskImage(background))
    # exit(1)

    textureHeight = float(textureImage.shape[0])
    textureWidth = float(textureImage.shape[1])
    textureRatio = textureHeight / textureWidth
    textureSizes2D = np.array([textureWidth, textureHeight])

    textureSizeU = 0.75
    textureSizeV = textureSizeU * textureRatio
    textureSizes = np.array([textureSizeU, textureSizeV])

    # calculate projection information
    planeMasks = []
    planeProjections = []
    planeRanges = []
    for planeIndex in range(planes.shape[0]):
        if textureType != 'logo' and planeIndex not in wallInds:
            continue

        globalMask = segmentation == planeIndex
        if globalMask.sum() < planeAreaThreshold:
            continue

        masks = measure.label(globalMask.astype(np.int32), background=0)
        # print(masks.max())
        # print(masks.min())
        #cv2.imwrite('test/mask.png', drawSegmentationImage(masks, blackIndex=planes.shape[0]))
        # exit(1)
        for maskIndex in range(masks.min() + 1, masks.max() + 1):
            mask = masks == maskIndex
            if mask.sum() < planeAreaThreshold:
                continue

            planeNormal = planesNormal[planeIndex]

            cluster = planeClusters[planeIndex]
            dominantNormal = dominantNormals[(cluster + 1) % 3]
            direction_u = np.cross(planeNormal, dominantNormal)
            direction_u = direction_u / \
                np.maximum(np.linalg.norm(direction_u), 1e-4)
            direction_v = np.cross(planeNormal, direction_u)
            direction_v = direction_v / \
                np.maximum(np.linalg.norm(direction_v), 1e-4)

            points = XYZ[mask]
            projection_u = np.tensordot(points, direction_u, axes=([1], [0]))
            range_u = [projection_u.min(), projection_u.max()]
            projection_v = np.tensordot(points, direction_v, axes=([1], [0]))
            range_v = [projection_v.min(), projection_v.max()]
            if textureType != 'wall' and range_v[1] - range_v[0] > range_u[1] - range_u[0]:
                range_u, range_v = range_v, range_u
                direction_u, direction_v = direction_v, direction_u
                pass
            if textureType != 'wall' and abs(direction_u[2]) > abs(direction_v[2]):
                range_u, range_v = range_v, range_u
                direction_u, direction_v = direction_v, direction_u
                pass

            if (np.argmax(np.abs(direction_v)) == 2 and direction_v[2] < 0) or (np.argmax(np.abs(direction_v)) != 2 and np.dot(np.array([0, 1, 0]), direction_v) < 0):
                direction_v *= -1
                projection_v *= -1
                range_v = [-range_v[1], -range_v[0]]
                pass
            if np.dot(np.cross(planeNormal, direction_v), direction_u) < 0:
                direction_u *= -1
                projection_u *= -1
                range_u = [-range_u[1], -range_u[0]]
                pass

            #print(planeIndex, dominantNormal, direction_u, direction_v)
            projection_u = np.tensordot(XYZ, direction_u, axes=([2], [0]))
            projection_v = np.tensordot(XYZ, direction_v, axes=([2], [0]))
            planeProjections.append(
                np.stack([projection_u, projection_v], axis=-1).reshape((-1, 2)))
            ranges = np.stack([range_u, range_v], axis=-1)
            ranges = np.stack([ranges.mean(0) - (ranges[1] - ranges[0]) *
                               0.35, ranges.mean(0) + (ranges[1] - ranges[0]) * 0.35], axis=0)
            planeRanges.append(ranges)
            planeMasks.append(mask.reshape(-1))
            continue
        continue

    numMasks = len(planeProjections)
    print(('the number of masks', numMasks))

    #maskImage = np.full(segmentation.shape, planes.shape[0])
    #ratios = np.full(2, 0.5)

    # move textures around
    planeRatios = np.random.random((numMasks, 2))
    randomDirection = np.random.random((numMasks, 2))
    if textureType == 'wall':
        randomDirection = np.stack(
            [np.ones(numMasks), np.zeros(numMasks)], axis=1)
        randomDirection[0] *= -1
        pass
    randomDirection = randomDirection / np.linalg.norm(randomDirection)
    stride = 0.01

    # write a sequence of images
    numFrames = 500
    for frameIndex in range(numFrames):

        # different ways of moving textures for different applications
        if textureType != 'TV':
            planeRatios += randomDirection * stride
        else:

            # tweak planeDynamicRanges and TVSize for better visualization
            ranges = np.array(planeRanges)
            planeDynamicRanges = np.concatenate(
                [ranges[:, 0], ranges[:, 1]], axis=1)
            TVSize = ranges[:, 1] - ranges[:, 0]

            for planeIndex in range(2):
                planeDynamicRanges[planeIndex, 2:] = planeDynamicRanges[planeIndex, :2] + max(min(float(
                    frameIndex - numFrames / 2 * planeIndex) / (numFrames / 3), 1.0), 0.0) * TVSize[planeIndex]
                continue
            ret, textureImage = textureVideo.read()
            if not ret:
                textureVideo.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)
                continue
                # break
            pass

        if textureType == 'logo':
            invalidMask = np.logical_or(planeRatios >= 1, planeRatios <= 0)
            planeRatios = np.maximum(np.minimum(planeRatios, 1), 0)
            randomDirection[invalidMask] *= -1
            pass

        resultImage = image.copy().reshape((-1, 3))
        for planeIndex in range(numMasks):
            mask = planeMasks[planeIndex]
            ranges = planeRanges[planeIndex]
            projections = planeProjections[planeIndex]
            ratios = planeRatios[planeIndex]

            offsets = ranges[0] + (ranges[1] - ranges[0]) * \
                ratios - textureSizes / 2

            #print(projections.max(0), projections.min(0))
            if textureType == 'TV':
                projectionsMoved = (projections - planeDynamicRanges[planeIndex, :2]) / np.maximum(
                    planeDynamicRanges[planeIndex, 2:] - planeDynamicRanges[planeIndex, :2], 1e-4)
            else:
                projectionsMoved = (projections - offsets) / textureSizes
                pass

            if textureType == 'wall':
                rectangleMask = mask
            else:
                rectangleMask = np.logical_and(
                    projectionsMoved >= 0, projectionsMoved <= 1)
                rectangleMask = np.logical_and(
                    rectangleMask[:, 0], rectangleMask[:, 1])
                rectangleMask = np.logical_and(rectangleMask, mask)
                pass

            rectangleIndices = rectangleMask.nonzero()[0]

            uv = projectionsMoved[rectangleIndices] * textureSizes2D
            uv[:, 1] = textureSizes2D[1] - 1 - uv[:, 1]
            if textureType == 'wall':
                uv = uv % (textureSizes2D - 1)
            else:
                uv = np.maximum(np.minimum(uv, textureSizes2D - 1), 0)
                pass

            u = uv[:, 0]
            v = uv[:, 1]
            u_min = np.floor(u).astype(np.int32)
            u_max = np.ceil(u).astype(np.int32)
            v_min = np.floor(v).astype(np.int32)
            v_max = np.ceil(v).astype(np.int32)

            area_11 = (u_max - u) * (v_max - v)
            area_12 = (u_max - u) * (v - v_min)
            area_21 = (u - u_min) * (v_max - v)
            area_22 = (u - u_min) * (v - v_min)

            area_11 = np.expand_dims(area_11, -1)
            area_12 = np.expand_dims(area_12, -1)
            area_21 = np.expand_dims(area_21, -1)
            area_22 = np.expand_dims(area_22, -1)

            colors_11 = textureImage[v_min, u_min]
            colors_12 = textureImage[v_max, u_min]
            colors_21 = textureImage[v_min, u_max]
            colors_22 = textureImage[v_max, u_max]

            alphas_11 = alphaMask[v_min, u_min]
            alphas_12 = alphaMask[v_max, u_min]
            alphas_21 = alphaMask[v_min, u_max]
            alphas_22 = alphaMask[v_max, u_max]

            colors = colors_11 * area_11 + colors_12 * area_12 + \
                colors_21 * area_21 + colors_22 * area_22
            alphas = alphas_11 * area_11 + alphas_12 * area_12 + \
                alphas_21 * area_21 + alphas_22 * area_22
            #alphas = np.expand_dims(alphas, -1)
            #foreground = foregroundMask[uv[:, 1], uv[:, 0]]
            #indices = rectangleIndices[foreground]
            #uv = uv[foreground]

            #rectangleMask = np.logical_and(rectangleMask, foreground)

            resultImage[rectangleIndices] = resultImage[rectangleIndices] * \
                (1 - alphas) + colors * alphas
            continue
        cv2.imwrite(folder + '/' + ('%04d' % frameIndex) +
                    '.png', resultImage.reshape(image.shape))
        continue
    #cv2.imwrite('test/mask.png', drawSegmentationImage(maskImage, blackIndex=planes.shape[0]))
    #cv2.imwrite('test/mask.png', drawSegmentationImage(maskImage, blackIndex=planes.shape[0]))

    return


# the ruler application
def addRulerPlane(textureImageFilename, folder, index, image, depth, planes, segmentation, info, startPixel, endPixel, fixedEndPoint=False):

    width = segmentation.shape[1]
    height = segmentation.shape[0]

    camera = getCameraFromInfo(info)

    # calculate corresponding 3D position for each pixel
    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange
    XYZ = np.stack([X, Y, Z], axis=2)
    #plane_depths = calcPlaneDepths(planes, width, height, info)

    # calculate plane offsets and normals
    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    planeAreaThreshold = width * height / 100

    normals = []
    for planeIndex in range(planes.shape[0]):
        mask = segmentation == planeIndex
        if mask.sum() < planeAreaThreshold:
            continue
        normals.append(planesNormal[planeIndex])
        continue
    normals = np.stack(normals, axis=0)
    normals[normals[:, 1] < 0] *= -1

    #texture_image_names = glob.glob('../texture_images/*.png') + glob.glob('../texture_images/*.jpg')

    #imageFilename = '/home/chenliu/Projects/PlaneNet/texture_images/CVPR.jpg'
    #textureImage = cv2.imread(imageFilename)

    #textureImage = cv2.imread('../texture_images/CVPR_transparent.png')
    textureImage = cv2.imread(textureImageFilename)
    alphaMask = np.ones(
        (textureImage.shape[0], textureImage.shape[1], 1), dtype=np.float32)
    #alphaMask = (textureImage.mean(2) < 224).astype(np.float32)
    #alphaMask = np.expand_dims(alphaMask, -1)

    #backgroundMask = cv2.erode(backgroundMask.astype(np.uint8), np.ones((3, 3)))
    #cv2.imwrite('test/mask.png', drawMaskImage(background))
    # exit(1)

    textureHeight = float(textureImage.shape[0])
    textureWidth = float(textureImage.shape[1])
    textureRatio = textureHeight / textureWidth
    textureSizes2D = np.array([textureWidth, textureHeight])

    textureSizeU = 0.96
    textureSizeV = textureSizeU * textureRatio
    textureSizes = np.array([textureSizeU, textureSizeV])
    #textureImage = cv2.imread('../textures/texture_2.jpg')
    #textureImage = cv2.resize(textureImage, (width, height), interpolation=cv2.INTER_LINEAR)

    # find the starting plane, the ending plane, and the boundary point
    startPlaneIndex = segmentation[startPixel[1]][startPixel[0]]
    endPlaneIndex = segmentation[endPixel[1]][endPixel[0]]
    assert(startPlaneIndex < planes.shape[0]
           and endPlaneIndex < planes.shape[0])
    startPoint = XYZ[startPixel[1]][startPixel[0]]
    endPoint = XYZ[endPixel[1]][endPixel[0]]

    mask = (segmentation == startPlaneIndex).astype(np.uint8)

    if startPlaneIndex != endPlaneIndex:
        boundary = mask - cv2.erode(mask, np.ones((3, 3), dtype=np.uint8))
        boundaryPoints = XYZ[boundary.nonzero()]
        if fixedEndPoint:
            distances = np.linalg.norm(
                boundaryPoints - startPoint, axis=-1) + np.linalg.norm(boundaryPoints - endPoint, axis=-1)
            boundaryPoint = boundaryPoints[np.argmin(distances)]
        else:
            endPlane = planes[endPlaneIndex]
            endPlaneD = np.linalg.norm(endPlane)
            endPlaneNormal = endPlane / endPlaneD
            endDistances = endPlaneD - \
                np.tensordot(boundaryPoints, endPlaneNormal, axes=(1, 0))
            distances = np.linalg.norm(
                boundaryPoints - startPoint, axis=-1) + np.abs(endDistances)
            boundaryPointIndex = np.argmin(distances)
            boundaryPoint = boundaryPoints[boundaryPointIndex]
            endDistance = endDistances[boundaryPointIndex]
            endPoint = boundaryPoint + endDistance * endPlaneNormal
            pass
    else:
        boundaryPoint = startPoint
        pass

    # find planes which the ruler passes by on the image domain
    passbyPlaneInds = []
    for offset in np.arange(0.1, 1, 0.1):
        point = boundaryPoint + (endPoint - boundaryPoint) * offset
        u = int(round(point[0] / point[1] * camera['fx'] + camera['cx']))
        v = int(round(-point[2] / point[1] * camera['fy'] + camera['cy']))
        planeIndex = segmentation[v][u]
        if planeIndex != startPlaneIndex and planeIndex < planes.shape[0] and planeIndex not in passbyPlaneInds:
            passbyPlaneInds.append(planeIndex)
            pass
        continue
    print(passbyPlaneInds)
    if len(passbyPlaneInds):
        passbyPlaneNormal = planesNormal[passbyPlaneInds[0]]
    else:
        passbyPlaneNormal = np.array([0, 1, 0])
        pass

    resultImage = image.copy().reshape((-1, 3))
    distanceOffset = 0

    # draw two segments of ruler (from the starting point to the boundary point and from the boundary point to the ending point)
    for point_1, point_2, planeNormal, planeInds in [(startPoint, boundaryPoint, planesNormal[startPlaneIndex], [startPlaneIndex]), (boundaryPoint, endPoint, passbyPlaneNormal, passbyPlaneInds)]:
        if point_1[0] == point_2[0] and point_1[1] == point_2[1]:
            continue

        direction_u = point_2 - point_1
        direction_u = direction_u / \
            np.maximum(np.linalg.norm(direction_u), 1e-4)
        direction_v = -np.cross(planeNormal, direction_u)
        direction_v = direction_v / \
            np.maximum(np.linalg.norm(direction_v), 1e-4)
        projection_u = np.tensordot(
            XYZ, direction_u, axes=([2], [0])).reshape(-1)
        projection_v = np.tensordot(
            XYZ, direction_v, axes=([2], [0])).reshape(-1)

        offset_u = np.dot(point_1, direction_u)
        offset_v = np.dot(point_1, direction_v)

        projection_u = (projection_u - offset_u) / textureSizeU
        projection_v = (projection_v - offset_v) / textureSizeV

        rectangleMask = np.logical_and(np.logical_and(projection_u >= distanceOffset / textureSizeU, projection_u <= (
            distanceOffset + np.linalg.norm(point_2 - point_1)) / textureSizeU), np.logical_and(projection_v >= 0, projection_v <= 1))

        if len(planeInds) > 0:
            validMask = np.zeros(segmentation.shape, dtype=np.bool)
            for planeIndex in planeInds:
                validMask = np.logical_or(
                    validMask, segmentation == planeIndex)
                continue
            rectangleMask = np.logical_and(
                rectangleMask, validMask.reshape(-1))
            pass

        rectangleIndices = rectangleMask.nonzero()[0]

        projections = np.stack(
            [projection_u[rectangleIndices], projection_v[rectangleIndices]], axis=1)
        uv = projections * textureSizes2D

        uv[:, 1] = textureSizes2D[1] - 1 - uv[:, 1]
        uv = np.maximum(np.minimum(uv, textureSizes2D - 1), 0)

        u = uv[:, 0]
        v = uv[:, 1]
        u_min = np.floor(u).astype(np.int32)
        u_max = np.ceil(u).astype(np.int32)
        v_min = np.floor(v).astype(np.int32)
        v_max = np.ceil(v).astype(np.int32)

        area_11 = (u_max - u) * (v_max - v)
        area_12 = (u_max - u) * (v - v_min)
        area_21 = (u - u_min) * (v_max - v)
        area_22 = (u - u_min) * (v - v_min)

        area_11 = np.expand_dims(area_11, -1)
        area_12 = np.expand_dims(area_12, -1)
        area_21 = np.expand_dims(area_21, -1)
        area_22 = np.expand_dims(area_22, -1)

        colors_11 = textureImage[v_min, u_min]
        colors_12 = textureImage[v_max, u_min]
        colors_21 = textureImage[v_min, u_max]
        colors_22 = textureImage[v_max, u_max]

        alphas_11 = alphaMask[v_min, u_min]
        alphas_12 = alphaMask[v_max, u_min]
        alphas_21 = alphaMask[v_min, u_max]
        alphas_22 = alphaMask[v_max, u_max]

        colors = colors_11 * area_11 + colors_12 * area_12 + \
            colors_21 * area_21 + colors_22 * area_22
        alphas = alphas_11 * area_11 + alphas_12 * area_12 + \
            alphas_21 * area_21 + alphas_22 * area_22

        resultImage[rectangleIndices] = resultImage[rectangleIndices] * \
            (1 - alphas) + colors * alphas

        distanceOffset += np.linalg.norm(point_2 - point_1)
        print((point_1, point_2))
        print(direction_u)
        print(direction_v)
        cv2.imwrite('test/result.png', resultImage.reshape(image.shape))
        exit(1)
        continue
    return

# the ruler application (video version)


def addRuler(textureImage, folder, indexOffset, image, depth, planes, segmentation, info, startPoint, endPoint, boundaryPoints, startPlaneIndex, fixedEndPoint=False, numFrames=1):
    width = segmentation.shape[1]
    height = segmentation.shape[0]

    #info[0] -= 40
    #info[5] -= 40

    camera = getCameraFromInfo(info)

    # calculate plane offsets and normals
    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    alphaMask = np.ones(
        (textureImage.shape[0], textureImage.shape[1], 1), dtype=np.float32)
    #alphaMask = (textureImage.mean(2) < 224).astype(np.float32)
    #alphaMask = np.expand_dims(alphaMask, -1)

    #backgroundMask = cv2.erode(backgroundMask.astype(np.uint8), np.ones((3, 3)))
    #cv2.imwrite('test/mask.png', drawMaskImage(background))
    # exit(1)

    textureHeight = float(textureImage.shape[0])
    textureWidth = float(textureImage.shape[1])
    textureRatio = textureHeight / textureWidth
    textureSizes2D = np.array([textureWidth, textureHeight])

    #textureSizeU = 0.96
    #textureSizeU = 0.3048
    textureSizeU = 0.9144
    #textureSizeU = 0.78
    textureSizeV = textureSizeU * textureRatio
    textureSizes = np.array([textureSizeU, textureSizeV])
    #textureImage = cv2.imread('../textures/texture_2.jpg')
    #textureImage = cv2.resize(textureImage, (width, height), interpolation=cv2.INTER_LINEAR)

    # find the boundary point
    distances = np.linalg.norm(boundaryPoints - startPoint, axis=-1) + \
        np.linalg.norm(boundaryPoints - endPoint, axis=-1)
    boundaryPoint = boundaryPoints[np.argmin(distances)]

    print(startPoint)
    print((startPoint[0] / startPoint[1] * camera['fx'] + camera['cx'], -
           startPoint[2] / startPoint[1] * camera['fy'] + camera['cy']))
    print(boundaryPoint)
    print((boundaryPoint[0] / boundaryPoint[1] * camera['fx'] + camera['cx'], -
           boundaryPoint[2] / boundaryPoint[1] * camera['fy'] + camera['cy']))

    boundaryPointNeighbors = boundaryPoints[np.linalg.norm(
        boundaryPoints - boundaryPoint, axis=-1) < 0.05]
    boundaryDirections = []
    for boundaryPointNeighbor in boundaryPointNeighbors:
        boundaryDirection = boundaryPointNeighbor - boundaryPoint
        norm = np.linalg.norm(boundaryDirection, axis=-1)
        if norm < 1e-4:
            continue
        boundaryDirection /= norm
        if np.dot(np.cross(boundaryPoint - startPoint, planesNormal[startPlaneIndex]), boundaryDirection) > 0:
            boundaryDirections.append(boundaryDirection)
        else:
            boundaryDirections.append(-boundaryDirection)
            pass
        continue

    if len(boundaryDirections) == 0:
        distances = np.argmin(np.linalg.norm(
            boundaryPoints - boundaryPoint, axis=-1))
        neighborIndex = np.argpartition(distances, 2)[1]
        boundaryNeighbor = boundaryPoints[neighborIndex]
        boundaryDirection = boundaryPointNeighbor - boundaryPoint
        norm = np.linalg.norm(boundaryDirection, axis=-1)
        boundaryDirection /= norm
        boundaryDirections.append(boundaryDirection)
        pass

    boundaryDirections = np.array(boundaryDirections)

    boundaryDirection = boundaryDirections.mean(0)
    boundaryDirection /= np.linalg.norm(boundaryDirection)

    boundaryNormal = np.cross(boundaryDirection, endPoint - boundaryPoint)
    boundaryNormal /= np.linalg.norm(boundaryNormal)

    totalLength = np.linalg.norm(
        endPoint - boundaryPoint) + np.linalg.norm(boundaryPoint - startPoint)
    distanceOffset = 0

    resultImage = image.copy().reshape((-1, 3))

    camera = getCameraFromInfo(info)
    # print(camera)
    #print('total length', totalLength, np.linalg.norm(endPoint - boundaryPoint), np.linalg.norm(boundaryPoint - startPoint))
    # exit(1)
    firstSegment = True

    #IBL = IBL.reshape((width * height, -1))

    # draw two segments of ruler (from the starting point to the boundary point and from the boundary point to the ending point)
    for point_1, point_2, planeNormal in [(startPoint, boundaryPoint, planesNormal[startPlaneIndex]), (boundaryPoint, endPoint, boundaryNormal)]:
        if point_1[0] == point_2[0] and point_1[1] == point_2[1]:
            continue

        #planeNormal = np.cross(endPoint - startPoint, verticalDirection)
        #planeNormal = planeNormal / np.linalg.norm(planeNormal)
        planeD = np.dot(point_1, planeNormal)

        urange = (np.arange(width, dtype=np.float32) / width *
                  camera['width'] - camera['cx']) / camera['fx']
        urange = urange.reshape(1, -1).repeat(height, 0)
        vrange = (np.arange(height, dtype=np.float32) / height *
                  camera['height'] - camera['cy']) / camera['fy']
        vrange = vrange.reshape(-1, 1).repeat(width, 1)

        coef = urange * planeNormal[0] + \
            planeNormal[1] + (-vrange) * planeNormal[2]
        Y = planeD / coef
        X = urange * Y
        Z = -vrange * Y
        XYZ = np.stack([X, Y, Z], axis=2)

        direction_u = point_2 - point_1
        direction_u = direction_u / \
            np.maximum(np.linalg.norm(direction_u), 1e-4)
        direction_v = -np.cross(planeNormal, direction_u)
        direction_v = direction_v / \
            np.maximum(np.linalg.norm(direction_v), 1e-4)

        offset_v = np.dot(point_1, direction_v)

        if firstSegment:
            direction_u *= 0.6
            #point_2 -= direction_u * 0.001
            offset_v -= 0.002
        else:
            distanceOffset -= 0.02
            pass

        offset_u = np.dot(point_1, direction_u)

        projection_u = np.tensordot(
            XYZ, direction_u, axes=([2], [0])).reshape(-1)
        projection_v = np.tensordot(
            XYZ, direction_v, axes=([2], [0])).reshape(-1)

        projection_u = (projection_u - offset_u +
                        distanceOffset) / textureSizeU
        projection_v = (projection_v - offset_v) / textureSizeV

        # print('u', projection_u[850 * width + 1050])
        # print('u', projection_u[958 * width + 1060])
        # print('u', projection_u[1064 * width + 1074])
        # print(point_1, point_2, planeNormal)
        # print(np.dot(planeNormal, point_2 - point_1))
        # print(np.dot(point_1, planeNormal) - planeD, np.dot(point_2, planeNormal) - planeD)

        for frameIndex in range(numFrames):
            maxOffset = min(float(frameIndex + 1) / numFrames * totalLength,
                            distanceOffset + np.linalg.norm(point_2 - point_1))
            minOffset = max(float(frameIndex) / numFrames *
                            totalLength, distanceOffset)
            #print(minOffset, maxOffset)
            if minOffset >= maxOffset:
                continue

            if firstSegment:
                maxOffset = min(maxOffset, distanceOffset +
                                np.linalg.norm(point_2 - point_1) - 0.018)
                pass

            rectangleMask = np.logical_and(np.logical_and(projection_u >= minOffset / textureSizeU, projection_u <
                                                          maxOffset / textureSizeU), np.logical_and(projection_v >= 0, projection_v <= 1))

            rectangleIndices = rectangleMask.nonzero()[0]

            projections = np.stack(
                [projection_u[rectangleIndices], projection_v[rectangleIndices]], axis=1)
            uv = projections * textureSizes2D

            uv[:, 1] = textureSizes2D[1] - 1 - uv[:, 1]
            uv = np.maximum(np.minimum(uv, textureSizes2D - 1), 0)

            u = uv[:, 0]
            v = uv[:, 1]
            u_min = np.floor(u).astype(np.int32)
            u_max = np.ceil(u).astype(np.int32)
            v_min = np.floor(v).astype(np.int32)
            v_max = np.ceil(v).astype(np.int32)

            area_11 = (u_max - u) * (v_max - v)
            area_12 = (u_max - u) * (v - v_min)
            area_21 = (u - u_min) * (v_max - v)
            area_22 = (u - u_min) * (v - v_min)

            area_11 = np.expand_dims(area_11, -1)
            area_12 = np.expand_dims(area_12, -1)
            area_21 = np.expand_dims(area_21, -1)
            area_22 = np.expand_dims(area_22, -1)

            colors_11 = textureImage[v_min, u_min]
            colors_12 = textureImage[v_max, u_min]
            colors_21 = textureImage[v_min, u_max]
            colors_22 = textureImage[v_max, u_max]

            alphas_11 = alphaMask[v_min, u_min]
            alphas_12 = alphaMask[v_max, u_min]
            alphas_21 = alphaMask[v_min, u_max]
            alphas_22 = alphaMask[v_max, u_max]

            colors = colors_11 * area_11 + colors_12 * area_12 + \
                colors_21 * area_21 + colors_22 * area_22
            alphas = alphas_11 * area_11 + alphas_12 * area_12 + \
                alphas_21 * area_21 + alphas_22 * area_22

            #print(np.expand_dims(IBL[rectangleIndices], -1))

            resultImage[rectangleIndices] = np.minimum(
                resultImage[rectangleIndices] * (1 - alphas) + colors * alphas, 255).astype(np.uint8)
            cv2.imwrite(folder + ('/%04d.png' % (indexOffset +
                                                 frameIndex)), resultImage.reshape(image.shape))
            continue

        distanceOffset += np.linalg.norm(point_2 - point_1)
        #print(point_1, point_2)
        # print(direction_u)
        # print(direction_v)
        firstSegment = False

        continue
    return


def addRulerComplete(textureImageFilename, folder, indexOffset, image, depth, planes, segmentation, info, startPixel, endPixel, fixedEndPoint=False, numFrames=1):
    width = segmentation.shape[1]
    height = segmentation.shape[0]

    #IBL = cv2.imread('../ibl_output/IMG_0103_IBL.exr', -1)
    # print(IBL.shape)
    # print(IBL.max())
    # print(IBL.min())
    # print(IBL.dtype)
    #IBL = cv2.resize(IBL, (width, height))
    # exit(1)

    #info[0] += 200
    #info[5] += 200
    #info[6] = height - info[6]

    camera = getCameraFromInfo(info)

    # calculate corresponding 3D position for each pixel
    urange = (np.arange(width, dtype=np.float32) / width *
              camera['width'] - camera['cx']) / camera['fx']
    urange = urange.reshape(1, -1).repeat(height, 0)
    vrange = (np.arange(height, dtype=np.float32) / height *
              camera['height'] - camera['cy']) / camera['fy']
    vrange = vrange.reshape(-1, 1).repeat(width, 1)
    X = depth * urange
    Y = depth
    Z = -depth * vrange
    XYZ = np.stack([X, Y, Z], axis=2)
    #plane_depths = calcPlaneDepths(planes, width, height, info)

    planesD = np.linalg.norm(planes, axis=-1, keepdims=True)
    planesNormal = planes / np.maximum(planesD, 1e-4)

    # find the starting plane, the ending plane, and the boundary point
    startPlaneIndex = segmentation[startPixel[1]][startPixel[0]]
    endPlaneIndex = segmentation[endPixel[1]][endPixel[0]]
    assert(startPlaneIndex < planes.shape[0]
           and endPlaneIndex < planes.shape[0])
    startPoint = XYZ[startPixel[1]][startPixel[0]]
    endPoint = XYZ[endPixel[1]][endPixel[0]]

    mask = (segmentation == startPlaneIndex).astype(np.uint8)

    boundary = mask - cv2.erode(mask, np.ones((3, 3), dtype=np.uint8))
    boundaryPoints = XYZ[boundary.nonzero()]
    boundaryPoints = boundaryPoints[boundaryPoints[:, 1] < startPoint[1]]

    endPlane = planes[endPlaneIndex]
    endPlaneD = np.linalg.norm(endPlane)
    endPlaneNormal = endPlane / endPlaneD
    endDistances = endPlaneD - \
        np.tensordot(boundaryPoints, endPlaneNormal, axes=(1, 0))
    distances = np.linalg.norm(
        boundaryPoints - startPoint, axis=-1) + np.abs(endDistances)
    boundaryPointIndex = np.argmin(distances)
    boundaryPoint = boundaryPoints[boundaryPointIndex]
    endDistance = endDistances[boundaryPointIndex]
    #finalEndPoint = boundaryPoint + endDistance * endPlaneNormal
    #finalEndPoint = boundaryPoint + 0.30 * planesNormal[startPlaneIndex]
    finalEndPoint = endPoint

    print(('points', startPoint, boundaryPoint, endPoint))
    print((startPoint[0] / startPoint[1] * camera['fx'] + camera['cx'], -
           startPoint[2] / startPoint[1] * camera['fy'] + camera['cy']))
    print((boundaryPoint[0] / boundaryPoint[1] * camera['fx'] + camera['cx'], -
           boundaryPoint[2] / boundaryPoint[1] * camera['fy'] + camera['cy']))
    print(finalEndPoint)
    print((finalEndPoint[0] / finalEndPoint[1] * camera['fx'] + camera['cx'], -
           finalEndPoint[2] / finalEndPoint[1] * camera['fy'] + camera['cy']))

    print((np.dot(planesNormal[startPlaneIndex], boundaryPoint - startPoint)))
    print((startPlaneIndex, endPlaneIndex))
    print(planes)
    print((planesNormal[startPlaneIndex]))
    print(planesD)
    # exit(1)

    # exit(1)
    #numExtendingFrames = 1000
    #numAdjustFrames = 100
    numExtendingFrames = 200

    textureImage = cv2.imread(textureImageFilename)

    # draw the image sequence
    addRuler(textureImage, folder, 0, image, depth, planes, segmentation, info, startPoint, endPoint,
             boundaryPoints, startPlaneIndex=startPlaneIndex, fixedEndPoint=True, numFrames=numExtendingFrames)

    # numAdjustFrames = 0
    # for frameIndex in xrange(numAdjustFrames):
    #     newEndPoint = endPoint + (finalEndPoint - endPoint) * (frameIndex + 1) / numAdjustFrames
    #     addRuler(textureImage, folder, numExtendingFrames + frameIndex, image, depth, planes, segmentation, info, startPoint, newEndPoint, boundaryPoints, startPlaneIndex=startPlaneIndex, fixedEndPoint=True, numFrames=1)
    #     continue
    return


def writeGridImage(image_list, width, height, gridSize):
    gridImage = np.zeros((height, width, 3))
    gapX = 0.1
    gapBetween = 0.08
    imageWidth = float(
        width) / (gridSize[0] * 2 + gridSize[0] * gapBetween + (gridSize[0] + 1) * gapX)
    gapX *= imageWidth
    gapBetween *= imageWidth

    imageHeight = imageWidth * 3 / 4

    imageWidth = int(round(imageWidth))
    imageHeight = int(round(imageHeight))
    gapX = int(round(gapX))
    gapBetween = int(round(gapBetween))
    gapY = int(
        round(float(height - imageHeight * gridSize[1]) / (gridSize[1] + 1)))

    for gridY in range(gridSize[1]):
        for gridX in range(gridSize[0]):
            image_filename = image_list[gridY * gridSize[0] + gridX]
            image = cv2.imread(image_filename)
            image = cv2.resize(image, (imageWidth, imageHeight))
            offsetY = gapY * (gridY + 1) + imageHeight * gridY
            offsetX = gapX * (gridX + 1) + imageWidth * \
                gridX * 2 + gapBetween * gridX
            gridImage[offsetY:offsetY + imageHeight,
                      offsetX:offsetX + imageWidth] = image

            segmentation_filename = image_filename.replace(
                'image', 'segmentation_pred_blended_0')
            segmentation = cv2.imread(segmentation_filename)
            segmentation = cv2.resize(segmentation, (imageWidth, imageHeight))

            offsetX = gapX * (gridX + 1) + imageWidth * gridX * \
                2 + gapBetween * gridX + imageWidth + gapBetween
            print((offsetX, imageWidth))
            gridImage[offsetY:offsetY + imageHeight,
                      offsetX:offsetX + imageWidth] = segmentation
            continue
        continue
    return gridImage
