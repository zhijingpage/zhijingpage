In-hand rotation. — original motion study for Zhi Jing

The hand has 15 articulated phalanges. The finger gait, cube movement and wrist
tilt are keyframed in the same coordinate system. The square block has fourfold
symmetry, so successive quarter turns make a seamless loop.

To regenerate the 4-second, 24-fps film with Blender 4.5 and FFmpeg:
  blender -b --factory-startup -P studio.py -- --out frames --start 1 --end 96 --w 896 --h 784 --samples 24 --save in-hand-rotation.blend
  ffmpeg -framerate 24 -start_number 1 -i frames/%04d.png -frames:v 96 -an -c:v libx264 -crf 19 -preset slow -pix_fmt yuv420p -movflags +faststart in-hand-rotation.mp4
Add --device METAL to the Blender script arguments for an Apple GPU.
