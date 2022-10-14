# Midiator
This application can be used to display Elektron Analog Rytm Songs.
<img src="https://raw.githubusercontent.com/nerdprojects/midiator/main/midiator.png"/>

## Info
The idea behind this is, that two or more musicians can synchronize their performance based on the visual representation of the Rytm song and its patterns.

The application listens on the MIDI interface for a Rytm Song SYSEX message.
When it receives one, it parses it and fills the screen and its 12 tracks with alternating colors for the defined patterns.
Mutes are shown in a darker color.
It also listens to MIDI clock messages, which advance the songs position accordingly. Besides that start, stop and song position messages are picked up.

## How To
1. Connect the computer that runs the midiator.py script to the Rytm via MIDI.
   (I successfully tried it on a Mac and a Raspberry with a USB MIDI adapter)
2. Start midiator.py (adjust the MIDI port if required, by choosing the correct number as first parameter).
3. On the Rytm, export the song you want with the "SYSEX DUMP / SYSEX SAVE" menu.
4. The song should then show up on the Midiator screen.
5. Hit play on the Rytm to start sending the MIDI clock messages, this should foreward the song on the screen.

There is also a simulator.py script with an example SYSEX song that can be used to simulate the MIDI messages the Rytm sends.
1. Use hardware or software to create a MIDI loop, so the midiator.py and simulator.py are on the same MIDI bus.
2. Start both applications.
3. On the Simulator window hit "x" and "Enter" to send the SYSEX song stored in song.syx.
4. Hit "s" and "Enter" to start the MIDI clock.
5. For other available commands, you can hit "?" and "Enter".
