from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import argparse
import imutils
import time
import dlib
import math
import cv2
import pygame
import numpy as np
from EAR import eye_aspect_ratio
from MAR import mouth_aspect_ratio
from HeadPose import getHeadTiltAndCoords

pygame.init()

alarm_sound_1 = 'alarm.wav'

# initialize dlib's face detector (HOG-based) and then create the
# facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(
    './dlib_shape_predictor/shape_predictor_68_face_landmarks.dat')

# initialize the video stream and sleep for a bit, allowing the
# camera sensor to warm up
print("[INFO] initializing camera...")

vs = VideoStream(src=0).start()
# vs = VideoStream(usePiCamera=True).start() # Raspberry Pi
time.sleep(2.0)

# 400x225 to 1024x576
frame_width = 1024
frame_height = 576

# loop over the frames from the video stream
# 2D image points. If you change the image, you need to change vector
image_points = np.array([
    (359, 391),     # Nose tip 34
    (399, 561),     # Chin 9
    (337, 297),     # Left eye left corner 37
    (513, 301),     # Right eye right corne 46
    (345, 465),     # Left Mouth corner 49
    (453, 469)      # Right mouth corner 55
], dtype="double")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

EYE_AR_THRESH = 0.25
MOUTH_AR_THRESH = 0.79
EYE_AR_CONSEC_FRAMES = 3
COUNTER = 0
# blink count
blink = 0
drowsyLimit = 30

# grab the indexes of the facial landmarks for the mouth
(mStart, mEnd) = (49, 68)

while True:
    # grab the frame from the threaded video stream, resize it to
    # have a maximum width of 400 pixels, and convert it to
    # grayscale
    # frame = vs.read()
    frame = vs.read()
    if frame is None:
        print("Error: Unable to capture a frame.")
        continue  # Skip the current iteration and continue with the next frame

    frame = imutils.resize(frame, width=1024, height=576)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    size = gray.shape

    # detect faces in the grayscale frame
    rects = detector(gray, 0)

    # check to see if a face was detected, and if so, draw the total
    # number of faces on the frame
    if len(rects) > 0:
        text = "{} face(s) found".format(len(rects))
        cv2.putText(frame, text, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # loop over the face detections
    for rect in rects:
        # compute the bounding box of the face and draw it on the
        # frame
        (bX, bY, bW, bH) = face_utils.rect_to_bb(rect)
        cv2.rectangle(frame, (bX, bY), (bX + bW, bY + bH), (0, 255, 0), 1)
        # determine the facial landmarks for the face region, then
        # convert the facial landmark (x, y)-coordinates to a NumPy
        # array
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        # extract the left and right eye coordinates, then use the
        # coordinates to compute the eye aspect ratio for both eyes
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        # average the eye aspect ratio together for both eyes
        ear = (leftEAR + rightEAR) / 2.0

        # compute the convex hull for the left and right eye, then
        # visualize each of the eyes
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        # check to see if the eye aspect ratio is below the blink
        # threshold, and if so, increment the blink frame counter

        if ear < EYE_AR_THRESH:
            COUNTER += 1
            # if the eyes were closed for a sufficient number of times
            # then show the warning
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                cv2.putText(frame, "Eyes Closed!", (500, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                blink += 1
                if blink % drowsyLimit == 0:
                    print("Driver us drowsy!")
                    pygame.mixer.music.load(alarm_sound_1)
                    pygame.mixer.music.play()
            # otherwise, the eye aspect ratio is not below the blink
            # threshold, so reset the counter and alarm
        else:
            COUNTER = 0
        
        cv2.putText(frame, "Blink Count : " + str(blink), (820, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        mouth = shape[mStart:mEnd]

        mouthMAR = mouth_aspect_ratio(mouth)
        mar = mouthMAR
        # compute the convex hull for the mouth, then
        # visualize the mouth
        mouthHull = cv2.convexHull(mouth)

        cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)
        cv2.putText(frame, "MAR: {:.2f}".format(mar), (650, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Draw text if mouth is open
        if mar > MOUTH_AR_THRESH:
            cv2.putText(frame, "Yawning!", (800, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


        # loop over the (x, y)-coordinates for the facial landmarks
        # and draw each of them
        for (i, (x, y)) in enumerate(shape):
            if i == 33:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[0] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            elif i == 8:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[1] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            elif i == 36:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[2] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            elif i == 45:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[3] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            elif i == 48:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[4] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            elif i == 54:
                # something to our key landmarks
                # save to our new key point list
                # i.e. keypoints = [(i,(x,y))]
                image_points[5] = np.array([x, y], dtype='double')
                # write on frame in Green
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            else:
                # everything to all other landmarks
                # write on frame in Red
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)
                cv2.putText(frame, str(i + 1), (x - 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        #Draw the determinant image points onto the person's face
        for p in image_points:
            cv2.circle(frame, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)

        # head_tilt_degree, start_point, end_point, end_point_alternate, angle_history = getHeadTiltAndCoords(size, image_points, frame_height)
        (head_tilt_degree, start_point, end_point, 
            end_point_alt) = getHeadTiltAndCoords(size, image_points, frame_height)

        cv2.line(frame, start_point, end_point, (255, 0, 0), 2)
        cv2.line(frame, start_point, end_point_alt, (0, 0, 255), 2)

        if head_tilt_degree:
            cv2.putText(frame, 'Head Tilt Degree: ' + str(head_tilt_degree[0]), (170, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # extract the mouth coordinates, then use the
        # coordinates to compute the mouth aspect ratio
    # show the frameq
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# print(image_points)

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()





















# # print("Hello world")
# import dlib
# import sys
# import cv2
# import time
# import numpy as np
# from scipy.spatial import distance as dist
# from threading import Thread
# import playsound
# import pygame
# #import Queue as queue

# import queue
# #import Queue
# # from light_variability import adjust_gamma

# FACE_DOWNSAMPLE_RATIO = 1.5
# RESIZE_HEIGHT = 460

# thresh = 0.27
# # modelPath = "models/shape_predictor_81_face_landmarks.dat"
# p = "shape_predictor_68_face_landmarks.dat"
# sound_path = "alarm.wav"

# detector = dlib.get_frontal_face_detector()
# # predictor = dlib.shape_predictor(modelPath)
# predictor = dlib.shape_predictor(p)

# leftEyeIndex = [36, 37, 38, 39, 40, 41]
# rightEyeIndex = [42, 43, 44, 45, 46, 47]

# blinkCount = 0
# drowsy = 0
# state = 0
# blinkTime = 0.15 #150ms
# drowsyTime = 1.5  #1500ms
# ALARM_ON = False
# GAMMA = 1.5
# threadStatusQ = queue.Queue()

# invGamma = 1.0/GAMMA
# table = np.array([((i / 255.0) ** invGamma) * 255 for i in range(0, 256)]).astype("uint8")

# def gamma_correction(image):
#     return cv2.LUT(image, table)

# def histogram_equalization(image):
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     return cv2.equalizeHist(gray) 


# def soundAlert(path, threadStatusQ):
#     pygame.mixer.init()
#     pygame.mixer.music.load(path)
#     pygame.mixer.music.play()

#     while pygame.mixer.music.get_busy():
#         if not threadStatusQ.empty():
#             FINISHED = threadStatusQ.get()
#             if FINISHED:
#                 break


# def eye_aspect_ratio(eye):
#     A = dist.euclidean(eye[1], eye[5])
#     B = dist.euclidean(eye[2], eye[4])
#     C = dist.euclidean(eye[0], eye[3])
#     ear = (A + B) / (2.0 * C)

#     return ear


# def checkEyeStatus(landmarks):
#     mask = np.zeros(frame.shape[:2], dtype = np.float32)
    
#     hullLeftEye = []
#     for i in range(0, len(leftEyeIndex)):
#         hullLeftEye.append((landmarks[leftEyeIndex[i]][0], landmarks[leftEyeIndex[i]][1]))

#     cv2.fillConvexPoly(mask, np.int32(hullLeftEye), 255)

#     hullRightEye = []
#     for i in range(0, len(rightEyeIndex)):
#         hullRightEye.append((landmarks[rightEyeIndex[i]][0], landmarks[rightEyeIndex[i]][1]))


#     cv2.fillConvexPoly(mask, np.int32(hullRightEye), 255)

#     # lenLeftEyeX = landmarks[leftEyeIndex[3]][0] - landmarks[leftEyeIndex[0]][0]
#     # lenLeftEyeY = landmarks[leftEyeIndex[3]][1] - landmarks[leftEyeIndex[0]][1]

#     # lenLeftEyeSquared = (lenLeftEyeX ** 2) + (lenLeftEyeY ** 2)
#     # eyeRegionCount = cv2.countNonZero(mask)

#     # normalizedCount = eyeRegionCount/np.float32(lenLeftEyeSquared)

#     #############################################################################
#     leftEAR = eye_aspect_ratio(hullLeftEye)
#     rightEAR = eye_aspect_ratio(hullRightEye)

#     ear = (leftEAR + rightEAR) / 2.0
#     #############################################################################

#     eyeStatus = 1          # 1 -> Open, 0 -> closed
#     if (ear < thresh):
#         eyeStatus = 0

#     return eyeStatus  

# def checkBlinkStatus(eyeStatus):
#     global state, blinkCount, drowsy
#     if(state >= 0 and state <= falseBlinkLimit):
#         if(eyeStatus):
#             state = 0

#         else:
#             state += 1

#     elif(state >= falseBlinkLimit and state < drowsyLimit):
#         if(eyeStatus):
#             blinkCount += 1 
#             state = 0

#         else:
#             state += 1


#     else:
#         if(eyeStatus):
#             state = 0
#             drowsy = 1
#             blinkCount += 1

#         else:
#             drowsy = 1

# def getLandmarks(im):
#     imSmall = cv2.resize(im, None, 
#                             fx = 1.0/FACE_DOWNSAMPLE_RATIO, 
#                             fy = 1.0/FACE_DOWNSAMPLE_RATIO, 
#                             interpolation = cv2.INTER_LINEAR)

#     rects = detector(imSmall, 0)
#     if len(rects) == 0:
#         return 0

#     newRect = dlib.rectangle(int(rects[0].left() * FACE_DOWNSAMPLE_RATIO),
#                             int(rects[0].top() * FACE_DOWNSAMPLE_RATIO),
#                             int(rects[0].right() * FACE_DOWNSAMPLE_RATIO),
#                             int(rects[0].bottom() * FACE_DOWNSAMPLE_RATIO))

#     points = []
#     [points.append((p.x, p.y)) for p in predictor(im, newRect).parts()]
#     return points

# capture = cv2.VideoCapture(0)

# if capture:
#     print(True)

# for i in range(10):
#     ret, frame = capture.read()
#     if not ret or frame is None:
#         print("Failed to capture frame or end of video stream")
#         break

# totalTime = 0.0
# validFrames = 0
# dummyFrames = 100

# print("Caliberation in Progress!")
# while(validFrames < dummyFrames):
#     validFrames += 1
#     t = time.time()
#     ret, frame = capture.read()
#     height, width = frame.shape[:2]
#     IMAGE_RESIZE = np.float32(height)/RESIZE_HEIGHT
#     frame = cv2.resize(frame, None, 
#                         fx = 1/IMAGE_RESIZE, 
#                         fy = 1/IMAGE_RESIZE, 
#                         interpolation = cv2.INTER_LINEAR)

#     # adjusted = gamma_correction(frame)
#     adjusted = histogram_equalization(frame)

#     landmarks = getLandmarks(adjusted)
#     timeLandmarks = time.time() - t

#     if landmarks == 0:
#         validFrames -= 1
#         cv2.putText(frame, "Unable to detect face, Please check proper lighting", (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
#         cv2.putText(frame, "or decrease FACE_DOWNSAMPLE_RATIO", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
#         cv2.imshow("Blink Detection Demo", frame)
#         if cv2.waitKey(1) & 0xFF == 27:
#             sys.exit()

#     else:
#         totalTime += timeLandmarks
#         # cv2.putText(frame, "Caliberation in Progress", (200, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
#         # cv2.imshow("Blink Detection Demo", frame)
        
#     # if cv2.waitKey(1) & 0xFF == 27:
#     #         sys.exit()

# print("Caliberation Complete!")

# spf = totalTime/dummyFrames
# print("Current SPF (seconds per frame) is {:.2f} ms".format(spf * 1000))

# drowsyLimit = drowsyTime/spf
# falseBlinkLimit = blinkTime/spf
# print("drowsy limit: {}, false blink limit: {}".format(drowsyLimit, falseBlinkLimit))

# if __name__ == "__main__":
#     vid_writer = cv2.VideoWriter('output-low-light-2.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 15, (frame.shape[1],frame.shape[0]))
#     while(1):
#         try:
#             t = time.time()
#             ret, frame = capture.read()
#             height, width = frame.shape[:2]
#             IMAGE_RESIZE = np.float32(height)/RESIZE_HEIGHT
#             frame = cv2.resize(frame, None, 
#                                 fx = 1/IMAGE_RESIZE, 
#                                 fy = 1/IMAGE_RESIZE, 
#                                 interpolation = cv2.INTER_LINEAR)

#             # adjusted = gamma_correction(frame)
#             adjusted = histogram_equalization(frame)

#             landmarks = getLandmarks(adjusted)
#             if landmarks == 0:
#                 validFrames -= 1
#                 cv2.putText(frame, "Unable to detect face, Please check proper lighting", (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
#                 cv2.putText(frame, "or decrease FACE_DOWNSAMPLE_RATIO", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
#                 cv2.imshow("Blink Detection Demo", frame)
#                 if cv2.waitKey(1) & 0xFF == 27:
#                     break
#                 continue

#             eyeStatus = checkEyeStatus(landmarks)
#             checkBlinkStatus(eyeStatus)

#             for i in range(0, len(leftEyeIndex)):
#                 cv2.circle(frame, (landmarks[leftEyeIndex[i]][0], landmarks[leftEyeIndex[i]][1]), 1, (0, 0, 255), -1, lineType=cv2.LINE_AA)

#             for i in range(0, len(rightEyeIndex)):
#                 cv2.circle(frame, (landmarks[rightEyeIndex[i]][0], landmarks[rightEyeIndex[i]][1]), 1, (0, 0, 255), -1, lineType=cv2.LINE_AA)

#             if drowsy:
#                 cv2.putText(frame, "! ! ! DROWSINESS ALERT ! ! !", (70, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
#                 if not ALARM_ON:
#                     ALARM_ON = True
#                     threadStatusQ.put(not ALARM_ON)
#                     thread = Thread(target=soundAlert, args=(sound_path, threadStatusQ,))
#                     thread.setDaemon(True)
#                     thread.start()

#             else:
#                 cv2.putText(frame, "Blinks : {}".format(blinkCount), (460, 80), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0,0,255), 2, cv2.LINE_AA)
#                 # (0, 400)
#                 ALARM_ON = False


#             cv2.imshow("Blink Detection Demo", frame)
#             vid_writer.write(frame)

#             k = cv2.waitKey(1) 
#             if k == ord('r'):
#                 state = 0
#                 drowsy = 0
#                 ALARM_ON = False
#                 threadStatusQ.put(not ALARM_ON)

#             elif k == 27:
#                 break

#             # print("Time taken", time.time() - t)

#         except Exception as e:
#             print(e)

#     capture.release()
#     vid_writer.release()
#     cv2.destroyAllWindows()

#!/usr/bin/env python