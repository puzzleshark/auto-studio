from ctypes import *
import pythoncom
import datetime
import os

edsdk = windll.edsdk


def add_time(fname):
    now = datetime.datetime.now()
    nname = fname[:-4]+'_'+now.isoformat()[:-7].replace(':','-')+fname[-4:]
    return nname


class EDSDKError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def EDErrorMsg(code):
	return "EDSDK error code: " + hex(code)
	
def Call(code):
	if code!=0:
		raise EDSDKError(EDErrorMsg(code))
		
def Release(ref):
	edsdk.EdsRelease(ref)
	
def GetChildCount(ref):
	i = c_int()
	Call(edsdk.EdsGetChildCount(ref,byref(i)))
	return i.value

def GetChild(ref,number):
	c = c_void_p()
	Call(edsdk.EdsGetChildAtIndex(ref,number,byref(c)))
	return c
	

kEdsObjectEvent_DirItemRequestTransfer  =    0x00000208
kEdsObjectEvent_DirItemCreated       =       0x00000204


ObjectHandlerType = WINFUNCTYPE   (c_int,c_int,c_void_p,c_void_p)
def ObjectHandler_py(event,object,context):
	if event==kEdsObjectEvent_DirItemCreated:
		DownloadImage(object)
	return 0
ObjectHandler = ObjectHandlerType(ObjectHandler_py)


kEdsStateEvent_WillSoonShutDown       =      0x00000303

StateHandlerType = WINFUNCTYPE   (c_int,c_int,c_int,c_void_p)
def StateHandler_py(event,state,context):
	if event==kEdsStateEvent_WillSoonShutDown:
		print("cam about to shut off")
		Call(edsdk.EdsSendCommand(context,1,0))
	return 0
StateHandler = StateHandlerType(StateHandler_py)


PropertyHandlerType = WINFUNCTYPE   (c_int,c_int,c_int,c_int,c_void_p)
def PropertyHandler_py(event,property,param,context):
	return 0
PropertyHandler = PropertyHandlerType(PropertyHandler_py)


class DirectoryItemInfo(Structure):
	_fields_ = [("size", c_int),
				("isFolder", c_int),
				("groupID",c_int),
				("option",c_int),
				("szFileName",c_char*256),
				("format",c_int)]

WaitingForImage = False
ImageFilename = None

def DownloadImage(image):
	dirinfo = DirectoryItemInfo()
	Call(edsdk.EdsGetDirectoryItemInfo(image,byref(dirinfo)))
	stream = c_void_p()
	global ImageFilename
	if ImageFilename is None:
		print("Image was taken manually")
		ImageFilename = add_time("IMG.jpg")
	Call(edsdk.EdsCreateFileStream(ImageFilename,1,2,byref(stream)))
	
	Call(edsdk.EdsDownload(image,dirinfo.size,stream))
	Call(edsdk.EdsDownloadComplete(image))
	Release(stream)
	
	global WaitingForImage
	WaitingForImage = False


kEdsSaveTo_Camera       =   1
kEdsSaveTo_Host         =   2
kEdsSaveTo_Both         =   kEdsSaveTo_Camera | kEdsSaveTo_Host
kEdsPropID_SaveTo  = 0x0000000b



class EdsCapacity(Structure):
	_fields_ = [("numberOfFreeClusters", c_int),
				("bytesPerSector", c_int),
				("reset",c_int)]


class Camera:
	def __init__(self):
		edsdk.EdsInitializeSDK()
		pythoncom.CoInitialize()
		self.cam = None
		l = CameraList()
		self.cam = l.GetCam(0)
		Call(edsdk.EdsSetObjectEventHandler(self.cam, 0x00000200, ObjectHandler, None))
		# Call(edsdk.EdsSetPropertyEventHandler(self.cam,0x100,PropertyHandler,None))
		# Call(edsdk.EdsSetCameraStateEventHandler(self.cam,0x300,StateHandler,self.cam))
		Call(edsdk.EdsOpenSession(self.cam))
		
		self.SetProperty(kEdsPropID_SaveTo,kEdsSaveTo_Camera)
		
		# set large capacity
		# cap = EdsCapacity(10000000,512,1)
		# Call(edsdk.EdsSetCapacity(self.cam,cap))
	def __del__(self):
		if self.cam is not None:
			Call(edsdk.EdsCloseSession(self.cam))
			Call(edsdk.EdsTerminateSDK())
			# Call(Release(self.cam))
	def SetProperty(self,hey,param):
		d = c_int(param)
		Call(edsdk.EdsSetPropertyData(self.cam,hey,0,4,byref(d)))
	def AutoFocus(self):
#	kEdsCameraCommand_ShutterButton_OFF					= 0x00000000,
#	kEdsCameraCommand_ShutterButton_Halfway				= 0x00000001,
#	kEdsCameraCommand_ShutterButton_Completely			= 0x00000003,
#	kEdsCameraCommand_ShutterButton_Halfway_NonAF		= 0x00010001,
#	kEdsCameraCommand_ShutterButton_Completely_NonAF	= 0x00010003,
		# note that this can fail when AF fails (error code 0x8D01)
		self.SendCommand(4,1)
	def Shoot(self,fname=None):
		# set saving flag
		global WaitingForImage
		WaitingForImage = True

		# set filename
		global ImageFilename
		if fname is None:
			ImageFilename = add_time("IMG.jpg")
		else:
			ImageFilename = fname

		# note that this can fail when AF fails (error code 0x8D01)
		self.SendCommand(0)
		# capture succeeded so go on to download image
		while WaitingForImage:
			pythoncom.PumpWaitingMessages()
		return ImageFilename
	def KeepOn(self):
		# important command - keeps the camera connected when not used
		self.SendCommand(1)
	def SendCommand(self,command,param=0):
		#define kEdsCameraCommand_TakePicture                     0x00000000
		#define kEdsCameraCommand_ExtendShutDownTimer             0x00000001
		#define kEdsCameraCommand_BulbStart						  0x00000002 
		#define kEdsCameraCommand_BulbEnd						  0x00000003 
		#define kEdsCameraCommand_DoEvfAf                         0x00000102
		#define kEdsCameraCommand_DriveLensEvf                    0x00000103
		#define kEdsCameraCommand_DoClickWBEvf                    0x00000104		
		#define kEdsCameraCommand_PressShutterButton			  0x00000004
		Call(edsdk.EdsSendCommand(self.cam,command,param))

	def start_recording(self, save_folder):
		
		if (not os.path.exists(save_folder)):
			os.makedirs(save_folder)
		
		self.save_folder = save_folder
		# set saving flag
		global WaitingForImage
		WaitingForImage = True

		# set filename
		self.SetProperty(0x00000510, 4)

	def stop_recording(self):
		global ImageFilename
		ImageFilename = os.path.join(self.save_folder, add_time("mov.mp4"))
		self.SetProperty(0x00000510, 0)
		while WaitingForImage:
			pythoncom.PumpWaitingMessages()
		return ImageFilename

class CameraList:
	def __init__(self):
		self.list = c_void_p(None)
		Call(edsdk.EdsGetCameraList(byref(self.list)))
		print("found " + str(GetChildCount(self.list)) + " cameras")
	def Count(self):
		return GetChildCount(self.list)
	def GetCam(self,number=0):
		print("get cam")
		if self.Count()<(number+1):
			raise ValueError("Camera not found, make sure it's on and connected")
		return GetChild(self.list,number)
	def __del__(self):
		Release(self.list)
	
if __name__=="__main__":
	c = Camera()
	from time import sleep

	# c.Shoot()
	c.start_recording()
	sleep(5)
	c.stop_recording()
	sleep(2)
	
	# c.AutoFocus()
	# c.Shoot()
	# input("Press Enter to continue...")
	
	del c

	sleep(2)
