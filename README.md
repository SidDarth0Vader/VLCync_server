# VLCync server
VLCync server component to host [VLCync](https://github.com/SidDarth0Vader/VLCync) watch party [VLC media player](https://github.com/videolan/vlc)

## Features
These features allow propogation of any one party member's inputs to all other members
* Play/Pause
* Seeking
* Resume play from where you left off (As long as the server remains active through the session)

## Usage

* Run the VLCync executable
* Provide a username, VLCync_server IP and port and password generated by the VLCync_server exectuable
* Navigate to video file to play
* Vote to start the show and await other party members!

## Build instructions

* Install the requirements file a new environment(preferably)

* Run the following command in that environment
```sh
pyinstaller main.py -F -n VLCync_server --clean --codesign-identity VLCync_server
```

* Clear the build directory before rebuilding the project