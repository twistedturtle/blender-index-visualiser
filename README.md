# Index Visualiser
Show the indices of mesh components in a readable manner. Works with verts, edges and faces.

The selection mode determines which indices are displayed. The other controls are found in the Overlay menu when in EDIT mode, under the Dev header. 

<img src="pics/screenshot.png" width="600">

Two keyboard shortcuts are defined by default.

F5 - Reload scripts <br>
F6 - Toggle labels

If you reload scripts normally whilst the labels are displayed, then you'll lose the reference to the draw callback. This means you won't be able to turn the labels off until you restart blender. 

The custom reload scripts operator (F5) simply removes the callback, then reloads scripts using `bpy.ops.script.reload()` (the normal method) and should it be necessary re-adds the callback afterwards. 

### Install

Copy `index-visualiser.py` to the blender addon directory, or use the install button in the preferences.

Arch based distros -  An AUR PKGBUILD may be forthcoming.


### Questions/Bugs/Issues/Feature requests etc
If you have any questions or feedback etc, please open an issue.
