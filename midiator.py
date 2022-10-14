#!/usr/bin/env python3

import mido,sys,signal,time,tkinter,platform,math

# globals
currentBPM = 0
currentClock = 0
isPlayback = False
currentBeat = 0
run = True

barSize = 4
patternSize = 4 # 1 pattern = 4 bar = 16 beats
trackCount = 12

song = []

screenWidth = 800
screenHeight = 480
#screenWidth = 1920
#screenHeight = 1080
screenBeatCount = 60

# platform detecter for those ugly hacks
platform = platform.system()

# signal handler
def signal_handler(signal, frame):
  global run
  print('received ctrl+c, shutting down')
  run = False
signal.signal(signal.SIGINT, signal_handler)

def getTime():
  return int(round(time.time() * 100000))

def loadSong(syxData):
  syxElectronSongHeader = [0xf0, 0x00, 0x20, 0x3c, 0x07, 0x00, 0x55, 0x01]
  if syxData[0:8] != syxElectronSongHeader:
    print('header does not match elektron song header')
    return
  else:
    print('header maches elektron song header')
  syxHeader = syxData[1:10]
  syxEncodedData = syxData[10:len(syxData)-5]
  syxChecksum = syxData[len(syxData)-5:len(syxData)-3]
  syxDataSize = syxData[len(syxData)-2]<<4 | syxData[len(syxData)-3]

  # check checksum
  tmpChecksum = sum(syxEncodedData)
  calculatedChecksum = []
  calculatedChecksum.append(tmpChecksum >> 7)
  calculatedChecksum.append(tmpChecksum & 127)
  if syxChecksum == calculatedChecksum:
    print('checksum does match')
  else:
    print('checksum is wrong')
    return

  # decode data
  decodedData = []
  mostSignificantBits = 0
  for i, byte in enumerate(syxEncodedData):
    # every 8th byte is used to hold the MSB information for the other 7 bytes
    # this is because midi only transmits 7bit numbers,
    # therefore the MSB of 8bit values need to be transmitted on their own
    if i % 8 == 0:
      mostSignificantBits = byte
    else:
      # shift the msbs one over, we start with the 7th bit and go through the loop until the 1th bit
      mostSignificantBits = mostSignificantBits << 1
      # OR the byte with the relevant bit. we mask msbs with 0x80 (1000 0000) so we only OR the relevant bit
      decodedByte = byte | (mostSignificantBits & 0x80 )
      decodedData.append(decodedByte)

  # some syx song file offsets
  # 0x19 = first row
  # 0x11b = first pattern placement
  # 0x1b = repeat on pattern setting
  # 0x118 = start of the 2 mute bytes
  reachedRowsEnd = False
  i = 0
  patternPointer = 0
  lastPattern = decodedData[0x11b]
  patternColor = 0
  while not reachedRowsEnd:
    patternCount = decodedData[0x19+4*i];
    rowRepeat = decodedData[0x1b+4*i]+1
    #print('list '+str(i)+'    offset '+str(0x19+4*i)+'   pattern count '+str(patternCount)+'   pattern repeat '+str(rowRepeat))
    row = []
    if patternCount != 0:
      for j in range(patternCount):
        pattern = decodedData[0x11b+4*patternPointer];
        trackMutes = []
        muteData = decodedData[0x118+4*patternPointer]<<8|decodedData[0x119+4*patternPointer];
        for track in range(trackCount):
          # mask out the 1st bit and convert it to boolean
          trackMutes.append(bool(muteData & 0x1))
          # shift to the next bit for the next iteration
          muteData = muteData >> 1
        #print('offset '+str(0x11b+4*patternPointer))
        patternPointer = patternPointer + 1
        if lastPattern != pattern:
          patternColor = patternColor + 1
          lastPattern = pattern
          if patternColor > 4:
            patternColor = 0
        for l in range(patternSize):
          row.append({"pattern":pattern,"trackMutes":trackMutes,"color":patternColor})
      for j in range(rowRepeat):
        for rowEntry in row:
          song.append(rowEntry)
  
    else:
      reachedRowsEnd = True

    i = i + 1

  print("loaded following song")
  print(song)

# draw canvas
# TODO interpolate inbetween frames to achive smooth animations
def drawCanvas():
  global canvas, song, platform, trackCount, currentBeat, patternSize
  if platform == 'Darwin':
    fontSizeFactor = 1.0
  else:
    fontSizeFactor = 0.7

  # clear all elements
  list = canvas.find_all()
  for l in list:
    if 'circleBPM' not in canvas.gettags(l):
      canvas.delete(l)

  # draw patterns
  headerHeight = 26
  footerHeight = 70
  trackHeight = (screenHeight - footerHeight - headerHeight) / trackCount
  startPos = int(currentBeat/barSize)
  endPosScreenCount = int((currentBeat+screenBeatCount)/barSize)+1
  endPosSong = len(song)
  if endPosScreenCount >= endPosSong:
    endPos = endPosSong
  else:
    endPos = endPosScreenCount

  for i in range(startPos, endPos):
    xPos = i * (screenWidth/screenBeatCount) * barSize - (currentBeat*(screenWidth/screenBeatCount))
    xWidth = (screenWidth/screenBeatCount) * barSize + xPos
    colors = ['#155a9c','#19b914','#6d1da2','#d25215']
    muteColors = ['#041326','#001c00','#180529','#210000']
    #colors = colors[3:]+colors[:1]
    #muteColors = muteColors[3:]+muteColors[:1]
    colorPointer = song[i]["color"]
    # pattern
    yPos = screenHeight-footerHeight-trackHeight
    for mute in song[i]["trackMutes"]:
      if mute:
        canvas.create_rectangle(xPos, yPos, xWidth, yPos+trackHeight, fill=muteColors[colorPointer], outline='')
      else:
        canvas.create_rectangle(xPos, yPos, xWidth, yPos+trackHeight, fill=colors[colorPointer], outline='')
      yPos = yPos - trackHeight

  # vertical lines and numbers
  for i in range(startPos, endPosScreenCount):
    xPos = i * (screenWidth/screenBeatCount) * barSize - (currentBeat*(screenWidth/screenBeatCount))
    canvas.create_line(xPos, 0, xPos, screenHeight-footerHeight, fill='#202020', width=1)
    canvas.create_text(xPos+5, 2, anchor="nw", text=str(i+1), fill='white', font=("DefaultFont", int(16*fontSizeFactor)))
   # if i % patternSize == 0:
      #canvas.create_text(xPos+5, 2, anchor="nw", text=str(int(i/patternSize)+1), fill='white', font=("DefaultFont", int(16*fontSizeFactor)))
  # horizontal lines
  yPos = screenHeight-footerHeight
  for i in range(trackCount+1):
    canvas.create_line(0, yPos, screenWidth, yPos, fill='#202020', width=1)
    yPos = yPos-trackHeight

  # play/stop button
  if isPlayback:
    xOffset = 20
    yOffset = screenHeight - 55
    canvas.create_polygon([0+xOffset,0+yOffset,35+xOffset,20+yOffset,0+xOffset,40+yOffset], fill='#66ff00')
  else:
    xOffset = 20
    yOffset = screenHeight - 52
    canvas.create_rectangle(xOffset, yOffset, xOffset+35, yOffset+35, fill='#cc1717', outline='')

  # bpm
  canvas.create_text(screenWidth-75, screenHeight-8, anchor="se", text=str(int(round(currentBPM))), fill='white', font=("DefaultFont", int(48*fontSizeFactor)))
  canvas.create_text(screenWidth-15, screenHeight-14, anchor="se", text='BPM', fill='white', font=("DefaultFont", int(26*fontSizeFactor)))

  # beats / bars / pattern
  text = str(int(currentBeat/barSize/patternSize)+1)+' / '+str(int(currentBeat/barSize)+1)+' / '+str(currentBeat+1)
  canvas.create_text(screenWidth/2, screenHeight-37, text=text, fill='white', font=("DefaultFont", int(28*fontSizeFactor)))

def pulseBPM():
  global canvas, lastBeatTime, platform
  # calculate some value from beat thime that can be used to set the color of the pulsing box
  value = int((getTime() - lastBeatTime)/100)
  circleBPM = canvas.find_withtag("circleBPM")
  if not circleBPM:
    # bpm pulse
    xOffset = screenWidth - 67
    yOffset = screenHeight - 52
    canvas.create_rectangle(xOffset, yOffset, xOffset+50, yOffset+8, fill='white', outline='', tag='circleBPM')

  color = max(48, 255-value)
  colorString = "#%02x%02x%02x" % (color, color, color)
  canvas.itemconfig(circleBPM, fill=colorString) # change color
  #canvas.delete(circleBPM)

def quit():
  global run
  run = False

# load file and parse syx and setup song
#with open('./song.syx', 'rb') as syxFile:
#  syxData = syxFile.read()
#  loadSong(list(syxData))

# setup gui
mainWindow = tkinter.Tk()
mainWindow.title('Midiator')
mainWindow.protocol("WM_DELETE_WINDOW", quit)
canvas = tkinter.Canvas(master=mainWindow, width=screenWidth, height=screenHeight, bg='#303030',  highlightthickness=0)
drawCanvas()
canvas.pack()

# handle midi
lastBeatTime = 0
lastClock = currentClock
def midiCallback(midiMessage):
  global currentBPM, isPlayback, currentBeat, currentClock, lastBeatTime, lastClock
  if midiMessage.dict()['type'] == 'clock':
    currentClock = currentClock + 1
    # do on every beat
    if currentClock - lastClock >= 24:
      # increase beat
      currentBeat = currentBeat + 1
      lastClock = currentClock
      # calc BPM
      beatTime = getTime() - lastBeatTime
      currentBPM = 1000 / beatTime * 60 * 100
      lastBeatTime = getTime()

  # handle start & stop
  if midiMessage.dict()['type'] == 'start' or midiMessage.dict()['type'] == 'continue':
    isPlayback = True
  if midiMessage.dict()['type'] == 'stop':
    isPlayback = False
  # handle song position
  if midiMessage.dict()['type'] == 'songpos':
    currentBeat = midiMessage.dict()['pos']
    currentClock = 0
    lastClock = 0
  # load song
  if midiMessage.dict()['type'] == 'sysex':
    print('received sysex with '+str(len(midiMessage.bytes()))+' bytes')
    loadSong(midiMessage.bytes())
  # debug message
  if midiMessage.dict()['type'] != 'clock':
    print(midiMessage.dict())

# midi port chooser
midiInputPorts = mido.get_input_names()
if len(midiInputPorts) <= 0:
  print('### Error: No Midi Input Ports found ###')
  sys.exit(-1)
print('### Available Midi Input Ports ###')
for i, port in enumerate(midiInputPorts):
  print(str(i)+': '+port)

portNumber = 0
# alsa creates always a midi through on port 0, so check if we have something on port 1
if platform == 'Linux':
  if len(midiInputPorts) >= 1:
    portNumber = 1

if len(sys.argv) >= 2 and str.isdigit(sys.argv[1]):
  portNumber = int(sys.argv[1])

midiDevice = midiInputPorts[portNumber]
inport = mido.open_input(midiDevice)
print('Chosen '+midiDevice+' as Input Port')
print('##################################')

inport.callback = midiCallback

lastTime = getTime()
lastBeatTime = 0
lastClockCount = currentClock
while run:

  oldTime = getTime()
  drawCanvas()
  pulseBPM();
  mainWindow.update()
  #print('update took '+str(getTime() - oldTime));

  # do stuff every second
  if getTime() - lastTime >= 100000:
    print("BPM = "+str("{0:.4f}".format(currentBPM))+"    Clock = "+str(currentClock)+"    Playback = "+str(isPlayback)+"    Position = "+str(currentBeat)+"/"+str(currentBeat/barSize))
    lastTime = getTime()
    

