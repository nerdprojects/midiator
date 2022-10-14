#!/usr/bin/env python3
import mido,sys,signal,time,tkinter,platform,math,threading

# globals
bpm = 120
run = True
playback = False
reverse = False
foreward = False
songpos = 0

# signal handler
def signal_handler(signal, frame):
  global run
  print('received ctrl+c, hit enter to shut down')
  run = False
signal.signal(signal.SIGINT, signal_handler)

def get_time():
  return int(round(time.time() * 100000))

def send_midi_clock_thread(arg):
  global outport, playback, run, songpos
  last_beat_time = get_time()
  last_clock_time = get_time()
  while run:
    if playback and get_time() - last_beat_time >= 6000000 / (bpm):
      songpos += 1
      last_beat_time = get_time()
    if playback and get_time() - last_clock_time >= 6000000 / (24 * bpm):
      outport.send(mido.Message('clock'))
      last_clock_time = get_time()
    if foreward:
      if(songpos < 16383):
        songpos += 1
        outport.send(mido.Message('songpos', pos=songpos))
        time.sleep(0.01)
    if reverse:
      if(songpos > 0):
        songpos -= 1
        outport.send(mido.Message('songpos', pos=songpos))
        time.sleep(0.01)

def print_usage():
  print('+/++/+++ : Increase BPM')
  print('-/--/--- : Increase BPM')
  print('s : Start / Stop')
  print('f : Fast Foreward')
  print('r : Reverse')
  print('p0..16383 : Set song position')
  print('x : Send SYX song')
  print('q : Quit')

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
outport = mido.open_output(midiDevice)
print('Chosen '+midiDevice+' as Output Port')
print('##################################')

thread = threading.Thread(target=send_midi_clock_thread, args=('task', ))
thread.start()

while run:
  input_value = input()
  if(input_value == '+'):
    bpm += 1
  elif(input_value == '++'):
    bpm += 10
  elif(input_value == '+++'):
    bpm += 100
  elif(input_value == '-'):
    bpm -= 1
  elif(input_value == '--'):
    bpm -= 10
  elif(input_value == '---'):
    bpm -= 100
  elif(input_value == 'f'):
    if playback:
      playback = False
      outport.send(mido.Message('stop'))
    reverse = False
    foreward = True
  elif(input_value == 'r'):
    playback = False
    foreward = False
    reverse = True
  elif(input_value == 's'):
    if playback or foreward or reverse:
      outport.send(mido.Message('stop'))
      playback = False
      foreward = False
      reverse = False
    else:
      outport.send(mido.Message('start'))
      foreward = False
      reverse = False
      playback = True
  elif(input_value.startswith('p')):
    try:
      position = int(input_value[1:])
      print(str(position))
      if position < 0 or position > 16383:
        print_usage()
        continue
      songpos = position
      outport.send(mido.Message('songpos', pos=position))
    except ValueError:
      print_usage()
      continue
  elif(input_value == 'x'):
    messages = mido.read_syx_file('song.syx')
    for message in messages:
      outport.send(message)
  elif(input_value == 'q'):
    run = False
    sys.exit()
  else:
    print_usage()

