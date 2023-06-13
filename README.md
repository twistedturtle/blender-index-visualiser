# Index Visualiser
Show the indices of mesh components in a readable manner. Works with verts, edges and faces.

The selection mode determines which indices are displayed. The other controls are found in the Overlay menu when in EDIT mode, under the Dev header. 

<img src="pics/screenshot.png" width="600">

Two keyboard shortcuts are defined by default:

F5 - Reloads scripts (whilst modal operator is activated)* <br>
F6 - Toggles display of index labels

*You can't reload scripts whilst a modal operator is running. This stops the modal if it's running, reloads the scripts, and restarts the modal if it was running before. Works any other time too.

### Install

Copy `index-visualiser.py` to the blender addon directory, or use the install button in the preferences.

Arch based distros -  An AUR PKGBUILD may be forthcoming.


### Questions/Bugs/Issues/Feature requests etc
If you have any questions or feedback etc please open an issue.
