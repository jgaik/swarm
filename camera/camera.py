import cv2
import numpy as np
from threading import Thread

class Camera:
    data = {}
    _scale_factor = 0.75
    _perspective_matrix = None
    _mask_size = None

    _frame_current = None

    def __init__(self):
        self.camera = None
        self.dictionary = cv2.aruco.custom_dictionary(20, 3, 2020)
        self.parameters = cv2.aruco.DetectorParameters_create()
        self.markers = np.zeros((20, 4))

    def __enter__(self):
        self.camera = cv2.VideoCapture(0)
        self._calibrateCamera()
        Thread(target=self._readCameraThread).start()
        print("[Camera]: Camera calibrated")

    def __exit__(self, _, __, ___):
        self.camera.release()
        self.camera = None

    def getMarkerData(self):
        self.markers[4:, :] = np.zeros((16,4))
        
        frame = cv2.warpPerspective(self._frame_current, self._perspective_matrix, self._mask_size)
        frame = cv2.resize(frame, (0, 0), fx=self._scale_factor, fy=self._scale_factor,
                           interpolation=cv2.INTER_CUBIC)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        rawCorners, rawIds, _ = cv2.aruco.detectMarkers(
            frame, self.dictionary, parameters=self.parameters)
        if rawIds is not None:
            ids = rawIds.reshape(-1)
            corners = np.array(rawCorners).squeeze(1)
            vectors = np.diff(np.delete(corners, [2, 3], axis=1), axis=1)
            centers = corners.mean(1)
            centers[:,1] = self._mask_size[1]*self._scale_factor - centers[:,1]
            visible = np.ones((len(ids), 1))
            referenceVec = np.array([0, -1])
            angles = np.pi/2 + np.arctan2(np.cross(vectors, referenceVec),
                                            np.dot(vectors, referenceVec))
            angles = np.around(angles,3)
            self.markers[ids] = np.concatenate(
                (centers, angles, visible), axis=1)
        self.data["markers"] = self.markers.tolist()
        #cv2.imwrite('piCamera1.png', frame)
        return self.data

    def _calibrateCamera(self):
        stateOK = False
        frameOut = 100
        state = [False]*4
        src = np.zeros((4, 2), dtype = "float32")
        for f in range(frameOut): 
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("[Camera]: !!!Couldn't read initial camera frame!!!")

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rawCorners, rawIds, _ = cv2.aruco.detectMarkers(
                frame, self.dictionary, parameters=self.parameters)

            if rawIds is not None:
                ids = rawIds.reshape(-1)
                corners = np.array(rawCorners).squeeze(1)
                for id in range(0,4):
                    if id in ids:
                        src[id] = corners[np.where(ids == id)[0][0]][(id + 3) % 4]
                        state[id] = True

            if all(state):
                stateOK = True
                
                #cv2.imwrite('piCamera0.png',frame)

            if stateOK:
                break

        if not stateOK:
            raise Exception("[Camera]: !!!The initial markers are not visible!!!")


        wid1 = np.sqrt(((src[3][0] - src[0][0])**2) + ((src[3][1] - src[0][1])**2))
        wid2 = np.sqrt(((src[2][0] - src[1][0])**2) + ((src[2][1] - src[1][1])**2))
        width = int(max(wid1, wid2))

        hei1 = np.sqrt(((src[3][0] - src[2][0])**2) + ((src[3][1] - src[2][1])**2))
        hei2 = np.sqrt(((src[0][0] - src[1][0])**2) + ((src[0][1] - src[1][1])**2))
        height = int(max(hei1, hei2))
        dst = np.array([[0, height-1],
                        [0, 0],
                        [width-1, 0],
                        [width-1, height-1]], dtype="float32")
        self._perspective_matrix = cv2.getPerspectiveTransform(src, dst)
        self._mask_size = (width, height)

        self.markers[0:4, :] = [[0, 0, 0, 1], 
                            [0, height * self._scale_factor, 0, 1], 
                            [width * self._scale_factor, height * self._scale_factor, 0, 1],
                            [width * self._scale_factor, 0, 0, 1]]

    def _readCameraThread(self):
        while True:
            ret, self._frame_current = self.camera.read()
            if not ret:
                self._frame_current = None
                raise Exception("[Camera]: !!!Couldn't read camera frame!!!")